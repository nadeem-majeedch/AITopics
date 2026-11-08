"""Tracking vehicles across frames, and the vocabulary for when it goes wrong.

The tracker here is a small IoU tracker with constant-velocity prediction, in the spirit of
SORT. It is about 150 lines because the interesting part of tracking is not the algorithm -
it is the failure modes, and those are easier to see when the algorithm is legible:

* **Occlusion.** A bus passing in front of a car erases it for a dozen frames. A tracker
  that drops it and re-acquires it issues a new ID, which corrupts any per-vehicle count.
* **Camera movement.** If the camera shakes, every box moves by the same amount; a tracker
  that compares raw positions sees motion that is not there. The fix is to track relative to
  the frame's dominant motion, or to accept the hit and say so.
* **Fragmentation.** A track that keeps its ID but disappears for a few frames still breaks
  a "count each ID once" rule if the counter is naive about gaps.
* **Class flapping.** A distant truck is classified car in one frame and bus in the next;
  majority voting over a track's lifetime fixes the label, not the box.

Every one of those is measured in Lab 3 rather than asserted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
from scipy.optimize import linear_sum_assignment

from . import labels as labels_mod
from . import metrics


@dataclass
class Track:
    """One tracked object, with just enough state to survive a short occlusion."""

    track_id: int
    box: list[float]
    label: int
    hits: int = 1
    age: int = 0
    hits_since_update: int = 0
    wins: int = 0
    label_votes: dict[int, int] = field(default_factory=dict)
    trail: list[tuple[float, float]] = field(default_factory=list)
    velocity: tuple[float, float] = (0.0, 0.0)

    def predicted_box(self) -> list[float]:
        dx, dy = self.velocity
        return [self.box[0] + dx, self.box[1] + dy, self.box[2] + dx, self.box[3] + dy]

    def centre(self) -> tuple[float, float]:
        return ((self.box[0] + self.box[2]) / 2.0, (self.box[1] + self.box[3]) / 2.0)

    @property
    def label_name(self) -> str:
        return labels_mod.LABELS[self.label]


class IoUTracker:
    """Greedy-global IoU tracker with velocity prediction and a confirmation delay.

    Why the pieces exist:

    * ``max_age`` frames of coasting: a track survives this many frames without a detection,
      which is what lets it survive a short occlusion. Too small and a bus hides a car
      forever; too large and a departed car keeps collecting detections.
    * ``min_hits``: a track is reported only after this many detections. One-frame false
      positives are the most common detector error and they must not become IDs, because
      every new ID is a potential count.
    * velocity: boxes are predicted forward before matching, so a fast vehicle still
      overlaps its own prediction after the detector misses a frame.
    """

    def __init__(self, *, iou_threshold: float = 0.30, max_age: int = 6, min_hits: int = 2,
                 velocity_smoothing: float = 0.6) -> None:
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.min_hits = min_hits
        self.velocity_smoothing = velocity_smoothing
        self.tracks: list[Track] = []
        self._next_id = 1
        self.frame_index = 0

    def reset(self) -> None:
        self.tracks.clear()
        self._next_id = 1
        self.frame_index = 0

    def update(self, detections: Sequence[metrics.Detection]) -> list[Track]:
        """Advance one frame and return the tracks that should be reported."""
        self.frame_index += 1
        for track in self.tracks:
            track.age += 1
            track.hits_since_update += 1

        if not self.tracks:
            matches = []
            unmatched_tracks = []
            unmatched_dets = list(range(len(detections)))
        else:
            # Cost is 1 - IoU against the *predicted* box. Matching deliberately ignores
            # class: a detector that flips car/truck on consecutive frames must not spawn a
            # new ID for the same vehicle. The label is settled afterwards by voting over
            # the track's life, which is both more stable and closer to how SORT works.
            predicted = [t.predicted_box() for t in self.tracks]
            cost = np.ones((len(self.tracks), len(detections)), dtype=np.float32)
            for ti, track in enumerate(self.tracks):
                for di, det in enumerate(detections):
                    value = metrics.iou(predicted[ti], det.box)
                    if value >= self.iou_threshold:
                        cost[ti, di] = 1.0 - value
            rows, cols = linear_sum_assignment(cost)
            matches = [(r, c) for r, c in zip(rows, cols) if cost[r, c] < 1.0 - 1e-6]
            matched_tracks = {r for r, _ in matches}
            matched_dets = {c for _, c in matches}
            unmatched_tracks = [i for i in range(len(self.tracks)) if i not in matched_tracks]
            unmatched_dets = [i for i in range(len(detections)) if i not in matched_dets]

        for ti, di in matches:
            track = self.tracks[ti]
            det = detections[di]
            old_cx, old_cy = track.centre()
            new_box = metrics.clip_box(det.box, 10_000, 10_000)
            new_cx = (new_box[0] + new_box[2]) / 2.0
            new_cy = (new_box[1] + new_box[3]) / 2.0
            # EMA on velocity: one-frame box jitter must not become a trajectory.
            a = self.velocity_smoothing
            vx = a * (new_cx - old_cx) + (1 - a) * track.velocity[0]
            vy = a * (new_cy - old_cy) + (1 - a) * track.velocity[1]
            track.velocity = (vx, vy)
            track.box = new_box
            track.hits += 1
            track.hits_since_update = 0
            track.label_votes[det.label] = track.label_votes.get(det.label, 0) + 1
            track.label = max(track.label_votes, key=track.label_votes.get)
            track.trail.append((new_cx, new_cy))
            if len(track.trail) > 24:
                track.trail.pop(0)

        for di in unmatched_dets:
            det = detections[di]
            track = Track(self._next_id, list(metrics.clip_box(det.box, 10_000, 10_000)),
                          int(det.label))
            track.label_votes[track.label] = 1
            cx, cy = track.centre()
            track.trail.append((cx, cy))
            self.tracks.append(track)
            self._next_id += 1

        # Retire tracks that have gone unseen for too long. Reported count is unaffected:
        # a retired track already contributed whatever it was going to contribute.
        self.tracks = [t for t in self.tracks if t.hits_since_update <= self.max_age]

        # Collapse duplicates. A detector that emits two overlapping boxes for one vehicle
        # (common when it cannot decide between car and truck) would otherwise keep two
        # tracks alive for that vehicle forever, because each frame supplies one more box for
        # each of them. Keeping the track with more hits and dropping the other is the
        # cheapest fix that does not require knowing which duplicate was "right".
        self.tracks = _dedupe(self.tracks, iou_threshold=0.60)

        for track in self.tracks:
            if track.hits_since_update == 0:
                track.wins += 1

        return [t for t in self.tracks if t.hits >= self.min_hits and t.hits_since_update == 0]


def _dedupe(tracks: list[Track], *, iou_threshold: float) -> list[Track]:
    """Drop tracks that overlap a better-established track on the same frame."""
    if len(tracks) < 2:
        return tracks
    keep: list[Track] = []
    for track in sorted(tracks, key=lambda t: (-t.hits, t.track_id)):
        if any(metrics.iou(track.box, other.box) >= iou_threshold for other in keep):
            continue
        keep.append(track)
    return sorted(keep, key=lambda t: t.track_id)


def track_detections(
    detections_by_frame: Sequence[Sequence[metrics.Detection]],
    *,
    iou_threshold: float = 0.30,
    max_age: int = 6,
    min_hits: int = 2,
) -> list[list[dict]]:
    """Run the tracker over a sequence of detection lists.

    Returns one list per frame of ``{"box", "label", "score", "track_id", "class"}`` for the
    tracks reported that frame. Ground truth is not used: a tracker that reads the answers
    is not a tracker, and the lab's job is to compare its output with them afterwards.
    """
    tracker = IoUTracker(iou_threshold=iou_threshold, max_age=max_age, min_hits=min_hits)
    out: list[list[dict]] = []
    for detections in detections_by_frame:
        active = tracker.update(detections)
        # Report every live track, including coasted ones, so a frame where the detector
        # missed can still be counted and drawn.
        frame_tracks = []
        for track in tracker.tracks:
            if track.hits < tracker.min_hits and track.hits_since_update == 0:
                continue
            if track.hits_since_update > tracker.max_age:
                continue
            x1, y1, x2, y2 = track.box
            frame_tracks.append({
                "box": [round(float(x1), 2), round(float(y1), 2),
                        round(float(x2), 2), round(float(y2), 2)],
                "label": int(track.label),
                "class": track.label_name,
                "score": round(1.0 if track.hits_since_update == 0 else 0.0, 3),
                "track_id": int(track.track_id),
                "coasting": bool(track.hits_since_update > 0),
            })
        out.append(frame_tracks)
    return out


def tracker_report(predictions: Sequence[Sequence[dict]],
                   truth: Sequence[Sequence[dict]],
                   *, iou_threshold: float = 0.5) -> dict:
    """MOTA, ID switches, fragments, and the per-frame count error.

    ``truth`` entries need ``box``, ``class`` and ``track_id``; predictions come from
    :func:`track_detections`.
    """
    pairs = [([{**p, "label": int(p["label"])} for p in preds],
              [{"box": t["box"], "label": labels_mod.LABEL_TO_INDEX.get(t["class"], 0),
                "track_id": t["track_id"]} for t in truths])
             for preds, truths in zip(predictions, truth)]
    report = metrics.tracking_report(pairs, iou_threshold=iou_threshold)
    counts_pred = [len(p) for p in predictions]
    counts_true = [len(t) for t in truth]
    report["count_error_mean"] = round(float(np.mean(np.abs(np.array(counts_pred)
                                                             - np.array(counts_true)))), 3)
    report["frames"] = len(predictions)
    return report


def unique_track_count(predictions: Sequence[Sequence[dict]], *, min_frames: int = 2) -> dict:
    """Count distinct track IDs that were seen for at least ``min_frames`` frames.

    This is the number a "vehicles seen" dashboard shows, and it is *not* the same as the
    number of vehicles that crossed a line: a track that appears at the frame edge and
    leaves the same way counts here and never crosses.
    """
    seen: dict[int, int] = {}
    for frame in predictions:
        for pred in frame:
            seen[int(pred["track_id"])] = seen.get(int(pred["track_id"]), 0) + 1
    kept = {k: v for k, v in seen.items() if v >= min_frames}
    by_class: dict[str, int] = {}
    for frame in predictions:
        for pred in frame:
            if int(pred["track_id"]) in kept:
                by_class[pred["class"]] = by_class.get(pred["class"], 0) + 0
    labels_by_id: dict[int, str] = {}
    for frame in predictions:
        for pred in frame:
            labels_by_id.setdefault(int(pred["track_id"]), pred["class"])
    for tid in kept:
        name = labels_by_id.get(tid, "?")
        by_class[name] = by_class.get(name, 0) + 1
    return {
        "unique_tracks": len(kept),
        "by_class": by_class,
        "all_track_ids": len(seen),
        "dropped_short_tracks": len(seen) - len(kept),
    }
