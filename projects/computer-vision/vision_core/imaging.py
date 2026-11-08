"""Image representation, conversion, resizing, normalization, and augmentation.

Everything here works on NumPy arrays in HWC layout with uint8 values 0-255 for
storage and float32 0-1 (or normalized) for modelling. Pillow handles decode and
resample; no OpenCV or scikit-image is required.

Channel conventions used across the section:

* ``HWC`` - height, width, channels. What Pillow and the filesystem give you.
* ``CHW`` - channels, height, width. What PyTorch convolutions expect.
* ``NHWC``/``NCHW`` - the same with a leading batch axis.

Most beginner vision bugs are a channel-axis or value-range mistake that silently
produces a plausible-looking but meaningless tensor. The helpers below keep the
conversion explicit so those bugs surface early.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import Image

# Formats the course reads and writes. PPM is included because it is uncompressed
# and trivially inspectable; JPEG because it is where lossy artifacts live.
READABLE_FORMATS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".bmp", ".ppm", ".webp")
LOSSLESS_FORMATS: tuple[str, ...] = (".png", ".bmp", ".ppm")

# Rec. 601 luma weights: the standard conversion used by most vision pipelines.
LUMA_WEIGHTS = np.array([0.299, 0.587, 0.114], dtype=np.float32)

# ImageNet statistics, reused by every pretrained-model lab. Using the wrong
# statistics is the single most common cause of "pretrained model performs badly".
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


# ---------------------------------------------------------------------------
# Loading and saving
# ---------------------------------------------------------------------------


def load_image(path: str | Path, mode: str = "RGB") -> np.ndarray:
    """Read an image file into an HWC uint8 array.

    ``mode`` follows Pillow: ``"RGB"`` (3 channels), ``"L"`` (grayscale, 1
    channel), ``"RGBA"`` (4 channels). Converting on load is deliberate - a
    dataset that mixes grayscale and RGB files will otherwise produce a tensor
    stack that fails or, worse, silently broadcasts.
    """
    path = Path(path)
    if path.suffix.lower() not in READABLE_FORMATS:
        raise ValueError(f"unsupported image extension {path.suffix!r}; expected one of {READABLE_FORMATS}")
    with Image.open(path) as img:
        converted = img.convert(mode)
        return np.asarray(converted, dtype=np.uint8)


def save_image(array: np.ndarray, path: str | Path, quality: int = 92) -> Path:
    """Write an HWC array (uint8, or float 0-1) to disk, creating parents.

    JPEG is lossy and the loss is what Module 1 measures; PNG is lossless and
    reversible. ``quality`` is ignored for PNG.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    array = as_uint8(array)
    if array.ndim == 2:
        img = Image.fromarray(array, mode="L")
    elif array.ndim == 3 and array.shape[2] == 1:
        img = Image.fromarray(array[..., 0], mode="L")
    elif array.ndim == 3 and array.shape[2] in (3, 4):
        mode = "RGB" if array.shape[2] == 3 else "RGBA"
        img = Image.fromarray(array, mode=mode)
    else:
        raise ValueError(f"expected HxW or HxWxC with C in (1,3,4), got shape {array.shape}")

    suffix = path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        img = img.convert("RGB")
        img.save(path, quality=int(quality), subsampling=0)
    else:
        img.save(path)
    return path


def image_info(path: str | Path) -> dict:
    """Metadata without decoding pixel data: size, mode, format, bytes on disk."""
    path = Path(path)
    with Image.open(path) as img:
        return {
            "path": str(path),
            "format": img.format,
            "mode": img.mode,
            "width": img.width,
            "height": img.height,
            "bytes": path.stat().st_size,
            "bits_per_pixel": len(img.getbands()) * 8,
        }


# ---------------------------------------------------------------------------
# Value range and dtype conversion
# ---------------------------------------------------------------------------


def as_uint8(array: np.ndarray) -> np.ndarray:
    """Convert float 0-1 (or already-uint8) data to uint8 without wrapping.

    Naive ``astype(np.uint8)`` on a float array truncates and, if values exceed
    1.0, produces garbage. This clips first so the failure is visible in the
    output rather than in the dtype.
    """
    array = np.asarray(array)
    if array.dtype == np.uint8:
        return array
    if np.issubdtype(array.dtype, np.floating):
        return np.clip(np.rint(array * 255.0), 0, 255).astype(np.uint8)
    return np.clip(array, 0, 255).astype(np.uint8)


def to_float(array: np.ndarray) -> np.ndarray:
    """Scale uint8 0-255 to float32 0-1. Idempotent for float input."""
    array = np.asarray(array)
    if np.issubdtype(array.dtype, np.floating):
        return array.astype(np.float32)
    return (array.astype(np.float32) / 255.0).clip(0.0, 1.0)


def to_tensor(array: np.ndarray) -> np.ndarray:
    """HWC -> CHW. Keeps the dtype and value range unchanged."""
    array = np.asarray(array)
    if array.ndim == 2:
        return array[None, ...]
    if array.ndim != 3:
        raise ValueError(f"expected HxW or HxWxC, got shape {array.shape}")
    return np.transpose(array, (2, 0, 1))


def from_tensor(array: np.ndarray) -> np.ndarray:
    """CHW -> HWC. The inverse of :func:`to_tensor`."""
    array = np.asarray(array)
    if array.ndim == 2:
        return array
    if array.ndim != 3:
        raise ValueError(f"expected CxHxW, got shape {array.shape}")
    return np.transpose(array, (1, 2, 0))


# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------


def to_gray(array: np.ndarray) -> np.ndarray:
    """HWC RGB -> HW float32 luminance using Rec. 601 weights.

    Averaging the three channels (``mean(axis=2)``) is a common shortcut and a
    different transform: it makes pure blue and pure red equally bright, while
    luma makes blue much darker. The weights are a modelling choice, not a
    detail, which is why edge detectors and face templates behave differently
    under each.
    """
    array = to_float(array)
    if array.ndim == 2:
        return array
    if array.shape[2] == 1:
        return array[..., 0]
    return np.tensordot(array[..., :3], LUMA_WEIGHTS, axes=([-1], [0])).astype(np.float32)


def to_channels(array: np.ndarray, channels: int) -> np.ndarray:
    """Force an image to 1, 3, or 4 channels (HWC, float32 0-1)."""
    array = to_float(array)
    if array.ndim == 2:
        array = array[..., None]
    have = array.shape[2]
    if channels == have:
        return array
    if channels == 1:
        return to_gray(array)[..., None]
    if channels == 3:
        if have == 1:
            return np.repeat(array, 3, axis=2)
        return array[..., :3]
    if channels == 4:
        if have == 3:
            alpha = np.ones(array.shape[:2] + (1,), dtype=np.float32)
            return np.concatenate([array, alpha], axis=2)
        if have == 1:
            return np.concatenate([np.repeat(array, 3, axis=2), np.ones_like(array)], axis=2)
    raise ValueError(f"cannot convert {have} channels to {channels}")


def split_channels(array: np.ndarray) -> dict[str, np.ndarray]:
    """Named single-channel views, for teaching what each channel carries."""
    array = to_float(array)
    if array.ndim == 2:
        array = array[..., None]
    names = ("red", "green", "blue", "alpha")
    return {name: array[..., i] for i, name in enumerate(names[: array.shape[2]])}


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------


def resize(array: np.ndarray, size: tuple[int, int], resample: str = "bilinear") -> np.ndarray:
    """Resize to ``size=(width, height)`` and return uint8 HWC.

    Note the (width, height) order - it is Pillow's, and swapping it is the
    second most common beginner bug after channel order. Non-square resizing
    distorts aspect ratio, which changes object shape; :func:`letterbox`
    preserves it at the cost of padding.
    """
    filters = {
        "nearest": Image.NEAREST,
        "bilinear": Image.BILINEAR,
        "bicubic": Image.BICUBIC,
        "lanczos": Image.LANCZOS,
    }
    if resample not in filters:
        raise ValueError(f"unknown resample {resample!r}; choose from {sorted(filters)}")
    width, height = int(size[0]), int(size[1])
    if width <= 0 or height <= 0:
        raise ValueError(f"size must be positive, got {size}")
    source = as_uint8(array)
    img = Image.fromarray(source[..., 0] if source.ndim == 3 and source.shape[2] == 1 else source)
    return np.asarray(img.resize((width, height), resample=filters[resample]), dtype=np.uint8)


def letterbox(array: np.ndarray, size: tuple[int, int], fill: int = 114) -> tuple[np.ndarray, dict]:
    """Resize preserving aspect ratio, pad the remainder, and return the mapping.

    The returned ``scale`` and ``pad`` let you map predicted boxes back to the
    original coordinates. Forgetting that step is why augmented-model detections
    land in the wrong place.
    """
    src = as_uint8(array)
    h, w = src.shape[:2]
    width, height = int(size[0]), int(size[1])
    scale = min(width / w, height / h)
    new_w, new_h = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    resized = resize(src, (new_w, new_h), resample="bilinear")
    canvas = np.full((height, width, resized.shape[2]), fill, dtype=np.uint8)
    top, left = (height - new_h) // 2, (width - new_w) // 2
    canvas[top : top + new_h, left : left + new_w] = resized
    return canvas, {"scale": scale, "pad": (left, top), "original": (w, h), "resized": (new_w, new_h)}


def center_crop(array: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    """Crop a centred window of ``size=(width, height)``, padding if needed."""
    src = as_uint8(array)
    h, w = src.shape[:2]
    width, height = int(size[0]), int(size[1])
    out = np.zeros((height, width, src.shape[2]), dtype=np.uint8)
    top, left = max(0, (h - height) // 2), max(0, (w - width) // 2)
    src_top, src_left = max(0, (height - h) // 2), max(0, (width - w) // 2)
    copy_h = min(h - src_top, height - top)
    copy_w = min(w - src_left, width - left)
    out[top : top + copy_h, left : left + copy_w] = src[src_top : src_top + copy_h, src_left : src_left + copy_w]
    return out


def random_crop(array: np.ndarray, size: tuple[int, int], rng: np.random.Generator) -> np.ndarray:
    """Crop a random window; a cheap spatial augmentation."""
    src = as_uint8(array)
    h, w = src.shape[:2]
    width, height = min(int(size[0]), w), min(int(size[1]), h)
    top = int(rng.integers(0, h - height + 1))
    left = int(rng.integers(0, w - width + 1))
    return src[top : top + height, left : left + width]


# ---------------------------------------------------------------------------
# Intensity normalization
# ---------------------------------------------------------------------------


def normalize(array: np.ndarray, mean: Sequence[float] = IMAGENET_MEAN, std: Sequence[float] = IMAGENET_STD) -> np.ndarray:
    """Per-channel standardization: ``(x - mean) / std`` on float 0-1 data."""
    array = to_float(array)
    if array.ndim == 2:
        array = array[..., None]
    mean_arr = np.asarray(mean, dtype=np.float32).reshape(1, 1, -1)
    std_arr = np.asarray(std, dtype=np.float32).reshape(1, 1, -1)
    if mean_arr.shape[-1] != array.shape[-1]:
        raise ValueError(f"mean has {mean_arr.shape[-1]} values but image has {array.shape[-1]} channels")
    if np.any(std_arr == 0):
        raise ValueError("std must be non-zero")
    return ((array - mean_arr) / std_arr).astype(np.float32)


def denormalize(array: np.ndarray, mean: Sequence[float] = IMAGENET_MEAN, std: Sequence[float] = IMAGENET_STD) -> np.ndarray:
    """Inverse of :func:`normalize`, clipped to 0-1.

    Needed to *look* at an augmented image. Without it, a normalized tensor
    rendered as uint8 is a clipped mess and students conclude augmentation is
    broken.
    """
    array = np.asarray(array, dtype=np.float32)
    if array.ndim == 2:
        array = array[..., None]
    mean_arr = np.asarray(mean, dtype=np.float32).reshape(1, 1, -1)
    std_arr = np.asarray(std, dtype=np.float32).reshape(1, 1, -1)
    return np.clip(array * std_arr + mean_arr, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Augmentation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AugmentConfig:
    """Deterministic augmentation settings.

    ``p`` values are probabilities applied in a fixed order with a supplied
    seed, so the same seed reproduces the same batch. Randomness without a seed
    makes training curves impossible to compare.
    """

    hflip_p: float = 0.5
    rotate_deg: float = 0.0
    max_shift: int = 0
    brightness: float = 0.0
    contrast: float = 0.0
    noise_std: float = 0.0
    erase_p: float = 0.0


def augment(array: np.ndarray, config: AugmentConfig, rng: np.random.Generator) -> np.ndarray:
    """Apply the configured augmentations in a documented, reproducible order:

    horizontal flip -> rotation -> shift -> brightness -> contrast -> noise -> erase.

    Order matters: brightness applied before noise gives different pixels than
    noise before brightness, and the difference shows up when you compare two
    students' reported accuracy.
    """
    out = as_uint8(array)
    if out.ndim == 2:
        out = out[..., None]

    if config.hflip_p > 0 and rng.random() < config.hflip_p:
        out = out[:, ::-1, :]

    if config.rotate_deg > 0:
        angle = float(rng.uniform(-config.rotate_deg, config.rotate_deg))
        img = Image.fromarray(out[..., 0] if out.shape[2] == 1 else out)
        img = img.rotate(angle, resample=Image.BILINEAR, expand=False, fillcolor=0)
        out = np.asarray(img, dtype=np.uint8)
        if out.ndim == 2:
            out = out[..., None]

    if config.max_shift > 0:
        dy = int(rng.integers(-config.max_shift, config.max_shift + 1))
        dx = int(rng.integers(-config.max_shift, config.max_shift + 1))
        out = np.roll(out, shift=(dy, dx), axis=(0, 1))

    floats = to_float(out)
    if config.brightness > 0:
        factor = 1.0 + float(rng.uniform(-config.brightness, config.brightness))
        floats = floats * factor
    if config.contrast > 0:
        factor = 1.0 + float(rng.uniform(-config.contrast, config.contrast))
        floats = (floats - floats.mean(axis=(0, 1), keepdims=True)) * factor + floats.mean(axis=(0, 1), keepdims=True)
    if config.noise_std > 0:
        floats = floats + rng.normal(0.0, config.noise_std, size=floats.shape).astype(np.float32)
    floats = np.clip(floats, 0.0, 1.0)

    if config.erase_p > 0 and rng.random() < config.erase_p:
        h, w = floats.shape[:2]
        eh, ew = max(1, int(h * 0.25)), max(1, int(w * 0.25))
        top = int(rng.integers(0, max(1, h - eh)))
        left = int(rng.integers(0, max(1, w - ew)))
        floats[top : top + eh, left : left + ew] = 0.0

    return as_uint8(floats)


def augment_batch(images: np.ndarray, config: AugmentConfig, seed: int) -> np.ndarray:
    """Augment an NHWC batch with one derived RNG per image."""
    rng = np.random.default_rng(seed)
    return np.stack([augment(img, config, rng) for img in images])


# ---------------------------------------------------------------------------
# Degradations, used by the robustness lab
# ---------------------------------------------------------------------------


def add_noise(array: np.ndarray, std: float, seed: int = 0) -> np.ndarray:
    """Gaussian noise in 0-1 units, clipped. ``std`` is in the same units."""
    rng = np.random.default_rng(seed)
    floats = to_float(array) + rng.normal(0.0, std, size=to_float(array).shape).astype(np.float32)
    return as_uint8(np.clip(floats, 0.0, 1.0))


def adjust_brightness(array: np.ndarray, factor: float) -> np.ndarray:
    return as_uint8(np.clip(to_float(array) * float(factor), 0.0, 1.0))


def blur(array: np.ndarray, radius: float) -> np.ndarray:
    """Gaussian blur via Pillow, which avoids a scipy/skimage dependency."""
    img = Image.fromarray(as_uint8(array))
    from PIL import ImageFilter

    return np.asarray(img.filter(ImageFilter.GaussianBlur(radius=radius)), dtype=np.uint8)


def jpeg_roundtrip(array: np.ndarray, quality: int) -> np.ndarray:
    """Compress to JPEG in memory and decode again: measures compression loss."""
    buffer = __import__("io").BytesIO()
    Image.fromarray(as_uint8(array)).convert("RGB").save(buffer, format="JPEG", quality=int(quality))
    buffer.seek(0)
    with Image.open(buffer) as img:
        return np.asarray(img.convert("RGB"), dtype=np.uint8)


def occlude(array: np.ndarray, box: tuple[int, int, int, int], fill: int = 0) -> np.ndarray:
    """Paint a rectangle (x1, y1, x2, y2) - the occlusion robustness test."""
    out = as_uint8(array).copy()
    x1, y1, x2, y2 = (int(v) for v in box)
    out[max(0, y1) : max(0, y2), max(0, x1) : max(0, x2)] = fill
    return out
