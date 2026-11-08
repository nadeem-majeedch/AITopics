"""Synthetic, licence-clean image datasets and leakage-safe splitting.

Real labelled image datasets are large, sometimes ambiguously licensed, and
often contain the same photograph twice. This section ships a deterministic
renderer instead, so every lab runs offline, produces identical numbers on every
machine, and carries no licensing question at all. Module 2 explains the trade:
synthetic data is clean and cheap, and it is *not* a substitute for real
photographs when you care about real-world performance.

The renderer produces four datasets:

``classification``
    32x32 images of one shape (circle, square, triangle) - 3 classes.
``objects``
    Four coarse everyday-object silhouettes (mug, bottle, book, phone), used by
    the fine-tuning lab.
``detection``
    64x64 images with one or two shapes and YOLO + COCO annotations.
``segmentation``
    64x64 images with 3 regions (background, object, shadow) and masks.

Every record carries a ``source_id``. Images generated from one source share a
small random jitter, so they are near-duplicates of each other. Splitting by
``source_id`` is what prevents the classic mistake of training on a rotated copy
of a test image and then reporting 99% accuracy.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from .imaging import save_image, to_gray, to_float

SHAPE_CLASSES: tuple[str, ...] = ("circle", "square", "triangle")
OBJECT_CLASSES: tuple[str, ...] = ("mug", "bottle", "book", "phone")
SEGMENTATION_CLASSES: tuple[str, ...] = ("background", "object", "shadow")

# Deliberately restrained palette: enough variation to make the task non-trivial,
# not so much that colour alone solves it.
_PALETTE: tuple[tuple[int, int, int], ...] = (
    (220, 80, 70),
    (70, 120, 210),
    (90, 180, 110),
    (230, 190, 60),
    (170, 100, 200),
    (80, 200, 200),
)


@dataclass
class ImageRecord:
    """One image plus everything needed to evaluate it later."""

    image: np.ndarray
    label: int
    source_id: str
    meta: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"label": self.label, "source_id": self.source_id, **self.meta}


# ---------------------------------------------------------------------------
# Primitive drawing (NumPy only, so results are bit-identical everywhere)
# ---------------------------------------------------------------------------


def _canvas(size: int, background: float, rng: np.random.Generator) -> np.ndarray:
    """Slightly noisy grey background: pure zeros would make edge detection trivial."""
    base = np.full((size, size, 3), background, dtype=np.float32)
    return np.clip(base + rng.normal(0.0, 0.02, size=base.shape).astype(np.float32), 0.0, 1.0)


def _shape_mask(kind: str, size: int, cy: float, cx: float, radius: float) -> np.ndarray:
    """Boolean mask for a circle, square, or triangle of given radius."""
    yy, xx = np.mgrid[0:size, 0:size]
    if kind == "circle":
        return (yy - cy) ** 2 + (xx - cx) ** 2 <= radius**2
    if kind == "square":
        return (np.abs(yy - cy) <= radius * 0.9) & (np.abs(xx - cx) <= radius * 0.9)
    if kind == "triangle":
        # Point-in-triangle via three half-plane tests, apex up.
        h = radius * 1.8
        ax, ay = cx, cy - h * 0.55
        bx, by = cx - radius * 0.95, cy + h * 0.45
        cx_, cy_ = cx + radius * 0.95, cy + h * 0.45

        def side(px, py, qx, qy):
            return (qx - px) * (yy - py) - (qy - py) * (xx - px)

        d1, d2, d3 = side(ax, ay, bx, by), side(bx, by, cx_, cy_), side(cx_, cy_, ax, ay)
        neg = (d1 < 0) | (d2 < 0) | (d3 < 0)
        pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
        return ~(neg & pos)
    raise ValueError(f"unknown shape {kind!r}")


def _render_shape(kind: str, size: int, rng: np.random.Generator, colour: Sequence[int] | None = None) -> np.ndarray:
    background = float(rng.uniform(0.15, 0.55))
    canvas = _canvas(size, background, rng)
    radius = float(rng.uniform(size * 0.18, size * 0.34))
    margin = radius * 1.35
    cy = float(rng.uniform(margin, size - margin))
    cx = float(rng.uniform(margin, size - margin))
    colour = np.asarray(_PALETTE[int(rng.integers(len(_PALETTE)))] if colour is None else colour, dtype=np.float32) / 255.0
    mask = _shape_mask(kind, size, cy, cx, radius)

    # Soft edge + shading so the task is not a flat binary segmentation.
    dist = np.sqrt((np.mgrid[0:size, 0:size][0] - cy) ** 2 + (np.mgrid[0:size, 0:size][1] - cx) ** 2)
    shade = np.clip(1.25 - dist / (radius * 1.6), 0.55, 1.15).astype(np.float32)
    for c in range(3):
        canvas[..., c] = np.where(mask, colour[c] * shade, canvas[..., c])

    return (np.clip(canvas, 0, 1) * 255).astype(np.uint8)


def _render_object(kind: str, size: int, rng: np.random.Generator) -> np.ndarray:
    """Coarse silhouettes of four everyday objects.

    These are icons, not photographs. Module 6 is explicit that a model trained
    on them learns these drawings, not the objects in the world.
    """
    background = float(rng.uniform(0.15, 0.55))
    canvas = _canvas(size, background, rng)
    colour = np.asarray(_PALETTE[int(rng.integers(len(_PALETTE)))], dtype=np.float32) / 255.0
    yy, xx = np.mgrid[0:size, 0:size]
    cy = size * 0.5 + float(rng.uniform(-2, 2))
    cx = size * 0.5 + float(rng.uniform(-2, 2))
    w = size * float(rng.uniform(0.30, 0.42))
    h = size * float(rng.uniform(0.34, 0.46))

    if kind == "mug":
        body = (np.abs(xx - cx) <= w * 0.75) & (np.abs(yy - cy) <= h)
        handle = ((xx - (cx + w * 0.9)) ** 2 + (yy - cy) ** 2 <= (h * 0.55) ** 2) & (xx > cx + w * 0.7)
        mask = body | handle
        inner = (np.abs(xx - (cx + w * 0.9)) ** 2 + (yy - cy) ** 2 <= (h * 0.30) ** 2) & (xx > cx + w * 0.7)
        mask &= ~inner
    elif kind == "bottle":
        body = (np.abs(xx - cx) <= w * 0.7) & (np.abs(yy - cy) <= h)
        neck = (np.abs(xx - cx) <= w * 0.28) & (yy < cy - h * 0.7) & (yy > cy - h * 1.25)
        mask = body | neck
    elif kind == "book":
        mask = (np.abs(xx - cx) <= w) & (np.abs(yy - (cy + yy * 0)) <= h * 0.7)
        mask &= (yy >= cy - h * 0.75) & (yy <= cy + h * 0.55)
        mask &= np.abs(xx - cx) * 0.9 + (yy - cy) * 0.25 < w * 1.0
    elif kind == "phone":
        mask = (np.abs(xx - cx) <= w * 0.55) & (np.abs(yy - cy) <= h)
        screen = (np.abs(xx - cx) <= w * 0.45) & (np.abs(yy - cy) <= h * 0.78)
        mask = mask
        inner = screen
    else:
        raise ValueError(f"unknown object {kind!r}")

    shade = np.clip(1.15 - np.abs(xx - cx) / (size * 0.9) * 0.4, 0.7, 1.1).astype(np.float32)
    for c in range(3):
        canvas[..., c] = np.where(mask, colour[c] * shade, canvas[..., c])
    if kind == "phone":
        canvas = np.where(inner[..., None], canvas * 0.35, canvas)

    return (np.clip(canvas, 0, 1) * 255).astype(np.uint8)


def render_classification_sample(kind: str, size: int, rng: np.random.Generator) -> tuple[np.ndarray, dict]:
    """One classification image plus its geometry metadata."""
    image = _render_shape(kind, size, rng)
    return image, {"shape": kind, "size": size}


def render_object_sample(kind: str, size: int, rng: np.random.Generator) -> tuple[np.ndarray, dict]:
    image = _render_object(kind, size, rng)
    return image, {"object": kind, "size": size}


def _find_box(kind: str, size: int, rng: np.random.Generator) -> tuple[np.ndarray, list[tuple[str, list[int]]], list[list[int]]]:
    """Render one detection image and return its boxes (pixel coordinates)."""
    background = float(rng.uniform(0.15, 0.5))
    canvas = _canvas(size, background, rng)
    n_objects = int(rng.integers(1, 3))
    boxes: list[tuple[str, list[int]]] = []
    placed: list[tuple[float, float, float]] = []

    for _ in range(n_objects):
        for _attempt in range(12):
            radius = float(rng.uniform(size * 0.10, size * 0.18))
            margin = radius * 1.4
            if margin >= size / 2:
                continue
            cy = float(rng.uniform(margin, size - margin))
            cx = float(rng.uniform(margin, size - margin))
            if any((cy - py) ** 2 + (cx - px) ** 2 < (radius + pr + 3) ** 2 for py, px, pr in placed):
                continue
            kind = SHAPE_CLASSES[int(rng.integers(len(SHAPE_CLASSES)))]
            colour = np.asarray(_PALETTE[int(rng.integers(len(_PALETTE)))], dtype=np.float32) / 255.0
            mask = _shape_mask(kind, size, cy, cx, radius)
            for c in range(3):
                canvas[..., c] = np.where(mask, colour[c], canvas[..., c])
            ys, xs = np.nonzero(mask)
            boxes.append((kind, [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]))
            placed.append((cy, cx, radius))
            break

    image = (np.clip(canvas, 0, 1) * 255).astype(np.uint8)
    return image, boxes


def render_detection_sample(size: int, rng: np.random.Generator) -> tuple[np.ndarray, list[tuple[str, list[int]]]]:
    image, boxes = _find_box(SHAPE_CLASSES[0], size, rng)
    return image, boxes


def render_segmentation_sample(size: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Return an image and a class mask: 0 background, 1 object, 2 shadow."""
    image, boxes = render_detection_sample(size, rng)
    mask = np.zeros((size, size), dtype=np.uint8)
    for _kind, (x1, y1, x2, y2) in boxes:
        # Shadow: offset ellipse under the object, the reason this is not a
        # two-class problem.
        cy, cx = int((y1 + y2) / 2 + (y2 - y1) * 0.45), int((x1 + x2) / 2)
        rr = max(1.0, (x2 - x1) * 0.45)
        yy, xx = np.mgrid[0:size, 0:size]
        shadow = ((yy - cy) ** 2 / max(1.0, (rr * 0.5) ** 2) + (xx - cx) ** 2 / max(1.0, rr**2)) <= 1.0
        mask[shadow] = 2
    for _kind, (x1, y1, x2, y2) in boxes:
        region = image[y1 : y2 + 1, x1 : x2 + 1]
        if region.size == 0:
            continue
        # Object pixels are those that differ from the flat background mode.
        bg = np.median(region.reshape(-1, 3), axis=0)
        diff = np.abs(region.astype(np.float32) - bg).sum(axis=2)
        object_pixels = diff > np.percentile(diff, 35)
        sub = mask[y1 : y2 + 1, x1 : x2 + 1]
        sub[object_pixels] = 1
        mask[y1 : y2 + 1, x1 : x2 + 1] = sub
    return image, mask


# ---------------------------------------------------------------------------
# Dataset construction with source tracking
# ---------------------------------------------------------------------------


def _source_id(seed: int, index: int, tag: str) -> str:
    return f"{tag}-{seed}-{index}"


def make_classification_dataset(
    n_sources: int = 60,
    size: int = 32,
    seed: int = 0,
    variants_per_source: int = 3,
    classes: Sequence[str] = SHAPE_CLASSES,
) -> list[ImageRecord]:
    """Build records where each source yields several near-duplicate variants.

    The variants differ by a few pixels of jitter and brightness - realistic
    duplicates (burst photos, consecutive video frames), not exact copies.
    """
    rng = np.random.default_rng(seed)
    records: list[ImageRecord] = []
    for i in range(n_sources):
        kind = str(classes[i % len(classes)])
        base_rng = np.random.default_rng(seed * 1000 + i)
        base, meta = render_classification_sample(kind, size, base_rng)
        source = _source_id(seed, i, "cls")
        for v in range(variants_per_source):
            var_rng = np.random.default_rng(seed * 1000 + i * 17 + v)
            image = base.astype(np.float32) / 255.0
            image = np.roll(image, shift=(int(var_rng.integers(-2, 3)), int(var_rng.integers(-2, 3))), axis=(0, 1))
            image = np.clip(image * float(var_rng.uniform(0.9, 1.1)), 0, 1)
            records.append(
                ImageRecord(
                    image=(image * 255).astype(np.uint8),
                    label=list(classes).index(kind),
                    source_id=source,
                    meta={**meta, "variant": v},
                )
            )
    return records


def make_object_dataset(n_sources: int = 24, size: int = 32, seed: int = 1, variants_per_source: int = 3) -> list[ImageRecord]:
    rng = np.random.default_rng(seed)
    records: list[ImageRecord] = []
    for i in range(n_sources):
        kind = OBJECT_CLASSES[i % len(OBJECT_CLASSES)]
        base_rng = np.random.default_rng(seed * 2000 + i)
        base, meta = render_object_sample(kind, size, base_rng)
        source = _source_id(seed, i, "obj")
        for v in range(variants_per_source):
            var_rng = np.random.default_rng(seed * 2000 + i * 13 + v)
            image = base.astype(np.float32) / 255.0
            image = np.roll(image, shift=(int(var_rng.integers(-2, 3)), int(var_rng.integers(-2, 3))), axis=(0, 1))
            records.append(
                ImageRecord(
                    image=(np.clip(image, 0, 1) * 255).astype(np.uint8),
                    label=OBJECT_CLASSES.index(kind),
                    source_id=source,
                    meta={**meta, "variant": v},
                )
            )
    return records


def make_detection_dataset(n_images: int = 120, size: int = 64, seed: int = 2) -> list[ImageRecord]:
    """Detection records: label is ignored, ``meta['boxes']`` carries the truth."""
    records: list[ImageRecord] = []
    for i in range(n_images):
        rng = np.random.default_rng(seed * 3000 + i)
        image, boxes = render_detection_sample(size, rng)
        records.append(
            ImageRecord(
                image=image,
                label=-1,
                source_id=_source_id(seed, i, "det"),
                meta={"boxes": [{"class": k, "xyxy": b} for k, b in boxes], "width": size, "height": size},
            )
        )
    return records


def make_segmentation_dataset(n_images: int = 80, size: int = 64, seed: int = 3) -> list[ImageRecord]:
    records: list[ImageRecord] = []
    for i in range(n_images):
        rng = np.random.default_rng(seed * 4000 + i)
        image, mask = render_segmentation_sample(size, rng)
        records.append(
            ImageRecord(
                image=image,
                label=-1,
                source_id=_source_id(seed, i, "seg"),
                meta={"mask": mask, "class_counts": {c: int((mask == j).sum()) for j, c in enumerate(SEGMENTATION_CLASSES)}},
            )
        )
    return records


# ---------------------------------------------------------------------------
# Perceptual hashing and leakage audits
# ---------------------------------------------------------------------------


def dhash(image: np.ndarray, hash_size: int = 8) -> np.ndarray:
    """Difference hash: 64 bits describing coarse horizontal gradients.

    Robust to brightness and small shifts, so it catches near-duplicates that a
    filename or an exact-pixel check misses.
    """
    from PIL import Image

    gray = (to_gray(image) * 255).astype(np.uint8)
    img = Image.fromarray(gray).resize((hash_size + 1, hash_size), resample=Image.BILINEAR)
    arr = np.asarray(img, dtype=np.int16)
    diff = arr[:, 1:] > arr[:, :-1]
    return np.packbits(diff.reshape(-1))


def hamming(a: np.ndarray, b: np.ndarray) -> int:
    """Number of differing bits between two packed hashes."""
    return int(np.unpackbits(a.astype(np.uint8) ^ b.astype(np.uint8)).sum())


def near_duplicate_pairs(records: Sequence[ImageRecord], max_distance: int = 6) -> list[tuple[int, int, int]]:
    """Return ``(i, j, distance)`` for pairs whose perceptual hashes are close."""
    hashes = [dhash(r.image) for r in records]
    pairs = []
    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            d = hamming(hashes[i], hashes[j])
            if d <= max_distance:
                pairs.append((i, j, d))
    return pairs


def group_split(
    records: Sequence[ImageRecord],
    fractions: tuple[float, float, float] = (0.7, 0.15, 0.15),
    seed: int = 0,
) -> dict[str, list[ImageRecord]]:
    """Split by ``source_id`` group, never by individual image.

    Every variant of a source lands in exactly one split. This is the only
    splitting rule that survives near-duplicates, and it is why the synthetic
    generator bothers to record ``source_id`` at all.
    """
    if abs(sum(fractions) - 1.0) > 1e-6:
        raise ValueError(f"fractions must sum to 1, got {fractions}")
    groups: dict[str, list[ImageRecord]] = {}
    for rec in records:
        groups.setdefault(rec.source_id, []).append(rec)

    keys = sorted(groups)
    rng = np.random.default_rng(seed)
    rng.shuffle(keys)
    n = len(keys)
    n_train = int(round(n * fractions[0]))
    n_val = int(round(n * fractions[1]))
    n_train = min(n_train, n - 1)
    n_val = min(n_val, n - n_train - 0) if n - n_train > 1 else 0

    splits = {"train": keys[:n_train], "val": keys[n_train : n_train + n_val], "test": keys[n_train + n_val :]}
    return {name: [r for k in ks for r in groups[k]] for name, ks in splits.items()}


def stratified_group_split(
    records: Sequence[ImageRecord],
    fractions: tuple[float, float, float] = (0.7, 0.15, 0.15),
    seed: int = 0,
) -> dict[str, list[ImageRecord]]:
    """Group split that also guarantees every class reaches validation and test.

    ``group_split`` shuffles source ids without looking at labels. On a small
    multi-class set that can leave a class absent from test, which makes its
    precision and recall undefined. This variant shuffles sources *within each
    class*, then slices each class separately. It still keeps every variant of a
    source in one split, so the near-duplicate guarantee is unchanged.

    Every class needs at least two sources; three or more are recommended. A
    class with fewer sources cannot supply train, validation, and test groups.
    """

    if abs(sum(fractions) - 1.0) > 1e-6:
        raise ValueError(f"fractions must sum to 1, got {fractions}")
    by_label: dict[int, dict[str, list[ImageRecord]]] = {}
    for record in records:
        by_label.setdefault(record.label, {}).setdefault(record.source_id, []).append(record)

    rng = np.random.default_rng(seed)
    splits: dict[str, list[ImageRecord]] = {"train": [], "val": [], "test": []}
    for label in sorted(by_label):
        groups = by_label[label]
        keys = sorted(groups)
        if len(keys) < 2:
            raise ValueError(
                f"class {label} has {len(keys)} source group(s); at least 2 are needed "
                "for a train/test split"
            )
        rng.shuffle(keys)
        n = len(keys)
        n_train = max(1, int(round(n * fractions[0])))
        n_val = max(1, int(round(n * fractions[1]))) if n >= 3 else 0
        # Reserve at least one test source even when rounding fills train+val.
        if n_train + n_val >= n:
            n_train = max(1, n - n_val - 1)
        if n_train + n_val >= n:
            n_val = max(0, n - n_train - 1)
        assignment = (
            ["train"] * n_train
            + ["val"] * n_val
            + ["test"] * (n - n_train - n_val)
        )
        for key, split in zip(keys, assignment):
            splits[split].extend(groups[key])
    if not all(splits.values()):
        raise ValueError("stratified group split produced an empty split")
    return splits


def random_split(
    records: Sequence[ImageRecord],
    fractions: tuple[float, float, float] = (0.7, 0.15, 0.15),
    seed: int = 0,
) -> dict[str, list[ImageRecord]]:
    """Deliberately naive split - the control condition for the leakage lab.

    Provided so Lab 1 can show the inflated number next to the honest one
    instead of merely asserting that leakage is bad.
    """
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(records))
    n = len(records)
    n_train = int(n * fractions[0])
    n_val = int(n * fractions[1])
    idx = {
        "train": order[:n_train],
        "val": order[n_train : n_train + n_val],
        "test": order[n_train + n_val :],
    }
    return {name: [records[i] for i in ids] for name, ids in idx.items()}


def audit_leakage(splits: dict[str, list[ImageRecord]], max_hash_distance: int = 6) -> dict:
    """Report source overlap and near-duplicate pairs across splits.

    A non-empty result means the reported test score is not a test score.
    """
    names = list(splits)
    source_overlap = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = {r.source_id for r in splits[names[i]]}
            b = {r.source_id for r in splits[names[j]]}
            shared = sorted(a & b)
            if shared:
                source_overlap[f"{names[i]}|{names[j]}"] = shared

    cross_dupes = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            left = splits[names[i]]
            right = splits[names[j]]
            hashes_right = [(k, dhash(r.image)) for k, r in enumerate(right)]
            for k, rec in enumerate(left):
                h = dhash(rec.image)
                for m, h2 in hashes_right:
                    if hamming(h, h2) <= max_hash_distance:
                        cross_dupes.append((names[i], k, names[j], m))

    return {
        "source_overlap": source_overlap,
        "n_shared_sources": sum(len(v) for v in source_overlap.values()),
        "cross_split_near_duplicates": cross_dupes[:50],
        "cross_split_near_duplicate_count": len(cross_dupes),
        # A hard leak means the same source appears in two splits: the test score
        # is invalid. A soft leak means two different sources look alike, which is
        # a genuine ambiguity in the data rather than a splitting bug.
        "hard_leaky": bool(source_overlap),
        "soft_leaky": bool(cross_dupes),
        "leaky": bool(source_overlap or cross_dupes),
    }


def class_balance(records: Sequence[ImageRecord], classes: Sequence[str]) -> dict[str, int]:
    counts = {name: 0 for name in classes}
    for rec in records:
        if 0 <= rec.label < len(classes):
            counts[classes[rec.label]] += 1
    return counts


# ---------------------------------------------------------------------------
# CSV manifests, so datasets are inspectable without Python
# ---------------------------------------------------------------------------


def write_manifest(records: Sequence[ImageRecord], path: str | Path, label_names: Sequence[str] | None = None) -> Path:
    """Write a CSV manifest next to the images.

    Columns: ``file,label,label_name,source_id,split`` shall be filled by the
    caller-facing writer below; this low-level writer keeps the given order.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["file,label,label_name,source_id"]
    for i, rec in enumerate(records):
        name = label_names[rec.label] if label_names and 0 <= rec.label < len(label_names) else str(rec.label)
        lines.append(f"{i:05d}.png,{rec.label},{name},{rec.source_id}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def save_split_images(
    splits: dict[str, list[ImageRecord]],
    root: str | Path,
    label_names: Sequence[str] | None = None,
) -> dict[str, Path]:
    """Write ``root/<split>/<index>.png`` and a manifest per split."""
    root = Path(root)
    outputs: dict[str, Path] = {}
    for name, records in splits.items():
        directory = root / name
        directory.mkdir(parents=True, exist_ok=True)
        for i, rec in enumerate(records):
            save_image(rec.image, directory / f"{i:05d}.png")
        outputs[name] = write_manifest(records, root / f"{name}.csv", label_names)
    return outputs
