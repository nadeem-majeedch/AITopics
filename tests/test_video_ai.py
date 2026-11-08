"""Offline tests for the video AI section.

Every expected number is computed by hand in the test, not copied from a lab run, so a
changed formula fails here instead of silently changing a course number. Nothing downloads
weights, trains a model, or needs the generated ``data/video`` directory: videos are written
to a temporary folder from the section's own deterministic generator.

Run from the repository root:

    python -m unittest tests.test_video_ai -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "projects" / "video-ai"))

from video_core import (  # noqa: E402
    actions,
    counting,
    garments,
    labels,
    metrics,
    synth,
    tracking,
    video,
)


def box(x1, y1, x2, y2):
    return [float(x1), float(y1), float(x2), float(y2)]


def gt(frame, track_id, cls, b):
    return {"frame": frame, "track_id": track_id, "class": cls, "box": b}


class VideoIOTests(unittest.TestCase):
    def test_write_read_roundtrip_and_checksum(self):
        frames = [np.full((64, 64, 3), value, np.uint8) for value in (10, 60, 120, 200)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clip.mp4"
            video.write_video(path, frames, fps=10.0, size=(64, 64))
            info = video.probe(path, count_frames=True)
            self.assertEqual(info.frame_count, 4)
            self.assertAlmostEqual(info.fps, 10.0, places=1)
            self.assertEqual((info.width, info.height), (64, 64))

            read = [frame for _, _, frame in video.iter_frames(path)]
            self.assertEqual(len(read), 4)
            # Lossy codecs keep the brightness ordering even if exact values shift.
            means = [float(frame.mean()) for frame in read]
            self.assertEqual(means, sorted(means))

            self.assertEqual(video.checksum(path), video.checksum(path))

    def test_odd_dimensions_are_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(video.VideoError):
                video.write_video(Path(tmp) / "odd.mp4", [np.zeros((5, 5, 3), np.uint8)],
                                  fps=5.0, size=(5, 5))

    def test_unsupported_codec_is_a_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(video.VideoError) as ctx:
                video.VideoWriter(Path(tmp) / "x.mp4", 10.0, (64, 64), fourcc="avc1")
            self.assertIn("unsupported fourcc", ctx.exception.reason)

    def test_iter_frames_stride_uses_source_indices(self):
        frames = [np.full((32, 32, 3), i * 8, np.uint8) for i in range(10)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clip.mp4"
            video.write_video(path, frames, fps=10.0, size=(32, 32))
            indices = [index for index, _, _ in video.iter_frames(path, stride=3)]
            self.assertEqual(indices, [0, 3, 6, 9])
            stamps = [stamp for _, stamp, _ in video.iter_frames(path, stride=3)]
            for stamp, expected in zip(stamps, [0.0, 0.3, 0.6, 0.9]):
                self.assertAlmostEqual(stamp, expected, places=6)

    def test_contact_sheet_shape(self):
        frames = [np.zeros((90, 160, 3), np.uint8) for _ in range(5)]
        sheet = video.contact_sheet(frames, cols=3, thumb=(80, 45), pad=2)
        self.assertEqual(sheet.shape[0], 2 * (45 + 2) + 2)
        self.assertEqual(sheet.shape[1], 3 * (80 + 2) + 2)


class BoxAndAnnotationTests(unittest.TestCase):
    def test_coco_roundtrip(self):
        original = box(10, 20, 60, 80)
        self.assertEqual(labels.from_coco_box(labels.to_coco_box(original)), original)

    def test_yolo_roundtrip_within_tolerance(self):
        original = box(10, 20, 60, 80)
        back = labels.from_yolo(labels.to_yolo(original, 100, 200), 100, 200)
        for a, b in zip(original, back):
            self.assertAlmostEqual(a, b, places=6)

    def test_validation_flags_bad_boxes(self):
        records = [{"frame": 0, "objects": [
            {"track_id": 1, "class": "car", "box": box(0, 0, 0, 0)},        # degenerate
            {"track_id": 2, "class": "truck", "box": box(50, 40, 20, 10)},  # inverted
            {"track_id": 3, "class": "aeroplane", "box": box(1, 1, 9, 9)},  # unknown class
        ]}]
        report = labels.validate_records(records, width=100, height=100)
        self.assertFalse(report["ok"])
        self.assertEqual(report["objects"], 3)
        problems = " | ".join(report["problems"])
        self.assertIn("non-positive box", problems)
        self.assertIn("unknown class", problems)

    def test_video_split_has_no_shared_video(self):
        items = [{"video": f"v{i}", "frame": f} for i in range(10) for f in range(4)]
        splits = labels.split_by_video(items, fractions=(0.6, 0.2, 0.2), seed=0)
        report = labels.video_leakage(splits)
        self.assertFalse(report["leaky"])
        self.assertEqual(sum(report["videos"].values()), 10)

    def test_frame_split_leakage_is_detected(self):
        items = [{"video": f"v{i}", "frame": f} for i in range(4) for f in range(3)]
        leaky = {"train": items[:6], "test": items[6:]}
        # Frame indices restart per video, so a frame-level split shares frame ids.
        self.assertTrue(labels.frame_split_leakage(items, leaky)["leaky"])


class MetricTests(unittest.TestCase):
    def test_iou_hand_computed(self):
        self.assertAlmostEqual(metrics.iou(box(0, 0, 10, 10), box(5, 0, 15, 10)), 0.5 / 1.5)
        self.assertEqual(metrics.iou(box(0, 0, 10, 10), box(20, 20, 30, 30)), 0.0)
        self.assertAlmostEqual(metrics.iou(box(0, 0, 10, 10), box(0, 0, 10, 10)), 1.0)

    def test_matching_is_class_aware(self):
        detections = [metrics.Detection(box(0, 0, 10, 10), 0, 0.9)]
        truth = [{"box": box(0, 0, 10, 10), "label": 1}]
        matches, unmatched_det, unmatched_gt, _ = metrics.match_frame(detections, truth)
        self.assertEqual(matches, [])
        self.assertEqual(len(unmatched_det), 1)
        self.assertEqual(len(unmatched_gt), 1)

    def test_average_precision_hand_computed(self):
        # TP, FP, TP with two ground truths: recall 0.5 at precision 1.0, then recall 1.0
        # at precision 2/3. All-point AP = 0.5*1.0 + 0.5*(2/3) = 0.8333...
        pairs = [(0.9, True), (0.8, False), (0.7, True)]
        self.assertAlmostEqual(metrics.average_precision(pairs, n_truth=2), 5 / 6, places=6)
        self.assertEqual(metrics.average_precision([], n_truth=3), 0.0)
        self.assertNotEqual(metrics.average_precision([], n_truth=0),
                            metrics.average_precision([], n_truth=0))  # NaN

    def test_detection_report_perfect_detector(self):
        frames = []
        for i in range(3):
            truth = [{"box": box(10, 10, 30, 30), "label": 0}]
            dets = [metrics.Detection(box(10, 10, 30, 30), 0, 0.9)]
            frames.append((dets, truth))
        report = metrics.detection_report(frames, num_classes=4,
                                         class_names=list(labels.LABELS))
        self.assertAlmostEqual(report["map50"], 1.0)
        self.assertEqual(report["precision"], 1.0)
        self.assertEqual(report["recall"], 1.0)

    def test_counting_report_tallies_by_class_and_direction(self):
        truth = [{"class": "car", "direction": "positive"},
                 {"class": "bus", "direction": "negative"}]
        found = [{"class": "car", "direction": "positive"},
                 {"class": "car", "direction": "negative"}]
        report = metrics.counting_report(truth, found)
        self.assertFalse(report["exact"])
        self.assertEqual(report["per_class_direction"]["car:positive"],
                         {"expected": 1, "counted": 1})
        self.assertEqual(report["absolute_error"], 2)

    def test_mota_penalises_id_switch(self):
        truth = [[{"box": box(0, 0, 10, 10), "label": 0, "track_id": 7}] for _ in range(2)]
        predictions = [
            [{"box": box(0, 0, 10, 10), "label": 0, "track_id": 1}],
            [{"box": box(1, 0, 11, 10), "label": 0, "track_id": 2}],
        ]
        report = metrics.tracking_report(list(zip(predictions, truth)))
        self.assertEqual(report["id_switches"], 1)
        self.assertAlmostEqual(report["mota"], 1.0 - 1 / 2)


class TrackerTests(unittest.TestCase):
    def _sequence(self, frames=10, step=3.0, gap=None, ids=(1,)):
        """Detections for vehicles moving right at ``step`` px/frame, optional dropout."""
        out = []
        for f in range(frames):
            dets = []
            for i, start in enumerate(ids):
                if gap and gap[0] <= f < gap[1] and i == 0:
                    continue
                x = 10 + start + step * f
                dets.append(metrics.Detection(box(x, 100, x + 40, 140), 0 if i == 0 else 1,
                                              0.9))
            out.append(dets)
        return out

    def test_one_id_per_object(self):
        tracks = tracking.track_detections(self._sequence(ids=(0, 120)))
        ids = {p["track_id"] for frame in tracks for p in frame}
        self.assertEqual(len(ids), 2)

    def test_short_occlusion_keeps_the_id(self):
        tracks = tracking.track_detections(self._sequence(gap=(4, 7)), max_age=6)
        ids = {p["track_id"] for frame in tracks for p in frame}
        self.assertEqual(len(ids), 1, f"occlusion created a new id: {ids}")

    def test_long_occlusion_breaks_the_id(self):
        tracks = tracking.track_detections(self._sequence(frames=20, gap=(4, 16)), max_age=6)
        ids = {p["track_id"] for frame in tracks for p in frame}
        self.assertEqual(len(ids), 2, "a 12-frame gap should outlast max_age=6")

    def test_duplicate_boxes_collapse_to_one_track(self):
        frames = []
        for f in range(8):
            x = 10 + 3 * f
            frames.append([
                metrics.Detection(box(x, 100, x + 40, 140), 0, 0.90),
                metrics.Detection(box(x + 2, 102, x + 42, 142), 1, 0.85),
            ])
        tracks = tracking.track_detections(frames)
        ids = {p["track_id"] for frame in tracks for p in frame}
        self.assertEqual(len(ids), 1)

    def test_tracker_ignores_ground_truth(self):
        # Feeding an empty detection list must produce no tracks, whatever the truth is.
        tracks = tracking.track_detections([[] for _ in range(5)])
        self.assertTrue(all(frame == [] for frame in tracks))


class CountingTests(unittest.TestCase):
    def test_direction_convention_for_vertical_line(self):
        counter = counting.LineCounter((100, 0), (100, 200))
        # Right of a top-to-bottom line is positive.
        self.assertGreater(counter.side((150, 100)), 0)
        self.assertLess(counter.side((50, 100)), 0)

    def test_crossing_counts_once_per_track(self):
        counter = counting.LineCounter((100, 0), (100, 200))
        events = []
        for f, x in enumerate([80, 90, 101, 120, 130]):
            events += counter.update([{"track_id": 3, "box": box(x, 150, x + 20, 190),
                                       "label": 0, "class": "car"}], f)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].direction, "positive")
        self.assertEqual(len(counter.events), 1)

    def test_no_crossing_when_track_stays_put(self):
        counter = counting.LineCounter((100, 0), (100, 200))
        for f in range(5):
            counter.update([{"track_id": 1, "box": box(20, 150, 40, 190),
                             "label": 0, "class": "car"}], f)
        self.assertEqual(counter.tally(), {})

    def test_anchor_choice_changes_the_moment_not_the_rule(self):
        bottom = counting.LineCounter((100, 0), (100, 200), anchor="bottom")
        centre = counting.LineCounter((100, 0), (100, 200), anchor="center")
        track = {"track_id": 1, "box": box(85, 150, 105, 190), "label": 0, "class": "car"}
        # Bottom-centre is the road contact point; centre is halfway up the box. For this
        # box they share an x, so the difference has to be shown on y.
        self.assertEqual(bottom.anchor_point(track["box"]), (95.0, 190.0))
        self.assertEqual(centre.anchor_point(track["box"]), (95.0, 170.0))

    def test_flow_arithmetic(self):
        flow = counting.flow_summary({"car:positive": 4, "bus:negative": 2}, duration_s=6.0)
        self.assertEqual(flow["total"], 6)
        self.assertAlmostEqual(flow["rate_per_s"], 1.0, places=6)
        self.assertAlmostEqual(flow["per_hour"], 3600.0, places=1)
        self.assertTrue(flow["extrapolated"])

    def test_speed_estimate_is_per_second_not_per_frame(self):
        tracks = []
        for f in range(10):
            x = 10 + 5 * f
            tracks.append([{"track_id": 2, "box": box(x, 100, x + 20, 140),
                            "label": 0, "class": "car"}])
        speeds = counting.speed_estimates(tracks, fps=10.0)
        self.assertAlmostEqual(speeds["tracks"][0]["speed_px_per_s"], 50.0, places=3)
        self.assertNotIn("speed_km_per_h", speeds["tracks"][0])


class SyntheticDataTests(unittest.TestCase):
    def test_traffic_scene_is_deterministic(self):
        first = synth.make_traffic_config(condition="day", seed=5, frames=4)
        second = synth.make_traffic_config(condition="day", seed=5, frames=4)
        a, _ = synth.render_frame(first, 2)
        b, _ = synth.render_frame(second, 2)
        self.assertEqual(video.frame_digest([a]), video.frame_digest([b]))

    def test_different_seeds_render_different_frames(self):
        a, _ = synth.render_frame(synth.make_traffic_config(seed=1, frames=3), 1)
        b, _ = synth.render_frame(synth.make_traffic_config(seed=2, frames=3), 1)
        self.assertNotEqual(video.frame_digest([a]), video.frame_digest([b]))

    def test_ground_truth_boxes_are_inside_the_frame(self):
        cfg = synth.make_traffic_config(seed=3, frames=5)
        for frame_index in range(5):
            _, objects = synth.render_frame(cfg, frame_index)
            for obj in objects:
                x1, y1, x2, y2 = obj["box"]
                self.assertLess(x1, x2)
                self.assertLess(y1, y2)
                self.assertIn(obj["class"], labels.LABELS)

    def test_counting_line_expected_uses_centre_crossing(self):
        cfg = synth.make_traffic_config(direction="right", seed=4, frames=20)
        line = synth.counting_line(cfg)
        self.assertTrue(all(c["direction"] == "positive" for c in line["expected_crossings"]))
        self.assertEqual(line["expected_total"], len(cfg.vehicles))

    def test_action_clip_classes_differ(self):
        right, _ = synth.action_clip("right", seed=0)
        left, _ = synth.action_clip("left", seed=0)
        self.assertEqual(right.shape, left.shape)
        self.assertNotEqual(video.frame_digest(list(right)), video.frame_digest(list(left)))

    def test_garment_dataset_is_balanced_and_in_range(self):
        per_class = len(synth.GARMENT_COLOURS)
        images, categories, colours = synth.garment_dataset(n_per_class=per_class, seed=1)
        self.assertEqual(images.shape[0], per_class * len(synth.GARMENT_CATEGORIES))
        self.assertEqual(np.bincount(categories).min(), per_class)
        self.assertGreaterEqual(float(images.min()), 0.0)
        self.assertLessEqual(float(images.max()), 1.0)
        # Every colour appears at least once, because the generator cycles through them.
        self.assertEqual(len(set(colours.tolist())), len(synth.GARMENT_COLOURS))


class TensorAndPerturbationTests(unittest.TestCase):
    def test_frame_tensor_shape_and_range(self):
        frame = np.full((360, 640, 3), 128, np.uint8)
        from video_core import detect

        converted = detect.frame_to_tensor(frame)
        self.assertEqual(tuple(converted.shape), (1, 3, detect.INPUT_H, detect.INPUT_W))
        self.assertGreaterEqual(float(converted.min()), 0.0)
        self.assertLessEqual(float(converted.max()), 1.0)

    def test_action_tensor_shapes(self):
        clips = np.zeros((2, 8, 64, 64), np.float32)
        self.assertEqual(tuple(actions._to_clip_tensor(clips).shape), (2, 8, 1, 64, 64))
        frames = np.zeros((5, 64, 64), np.float32)
        self.assertEqual(tuple(actions._to_tensor(frames).shape), (5, 1, 64, 64))

    def test_garment_perturbation_stays_in_range(self):
        images = np.random.default_rng(0).random((4, 48, 48, 3)).astype(np.float32)
        for kwargs in ({"brightness": 0.5}, {"brightness": 2.0}, {"occlusion": 0.5},
                       {"background": 0.5}):
            out = garments.perturb(images, seed=1, **kwargs)
            self.assertEqual(out.shape, images.shape)
            self.assertGreaterEqual(float(out.min()), 0.0)
            self.assertLessEqual(float(out.max()), 1.0)

    def test_as_float01_accepts_uint8_and_float(self):
        uint8_image = np.full((4, 4, 3), 200, np.uint8)
        self.assertAlmostEqual(float(garments.as_float01(uint8_image).max()), 200 / 255, places=5)
        float_image = np.full((4, 4, 3), 0.5, np.float32)
        self.assertAlmostEqual(float(garments.as_float01(float_image).max()), 0.5, places=5)

    def test_detector_param_count_is_stable(self):
        from video_core import detect

        model = detect.TinyDetector()
        count = sum(p.numel() for p in model.parameters())
        self.assertGreater(count, 100_000)
        self.assertLess(count, 200_000)


if __name__ == "__main__":
    unittest.main()
