"""Reading, probing, and writing video files with OpenCV.

Video is the first data type in this course that is *not* a single array. A file is a
container (MP4, AVI), holding a stream encoded with a codec (H.264, MPEG-4 part 2, MJPEG),
holding frames at some frame rate, with timestamps that may or may not be uniform. Three
consequences drive every lab in this section:

* you cannot index a frame by time without knowing the frame rate;
* a codec can change pixel values slightly, so two decodes of the same file may differ;
* an unreadable file fails silently in most APIs - ``cap.read()`` returns ``False`` and a
  program that does not check keeps going with an empty frame.

Everything here wraps OpenCV and adds the two things the raw API does not give you: an
explicit failure type (``VideoError``) and a probe that reports what the file actually is
rather than what its extension claims.

No side effects at import: the module only touches the filesystem when a function is called.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Sequence

import cv2
import numpy as np

# OpenCV logs codec problems to stderr before returning an error code. The labs handle
# errors explicitly, so silence the duplicate library chatter and keep the transcript
# readable. Set VIDEO_CORE_VERBOSE=1 to see it again while debugging.
if os.environ.get("VIDEO_CORE_VERBOSE", "0") != "1":
    try:
        cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)
    except Exception:  # pragma: no cover - depends on the OpenCV build
        pass

# Codecs verified on this machine. H.264 ("avc1"/"H264") needs an external encoder
# (OpenH264 or x264) and is refused here with an explicit error instead of a silent
# zero-byte file. MPEG-4 part 2 ("mp4v") works in every OpenCV wheel we have tested and
# plays in browsers; MJPEG ("MJPG") is larger but decodes fastest and is the best choice
# for intermediate frames that will be read back immediately.
SUPPORTED_FOURCC = {
    "mp4v": ".mp4",
    "MJPG": ".avi",
    "XVID": ".avi",
}

# COCO class names that matter for traffic work, in torchvision's index order.
TRAFFIC_CLASSES = ("car", "motorcycle", "bus", "truck")


class VideoError(RuntimeError):
    """Raised when a video cannot be opened, decoded, or written.

    Carries ``reason`` so a caller can distinguish "file is corrupt" from "codec is
    missing" without parsing a message string.
    """

    def __init__(self, path: str | Path, reason: str, detail: str = "") -> None:
        self.path = str(path)
        self.reason = reason
        self.detail = detail
        message = f"{self.path}: {reason}"
        if detail:
            message += f" ({detail})"
        super().__init__(message)


@dataclass
class VideoInfo:
    """What a file actually contains, as reported by the decoder."""

    path: str
    width: int
    height: int
    fps: float
    frame_count: int
    fourcc: str
    codec_note: str = ""
    backend: str = ""

    @property
    def duration_s(self) -> float:
        """Duration in seconds from the decoder's own frame count and frame rate.

        This is the *nominal* duration. Variable-frame-rate files report an average,
        so treat anything derived from it as approximate, and say so when you quote it.
        """
        if self.fps <= 0:
            return 0.0
        return self.frame_count / self.fps

    @property
    def megapixels(self) -> float:
        return self.width * self.height / 1e6

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "width": self.width,
            "height": self.height,
            "fps": round(self.fps, 3),
            "frame_count": self.frame_count,
            "duration_s": round(self.duration_s, 3),
            "fourcc": self.fourcc,
            "megapixels": round(self.megapixels, 3),
            "codec_note": self.codec_note,
            "backend": self.backend,
        }


def _fourcc_string(value: float) -> str:
    code = int(value)
    if code <= 0:
        return "????"
    text = "".join(chr((code >> (8 * i)) & 0xFF) for i in range(4))
    return text.strip() or "????"


def probe(path: str | Path, *, count_frames: bool = False) -> VideoInfo:
    """Open a video and report its properties without decoding every frame.

    ``count_frames=True`` decodes the whole file to count frames, which is the only
    reliable way to learn the true frame count of a container whose header lies (a
    common problem with files written by partial downloads or by some phone cameras).
    """
    path = Path(path)
    if not path.exists():
        raise VideoError(path, "file not found")

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise VideoError(path, "cannot open with any installed decoder",
                         "unsupported container, missing codec, or not a video")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    reported = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc = _fourcc_string(cap.get(cv2.CAP_PROP_FOURCC))
    backend = cap.getBackendName() if hasattr(cap, "getBackendName") else "unknown"

    note = ""
    if fps <= 0 or fps != fps:  # NaN check
        fps = 0.0
        note = "decoder reported no frame rate"
    if reported <= 0:
        note = (note + "; " if note else "") + "header has no frame count"

    frames = reported
    if count_frames:
        frames = 0
        while True:
            ok, _ = cap.read()
            if not ok:
                break
            frames += 1
        if reported > 0 and frames != reported:
            note = (note + "; " if note else "") + f"header said {reported} frames, decoded {frames}"

    cap.release()
    return VideoInfo(str(path), width, height, fps, frames, fourcc, note, backend)


def iter_frames(
    path: str | Path,
    *,
    stride: int = 1,
    start: int = 0,
    limit: int | None = None,
    resize: tuple[int, int] | None = None,
) -> Iterator[tuple[int, float, np.ndarray]]:
    """Yield ``(frame_index, timestamp_s, frame_bgr)`` for every ``stride``-th frame.

    ``stride`` is the sampling interval in *frames*, not seconds: a fixed frame stride is
    what a detector pipeline actually does, and it keeps the mapping from output frame to
    source frame exact. Use :func:`sample_by_time` when you want a time interval instead.

    The timestamp comes from ``CAP_PROP_POS_MSEC`` and is therefore the container's
    timestamp, not a recomputed ``index / fps``. Comparing the two is a good exercise:
    on a constant-frame-rate file they agree to milliseconds, on a variable-rate file
    they do not.
    """
    if stride < 1:
        raise ValueError("stride must be at least 1")
    path = Path(path)
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise VideoError(path, "cannot open with any installed decoder")

    index = 0
    emitted = 0
    try:
        if start > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start)
            index = start
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if index % stride == 0:
                stamp = float(cap.get(cv2.CAP_PROP_POS_MSEC)) / 1000.0
                if resize is not None:
                    frame = cv2.resize(frame, resize, interpolation=cv2.INTER_AREA)
                yield index, stamp, frame
                emitted += 1
                if limit is not None and emitted >= limit:
                    break
            index += 1
    finally:
        cap.release()


def sample_by_time(
    path: str | Path,
    every_s: float,
    *,
    limit: int | None = None,
) -> list[tuple[int, float, np.ndarray]]:
    """Extract frames at a fixed *time* interval by seeking.

    Seeking costs more per frame than sequential decoding, so this is the right tool for
    "give me one frame per second" and the wrong tool for "give me every frame".
    """
    info = probe(path)
    if info.fps <= 0:
        raise VideoError(path, "cannot sample by time without a frame rate")
    step = max(1, int(round(every_s * info.fps)))
    return list(iter_frames(path, stride=step, limit=limit))


def frame_at(path: str | Path, index: int) -> np.ndarray:
    """Random access to a single frame. Decodes from the start; use sparingly."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise VideoError(path, "cannot open with any installed decoder")
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(index))
        ok, frame = cap.read()
    finally:
        cap.release()
    if not ok:
        raise VideoError(path, f"no frame at index {index}")
    return frame


class VideoWriter:
    """Context-managed writer that refuses to create a silently empty file.

    OpenCV's ``VideoWriter`` opens successfully even when the codec is unavailable and
    then writes nothing, which is how students end up with a 0-byte MP4 and no error.
    This wrapper checks the codec against :data:`SUPPORTED_FOURCC`, verifies the handle,
    and raises ``VideoError`` instead.
    """

    def __init__(self, path: str | Path, fps: float, size: tuple[int, int],
                 fourcc: str = "mp4v", *, quality: int | None = None) -> None:
        if fourcc not in SUPPORTED_FOURCC:
            raise VideoError(path, f"unsupported fourcc {fourcc!r}",
                             f"choose one of {sorted(SUPPORTED_FOURCC)}")
        if fps <= 0:
            raise VideoError(path, "fps must be positive")
        width, height = int(size[0]), int(size[1])
        if width <= 0 or height <= 0:
            raise VideoError(path, "size must be positive")
        if width % 2 or height % 2:
            # Many codecs require even dimensions; odd sizes either fail or get cropped.
            raise VideoError(path, "width and height must be even for mp4v/MJPG")

        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.size = (width, height)
        self.fps = float(fps)
        self.frames_written = 0
        self._cap = cv2.VideoWriter(
            str(self.path), cv2.VideoWriter_fourcc(*fourcc), float(fps), (width, height)
        )
        if not self._cap.isOpened():
            self._cap.release()
            raise VideoError(self.path, f"cannot open writer for {fourcc}")
        if quality is not None:
            self._cap.set(cv2.VIDEOWRITER_PROP_QUALITY, float(quality))

    def write(self, frame: np.ndarray) -> None:
        if frame.shape[1] != self.size[0] or frame.shape[0] != self.size[1]:
            frame = cv2.resize(frame, self.size, interpolation=cv2.INTER_AREA)
        if frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        self._cap.write(frame)
        self.frames_written += 1

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> "VideoWriter":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def write_video(
    path: str | Path,
    frames: Iterable[np.ndarray],
    fps: float,
    size: tuple[int, int],
    fourcc: str = "mp4v",
) -> Path:
    """Write an iterable of frames to ``path`` and return the path."""
    path = Path(path)
    with VideoWriter(path, fps, size, fourcc) as writer:
        for frame in frames:
            writer.write(frame)
    if path.stat().st_size == 0:
        raise VideoError(path, "writer produced an empty file")
    return path


def contact_sheet(
    frames: Sequence[np.ndarray],
    *,
    cols: int = 4,
    thumb: tuple[int, int] = (160, 90),
    labels: Sequence[str] | None = None,
    pad: int = 4,
) -> np.ndarray:
    """Tile frames into one image, with optional captions.

    A contact sheet is the fastest way to see whether a video's frames are what you think
    they are: exposure changes, a static camera, a file that is actually one long freeze.
    """
    if not frames:
        raise ValueError("contact_sheet needs at least one frame")
    rows = (len(frames) + cols - 1) // cols
    th, tw = thumb[1], thumb[0]
    sheet = np.full((rows * (th + pad) + pad, cols * (tw + pad) + pad, 3), 24, np.uint8)
    for i, frame in enumerate(frames):
        r, c = divmod(i, cols)
        tile = cv2.resize(frame, (tw, th), interpolation=cv2.INTER_AREA)
        if tile.ndim == 2:
            tile = cv2.cvtColor(tile, cv2.COLOR_GRAY2BGR)
        y = pad + r * (th + pad)
        x = pad + c * (tw + pad)
        sheet[y:y + th, x:x + tw] = tile
        if labels is not None and i < len(labels):
            cv2.putText(sheet, labels[i], (x + 3, y + th - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)
    return sheet


def save_contact_sheet(path: str | Path, sheet: np.ndarray) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), sheet):
        raise VideoError(path, "could not write contact sheet")
    return path


def checksum(path: str | Path, *, chunk: int = 1 << 20) -> str:
    """SHA-256 of a file, streamed.

    Quote this next to any number derived from a video: two files with the same name and
    different bytes are the most common cause of "the results changed and nothing did".
    """
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def frame_digest(frames: Iterable[np.ndarray]) -> str:
    """Deterministic digest of a decoded frame sequence, for regression tests."""
    digest = hashlib.sha256()
    for frame in frames:
        arr = np.ascontiguousarray(frame)
        digest.update(str(arr.shape).encode())
        digest.update(arr.tobytes())
    return digest.hexdigest()


def annotate_frame(
    frame: np.ndarray,
    boxes: Sequence[Sequence[float]],
    labels: Sequence[str] | None = None,
    *,
    colour: tuple[int, int, int] = (80, 220, 80),
    thickness: int = 2,
    text_scale: float = 0.45,
) -> np.ndarray:
    """Draw boxes (and optional captions) on a copy of ``frame``."""
    out = frame.copy()
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = [int(round(v)) for v in box[:4]]
        cv2.rectangle(out, (x1, y1), (x2, y2), colour, thickness)
        if labels is not None and i < len(labels):
            text = labels[i]
            (tw, th), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, text_scale, 1)
            y = max(0, y1 - th - 4)
            cv2.rectangle(out, (x1, y), (x1 + tw + 4, y + th + base), colour, -1)
            cv2.putText(out, text, (x1 + 2, y + th + 1),
                        cv2.FONT_HERSHEY_SIMPLEX, text_scale, (16, 16, 16), 1, cv2.LINE_AA)
    return out


def draw_trails(
    frame: np.ndarray,
    trails: Sequence[Sequence[tuple[float, float]]],
    *,
    colours: Sequence[tuple[int, int, int]] | None = None,
) -> np.ndarray:
    """Draw short motion trails, one polyline per track, for reviewing tracking output."""
    out = frame.copy()
    for i, trail in enumerate(trails):
        if len(trail) < 2:
            continue
        colour = colours[i % len(colours)] if colours else (60, 180, 240)
        pts = np.array([[int(x), int(y)] for x, y in trail], np.int32)
        cv2.polylines(out, [pts], False, colour, 2, cv2.LINE_AA)
    return out


def aspect_note(info: VideoInfo) -> str:
    """Human-readable aspect ratio, e.g. '16:9 (1.78)'."""
    from math import gcd

    g = gcd(int(info.width), int(info.height)) or 1
    return f"{info.width // g}:{info.height // g} ({info.width / max(info.height, 1):.2f})"
