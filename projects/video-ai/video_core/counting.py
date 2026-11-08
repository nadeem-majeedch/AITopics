"""Counting vehicles across a virtual line, and traffic-flow summaries.

Counting looks trivial and is not. The three decisions that change the number are:

1. **What counts as a crossing.** The centre of the box, the bottom centre (where the
   vehicle touches the road), or any overlap with the line? This module uses a *crossing of
   the anchor point* from one side to the other, because that is the only rule that does not
   double-count a vehicle that stops on the line.
2. **When a track is allowed to count.** Once per track ID, ever. A tracker that loses and
   re-acquires a vehicle issues a new ID and the same car is counted twice; that is what
   Lab 3 measures.
3. **What direction means.** "Positive" is the side the line's normal points to, computed
   from the line's orientation, not from screen axes. A vertical line therefore reports
   left-to-right and right-to-left separately, which is what a two-way traffic count needs.

The summary also reports a rate and a simple flow estimate, with the arithmetic shown, so
that a student can check it by hand.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np


@dataclass
class CrossingEvent:
    track_id: int
    label: int
    class_name: str
    frame: int
    direction: str
    anchor: tuple[float, float]

    def as_dict(self) -> dict:
        return {
            "track_id": int(self.track_id),
            "class": self.class_name,
            "frame": int(self.frame),
            "direction": self.direction,
            "anchor": [round(self.anchor[0], 1), round(self.anchor[1], 1)],
        }


class LineCounter:
    """Tripwire counter with a per-track memory of which side it was last seen on.

    The anchor is the bottom-centre of the box: for a road scene, that is the contact point
    with the road, which is the point that actually crosses a painted line. Using the box
    centre instead shifts every event by half a vehicle length and, for a line near the
    frame edge, changes the count.
    """

    def __init__(self, p1: Sequence[float], p2: Sequence[float], *,
                 anchor: str = "bottom") -> None:
        self.p1 = (float(p1[0]), float(p1[1]))
        self.p2 = (float(p2[0]), float(p2[1]))
        if self.p1 == self.p2:
            raise ValueError("counting line needs two distinct points")
        self.anchor = anchor
        self.sides: dict[int, float] = {}
        self.counted: set[int] = set()
        self.events: list[CrossingEvent] = []

    def side(self, point: tuple[float, float]) -> float:
        """Signed area test: positive on one side of the line, negative on the other.

        The orientation is fixed by the order of the two points. Draw a vertical line from
        top to bottom (the usual way a traffic tripwire is specified) and the *right* side of
        the frame is positive, so right-moving traffic counts as ``positive``. Draw a
        horizontal line from left to right and the side above the line is positive. That is
        a convention, not a law - the important thing is that it is documented and stable,
        because a sign flip silently swaps two columns of a traffic report.
        """
        (x1, y1), (x2, y2) = self.p1, self.p2
        return (y2 - y1) * (point[0] - x1) - (x2 - x1) * (point[1] - y1)

    def anchor_point(self, box: Sequence[float]) -> tuple[float, float]:
        x1, y1, x2, y2 = [float(v) for v in box[:4]]
        cx = (x1 + x2) / 2.0
        return (cx, y2) if self.anchor == "bottom" else (cx, (y1 + y2) / 2.0)

    def update(self, tracks: Sequence[dict], frame: int) -> list[CrossingEvent]:
        """Feed one frame of tracks; return the events that happened *this* frame."""
        new_events: list[CrossingEvent] = []
        for track in tracks:
            tid = int(track["track_id"])
            point = self.anchor_point(track["box"])
            value = self.side(point)
            if value == 0.0:
                # Exactly on the line: no side to record. Skipping keeps the last real side,
                # so a track that pauses on the tripwire still counts once when it leaves -
                # and does not acquire a direction from a position that has none.
                continue
            previous = self.sides.get(tid)
            self.sides[tid] = value
            if previous is None or tid in self.counted:
                continue
            if (previous < 0 <= value) or (previous > 0 >= value):
                direction = "positive" if value > 0 else "negative"
                event = CrossingEvent(tid, int(track["label"]), str(track["class"]), frame,
                                      direction, point)
                self.events.append(event)
                new_events.append(event)
                self.counted.add(tid)
        return new_events

    # -- results -----------------------------------------------------------
    def tally(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for event in self.events:
            key = f"{event.class_name}:{event.direction}"
            out[key] = out.get(key, 0) + 1
        return out

    def events_as_dicts(self) -> list[dict]:
        return [event.as_dict() for event in self.events]


def run_counter(tracks_by_frame: Sequence[Sequence[dict]], p1: Sequence[float],
                p2: Sequence[float], *, anchor: str = "bottom") -> dict:
    """Apply a counter to a whole track sequence."""
    counter = LineCounter(p1, p2, anchor=anchor)
    per_frame: list[dict] = []
    for frame, tracks in enumerate(tracks_by_frame):
        events = counter.update(tracks, frame)
        if events:
            per_frame.append({"frame": frame, "events": [e.as_dict() for e in events]})
    return {
        "counts": counter.tally(),
        "total": len(counter.events),
        "events": counter.events_as_dicts(),
        "event_frames": per_frame,
        "line": {"p1": list(counter.p1), "p2": list(counter.p2), "anchor": anchor},
    }


def flow_summary(counts: dict[str, int], *, duration_s: float,
                 lanes: int = 1) -> dict:
    """Convert counts into the units a traffic engineer would ask for.

    * **Rate**: vehicles per second across the line.
    * **Flow**: vehicles per hour, extrapolated. On a six-second clip this number is a
      fiction with a decimal point - the clip is far too short to estimate an hourly rate -
      so it is returned with ``extrapolated: True`` and the labs print the caveat next to it.
    * **Per lane**: flow divided by the number of lanes, assuming even distribution, which
      is an assumption worth stating rather than hiding.
    """
    total = int(sum(counts.values()))
    if duration_s <= 0:
        return {"total": total, "rate_per_s": float("nan"), "per_hour": float("nan"),
                "lanes": lanes, "extrapolated": True}
    rate = total / duration_s
    return {
        "total": total,
        "duration_s": round(float(duration_s), 3),
        "rate_per_s": round(rate, 3),
        "per_hour": round(rate * 3600.0, 1),
        "per_lane_per_hour": round(rate * 3600.0 / max(lanes, 1), 1),
        "lanes": lanes,
        "extrapolated": True,
        "note": "per-hour figures extrapolate a few seconds of video; treat as a rate, not a forecast",
    }


def speed_estimates(tracks_by_frame: Sequence[Sequence[dict]], *, fps: float,
                    pixels_per_metre: float | None = None) -> dict:
    """Per-track speed in pixels/second, optionally converted to metres/second.

    Without a calibrated ``pixels_per_metre`` the metres column is absent rather than
    guessed: a speed in km/h from an uncalibrated camera is the most confidently wrong
    number in traffic analytics, because the scale changes with every camera position.
    """
    positions: dict[int, list[tuple[int, float, float]]] = {}
    for frame, tracks in enumerate(tracks_by_frame):
        for track in tracks:
            x1, y1, x2, y2 = track["box"]
            positions.setdefault(int(track["track_id"]), []).append(
                (frame, (x1 + x2) / 2.0, (y1 + y2) / 2.0))
    speeds = []
    for tid, seq in positions.items():
        if len(seq) < 3:
            continue
        # Least-squares slope over the track's whole life: more stable than first/last.
        frames = np.array([s[0] for s in seq], dtype=np.float64)
        xs = np.array([s[1] for s in seq], dtype=np.float64)
        ys = np.array([s[2] for s in seq], dtype=np.float64)
        if frames.std() == 0:
            continue
        vx = float(np.polyfit(frames, xs, 1)[0])
        vy = float(np.polyfit(frames, ys, 1)[0])
        speed_px_s = float(np.hypot(vx, vy) * fps)
        item = {"track_id": tid, "speed_px_per_s": round(speed_px_s, 2),
                "frames": len(seq)}
        if pixels_per_metre:
            item["speed_m_per_s"] = round(speed_px_s / pixels_per_metre, 2)
            item["speed_km_per_h"] = round(speed_px_s / pixels_per_metre * 3.6, 1)
        speeds.append(item)
    speeds.sort(key=lambda s: -s["speed_px_per_s"])
    return {
        "tracks_measured": len(speeds),
        "median_px_per_s": round(float(np.median([s["speed_px_per_s"] for s in speeds])), 2)
        if speeds else 0.0,
        "calibrated": bool(pixels_per_metre),
        "tracks": speeds[:20],
    }
