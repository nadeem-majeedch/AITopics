"""Lab 1 - Video preprocessing: metadata, frame extraction, and a contact sheet.

Goal: open a video, describe it truthfully, pull frames out of it at a chosen interval, and
leave behind metadata that the rest of a pipeline can trust.

The first lesson is that a video's header is a claim, not a fact. ``CAP_PROP_FRAME_COUNT``
is often wrong for files written by partial downloads, phone cameras, or OpenCV itself, so
this lab reports the header count and the decoded count side by side and treats the decoded
count as the answer. The second lesson is timestamps: frame ``i`` is at ``i / fps`` seconds,
and the interval you *ask* for (every 0.5 s) is not the interval you *get* (every 5 frames)
unless you account for rounding. Both are printed.

Run:

    python lab1_video_preprocessing.py
    python lab1_video_preprocessing.py --selftest     # one video, assertions only
    python lab1_video_preprocessing.py --interval 1.0 # one frame per second

Output:

    outputs/frames/<video>/frame_XXXX.jpg    extracted frames
    outputs/contact_<video>.png              contact sheet
    outputs/lab1_video_preprocessing.json    metadata for every video
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lab_support as support
from video_core import video


def frame_interval(fps: float, seconds: float) -> int:
    """Frames between two samples for a requested time interval.

    A 10 fps video sampled every 0.4 s must step 4 frames, not 3.999 - and the achievable
    interval is quantised to the frame rate, which is why this returns an integer and the
    lab prints the real interval next to the requested one.
    """
    return max(1, int(round(fps * seconds)))


def extract(name: str, *, interval_s: float, write_frames: bool) -> dict:
    path = support.video_path(name)
    header = video.probe(path)                      # header values only, no decoding
    decoded = video.probe(path, count_frames=True)  # ground truth by decoding everything

    step = frame_interval(decoded.fps, interval_s)
    out_dir = support.OUT / "frames" / name
    if write_frames:
        out_dir.mkdir(parents=True, exist_ok=True)

    extracted = []
    thumbnails = []
    for index, stamp, frame in video.iter_frames(path, stride=step):
        thumbnails.append(frame)
        record = {
            "frame": index,
            "t_s": round(stamp, 3),
            "expected_t_s": round(index / decoded.fps, 4),
            "shape": list(frame.shape),
            "mean_luma": round(float(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).mean()), 2),
            "digest": video.frame_digest([frame])[:16],
        }
        if write_frames:
            frame_path = out_dir / f"frame_{index:04d}.jpg"
            cv2.imwrite(str(frame_path), frame)
            record["file"] = frame_path.name
            record["bytes"] = frame_path.stat().st_size
        extracted.append(record)

    sheet = video.contact_sheet(
        thumbnails, cols=4,
        labels=[f"f{e['frame']} {e['t_s']:.1f}s" for e in extracted])
    sheet_path = support.OUT / f"contact_{name}.png"
    video.save_contact_sheet(sheet_path, sheet)

    expected_samples = len(range(0, decoded.frame_count, step))
    return {
        "video": name,
        "file": path.name,
        "header": header.as_dict(),
        "decoded": decoded.as_dict(),
        "header_frames": header.frame_count,
        "decoded_frames": decoded.frame_count,
        "header_matches_decode": header.frame_count == decoded.frame_count,
        "aspect": video.aspect_note(decoded),
        "requested_interval_s": interval_s,
        "frame_step": step,
        "achieved_interval_s": round(step / decoded.fps, 4),
        "expected_samples": expected_samples,
        "extracted": len(extracted),
        "contact_sheet": sheet_path.name,
        "frames": extracted,
        "file_size_kb": round(path.stat().st_size / 1024, 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--interval", type=float, default=0.5,
                        help="seconds between extracted frames (default 0.5)")
    parser.add_argument("--video", default=None, help="process one video by name")
    parser.add_argument("--selftest", action="store_true",
                        help="one video, no frame JPEGs, assertions only")
    parser.add_argument("--no-frames", action="store_true", help="skip writing frame JPEGs")
    args = parser.parse_args()

    end = support.rule
    end("data")
    names = [args.video] if args.video else [e["name"] for e in support.scenes()]
    if args.selftest:
        names = names[:1]
    for name in names:
        entry = support.scene(name)
        print(f"  {name:14s} {entry['split']:5s} {entry['frames']:3d} frames  "
              f"{entry['fps']:.0f} fps  {entry['condition']}")

    results: list[bool] = []
    summaries = []
    for name in names:
        entry = support.scene(name)
        end(f"{name}")
        info = extract(name, interval_s=args.interval, write_frames=not args.selftest)
        print(f"  resolution : {info['decoded']['width']}x{info['decoded']['height']} "
              f"({info['aspect']})")
        print(f"  fourcc     : {info['decoded']['fourcc']}  backend {info['decoded']['backend']}")
        print(f"  frames     : header says {info['header_frames']}, decoded "
              f"{info['decoded_frames']}  {entry['frames']} expected")
        print(f"  duration   : {info['decoded']['duration_s']:.2f} s  "
              f"({entry['duration_s']:.2f} s in the generator)")
        print(f"  interval   : asked {info['requested_interval_s']} s, used "
              f"{info['frame_step']} frames = {info['achieved_interval_s']} s")
        print(f"  extracted  : {info['extracted']} frames -> "
              f"{info['contact_sheet']}")
        if info["decoded"]["codec_note"]:
            print(f"  header note: {info['decoded']['note']}")

        results.append(support.check("decoded frame count matches the generator",
                                     info["decoded_frames"] == entry["frames"],
                                     f"{info['decoded_frames']} vs {entry['frames']}"))
        results.append(support.check("frame rate matches the generator",
                                     abs(info["decoded"]["fps"] - entry["fps"]) < 0.5,
                                     f"{info['decoded']['fps']:.2f}"))
        results.append(support.check("extraction count is what the interval implies",
                                     info["extracted"] == info["expected_samples"],
                                     f"{info['extracted']} of {info['expected_samples']}"))
        results.append(support.check("contact sheet written and nonempty",
                                     (support.OUT / info["contact_sheet"]).stat().st_size > 0))
        results.append(support.check("timestamps are monotonic and match frame/fps",
                                     all(abs(f["t_s"] - f["expected_t_s"]) < 0.11
                                         for f in info["frames"])))
        summaries.append(info)

    # Determinism: extracting the same frame twice must produce the same digest. This is the
    # check that makes "the frames are reproducible" a fact rather than a claim.
    if summaries:
        first = summaries[0]
        again = video.frame_at(support.video_path(first["video"]), first["frames"][0]["frame"])
        digest = video.frame_digest([again])[:16]
        results.append(support.check("re-reading a frame gives identical pixels",
                                     digest == first["frames"][0]["digest"],
                                     f"{digest} == {first['frames'][0]['digest']}"))

    support.rule("columns in the extracted table")
    sample = summaries[0]["frames"][:4] if summaries else []
    support.table([{k: f[k] for k in ("frame", "t_s", "mean_luma", "digest")} for f in sample],
                  ["frame", "t_s", "mean_luma", "digest"])

    support.write_report("lab1_video_preprocessing.json", {
        "lab": "video preprocessing",
        "interval_s": args.interval,
        "videos": summaries,
        "checks": results,
    })
    return support.all_checks(results)


if __name__ == "__main__":
    raise SystemExit(main())
