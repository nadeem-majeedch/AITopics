"""PCM audio I/O, framing, level handling, and simple effects.

Everything here works on plain float32 numpy arrays in the range [-1, 1]. The only
container implemented is 16-bit PCM WAV, via the standard library's ``wave`` module,
because it is the one format every machine can read without an extra dependency.

Deliberately absent: playback. A server or CI runner has no audio device, and a lab
that fails because nothing can be heard is not a lab. Playback is optional and guarded
(``play_wav`` returns a reason instead of raising).
"""

from __future__ import annotations

import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

DEFAULT_SR = 16_000


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------


def to_float(samples: np.ndarray) -> np.ndarray:
    """Accept int16 or float input and return float32 in [-1, 1]."""
    arr = np.asarray(samples)
    if arr.dtype == np.int16:
        return (arr.astype(np.float32) / 32768.0).clip(-1.0, 1.0)
    arr = arr.astype(np.float32)
    if arr.size and np.max(np.abs(arr)) > 1.5:
        # Looks like unscaled ints; scale rather than clipping every sample to +-1.
        return (arr / 32768.0).clip(-1.0, 1.0)
    return np.clip(arr, -1.0, 1.0)


def to_int16(samples: np.ndarray) -> np.ndarray:
    """Float [-1, 1] to int16 with clipping, never wrapping."""
    return (np.clip(np.asarray(samples, dtype=np.float32), -1.0, 1.0) * 32767.0).astype(np.int16)


def to_mono(samples: np.ndarray) -> np.ndarray:
    """(n,) stays as is; (n, channels) is averaged."""
    arr = np.asarray(samples, dtype=np.float32)
    return arr.mean(axis=1) if arr.ndim == 2 else arr


def duration_seconds(samples: np.ndarray, sample_rate: int = DEFAULT_SR) -> float:
    return len(samples) / float(sample_rate)


def rms(samples: np.ndarray) -> float:
    arr = np.asarray(samples, dtype=np.float64)
    return float(np.sqrt(np.mean(arr**2))) if arr.size else 0.0


def db(value: float, floor: float = 1e-10) -> float:
    """Power ratio to decibels; safe at zero."""
    return float(10.0 * np.log10(max(value, floor)))


def peak_normalize(samples: np.ndarray, target_db: float = -3.0) -> np.ndarray:
    """Scale so the loudest sample sits at ``target_db`` dBFS."""
    arr = to_float(samples)
    peak = float(np.max(np.abs(arr))) if arr.size else 0.0
    if peak <= 0.0:
        return arr
    target = 10.0 ** (target_db / 20.0)
    return (arr * (target / peak)).astype(np.float32)


def trim_silence(samples: np.ndarray, threshold: float = 0.01, pad: int = 160) -> np.ndarray:
    """Remove leading/trailing near-silence, keeping ``pad`` samples of margin."""
    arr = to_float(samples)
    loud = np.nonzero(np.abs(arr) > threshold)[0]
    if loud.size == 0:
        return arr[:0]
    start = max(0, int(loud[0]) - pad)
    stop = min(len(arr), int(loud[-1]) + pad + 1)
    return arr[start:stop]


# ---------------------------------------------------------------------------
# WAV I/O
# ---------------------------------------------------------------------------


def write_wav(path: str | Path, samples: np.ndarray, sample_rate: int = DEFAULT_SR) -> Path:
    """Write 16-bit PCM mono WAV. Returns the path written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = to_int16(to_mono(samples))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(int(sample_rate))
        handle.writeframes(pcm.tobytes())
    return path


def read_wav(path: str | Path) -> tuple[np.ndarray, int]:
    """Read a PCM WAV as ``(float32 mono samples, sample_rate)``.

    Stereo is averaged to mono. Non-PCM and floating-point WAVs raise a clear
    error rather than returning garbage, which is what a student needs to see.
    """
    path = Path(path)
    with wave.open(str(path), "rb") as handle:
        n_channels = handle.getnchannels()
        width = handle.getsampwidth()
        rate = handle.getframerate()
        raw = handle.readframes(handle.getnframes())
    if width != 2:
        raise ValueError(f"{path.name}: expected 16-bit PCM, found {width * 8}-bit")
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if n_channels > 1:
        samples = samples.reshape(-1, n_channels).mean(axis=1)
    return samples.astype(np.float32), rate


def wav_info(path: str | Path) -> dict:
    """Everything a student should be able to report about a file."""
    path = Path(path)
    with wave.open(str(path), "rb") as handle:
        frames = handle.getnframes()
        rate = handle.getframerate()
        channels = handle.getnchannels()
        width = handle.getsampwidth()
    samples, _ = read_wav(path)
    return {
        "file": path.name,
        "sample_rate": rate,
        "channels": channels,
        "bit_depth": width * 8,
        "frames": frames,
        "duration_s": round(frames / float(rate), 4),
        "rms": round(rms(samples), 5),
        "peak": round(float(np.max(np.abs(samples))) if samples.size else 0.0, 5),
        "bytes": path.stat().st_size,
    }


def play_wav(path: str | Path) -> tuple[bool, str]:
    """Best-effort playback. Returns ``(played, reason)`` and never raises.

    A headless machine, a CI runner, and a cloud container all lack an audio
    device. Failing loudly there would make the exercises unrunnable for no gain.
    """
    path = Path(path)
    try:
        if sys.platform.startswith("win"):
            if not shutil.which("powershell"):
                return False, "no PowerShell available for playback"
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"(New-Object Media.SoundPlayer '{path.resolve()}').PlaySync();",
                ],
                check=True,
                capture_output=True,
                timeout=30,
            )
            return True, "played with Windows SoundPlayer"
        if sys.platform == "darwin" and shutil.which("afplay"):
            subprocess.run(["afplay", str(path)], check=True, timeout=30)
            return True, "played with afplay"
        for player in ("aplay", "paplay", "ffplay"):
            if shutil.which(player):
                subprocess.run([player, "-q", str(path)], check=True, timeout=30)
                return True, f"played with {player}"
    except Exception as exc:  # noqa: BLE001 - playback is optional by design
        return False, f"playback unavailable: {exc}"
    return False, "no audio player found; the exercise works without playback"


# ---------------------------------------------------------------------------
# Sampling rate and framing
# ---------------------------------------------------------------------------


def resample(samples: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    """Band-limited resampling with a polyphase filter.

    Naive decimation by taking every k-th sample aliases high frequencies into low
    ones - the classic "the spectrogram grew a mirror image" bug. ``resample_poly``
    filters before it decimates.
    """
    from math import gcd

    from scipy.signal import resample_poly

    if source_rate == target_rate:
        return np.asarray(samples, dtype=np.float32)
    if source_rate <= 0 or target_rate <= 0:
        raise ValueError("sample rates must be positive")
    divisor = gcd(int(source_rate), int(target_rate))
    up, down = int(target_rate // divisor), int(source_rate // divisor)
    out = resample_poly(np.asarray(samples, dtype=np.float32), up, down)
    return out.astype(np.float32)


def frame_signal(samples: np.ndarray, frame_size: int, hop_size: int, pad: bool = True) -> np.ndarray:
    """Split into overlapping frames of ``frame_size`` with stride ``hop_size``."""
    arr = np.asarray(samples, dtype=np.float32)
    if frame_size <= 0 or hop_size <= 0:
        raise ValueError("frame_size and hop_size must be positive")
    if pad and len(arr) < frame_size:
        arr = np.pad(arr, (0, frame_size - len(arr)))
    if len(arr) < frame_size:
        return np.zeros((0, frame_size), dtype=np.float32)
    n_frames = 1 + (len(arr) - frame_size) // hop_size
    index = np.arange(frame_size)[None, :] + hop_size * np.arange(n_frames)[:, None]
    return arr[index]


def pad_or_trim(samples: np.ndarray, length: int) -> np.ndarray:
    """Fixed-length clips, for batching."""
    arr = np.asarray(samples, dtype=np.float32)
    if len(arr) == length:
        return arr
    if len(arr) > length:
        return arr[:length]
    return np.pad(arr, (0, length - len(arr)))


# ---------------------------------------------------------------------------
# Effects and mixtures
# ---------------------------------------------------------------------------


def add_noise(samples: np.ndarray, snr_db: float, seed: int = 0, colour: str = "white") -> np.ndarray:
    """Add noise at a target signal-to-noise ratio, measured on RMS power.

    ``snr_db`` of 20 is quiet background hiss; 0 dB is as loud as the signal.
    """
    arr = to_float(samples)
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(len(arr)).astype(np.float32)
    if colour == "pink":
        # Cheap 1/f shaping: cumulative sum of white noise, then renormalise.
        noise = np.cumsum(noise)
        noise -= noise.mean()
    elif colour == "brown":
        noise = np.cumsum(np.cumsum(noise))
        noise -= noise.mean()
    noise /= max(np.std(noise), 1e-9)
    signal_power = float(np.mean(arr**2))
    noise_power = signal_power / (10.0 ** (snr_db / 10.0)) if snr_db < 200 else 0.0
    return (arr + noise * np.sqrt(max(noise_power, 0.0))).astype(np.float32)


def change_gain(samples: np.ndarray, gain_db: float) -> np.ndarray:
    return (to_float(samples) * (10.0 ** (gain_db / 20.0))).astype(np.float32)


def time_stretch(samples: np.ndarray, factor: float, sample_rate: int = DEFAULT_SR) -> np.ndarray:
    """Change speaking rate without changing pitch class (simple OLA).

    Overlap-add on 20 ms frames. It is not studio quality; it is enough to test
    whether a recogniser survives a faster or slower talker.
    """
    if factor <= 0:
        raise ValueError("factor must be positive")
    arr = to_float(samples)
    frame = max(64, int(0.020 * sample_rate))
    hop_out = max(1, int(round(frame * factor)))
    window = np.hanning(frame).astype(np.float32)
    out = np.zeros(int(len(arr) / factor) + frame, dtype=np.float32)
    norm = np.zeros_like(out)
    for start in range(0, len(arr) - frame + 1, hop_out):
        segment = arr[start : start + frame]
        pos = int(start / factor)
        out[pos : pos + frame] += segment * window
        norm[pos : pos + frame] += window
    norm[norm < 1e-6] = 1.0
    return (out / norm).astype(np.float32)


def mix(signals: Sequence[np.ndarray], gains_db: Sequence[float] | None = None) -> np.ndarray:
    """Sum signals to the length of the longest, with optional per-signal gains."""
    if not signals:
        return np.zeros(0, dtype=np.float32)
    length = max(len(s) for s in signals)
    out = np.zeros(length, dtype=np.float32)
    for i, sig in enumerate(signals):
        gain = 1.0 if gains_db is None else 10.0 ** (gains_db[i] / 20.0)
        out[: len(sig)] += to_float(sig) * gain
    return out


def snr_between(reference: np.ndarray, estimate: np.ndarray) -> float:
    """SNR in dB of ``estimate`` against ``reference`` (both same length)."""
    ref = to_float(reference)
    est = to_float(estimate)
    n = min(len(ref), len(est))
    noise = est[:n] - ref[:n]
    return db(float(np.sum(ref[:n] ** 2)) / max(float(np.sum(noise**2)), 1e-12))


def concatenate(clips: Iterable[np.ndarray], gap: int = 0) -> np.ndarray:
    """Join clips with optional silence between them."""
    parts: list[np.ndarray] = []
    for clip in clips:
        parts.append(np.asarray(clip, dtype=np.float32))
        if gap:
            parts.append(np.zeros(gap, dtype=np.float32))
    return np.concatenate(parts) if parts else np.zeros(0, dtype=np.float32)


def int16_bytes(samples: np.ndarray) -> bytes:
    """Raw PCM bytes, useful for tests that check byte-level layout."""
    return struct.pack(f"<{len(samples)}h", *to_int16(samples).tolist())
