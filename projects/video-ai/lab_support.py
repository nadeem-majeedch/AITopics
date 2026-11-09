"""Shared plumbing for the video AI labs: paths, data loading, cached models, reports.

Nothing here is teaching material. Each lab imports this so that its own file is about the
experiment rather than about ``sys.path`` and cache filenames.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from video_core import detect, labels as labels_mod, metrics, synth, video  # noqa: E402
from video_core.report import check, read_json, rule, table, write_json  # noqa: E402

DATA = HERE / "data" / "video"
OUT = HERE / "outputs"
CACHE = OUT / "cache"

# One thread keeps timings comparable between runs and between machines that are busy with
# something else. Set VIDEO_AI_THREADS to override when measuring throughput properly.
_THREADS = int(os.environ.get("VIDEO_AI_THREADS", "1"))
try:  # torch is optional for the labs that only use OpenCV
    import torch

    torch.set_num_threads(max(1, _THREADS))
    torch.manual_seed(0)
except Exception:  # pragma: no cover - only exercised without torch installed
    torch = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


def ensure_data() -> dict:
    """Load ``data/video/manifest.json``, generating the data on first use."""
    manifest_path = DATA / "manifest.json"
    if not manifest_path.exists():
        print(f"  data missing - generating {DATA} (takes a few seconds)")
        sys.path.insert(0, str(HERE / "scripts"))
        import make_video_data  # noqa: PLC0415

        make_video_data.main([])
    return read_json(manifest_path)


_MANIFEST: dict | None = None


def manifest() -> dict:
    global _MANIFEST
    if _MANIFEST is None:
        _MANIFEST = ensure_data()
    return _MANIFEST


def scene(name: str) -> dict:
    for entry in manifest()["videos"]:
        if entry["name"] == name:
            return entry
    raise KeyError(f"unknown video {name!r}; have {[e['name'] for e in manifest()['videos']]}")


def video_path(name: str) -> Path:
    return DATA / scene(name)["file"]


def scenes(split: str | None = None) -> list[dict]:
    entries = manifest()["videos"]
    return [e for e in entries if split is None or e["split"] == split]


def ground_truth(name: str) -> list[dict]:
    """Per-frame ground truth in the format the metric helpers expect."""
    return detect.truth_to_metric(scene(name)["frames_gt"])


def counting_truth(name: str) -> dict:
    return scene(name)["counting_line"]


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------


def training_frames(*, stride: int = 4, limit_per_video: int | None = None,
                    videos: list[str] | None = None) -> list[detect.DetectionSample]:
    """Frames from the *train* split only, with boxes and labels.

    Sampling every ``stride``-th frame is what makes training take seconds rather than
    minutes, and it is honest: neighbouring frames are near-duplicates, so a detector gains
    almost nothing from seeing all of them.
    """
    names = videos or [e["name"] for e in scenes("train")]
    samples: list[detect.DetectionSample] = []
    for name in names:
        entry = scene(name)
        for i, (_, _, frame) in enumerate(video.iter_frames(video_path(name), stride=stride)):
            if limit_per_video is not None and i >= limit_per_video:
                break
            objects = entry["frames_gt"][i * stride]["objects"]
            if not objects:
                continue
            samples.append(detect.DetectionSample(
                frame=frame,
                boxes=[o["box"] for o in objects],
                labels=[labels_mod.LABEL_TO_INDEX[o["class"]] for o in objects],
            ))
    return samples


def train_tiny_detector(*, stride: int = 2, epochs: int = 30, seed: int = 0,
                        width: int = 24, force: bool = False, log: bool = False):
    """Train ``TinyDetector`` from scratch once and cache the weights.

    The cache key contains everything that changes the result - frame stride, epochs, seed,
    width - so a lab that asks for a different model gets a different file instead of a
    silently wrong one. Training from scratch on this machine takes roughly 30-60 seconds;
    every later run loads the cache in under a second.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    key = f"tiny_w{width}_e{epochs}_s{stride}_seed{seed}"
    path = CACHE / f"{key}.pt"
    if path.exists() and not force:
        model = detect.TinyDetector.load(path)
        return model, {"cached": True, "cache_key": key, "epochs": epochs}

    samples = training_frames(stride=stride)
    if not samples:
        raise RuntimeError("no training frames found; run python projects/video-ai/scripts/make_video_data.py")
    if log:
        print(f"  training TinyDetector on {len(samples)} frames ({key})")
    model, history = detect.train_detector(samples, epochs=epochs, seed=seed, width=width,
                                           log=log)
    model.save(path, extra={"key": key, "samples": len(samples), "history": history})
    return model, {"cached": False, "cache_key": key, "epochs": epochs,
                   "samples": len(samples), "history": history}


_SSDLITE = None


def ssdlite(score_threshold: float = 0.30):
    """The COCO-pretrained detector, loaded once per process.

    Returns ``(detector, status)``. ``status["available"]`` is False when the weights cannot
    be downloaded (no network, offline machine), in which case the labs degrade to reporting
    that instead of inventing numbers.
    """
    global _SSDLITE
    if _SSDLITE is None:
        det = detect.SSDLiteDetector(score_threshold=score_threshold)
        ok = det.load()
        _SSDLITE = det
        if not ok:
            print(f"  pretrained weights unavailable: {det.load_error}")
            print("  (the labs that need them will report zero detections and say why)")
    return _SSDLITE, _SSDLITE.info()


def train_traffic_ssdlite(*, epochs: int = 5, stride: int = 2, lr: float = 3e-4,
                          seed: int = 0, force: bool = False, log: bool = True):
    """Fine-tune the COCO detector on vehicle frames, once, and cache the weights.

    This is the expensive step in the section (about 40 s on CPU for five epochs). The cache
    key includes the learning rate and the number of frames, because those change the result
    and a stale-but-loadable checkpoint is worse than a retrain.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    key = f"ssdlite_traffic_e{epochs}_s{stride}_lr{lr:g}_seed{seed}"
    path = CACHE / f"{key}.pt"
    detector = detect.TrafficSSDLite(score_threshold=0.5)
    if path.exists() and not force:
        if detector.load_weights(path):
            return detector, {"cached": True, "cache_key": key, "epochs": epochs}

    if not detector.build():
        raise RuntimeError(f"pretrained weights unavailable: {detector.load_error}")
    samples = training_frames(stride=stride)
    if not samples:
        raise RuntimeError("no training frames found; run python projects/video-ai/scripts/make_video_data.py")
    if log:
        print(f"  fine-tuning SSDLite on {len(samples)} frames, {epochs} epochs ({key})")
    detector, history = detect.finetune_traffic_detector(samples, epochs=epochs, lr=lr,
                                                        seed=seed, log=log)
    detector.save(path, extra={"key": key, "samples": len(samples), "history": history})
    return detector, {"cached": False, "cache_key": key, "epochs": epochs,
                      "samples": len(samples), "history": history}


def detector_params(model) -> int:
    return int(sum(p.numel() for p in model.parameters()))


# ---------------------------------------------------------------------------
# Detections over a video
# ---------------------------------------------------------------------------


def detect_video_records(path, model, *, stride: int = 1, limit: int | None = None,
                         score_threshold: float = 0.5, nms_iou: float = 0.30) -> list[dict]:
    """Run a detector over a video file and return one record per processed frame.

    Defaults are tuned for this section's footage, not invented: ``score_threshold=0.5``
    removes the low-confidence boxes that would otherwise become phantom tracks, and
    ``nms_iou=0.30`` collapses the overlapping duplicates this detector produces for a single
    vehicle. Lab 8 measures what those two choices cost.
    """
    records: list[dict] = []
    for index, stamp, frame in video.iter_frames(path, stride=stride, limit=limit):
        try:
            detections = model.predict(frame, score_threshold=score_threshold,
                                       nms_iou=nms_iou)
        except TypeError:
            # The COCO wrapper keeps its threshold from construction; it takes no kwargs.
            detections = model.predict(frame)
        records.append({"frame": index, "t_s": round(stamp, 3),
                        "detections": [d.as_dict() for d in detections]})
    return records


def detect_scene(name: str, model, *, stride: int = 1, limit: int | None = None,
                 score_threshold: float = 0.5, nms_iou: float = 0.30) -> list[dict]:
    return detect_video_records(video_path(name), model, stride=stride, limit=limit,
                                score_threshold=score_threshold, nms_iou=nms_iou)


def pairs_for_report(name: str, records: list[dict]) -> list[tuple[list, list]]:
    """Align detection records (frame -> list) with ground truth for the same frames.

    ``stride`` means the records skip frames; ground truth is indexed by the record's own
    frame number so a sampled run is still scored against the right answers.
    """
    gt_by_frame = {g["frame"]: g["objects"] for g in scene(name)["frames_gt"]}
    pairs = []
    for rec in records:
        dets = [metrics.Detection(list(d["box"]), int(d["label"]), float(d["score"]))
                for d in rec["detections"]]
        truth = [{"box": o["box"], "label": labels_mod.LABEL_TO_INDEX[o["class"]]}
                 for o in gt_by_frame.get(rec["frame"], [])]
        pairs.append((dets, truth))
    return pairs


def detection_scores(name: str, records: list[dict], *, iou_threshold: float = 0.5) -> dict:
    return metrics.detection_report(pairs_for_report(name, records),
                                    num_classes=len(labels_mod.LABELS),
                                    class_names=list(labels_mod.LABELS),
                                    iou_threshold=iou_threshold)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


def report_path(name: str) -> Path:
    return OUT / name


def write_report(name: str, payload: dict) -> Path:
    path = write_json(OUT / name, payload)
    print(f"\n  report: {path.relative_to(HERE)}")
    return path


def all_checks(results: list[bool]) -> int:
    """Exit status for a lab: 0 only when every check passed."""
    passed = sum(1 for r in results if r)
    print(f"\n  {passed}/{len(results)} checks passed")
    return 0 if passed == len(results) else 1


__all__ = [
    "CACHE", "DATA", "HERE", "OUT", "all_checks", "check", "counting_truth", "detect_scene", "detect_video_records",
    "detection_scores", "detector_params", "ensure_data", "ground_truth", "manifest",
    "pairs_for_report", "read_json", "report_path", "rule", "scene", "scenes", "ssdlite",
    "synth", "table", "train_tiny_detector", "train_traffic_ssdlite", "training_frames", "video", "video_path",
    "write_report",
]
