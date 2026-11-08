"""Face detection, landmarks, embeddings, verification, and identification.

Scope, stated before the code because it is a design decision and not a caveat
buried in a footnote:

* Every face here is **synthetic**. There is no real person in the data, no
  scraped image, and no path by which this code could be pointed at one without
  the operator supplying images and therefore taking responsibility.
* The exercises cover **detection, landmarks, verification, identification, and
  embeddings** - the five concepts students confuse - using controlled,
  consent-based demonstrations.
* Nothing here builds surveillance: there is no video ingest, no persistent
  gallery, no face tracking, and :func:`enroll` requires an explicit list of
  images you already have the right to use.

The detector is deliberately classical (skin-tone region plus template
correlation) rather than a downloaded neural model. That choice is pedagogically
useful: its failure mode is *uneven recall across skin tones*, which is a real
and well-documented property of colour-based face detection, and Lab 6's bias
measurement shows it numerically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from .annotations import box_iou
from .imaging import to_float, to_gray

FACE_SIZE = 48


@dataclass
class FaceIdentity:
    """Parameters that make one synthetic person distinguishable from another."""

    name: str
    skin: tuple[int, int, int]
    tone_group: str  # used only to measure detector recall per group
    face_ratio: float = 0.62
    eye_spacing: float = 0.34
    eye_y: float = 0.36
    mouth_width: float = 0.26
    hair: float = 0.25

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "tone_group": self.tone_group,
            "face_ratio": self.face_ratio,
            "eye_spacing": self.eye_spacing,
            "eye_y": self.eye_y,
            "mouth_width": self.mouth_width,
        }


# Three tone groups with clearly different luminance. This is a property of the
# *synthetic data*, chosen to expose a detector bias; it is not a claim that
# real people fall into three groups.
DEFAULT_IDENTITIES: tuple[FaceIdentity, ...] = (
    FaceIdentity("id_amara", (150, 105, 80), "tone_a", 0.60, 0.32, 0.37, 0.24, 0.20),
    FaceIdentity("id_elif", (175, 130, 105), "tone_a", 0.63, 0.31, 0.38, 0.23, 0.45),
    FaceIdentity("id_ben", (205, 160, 125), "tone_b", 0.64, 0.35, 0.36, 0.28, 0.55),
    FaceIdentity("id_chen", (225, 185, 150), "tone_b", 0.62, 0.33, 0.35, 0.25, 0.15),
    FaceIdentity("id_farid", (235, 200, 170), "tone_b", 0.59, 0.34, 0.36, 0.27, 0.60),
    FaceIdentity("id_dara", (110, 75, 55), "tone_c", 0.61, 0.36, 0.37, 0.30, 0.30),
    FaceIdentity("id_kofi", (72, 48, 38), "tone_d_dark", 0.60, 0.34, 0.37, 0.26, 0.25),
    FaceIdentity("id_noor", (250, 240, 232), "tone_e_light", 0.62, 0.33, 0.36, 0.24, 0.35),
)


@dataclass
class FaceRecord:
    image: np.ndarray
    identity: str
    tone_group: str
    truth_box: tuple[int, int, int, int]
    landmarks: dict
    meta: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"identity": self.identity, "tone_group": self.tone_group, "truth_box": list(self.truth_box)}


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_face(identity: FaceIdentity, rng: np.random.Generator, size: int = FACE_SIZE) -> tuple[np.ndarray, tuple[int, int, int, int], dict]:
    """Draw one synthetic face and return the image, truth box, and landmarks."""
    background_level = float(rng.uniform(0.45, 0.85))
    canvas = np.full((size, size, 3), background_level, dtype=np.float32)
    canvas += rng.normal(0.0, 0.015, canvas.shape).astype(np.float32)

    face_w = size * identity.face_ratio * float(rng.uniform(0.94, 1.06))
    face_h = face_w * float(rng.uniform(1.15, 1.28))
    cx = size / 2 + float(rng.uniform(-1.5, 1.5))
    cy = size / 2 + float(rng.uniform(-1.5, 1.5))

    yy, xx = np.mgrid[0:size, 0:size]
    head = ((xx - cx) / (face_w / 2)) ** 2 + ((yy - cy) / (face_h / 2)) ** 2 <= 1.0
    skin = np.asarray(identity.skin, dtype=np.float32) / 255.0
    shading = np.clip(1.12 - np.abs(xx - cx) / (size * 1.4), 0.85, 1.08)
    for c in range(3):
        canvas[..., c] = np.where(head, skin[c] * shading, canvas[..., c])

    # Hair: an arc across the top of the head.
    hair_mask = head & (yy < cy - face_h * 0.18) & (np.abs(xx - cx) < face_w * 0.52)
    for c in range(3):
        canvas[..., c] = np.where(hair_mask, canvas[..., c] * (1 - identity.hair) + 0.12 * identity.hair, canvas[..., c])

    eye_dx = face_w * identity.eye_spacing / 2
    eye_y = cy - face_h * (0.5 - identity.eye_y)
    left_eye = (cx - eye_dx, eye_y)
    right_eye = (cx + eye_dx, eye_y)
    eye_r = max(1.2, face_w * 0.06)

    for ex, ey in (left_eye, right_eye):
        white = ((xx - ex) ** 2 + (yy - ey) ** 2) <= (eye_r * 1.5) ** 2
        pupil = ((xx - ex) ** 2 + (yy - ey) ** 2) <= eye_r**2
        canvas[white] = canvas[white] * 0.35 + 0.9 * 0.65
        canvas[pupil] = 0.08

    mouth_y = cy + face_h * 0.26
    mouth_w = face_w * identity.mouth_width
    mouth = (np.abs(xx - cx) <= mouth_w) & (np.abs(yy - mouth_y) <= max(1.0, face_h * 0.035))
    canvas[mouth] = 0.22

    x1 = int(max(0, cx - face_w / 2))
    y1 = int(max(0, cy - face_h / 2))
    x2 = int(min(size - 1, cx + face_w / 2))
    y2 = int(min(size - 1, cy + face_h / 2))
    landmarks = {
        "left_eye": [float(left_eye[0]), float(left_eye[1])],
        "right_eye": [float(right_eye[0]), float(right_eye[1])],
        "mouth": [float(cx), float(mouth_y)],
    }
    image = (np.clip(canvas, 0, 1) * 255).astype(np.uint8)
    return image, (x1, y1, x2, y2), landmarks


def make_face_dataset(
    identities: Sequence[FaceIdentity] = DEFAULT_IDENTITIES,
    per_identity: int = 6,
    size: int = FACE_SIZE,
    seed: int = 0,
) -> list[FaceRecord]:
    """Several variants per identity: the variation is what makes verification hard."""
    records: list[FaceRecord] = []
    for i, identity in enumerate(identities):
        for j in range(per_identity):
            rng = np.random.default_rng(seed * 5000 + i * 37 + j)
            image, box, landmarks = render_face(identity, rng, size)
            records.append(
                FaceRecord(
                    image=image,
                    identity=identity.name,
                    tone_group=identity.tone_group,
                    truth_box=box,
                    landmarks=landmarks,
                    meta={"variant": j},
                )
            )
    return records


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


def skin_mask(image: np.ndarray) -> np.ndarray:
    """Classic RGB skin-tone rule (Kovac et al.), used as the detector's first stage.

    The rule was tuned on a narrow range of skin tones and lighting; that is the
    bias the lab measures rather than hides.
    """
    arr = image.astype(np.int16)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    rule = (r > 95) & (g > 40) & (b > 20) & (r > g) & (r > b) & (np.abs(r - g) > 15)
    return rule.astype(np.uint8)


def _largest_component_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    """Bounding box of the largest 4-connected region, via iterative flood fill."""
    if mask.sum() < 20:
        return None
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best = None
    best_area = 0
    for sy in range(0, h, 2):
        for sx in range(0, w, 2):
            if not mask[sy, sx] or seen[sy, sx]:
                continue
            stack = [(sy, sx)]
            seen[sy, sx] = True
            area = 0
            min_y = max_y = sy
            min_x = max_x = sx
            while stack:
                y, x = stack.pop()
                area += 1
                min_y, max_y = min(min_y, y), max(max_y, y)
                min_x, max_x = min(min_x, x), max(max_x, x)
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            if area > best_area:
                best_area = area
                best = (min_x, min_y, max_x, max_y)
    if best is None or best_area < 40:
        return None
    return best


def detect_face(image: np.ndarray, min_area: int = 150) -> dict:
    """Return ``{"found", "box", "score"}`` for the largest face-like region."""
    mask = skin_mask(image)
    box = _largest_component_bbox(mask)
    if box is None:
        return {"found": False, "box": None, "score": 0.0}
    x1, y1, x2, y2 = box
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    if area < min_area:
        return {"found": False, "box": None, "score": 0.0}
    coverage = float(mask[y1 : y2 + 1, x1 : x2 + 1].mean())
    return {"found": True, "box": box, "score": coverage}


def detection_report(
    records: Sequence[FaceRecord],
    iou_threshold: float = 0.3,
    group_key: str = "tone_group",
) -> dict:
    """Detection recall overall and per group.

    A single overall recall hides exactly the failure that matters: a detector can
    score 0.85 overall while missing most of one group entirely. ``per_group`` is
    the number to report.
    """
    overall_hits, per_group = 0, {}
    for rec in records:
        result = detect_face(rec.image)
        hit = result["found"] and box_iou(tuple(result["box"]), rec.truth_box) >= iou_threshold
        overall_hits += int(bool(hit))
        key = getattr(rec, group_key)
        stats = per_group.setdefault(key, {"n": 0, "hits": 0})
        stats["n"] += 1
        stats["hits"] += int(bool(hit))

    return {
        "overall_recall": overall_hits / max(1, len(records)),
        "iou_threshold": iou_threshold,
        "per_group": {k: {"recall": v["hits"] / v["n"], "n": v["n"], "hits": v["hits"]} for k, v in per_group.items()},
        "n": len(records),
    }


# ---------------------------------------------------------------------------
# Landmarks
# ---------------------------------------------------------------------------


def locate_landmarks(image: np.ndarray, box: tuple[int, int, int, int]) -> dict:
    """Estimate eye and mouth positions inside a detected face box.

    Method: threshold the darkest pixels, then use geometry - two dark blobs in
    the upper half are eyes, the dark blob in the lower half is the mouth. Simple,
    inspectable, and obviously not a learned landmark model; the lab asks students
    to compare it with the truth landmarks and report the median error.
    """
    x1, y1, x2, y2 = (int(v) for v in box)
    crop = to_float(image[max(0, y1) : y2 + 1, max(0, x1) : x2 + 1])
    if crop.size == 0:
        return {"found": False}
    gray = to_gray(crop)
    threshold = float(np.percentile(gray, 8))
    dark = gray <= threshold
    h, w = gray.shape
    upper = dark[: int(h * 0.7)]
    lower = dark[int(h * 0.55) :]

    def centroid(mask: np.ndarray, offset_y: int = 0) -> list[float] | None:
        if mask.sum() < 2:
            return None
        ys, xs = np.nonzero(mask)
        return [float(xs.mean() + x1), float(ys.mean() + y1 + offset_y)]

    left_half = centroid(upper[:, : w // 2]) if upper.size else None
    right_half = centroid(upper[:, w // 2 :]) if upper.size else None
    if right_half is not None:
        right_half[0] += w // 2
    mouth = centroid(lower, int(h * 0.55)) if lower.size else None

    found = bool(left_half and right_half)
    return {"found": found, "left_eye": left_half, "right_eye": right_half, "mouth": mouth}


def landmark_error(predicted: dict, truth: dict) -> float:
    """Mean Euclidean distance between predicted and true landmarks, in pixels."""
    errors = []
    for key in ("left_eye", "right_eye", "mouth"):
        p, t = predicted.get(key), truth.get(key)
        if p and t:
            errors.append(float(np.hypot(p[0] - t[0], p[1] - t[1])))
    return float(np.mean(errors)) if errors else float("nan")


# ---------------------------------------------------------------------------
# Embeddings, verification, identification
# ---------------------------------------------------------------------------


def face_embedding(
    image: np.ndarray,
    box: tuple[int, int, int, int],
    landmarks: dict | None = None,
    size: int = 32,
) -> np.ndarray:
    """A 192-dim embedding from an aligned crop.

    Two features that survive lighting and small shifts: a 10x10 grayscale thumbnail
    (100 values) and a coarse histogram of image gradients (8 bins over an 8x8
    grid, 128 values). No training, so it is reproducible on any machine - and its
    weakness (it encodes appearance, not identity) is the honest finding of the
    verification lab.
    """
    from .imaging import resize

    x1, y1, x2, y2 = (int(v) for v in box)
    crop = image[max(0, y1) : y2 + 1, max(0, x1) : x2 + 1]
    if crop.size == 0:
        return np.zeros(228, dtype=np.float32)

    if landmarks and landmarks.get("left_eye") and landmarks.get("right_eye"):
        left = np.asarray(landmarks["left_eye"], dtype=np.float64) - np.array([x1, y1])
        right = np.asarray(landmarks["right_eye"], dtype=np.float64) - np.array([x1, y1])
        angle = float(np.degrees(np.arctan2(right[1] - left[1], right[0] - left[0])))
        if abs(angle) > 1.0:
            from PIL import Image

            crop = np.asarray(Image.fromarray(crop).rotate(angle, resample=Image.BILINEAR), dtype=np.uint8)

    small = resize(crop, (size, size), resample="bilinear")
    gray = to_gray(small)

    thumb = resize((gray * 255).astype(np.uint8), (10, 10), resample="bilinear").astype(np.float32) / 255.0
    thumb = thumb.reshape(-1)

    gy, gx = np.gradient(gray)
    magnitude = np.hypot(gx, gy)
    angle = (np.arctan2(gy, gx) + np.pi) % np.pi
    bins = 8
    cell = size // 8
    grid = []
    for by in range(8):
        for bx in range(8):
            m = magnitude[by * cell : (by + 1) * cell, bx * cell : (bx + 1) * cell].reshape(-1)
            a = angle[by * cell : (by + 1) * cell, bx * cell : (bx + 1) * cell].reshape(-1)
            hist, _ = np.histogram(a, bins=bins, range=(0, np.pi), weights=m)
            grid.append(hist / (hist.sum() + 1e-6))
    hog = np.concatenate(grid)

    vector = np.concatenate([thumb, hog]).astype(np.float32)
    return vector / max(1e-6, float(np.linalg.norm(vector)))


def embed_face_records(records: Sequence[FaceRecord]) -> tuple[np.ndarray, list[str]]:
    """Embeddings and labels for a set of face records, detecting + landmarking first."""
    vectors, labels = [], []
    for rec in records:
        detection = detect_face(rec.image)
        box = detection["box"] if detection["found"] else rec.truth_box
        landmarks = locate_landmarks(rec.image, box)
        vectors.append(face_embedding(rec.image, box, landmarks))
        labels.append(rec.identity)
    return np.stack(vectors), labels


def pair_scores(records: Sequence[FaceRecord]) -> tuple[list[float], list[bool]]:
    """Cosine similarity for every unordered pair, and whether it is the same person.

    Both directions matter: same-person pairs are what you want to accept, and
    different-person pairs are what you must reject. A single accuracy number over
    all pairs hides which of the two is failing.
    """
    embeddings, labels = embed_face_records(records)
    scores, same = [], []
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            scores.append(float(embeddings[i] @ embeddings[j]))
            same.append(labels[i] == labels[j])
    return scores, same


def enroll(records: Sequence[FaceRecord], consent_note: str = "") -> dict:
    """Build a gallery from records.

    ``consent_note`` is required in spirit, not enforced by code: this function is
    the point where a student must write down whose images these are. A gallery
    is personal data even when every image is synthetic, because the habit is what
    carries over to real use.
    """
    embeddings, labels = embed_face_records(records)
    return {
        "embeddings": embeddings,
        "labels": labels,
        "consent_note": consent_note,
        "size": len(labels),
    }
