#!/usr/bin/env python3
"""Generate the section's sample data: short synthetic traffic videos plus annotations.

Why synthetic: every number in this section - boxes, track IDs, line crossings - has to be
checkable, and a licence-free 6-second traffic clip with frame-exact ground truth does not
exist. These scenes are rendered deterministically by ``video_core.synth``, so re-running
this script reproduces byte-identical files, and the ground truth is exact rather than
hand-drawn.

What is written under ``data/video/``:

    street_day.mp4        training scene, clear weather
    street_dusk.mp4       training scene, low sun
    street_quiet.mp4      validation scene, light traffic
    street_night.mp4      test scene, headlights and low contrast
    street_rain.mp4       test scene, rain streaks and darker road
    street_shake.mp4      test scene, hand-held camera shake
    street_crowd.mp4      test scene, eight vehicles and real occlusion
    manifest.json         per-frame ground truth, counting lines, checksums, splits
    annotations/coco_*.json    COCO instances per video
    annotations/yolo/<video>/  YOLO txt per frame + classes.txt
    annotations/voc/<video>_<frame>.xml  two VOC examples showing the format
    dataset_card.md       what this data is, what it is not, and its licence

The videos are a few hundred kilobytes each and are ignored by Git (see
``projects/video-ai/.gitignore``). Re-run this script to restore them:

    python scripts/make_video_data.py            # writes data/video/
    python scripts/make_video_data.py --force    # overwrite existing files
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
sys.path.insert(0, str(PROJECT))

from video_core import labels as labels_mod  # noqa: E402
from video_core import synth, video  # noqa: E402
from video_core.report import markdown_table, rule, table, write_json  # noqa: E402

DATA = PROJECT / "data" / "video"

# name, condition, seed, vehicles, shake, split, note
SCENES = [
    ("street_day", "day", 11, 6, 0.0, "train", "clear midday, six vehicles"),
    ("street_dusk", "dusk", 12, 6, 0.0, "train", "low sun, warmer tones"),
    ("street_quiet", "day", 13, 4, 0.0, "val", "light traffic, four vehicles"),
    ("street_night", "night", 14, 6, 0.0, "test", "dark road, bright headlights"),
    ("street_rain", "rain", 15, 6, 0.0, "test", "rain streaks, wet road"),
    ("street_shake", "day", 16, 6, 3.0, "test", "hand-held camera, 3px shake"),
    ("street_crowd", "day", 17, 8, 0.0, "test", "eight vehicles, frequent occlusion"),
]


def build_scene(name: str, condition: str, seed: int, n_vehicles: int, shake: float,
                split: str, note: str, *, frames: int, fps: float) -> dict:
    cfg = synth.make_traffic_config(condition=condition, seed=seed, frames=frames,
                                    n_vehicles=n_vehicles, shake=shake, name=name)
    cfg.fps = fps
    rendered = synth.render_scene(cfg)

    path = DATA / f"{name}.mp4"
    video.write_video(path, (frame for frame, _ in rendered), fps, (synth.SCENE_W, synth.SCENE_H))

    gt_frames = [{"frame": i, "t_s": round(i / fps, 3), "objects": objects}
                 for i, (_, objects) in enumerate(rendered)]
    line = synth.counting_line(cfg)

    return {
        "name": name,
        "file": path.name,
        "split": split,
        "note": note,
        "condition": condition,
        "fps": fps,
        "frames": frames,
        "width": synth.SCENE_W,
        "height": synth.SCENE_H,
        "duration_s": round(frames / fps, 3),
        "shake_px": shake,
        "seed": seed,
        "sha256": video.checksum(path),
        "bytes": path.stat().st_size,
        "vehicles": [
            {"track_id": v.track_id, "class": v.kind, "lane_y": v.lane_y,
             "x0": round(v.x, 2), "speed_px_per_frame": round(v.speed, 3),
             "length": v.length, "height": v.height}
            for v in cfg.vehicles
        ],
        "counting_line": line,
        "frames_gt": gt_frames,
        "labels_present": sorted({o["class"] for g in gt_frames for o in g["objects"]}),
    }


def write_annotations(entry: dict) -> dict:
    """COCO for every video; YOLO for the training videos; two VOC examples."""
    name = entry["name"]
    records = [{"frame": g["frame"], "objects": g["objects"]} for g in entry["frames_gt"]]
    out = {"coco": str(labels_mod.write_coco(
        DATA / "annotations" / f"coco_{name}.json", records, image_name=name).relative_to(DATA))}
    if entry["split"] == "train":
        yolo_dir = DATA / "annotations" / "yolo" / name
        labels_mod.write_yolo(yolo_dir, records, width=entry["width"], height=entry["height"])
        out["yolo"] = str(yolo_dir.relative_to(DATA))
    if name in {"street_day", "street_night"}:
        ids = []
        for frame_index in (0, entry["frames"] // 2):
            path = labels_mod.write_voc(
                DATA / "annotations" / "voc" / f"{name}_{frame_index:04d}.xml",
                records[frame_index], width=entry["width"], height=entry["height"],
                image_name=f"{name}_{frame_index:04d}.jpg")
            ids.append(str(path.relative_to(DATA)))
        out["voc"] = ids
    return out


def dataset_card(manifest: dict) -> str:
    rows = [{
        "video": e["name"], "split": e["split"], "condition": e["condition"],
        "frames": e["frames"], "fps": e["fps"], "size": f'{e["width"]}x{e["height"]}',
        "kb": round(e["bytes"] / 1024, 1), "vehicles": len(e["vehicles"]),
        "crossings": e["counting_line"]["expected_total"],
    } for e in manifest["videos"]]
    totals = {
        "videos": len(manifest["videos"]),
        "frames": sum(e["frames"] for e in manifest["videos"]),
        "boxes": sum(len(g["objects"]) for e in manifest["videos"] for g in e["frames_gt"]),
        "bytes": sum(e["bytes"] for e in manifest["videos"]),
    }
    return f"""# Dataset card - synthetic traffic video set

Generated by `projects/video-ai/scripts/make_video_data.py`. Deterministic: the same script
and the same seeds always produce the same bytes, and `manifest.json` records the SHA-256 of
every file so a corrupted or hand-edited copy is detectable.

## What it is

{markdown_table(rows, ["video", "split", "condition", "frames", "fps", "size", "kb", "vehicles", "crossings"])}

Totals: {totals['videos']} videos, {totals['frames']} frames, {totals['boxes']} annotated
boxes, {round(totals['bytes'] / 1024, 1)} kB on disk.

Four vehicle classes: {', '.join(labels_mod.LABELS)}. Rendering is flat 2-D shapes on a
textured backdrop - there is no photographic detail, no pedestrian, no number plate, and
nothing that could be a real person.

## What it is for

* detection, tracking, and counting with frame-exact ground truth;
* measured domain shift: `street_night`, `street_rain` and `street_shake` exist so that a
  model that works on `street_day` can be shown to work less well on them;
* teaching annotation formats (COCO, YOLO, Pascal VOC) from one source of truth.

## What it is not

* **Not real footage.** A detector that scores 0.9 mAP here has learned rectangles on
  gradients. It says nothing about a real camera, and Module 6 and Lab 4 make that gap a
  measured result rather than a warning in prose.
* **Not a benchmark.** Seven six-second clips cannot rank models. They can expose failure
  modes, which is the job.
* **Not a person dataset.** No faces, no clothing worn by a person, no identifiers. The
  garment and action data in Labs 5 and 6 are likewise synthetic shapes.

## Licence and use

CC0-1.0: the data is generated by code in this repository, contains nothing taken from
anyone, and carries no restrictions. Do not present it as real traffic data, and do not use
it to claim real-world accuracy.

## Splits

{split_summary(manifest)}

Splits are by **video**, never by frame: frames from one clip share a camera, lighting, and
vehicle set, so a frame split leaks the answer. `video_core.labels.split_by_video` and
`video_leakage` exist to make that checkable.

## Checksums

{markdown_table([{"video": e["name"], "sha256": e["sha256"][:16] + "..."} for e in manifest["videos"]], ["video", "sha256"])}

Full digests are in `manifest.json`.
"""


def split_summary(manifest: dict) -> str:
    by_split: dict[str, list[str]] = {}
    for entry in manifest["videos"]:
        by_split.setdefault(entry["split"], []).append(entry["name"])
    return "\n".join(f"* **{split}**: {', '.join(names)}" for split, names in by_split.items())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=None,
                        help="output directory (default projects/video-ai/data/video)")
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    parser.add_argument("--frames", type=int, default=60, help="frames per video (default 60)")
    parser.add_argument("--fps", type=float, default=10.0, help="frames per second (default 10)")
    args = parser.parse_args(argv)

    global DATA
    DATA = Path(args.out) if args.out else PROJECT / "data" / "video"
    DATA.mkdir(parents=True, exist_ok=True)

    manifest_path = DATA / "manifest.json"
    if manifest_path.exists() and not args.force:
        print(f"{manifest_path} already exists; pass --force to regenerate")
        return 0

    rule(f"Rendering {len(SCENES)} synthetic videos into {DATA}")
    entries = []
    for name, condition, seed, n_vehicles, shake, split, note in SCENES:
        entry = build_scene(name, condition, seed, n_vehicles, shake, split, note,
                            frames=args.frames, fps=args.fps)
        entry["annotations"] = write_annotations(entry)
        entries.append(entry)
        print(f"  {name:14s} {entry['frames']:3d} frames  {entry['bytes'] / 1024:7.1f} kB  "
              f"{len(entry['vehicles'])} vehicles  {entry['counting_line']['expected_total']} "
              f"crossings  {entry['sha256'][:12]}")

    manifest = {
        "description": "Synthetic traffic video set for the AITopics video AI section",
        "licence": "CC0-1.0",
        "generator": "video_core.synth (deterministic)",
        "labels": list(labels_mod.LABELS),
        "scene_size": {"width": synth.SCENE_W, "height": synth.SCENE_H},
        "videos": entries,
    }
    write_json(manifest_path, manifest)
    (DATA / "dataset_card.md").write_text(dataset_card(manifest), encoding="utf-8")

    rule("Summary")
    table([{"video": e["name"], "split": e["split"], "frames": e["frames"],
            "kb": round(e["bytes"] / 1024, 1), "boxes": sum(len(g["objects"])
                                                            for g in e["frames_gt"]),
            "crossings": e["counting_line"]["expected_total"]} for e in entries],
          ["video", "split", "frames", "kb", "boxes", "crossings"])
    total_mb = sum(e["bytes"] for e in entries) / (1024 * 1024)
    print(f"\n  total {total_mb:.2f} MB - under the repository's sample-data budget")
    print(f"  manifest  {manifest_path}")
    print(f"  card      {DATA / 'dataset_card.md'}")
    print("\nGit: data/video/ is ignored - re-run this script after cloning.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
