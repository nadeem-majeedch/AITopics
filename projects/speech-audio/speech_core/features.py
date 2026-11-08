"""Waveform, spectrogram, Mel, and MFCC features - implemented with numpy only.

There is no librosa or torchaudio in the course environment, so every transform here
is written out. That is the point of Modules CV-S02/S03 in this section: students see
the window, the hop, the Mel filterbank, and the log, instead of calling one function.

Conventions, applied everywhere:

* audio is mono float32 in [-1, 1] at ``sample_rate``;
* ``stft`` returns complex ``(n_frames, n_freq)`` for rfft bins ``0..n_fft/2``;
* power spectrograms are ``|S|**2``;
* amplitudes are converted to dB with ``10*log10`` (power) and floored;
* features are ``(n_frames, n_features)`` - time first, because that is what
  sequence models consume.
"""

from __future__ import annotations

import numpy as np

DEFAULT_SR = 16_000
DEFAULT_N_FFT = 512
DEFAULT_HOP = 160  # 10 ms at 16 kHz
DEFAULT_WIN = 400  # 25 ms at 16 kHz
DEFAULT_N_MELS = 40


# ---------------------------------------------------------------------------
# Windows and STFT
# ---------------------------------------------------------------------------


def hann_window(size: int, periodic: bool = True) -> np.ndarray:
    """Hann window. Periodic is the convention for STFT (it sums to 1 under OLA)."""
    if size <= 0:
        raise ValueError("window size must be positive")
    n = np.arange(size)
    denom = size if periodic else max(1, size - 1)
    return (0.5 - 0.5 * np.cos(2 * np.pi * n / denom)).astype(np.float32)


def stft(
    samples: np.ndarray,
    sample_rate: int = DEFAULT_SR,
    n_fft: int = DEFAULT_N_FFT,
    hop_length: int = DEFAULT_HOP,
    win_length: int = DEFAULT_WIN,
    center: bool = True,
) -> np.ndarray:
    """Short-time Fourier transform, complex ``(n_frames, n_fft // 2 + 1)``.

    ``center=True`` pads by ``n_fft // 2`` on both sides so frame ``t`` is centred
    on sample ``t * hop``. Without it, every timestamp is off by half a window and
    frame-aligning transcripts gets confusing.
    """
    arr = np.asarray(samples, dtype=np.float32)
    if win_length > n_fft:
        raise ValueError("win_length must be <= n_fft")
    if center:
        arr = np.pad(arr, (n_fft // 2, n_fft // 2), mode="reflect" if len(arr) > 1 else "constant")
    if len(arr) < n_fft:
        arr = np.pad(arr, (0, n_fft - len(arr)))
    window = hann_window(win_length)
    if win_length < n_fft:
        padded = np.zeros(n_fft, dtype=np.float32)
        offset = (n_fft - win_length) // 2
        padded[offset : offset + win_length] = window
        window = padded
    n_frames = 1 + (len(arr) - n_fft) // hop_length
    index = np.arange(n_fft)[None, :] + hop_length * np.arange(n_frames)[:, None]
    frames = arr[index] * window[None, :]
    return np.fft.rfft(frames, n=n_fft, axis=1)


def power_spectrogram(samples: np.ndarray, **kwargs) -> np.ndarray:
    """``|STFT|**2``, shape ``(n_frames, n_freq)``."""
    return np.abs(stft(samples, **kwargs)) ** 2


def magnitude_spectrogram(samples: np.ndarray, **kwargs) -> np.ndarray:
    return np.abs(stft(samples, **kwargs))


def power_to_db(power: np.ndarray, ref: float = 1.0, top_db: float = 80.0, amin: float = 1e-10) -> np.ndarray:
    """Power to dB with a floor relative to the maximum.

    ``top_db`` clips the dynamic range so a silent frame does not dominate a colour
    map or a normalisation step.
    """
    arr = np.maximum(np.asarray(power, dtype=np.float64), amin)
    log_spec = 10.0 * np.log10(arr / max(ref, amin))
    if top_db is not None:
        log_spec = np.maximum(log_spec, log_spec.max() - top_db)
    return log_spec.astype(np.float32)


# ---------------------------------------------------------------------------
# Mel scale and filterbanks
# ---------------------------------------------------------------------------


def hz_to_mel(freq: np.ndarray | float) -> np.ndarray:
    """HTK-style mel scale."""
    return 2595.0 * np.log10(1.0 + np.asarray(freq, dtype=np.float64) / 700.0)


def mel_to_hz(mel: np.ndarray | float) -> np.ndarray:
    return 700.0 * (10.0 ** (np.asarray(mel, dtype=np.float64) / 2595.0) - 1.0)


def mel_filterbank(
    sample_rate: int = DEFAULT_SR,
    n_fft: int = DEFAULT_N_FFT,
    n_mels: int = DEFAULT_N_MELS,
    fmin: float = 20.0,
    fmax: float | None = None,
) -> np.ndarray:
    """Triangular filterbank, shape ``(n_mels, n_fft // 2 + 1)``.

    Each row sums to approximately 1 after area normalisation, so a log-mel value
    is comparable across filter widths. ``fmax`` defaults to Nyquist.
    """
    if n_mels <= 0:
        raise ValueError("n_mels must be positive")
    fmax = sample_rate / 2.0 if fmax is None else min(fmax, sample_rate / 2.0)
    if not 0 <= fmin < fmax:
        raise ValueError("require 0 <= fmin < fmax <= sample_rate / 2")
    fft_freqs = np.linspace(0.0, sample_rate / 2.0, n_fft // 2 + 1)
    mel_points = np.linspace(hz_to_mel(fmin), hz_to_mel(fmax), n_mels + 2)
    hz_points = mel_to_hz(mel_points)
    bank = np.zeros((n_mels, len(fft_freqs)), dtype=np.float32)
    for m in range(n_mels):
        left, centre, right = hz_points[m], hz_points[m + 1], hz_points[m + 2]
        rising = (fft_freqs - left) / max(centre - left, 1e-9)
        falling = (right - fft_freqs) / max(right - centre, 1e-9)
        bank[m] = np.maximum(0.0, np.minimum(rising, falling))
        area = bank[m].sum()
        if area > 0:
            bank[m] /= area
    return bank


def mel_band_frequencies(
    sample_rate: int = DEFAULT_SR,
    n_mels: int = DEFAULT_N_MELS,
    fmin: float = 20.0,
    fmax: float | None = None,
) -> np.ndarray:
    """Centre frequency of each Mel band, in Hz - the x axis of a Mel spectrogram."""
    fmax = sample_rate / 2.0 if fmax is None else min(fmax, sample_rate / 2.0)
    mel_points = np.linspace(hz_to_mel(fmin), hz_to_mel(fmax), n_mels + 2)
    return mel_to_hz(mel_points)[1:-1]


def mel_spectrogram(
    samples: np.ndarray,
    sample_rate: int = DEFAULT_SR,
    n_fft: int = DEFAULT_N_FFT,
    hop_length: int = DEFAULT_HOP,
    win_length: int = DEFAULT_WIN,
    n_mels: int = DEFAULT_N_MELS,
    fmin: float = 20.0,
    fmax: float | None = None,
    log: bool = True,
    top_db: float = 80.0,
) -> np.ndarray:
    """Log-Mel spectrogram ``(n_frames, n_mels)`` - the default audio front end."""
    power = power_spectrogram(
        samples, sample_rate=sample_rate, n_fft=n_fft, hop_length=hop_length, win_length=win_length
    )
    bank = mel_filterbank(sample_rate, n_fft, n_mels, fmin, fmax)
    mel = power @ bank.T
    return power_to_db(mel, top_db=top_db) if log else mel.astype(np.float32)


def dct_matrix(n_inputs: int, n_coeffs: int) -> np.ndarray:
    """Orthonormal DCT-II basis, shape ``(n_coeffs, n_inputs)``."""
    k = np.arange(n_coeffs)[:, None]
    n = np.arange(n_inputs)[None, :]
    mat = np.cos(np.pi * k * (2 * n + 1) / (2.0 * n_inputs)) * np.sqrt(2.0 / n_inputs)
    mat[0] /= np.sqrt(2.0)
    return mat.astype(np.float32)


def mfcc(
    samples: np.ndarray,
    sample_rate: int = DEFAULT_SR,
    n_mfcc: int = 13,
    n_mels: int = DEFAULT_N_MELS,
    n_fft: int = DEFAULT_N_FFT,
    hop_length: int = DEFAULT_HOP,
    win_length: int = DEFAULT_WIN,
) -> np.ndarray:
    """Mel-frequency cepstral coefficients ``(n_frames, n_mfcc)``.

    Cepstral coefficients decorrelate the Mel channels: coefficient 0 is overall
    energy, 1-3 carry the spectral envelope that distinguishes vowels, and higher
    coefficients mostly carry noise.
    """
    mel_db = mel_spectrogram(
        samples,
        sample_rate=sample_rate,
        n_fft=n_fft,
        hop_length=hop_length,
        win_length=win_length,
        n_mels=n_mels,
    )
    return (mel_db @ dct_matrix(n_mels, n_mfcc).T).astype(np.float32)


def deltas(features: np.ndarray, width: int = 2) -> np.ndarray:
    """First difference over time (a simple delta, not the full regression formula).

    Motion matters: the same vowel at two pitches has similar statics and different
    transitions.
    """
    arr = np.asarray(features, dtype=np.float32)
    if len(arr) < 2:
        return np.zeros_like(arr)
    padded = np.pad(arr, ((width, width), (0, 0)), mode="edge")
    num = np.zeros_like(arr)
    den = 0.0
    for n in range(1, width + 1):
        num += n * (padded[width + n : width + n + len(arr)] - padded[width - n : width - n + len(arr)])
        den += 2 * n * n
    return (num / max(den, 1e-9)).astype(np.float32)


def delta_features(features: np.ndarray) -> np.ndarray:
    """Static + delta + delta-delta, concatenated - the classic 39-dim MFCC vector."""
    first = deltas(features)
    second = deltas(first)
    return np.concatenate([features, first, second], axis=1)


# ---------------------------------------------------------------------------
# Normalisation and fixed-size inputs
# ---------------------------------------------------------------------------


def normalize_features(features: np.ndarray, mean: np.ndarray | None = None, std: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-feature standardisation; returns the statistics used.

    Pass the training statistics at inference. Recomputing them per file hides
    domain shift and makes a quiet recording look like a loud one.
    """
    arr = np.asarray(features, dtype=np.float32)
    mean = arr.mean(axis=0) if mean is None else np.asarray(mean, dtype=np.float32)
    std = arr.std(axis=0) if std is None else np.asarray(std, dtype=np.float32)
    std = np.where(std < 1e-5, 1.0, std)
    return ((arr - mean) / std).astype(np.float32), mean, std


def pad_or_truncate_features(features: np.ndarray, n_frames: int) -> np.ndarray:
    """Fix the time axis so clips can be stacked into a batch."""
    arr = np.asarray(features, dtype=np.float32)
    if len(arr) == n_frames:
        return arr
    if len(arr) > n_frames:
        return arr[:n_frames]
    return np.pad(arr, ((0, n_frames - len(arr)), (0, 0)))


# ---------------------------------------------------------------------------
# Visualisation (terminal and PNG, no matplotlib)
# ---------------------------------------------------------------------------


def ascii_spectrogram(features: np.ndarray, width: int = 60, height: int = 12) -> str:
    """Render a feature matrix as text, so it can be read in any terminal."""
    arr = np.asarray(features, dtype=np.float64)
    if arr.ndim != 2 or arr.size == 0:
        return "(empty)"
    rows = np.linspace(0, arr.shape[0] - 1, min(height, arr.shape[0])).astype(int)
    cols = np.linspace(0, arr.shape[1] - 1, min(width, arr.shape[1])).astype(int)
    grid = arr[np.ix_(rows, cols)]
    lo, hi = float(grid.min()), float(grid.max())
    ramp = " .:-=+*#%@"
    span = max(hi - lo, 1e-9)
    lines = []
    for row in grid[::-1]:  # low frequency at the bottom
        lines.append("".join(ramp[min(len(ramp) - 1, int((v - lo) / span * (len(ramp) - 1)))] for v in row))
    return "\n".join(lines)


def waveform_ascii(samples: np.ndarray, width: int = 60) -> str:
    """Two-line summary of a waveform's envelope (min/max per column)."""
    arr = np.asarray(samples, dtype=np.float32)
    if arr.size == 0:
        return "(empty)"
    step = max(1, len(arr) // width)
    trimmed = arr[: step * width].reshape(-1, step)
    upper = trimmed.max(axis=1)
    lower = trimmed.min(axis=1)
    top = "".join("^" if v > 0.2 else ("-" if v > 0.02 else " ") for v in upper)
    bottom = "".join("v" if v < -0.2 else ("-" if v < -0.02 else " ") for v in lower)
    return f"{top}\n{bottom}"


def save_spectrogram_png(
    features: np.ndarray,
    path: str,
    title: str = "",
    width: int = 480,
    height: int = 220,
) -> str:
    """Write a spectrogram as a PNG using Pillow (no matplotlib in this environment)."""
    from PIL import Image, ImageDraw

    arr = np.asarray(features, dtype=np.float64)
    if arr.ndim != 2 or arr.size == 0:
        raise ValueError("features must be a non-empty 2-D array")
    lo, hi = float(arr.min()), float(arr.max())
    scaled = (arr - lo) / max(hi - lo, 1e-9)
    image = Image.fromarray((scaled.T[::-1] * 255).astype(np.uint8), mode="L").resize((width, height))
    canvas = Image.new("RGB", (width, height + 18), (255, 255, 255))
    canvas.paste(image.convert("RGB"), (0, 18))
    draw = ImageDraw.Draw(canvas)
    draw.text((4, 3), title or "spectrogram", fill=(0, 0, 0))
    canvas.save(path)
    return path
