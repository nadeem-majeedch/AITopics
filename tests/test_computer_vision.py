"""Offline tests for the computer vision section.

Every numeric expectation is hand-computed in the test rather than captured from a
run, so a changed formula fails here instead of quietly changing a course number.

Run from the repository root:

    python -m unittest discover -s tests -v

No downloads, GPU, or generated data directory is required: datasets are built in
memory from the section's own seeds.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "projects" / "computer-vision"))

from vision_core import (  # noqa: E402
    annotations,
    cards,
    datasets,
    detection,
    manifest as dataset_manifest,
    detection_train,
    evaluation,
    faces,
    imaging,
    metrics,
    models,
    optimize,
    segmentation,
    similarity,
    training,
)


class TestImaging(unittest.TestCase):
    def test_float_uint8_roundtrip_and_clipping(self):
        arr = np.array([[[0, 128, 255]]], dtype=np.uint8)
        floats = imaging.to_float(arr)
        self.assertAlmostEqual(float(floats.max()), 1.0, places=6)
        self.assertEqual(imaging.as_uint8(floats).tolist(), arr.tolist())
        clipped = imaging.as_uint8(np.array([[[1.4, -0.2, 0.5]]], dtype=np.float32))
        self.assertEqual(clipped[0, 0].tolist(), [255, 0, 128])

    def test_tensor_layout_is_chw(self):
        arr = np.zeros((4, 6, 3), dtype=np.uint8)
        self.assertEqual(tuple(imaging.to_tensor(arr).shape), (3, 4, 6))
        self.assertEqual(imaging.from_tensor(imaging.to_tensor(arr)).shape, arr.shape)

    def test_gray_uses_luma_not_channel_mean(self):
        red = np.zeros((1, 1, 3), dtype=np.uint8)
        red[0, 0, 0] = 255
        blue = np.zeros((1, 1, 3), dtype=np.uint8)
        blue[0, 0, 2] = 255
        self.assertAlmostEqual(float(imaging.to_gray(red)[0, 0]), 0.299, places=3)
        self.assertAlmostEqual(float(imaging.to_gray(blue)[0, 0]), 0.114, places=3)

    def test_resize_takes_width_then_height(self):
        self.assertEqual(imaging.resize(np.zeros((10, 20, 3), dtype=np.uint8), (8, 4)).shape, (4, 8, 3))

    def test_letterbox_preserves_aspect_ratio(self):
        out, mapping = imaging.letterbox(np.zeros((10, 20, 3), dtype=np.uint8), (32, 32))
        self.assertEqual(out.shape, (32, 32, 3))
        self.assertAlmostEqual(mapping["scale"], 1.6, places=6)
        self.assertEqual(tuple(mapping["resized"]), (32, 16))

    def test_normalize_denormalize_roundtrip_and_validation(self):
        arr = np.full((2, 2, 3), 128, dtype=np.uint8)
        restored = imaging.denormalize(imaging.normalize(arr))
        self.assertTrue(np.allclose(restored, imaging.to_float(arr), atol=1e-5))
        with self.assertRaises(ValueError):
            imaging.normalize(arr, mean=(0.5,), std=(0.5,))
        with self.assertRaises(ValueError):
            imaging.normalize(arr, std=(0.5, 0.5, 0.0))

    def test_augmentation_is_reproducible_with_a_seed(self):
        arr = np.zeros((16, 16, 3), dtype=np.uint8)
        arr[4:10, 4:10] = 200
        config = imaging.AugmentConfig(hflip_p=0.5, rotate_deg=10, max_shift=2, brightness=0.2)
        first = imaging.augment(arr, config, np.random.default_rng(7))
        second = imaging.augment(arr, config, np.random.default_rng(7))
        self.assertTrue(np.array_equal(first, second))

    def test_jpeg_roundtrip_is_lossy(self):
        arr = np.random.default_rng(0).integers(0, 256, size=(16, 16, 3), dtype=np.uint8)
        lossy = imaging.jpeg_roundtrip(arr, quality=20)
        self.assertEqual(lossy.shape, arr.shape)
        self.assertFalse(np.array_equal(lossy, arr))


class TestAnnotations(unittest.TestCase):
    def test_box_conversions_roundtrip(self):
        box = (10.0, 20.0, 40.0, 60.0)
        self.assertEqual(annotations.xyxy_to_xywh(box), (10.0, 20.0, 30.0, 40.0))
        self.assertEqual(annotations.xywh_to_xyxy(annotations.xyxy_to_xywh(box)), box)
        self.assertEqual(annotations.cxcywh_to_xyxy(annotations.xyxy_to_cxcywh(box)), box)

    def test_iou_hand_computed(self):
        a, b = (0.0, 0.0, 10.0, 10.0), (5.0, 5.0, 15.0, 15.0)
        # intersection 25; union 100 + 100 - 25 = 175
        self.assertAlmostEqual(annotations.box_iou(a, b), 25.0 / 175.0, places=6)
        self.assertEqual(annotations.box_iou(a, (20.0, 20.0, 30.0, 30.0)), 0.0)
        self.assertAlmostEqual(annotations.box_iou(a, a), 1.0, places=6)

    def test_yolo_roundtrip_and_rejection(self):
        anns = [annotations.Annotation(1, (10.0, 10.0, 30.0, 20.0))]
        parsed = annotations.from_yolo_lines(annotations.to_yolo_lines(anns, 64, 64), 64, 64)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].class_id, 1)
        for got, want in zip(parsed[0].box, anns[0].box):
            self.assertAlmostEqual(got, want, places=3)
        with self.assertRaises(ValueError):
            annotations.from_yolo_lines(["0 1.5 0.5 0.2 0.2"], 64, 64)
        with self.assertRaises(ValueError):
            annotations.from_yolo_lines(["0 0.5 0.5"], 64, 64)

    def test_coco_roundtrip_keeps_boxes_upright(self):
        """Regression: the reader once applied xyxy->xywh to an already-xywh bbox,
        inverting every box and destroying every detection target."""
        images = {"a": np.zeros((32, 32, 3), dtype=np.uint8)}
        anns = {"a": [annotations.Annotation(2, (4.0, 6.0, 24.0, 18.0))]}
        data = annotations.to_coco(images, anns, ("circle", "square", "triangle"))
        self.assertEqual([c["id"] for c in data["categories"]], [1, 2, 3])
        self.assertEqual(data["annotations"][0]["category_id"], 3)
        parsed, names = annotations.from_coco(data)
        self.assertEqual(names, ["circle", "square", "triangle"])
        self.assertEqual(parsed["a"][0].class_id, 2)
        for got, want in zip(parsed["a"][0].box, anns["a"][0].box):
            self.assertAlmostEqual(got, want, places=6)

    def test_validation_reports_degenerate_out_of_range_and_bad_class(self):
        report = annotations.validate_annotations(
            [
                annotations.Annotation(0, (0.0, 0.0, 10.0, 10.0)),
                annotations.Annotation(0, (5.0, 5.0, 5.5, 5.5)),
                annotations.Annotation(7, (0.0, 0.0, 5.0, 5.0)),
                annotations.Annotation(1, (30.0, 30.0, 50.0, 50.0)),
            ],
            32,
            32,
            3,
        )
        self.assertEqual(report["n_input"], 4)
        # Out-of-range boxes are reported and clipped, not silently dropped.
        self.assertEqual(report["n_kept"], 2)
        self.assertEqual(len(report["problems"]), 3)
        self.assertEqual(tuple(report["kept"][1].box), (30.0, 30.0, 32.0, 32.0))


class TestDetectionMetrics(unittest.TestCase):
    def test_average_precision_all_point_and_eleven_point(self):
        # precision 1.0, 0.5, 0.667 at recall 0.5, 0.5, 1.0
        self.assertAlmostEqual(metrics.average_precision([0.9, 0.8, 0.7], [1, 0, 1], 2), 0.833333, places=5)
        self.assertAlmostEqual(metrics.average_precision([0.9, 0.8, 0.7], [1, 0, 1], 2, method="11"), 0.848485, places=5)
        self.assertEqual(metrics.average_precision([0.9], [1], 0), 0.0)
        self.assertEqual(metrics.average_precision([], [], 3), 0.0)

    def test_perfect_detector_scores_one(self):
        result = metrics.DetectionResult(
            predictions=[annotations.Annotation(0, (0.0, 0.0, 10.0, 10.0), score=0.9)],
            ground_truth=[annotations.Annotation(0, (0.0, 0.0, 10.0, 10.0))],
        )
        report = metrics.evaluate_detections([result], ["a"])
        self.assertEqual((report["tp"], report["fp"], report["fn"]), (1, 0, 0))
        self.assertAlmostEqual(report["precision"], 1.0)
        self.assertAlmostEqual(report["recall"], 1.0)
        self.assertAlmostEqual(metrics.mean_average_precision([result], ["a"])["map"], 1.0, places=6)

    def test_one_ground_truth_matches_once(self):
        truth = [annotations.Annotation(0, (0.0, 0.0, 10.0, 10.0))]
        predictions = [
            annotations.Annotation(0, (0.0, 0.0, 10.0, 10.0), score=0.9),
            annotations.Annotation(0, (0.0, 0.0, 10.0, 10.0), score=0.8),
        ]
        report = metrics.evaluate_detections([metrics.DetectionResult(predictions, truth)], ["a"])
        self.assertEqual((report["tp"], report["fp"]), (1, 1))

    def test_class_mismatch_is_not_a_match(self):
        result = metrics.DetectionResult(
            [annotations.Annotation(1, (0.0, 0.0, 10.0, 10.0), score=0.9)],
            [annotations.Annotation(0, (0.0, 0.0, 10.0, 10.0))],
        )
        report = metrics.evaluate_detections([result], ["a", "b"])
        self.assertEqual((report["tp"], report["fp"], report["fn"]), (0, 1, 1))

    def test_nms_keeps_best_box_per_duplicate(self):
        kept = metrics.non_max_suppression(
            [
                annotations.Annotation(0, (0.0, 0.0, 10.0, 10.0), score=0.9),
                annotations.Annotation(0, (1.0, 1.0, 11.0, 11.0), score=0.8),
                annotations.Annotation(0, (50.0, 50.0, 60.0, 60.0), score=0.7),
            ],
            iou_threshold=0.45,
        )
        self.assertEqual(len(kept), 2)
        self.assertAlmostEqual(kept[0].score, 0.9)

    def test_pr_curve_recall_is_monotone(self):
        results = [
            metrics.DetectionResult(
                [annotations.Annotation(0, (0.0, 0.0, 10.0, 10.0), score=s) for s in (0.9, 0.7, 0.5)],
                [
                    annotations.Annotation(0, (0.0, 0.0, 10.0, 10.0)),
                    annotations.Annotation(0, (40.0, 40.0, 50.0, 50.0)),
                ],
            )
        ]
        recalls = [p["recall"] for p in metrics.pr_curve(results, ["a"])]
        self.assertEqual(recalls, sorted(recalls))
        self.assertLessEqual(max(recalls), 0.5)


class TestSegmentationMetrics(unittest.TestCase):
    def test_all_background_control(self):
        truth = np.zeros((4, 4), dtype=np.uint8)
        truth[0, :] = 1  # 4 object pixels, 12 background
        report = metrics.segmentation_report(np.zeros((4, 4), dtype=np.uint8), truth, ["background", "object", "shadow"])
        self.assertAlmostEqual(report["pixel_accuracy"], 12 / 16, places=6)
        self.assertAlmostEqual(report["mean_iou"], (0.75 + 0.0) / 2, places=6)
        self.assertAlmostEqual(report["per_class_iou"]["object"], 0.0)

    def test_perfect_mask_scores_one(self):
        truth = np.zeros((4, 4), dtype=np.uint8)
        truth[0, :] = 1
        report = metrics.segmentation_report(truth, truth, ["background", "object"])
        self.assertAlmostEqual(report["mean_iou"], 1.0, places=6)
        self.assertAlmostEqual(report["pixel_accuracy"], 1.0, places=6)

    def test_shape_mismatch_raises(self):
        with self.assertRaises(ValueError):
            metrics.confusion_matrix(np.zeros((2, 2), dtype=np.uint8), np.zeros((3, 3), dtype=np.uint8), 2)

    def test_boundary_f1_is_strict_about_edges(self):
        truth = np.zeros((8, 8), dtype=np.uint8)
        truth[2:6, 2:6] = 1
        fat = np.zeros((8, 8), dtype=np.uint8)
        fat[1:7, 1:7] = 1
        self.assertAlmostEqual(metrics.boundary_f1(truth, truth), 1.0, places=6)
        self.assertLess(metrics.boundary_f1(fat, truth, tolerance=0), 1.0)


class TestClassificationMetrics(unittest.TestCase):
    def test_report_hand_computed(self):
        report = metrics.classification_report([0, 0, 1, 1], [0, 1, 1, 1], ["a", "b"])
        self.assertAlmostEqual(report["accuracy"], 0.75)
        self.assertAlmostEqual(report["per_class"]["a"]["recall"], 0.5)
        self.assertAlmostEqual(report["per_class"]["b"]["precision"], 2 / 3, places=6)
        self.assertAlmostEqual(report["per_class"]["b"]["recall"], 1.0)

    def test_ece_hand_computed(self):
        self.assertAlmostEqual(metrics.expected_calibration_error([1.0, 0.0], [1, 0], n_bins=2), 0.0, places=6)
        # confident and right everywhere -> 0; overconfident bin -> |0.6 - 0.5|
        self.assertAlmostEqual(metrics.expected_calibration_error([0.6, 0.6], [1, 0]), 0.1, places=6)


class TestFaceMetrics(unittest.TestCase):
    def test_far_and_frr_at_a_threshold(self):
        row = metrics.verification_metrics([0.9, 0.4], [True, False], threshold=0.5)
        self.assertAlmostEqual(row["far"], 0.0)
        self.assertAlmostEqual(row["frr"], 0.0)
        wrong = metrics.verification_metrics([0.9, 0.4], [False, True], threshold=0.5)
        self.assertAlmostEqual(wrong["far"], 1.0)
        self.assertAlmostEqual(wrong["frr"], 1.0)

    def test_eer_on_separable_scores(self):
        result = metrics.equal_error_rate([0.95, 0.92, 0.9, 0.2, 0.15, 0.1], [True, True, True, False, False, False])
        self.assertAlmostEqual(result["eer"], 0.0, places=6)

    def test_identification_rank1(self):
        report = metrics.identification_metrics(
            np.array([[1.0, 0.0]]), ["a"], np.array([[1.0, 0.0], [0.0, 1.0]]), ["a", "b"]
        )
        self.assertAlmostEqual(report["rank1_accuracy"], 1.0)


class TestDatasets(unittest.TestCase):
    def test_group_split_never_shares_a_source(self):
        records = datasets.make_classification_dataset(n_sources=12, size=16, seed=0, variants_per_source=2)
        splits = datasets.group_split(records, seed=0)
        self.assertEqual({r.source_id for r in splits["train"]} & {r.source_id for r in splits["test"]}, set())
        self.assertEqual(sum(len(v) for v in splits.values()), len(records))

    def test_random_split_leaks_and_group_split_does_not(self):
        records = datasets.make_classification_dataset(n_sources=10, size=16, seed=0, variants_per_source=3)
        audit = datasets.audit_leakage(datasets.random_split(records, seed=0))
        self.assertTrue(audit["hard_leaky"])
        self.assertGreater(audit["n_shared_sources"], 0)
        self.assertFalse(datasets.audit_leakage(datasets.group_split(records, seed=0))["hard_leaky"])

    def test_stratified_group_split_keeps_every_class_in_each_split(self):
        records = datasets.make_object_dataset(n_sources=12, size=16, seed=1, variants_per_source=2)
        splits = datasets.stratified_group_split(records, seed=1)
        source_sets = {name: {record.source_id for record in part} for name, part in splits.items()}
        self.assertFalse(source_sets["train"] & source_sets["val"])
        self.assertFalse(source_sets["train"] & source_sets["test"])
        self.assertFalse(source_sets["val"] & source_sets["test"])
        for name, part in splits.items():
            present = {record.label for record in part}
            self.assertEqual(present, set(range(len(datasets.OBJECT_CLASSES))), name)

    def test_dhash_is_identical_for_identical_images(self):
        records = datasets.make_classification_dataset(n_sources=3, size=16, seed=0, variants_per_source=1)
        self.assertEqual(datasets.hamming(datasets.dhash(records[0].image), datasets.dhash(records[0].image)), 0)

    def test_rendered_shapes_are_distinct_and_non_constant(self):
        rng = np.random.default_rng(0)
        images = [datasets.render_classification_sample(kind, 24, rng)[0] for kind in datasets.SHAPE_CLASSES]
        for image in images:
            self.assertEqual(image.shape, (24, 24, 3))
            self.assertGreater(float(np.std(image)), 5.0, "image is nearly constant")
        self.assertGreater(datasets.hamming(datasets.dhash(images[0]), datasets.dhash(images[1])), 4)


class TestTrainingAndModels(unittest.TestCase):
    def test_model_output_shape_and_size(self):
        import torch

        model = models.TinyCNN(num_classes=4, width=8)
        self.assertEqual(tuple(model(torch.zeros(2, 3, 32, 32)).shape), (2, 4))
        self.assertEqual(models.count_parameters(model), sum(p.numel() for p in model.parameters()))
        self.assertGreater(models.model_disk_bytes(model), 0)

    def test_two_epoch_train_records_history(self):
        records = datasets.make_classification_dataset(n_sources=9, size=24, seed=0, variants_per_source=2)
        images = np.stack([r.image for r in records])
        labels = np.array([r.label for r in records])
        history, trained = training.train_classifier(
            models.TinyCNN(num_classes=3, width=8),
            images[:12], labels[:12], images[12:], labels[12:],
            epochs=2, batch_size=6, seed=0, log=False,
        )
        self.assertIs(trained.__class__, models.TinyCNN)
        self.assertEqual(len(history.val_acc), 2)
        self.assertTrue(0.0 <= history.best_val_acc <= 1.0)
        self.assertIn("epochs", history.to_dict())

    def test_dataset_stats_are_per_channel(self):
        images = np.zeros((4, 8, 8, 3), dtype=np.uint8)
        images[..., 0] = 255
        mean, _ = training.dataset_stats(images)
        self.assertAlmostEqual(mean[0], 1.0, places=5)
        self.assertAlmostEqual(mean[1], 0.0, places=5)


class TestHeatmapDetection(unittest.TestCase):
    def test_target_has_a_peak_at_the_box_centre(self):
        heat, size, mask = detection_train.build_heatmap_target(
            [annotations.Annotation(1, (24.0, 24.0, 40.0, 40.0))], 64, 64, 3, stride=4
        )
        self.assertEqual(heat.shape, (3, 16, 16))
        self.assertEqual(np.unravel_index(int(np.argmax(heat[1])), heat[1].shape), (8, 8))
        self.assertAlmostEqual(float(size[0, 8, 8]), 16.0 / 64.0, places=6)
        self.assertGreater(float(mask.sum()), 1.0, "size must be supervised over the bump, not one cell")

    def test_focal_loss_prefers_the_confident_correct_answer(self):
        import torch

        target = torch.zeros((1, 4, 4))
        target[0, 2, 2] = 1.0
        good = torch.full((1, 4, 4), -6.0)
        good[0, 2, 2] = 6.0
        bad = -good
        self.assertLess(
            float(detection_train.centernet_focal_loss(good, target)),
            float(detection_train.centernet_focal_loss(bad, target)),
        )

    def test_decode_requires_a_unique_maximum(self):
        """A flat or saturated map must not produce a box per cell."""
        heat = np.zeros((3, 16, 16), dtype=np.float32)  # sigmoid 0.5 everywhere
        size = np.full((2, 16, 16), 0.25, dtype=np.float32)
        self.assertEqual(detection.decode_heatmap(heat, size, score_threshold=0.3), [])

    def test_decode_turns_a_peak_into_an_in_image_box(self):
        heat = np.full((3, 16, 16), -10.0, dtype=np.float32)
        heat[0, 8, 8] = 5.0
        size = np.zeros((2, 16, 16), dtype=np.float32)
        size[:, 8, 8] = 0.5
        boxes = detection.decode_heatmap(heat, size, stride=4, width=64, height=64, score_threshold=0.3)
        self.assertEqual(len(boxes), 1)
        self.assertEqual(boxes[0].class_id, 0)
        x1, y1, x2, y2 = boxes[0].box
        self.assertGreaterEqual(min(x1, y1), 0.0)
        self.assertLessEqual(max(x2, y2), 64.0)
        self.assertAlmostEqual((x1 + x2) / 2, 34.0, places=3)


class TestFaces(unittest.TestCase):
    def test_faces_are_deterministic_for_a_seed(self):
        a = faces.render_face(faces.DEFAULT_IDENTITIES[0], np.random.default_rng(3), 32)
        b = faces.render_face(faces.DEFAULT_IDENTITIES[0], np.random.default_rng(3), 32)
        self.assertTrue(np.array_equal(a[0], b[0]))
        self.assertEqual(a[1], b[1])

    def test_skin_rule_finds_a_mid_tone_face(self):
        image, _box, _landmarks = faces.render_face(faces.DEFAULT_IDENTITIES[0], np.random.default_rng(0), 48)
        self.assertGreater(int(faces.skin_mask(image).sum()), 100)
        self.assertTrue(faces.detect_face(image)["found"])

    def test_landmark_error_is_zero_against_itself(self):
        _image, _box, truth = faces.render_face(faces.DEFAULT_IDENTITIES[1], np.random.default_rng(1), 48)
        self.assertAlmostEqual(faces.landmark_error(truth, truth), 0.0, places=6)

    def test_embedding_is_unit_norm(self):
        image, box, landmarks = faces.render_face(faces.DEFAULT_IDENTITIES[2], np.random.default_rng(2), 48)
        self.assertAlmostEqual(float(np.linalg.norm(faces.face_embedding(image, box, landmarks))), 1.0, places=4)

    def test_detection_report_audits_every_group(self):
        records = faces.make_face_dataset(per_identity=2, size=40, seed=0)
        report = faces.detection_report(records)
        groups = report.get("per_group") or report.get("by_group")
        self.assertIsNotNone(groups, f"no per-group breakdown in {sorted(report)}")
        self.assertEqual(sum(v["n"] for v in groups.values()), len(records))
        for group in groups.values():
            self.assertTrue(0.0 <= group["recall"] <= 1.0)


class TestSimilarityAndDeployment(unittest.TestCase):
    def test_index_returns_the_query_itself_first(self):
        records = datasets.make_object_dataset(n_sources=6, size=16, seed=0, variants_per_source=1)
        index = similarity.EmbeddingIndex.from_records(records)
        hits = index.search(similarity.histogram_embedding(records[0].image), k=3)
        self.assertAlmostEqual(hits[0].score, 1.0, places=4)

    def test_precision_at_k_is_higher_when_self_matches_are_allowed(self):
        records = datasets.make_object_dataset(n_sources=8, size=16, seed=0, variants_per_source=2)
        index = similarity.EmbeddingIndex.from_records(records)
        with_self = index.precision_at_k(records, k=2, exclude_self=False)
        without_self = index.precision_at_k(records, k=2, exclude_self=True)
        self.assertGreaterEqual(with_self["precision_at_k"], without_self["precision_at_k"])

    def test_benchmark_and_quantization(self):
        import torch

        model = models.TinyCNN(num_classes=3, width=8)
        sample = torch.zeros(2, 3, 32, 32)
        stats = optimize.benchmark_model(model, sample, runs=3)
        self.assertGreater(stats.median_ms, 0.0)
        self.assertGreaterEqual(stats.p90_ms, stats.median_ms)
        with torch.no_grad():
            self.assertEqual(tuple(optimize.quantize_dynamic(model)(sample).shape), (2, 3))

    def test_segmentation_baselines(self):
        records = datasets.make_segmentation_dataset(n_images=3, size=32, seed=0)
        mask = segmentation.threshold_baseline(records[0].image)
        self.assertEqual(mask.shape, (32, 32))
        self.assertTrue(set(np.unique(mask)).issubset({0, 1}))
        control = segmentation.all_background_baseline(records)
        self.assertGreater(control["pixel_accuracy"], 0.5)
        self.assertLess(control["mean_iou"], 0.5)


class TestRobustnessAndCards(unittest.TestCase):
    def test_robustness_suite_reports_every_condition(self):
        records = datasets.make_classification_dataset(n_sources=6, size=24, seed=0, variants_per_source=2)
        images = np.stack([r.image for r in records])
        labels = [int(r.label) for r in records]
        mean, std = training.dataset_stats(images)
        report = evaluation.robustness_suite(models.TinyCNN(num_classes=3, width=8), images, labels, mean, std)
        names = [row["condition"] for row in report["conditions"]]
        self.assertEqual(len(names), 7)
        self.assertIn("clean", names)
        self.assertIn("worst_condition", report)

    def test_model_card_flags_unfilled_placeholders(self):
        rendered = cards.render(cards.MODEL_CARD_TEMPLATE, model_name="m", version="1", date="d", author="a")
        self.assertIn("{{intended_use}}", rendered)
        self.assertIn("Model card: m", rendered)
        self.assertIn("| acc | 0.9 |", cards.metrics_table([{"name": "acc", "value": "0.9", "dataset": "t", "note": ""}]))


class TestDatasetManifest(unittest.TestCase):
    """The P06 generator must prove the data it scored is the data it wrote."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "objects_p06"
        self.records = datasets.make_object_dataset(n_sources=20, size=16, seed=5, variants_per_source=2)
        self.splits = datasets.stratified_group_split(self.records, seed=5)
        datasets.save_split_images(self.splits, self.root, datasets.OBJECT_CLASSES)
        self.payload = dataset_manifest.build_manifest(
            self.root,
            self.splits,
            datasets.OBJECT_CLASSES,
            dataset="objects_p06",
            seed=5,
        )
        dataset_manifest.write_manifest(self.root, self.payload)

    def _codes(self) -> set[str]:
        return {problem["code"] for problem in dataset_manifest.check_dataset(self.root)["problems"]}

    def test_unchanged_dataset_passes(self):
        result = dataset_manifest.check_dataset(self.root)
        self.assertTrue(result["ok"], result["problems"])
        self.assertEqual(result["checked_files"], 40)
        self.assertEqual(result["class_counts"]["test"]["mug"], 2)
        self.assertEqual(len(result["class_counts"]), 3)
        self.assertEqual(result["source_overlap"], {})
        self.assertIn("OK", dataset_manifest.summarize(result)[0])

    def test_missing_image_is_reported(self):
        (self.root / "train" / "00000.png").unlink()
        result = dataset_manifest.check_dataset(self.root)
        self.assertFalse(result["ok"])
        self.assertIn("missing_file", {problem["code"] for problem in result["problems"]})

    def test_modified_image_is_reported(self):
        (self.root / "test" / "00000.png").write_bytes(b"not a png")
        self.assertIn("modified_file", self._codes())

    def test_unexpected_image_is_reported(self):
        (self.root / "test" / "99999.png").write_bytes(b"stray")
        self.assertIn("unexpected_file", self._codes())

    def test_byte_identical_files_are_reported_as_duplicates(self):
        shutil.copyfile(self.root / "train" / "00000.png", self.root / "train" / "00001.png")
        result = dataset_manifest.check_dataset(self.root)
        # Same split: redundant data, reported as a warning but not a failure.
        self.assertIn("duplicate_content", {w["code"] for w in result["warnings"]})

    def test_duplicate_across_splits_fails_the_check(self):
        shutil.copyfile(self.root / "train" / "00000.png", self.root / "test" / "00099.png")
        self.payload["files"]["test/00099.png"] = {
            **self.payload["files"]["train/00000.png"],
            "split": "test",
        }
        dataset_manifest.write_manifest(self.root, self.payload)
        self.assertIn("duplicate_across_splits", self._codes())

    def test_duplicate_source_ids_across_labels_are_reported(self):
        entries = list(self.payload["files"].items())
        first_relative, first = entries[0]
        other = next(
            entry
            for _, entry in entries
            if entry["label"] != first["label"] and entry["source_id"] != first["source_id"]
        )
        first["source_id"] = other["source_id"]
        dataset_manifest.write_manifest(self.root, self.payload)
        self.assertIn("source_label_conflict", self._codes())

    def test_missing_class_is_reported(self):
        result = dataset_manifest.check_dataset(
            self.root, classes=list(datasets.OBJECT_CLASSES) + ["laptop"]
        )
        self.assertFalse(result["ok"])
        missing = [p for p in result["problems"] if p["code"] == "class_missing"]
        self.assertEqual(len(missing), 3)  # one per split

    def test_source_in_two_splits_is_reported(self):
        source = self.payload["files"]["train/00000.png"]["source_id"]
        shutil.copyfile(self.root / "train" / "00000.png", self.root / "test" / "00099.png")
        self.payload["files"]["test/00099.png"] = {
            **self.payload["files"]["train/00000.png"],
            "split": "test",
            "source_id": source,
        }
        dataset_manifest.write_manifest(self.root, self.payload)
        result = dataset_manifest.check_dataset(self.root)
        self.assertIn("split_overlap", {p["code"] for p in result["problems"]})
        self.assertIn(source, result["source_overlap"])

    def test_declared_split_count_mismatch_is_reported(self):
        self.payload["splits"]["train"] += 1
        dataset_manifest.write_manifest(self.root, self.payload)
        self.assertIn("split_count_mismatch", self._codes())

    def test_manifest_is_deterministic(self):
        second = Path(self._tmp.name) / "second"
        datasets.save_split_images(self.splits, second, datasets.OBJECT_CLASSES)
        rebuilt = dataset_manifest.build_manifest(
            second,
            self.splits,
            datasets.OBJECT_CLASSES,
            dataset="objects_p06",
            seed=5,
        )
        self.assertEqual(rebuilt, self.payload)

    def test_missing_manifest_is_reported(self):
        (self.root / dataset_manifest.MANIFEST_NAME).unlink()
        result = dataset_manifest.check_dataset(self.root)
        self.assertFalse(result["ok"])
        self.assertEqual(result["problems"][0]["code"], "manifest_missing")


if __name__ == "__main__":
    unittest.main()
