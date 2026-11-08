"""Deterministic synthesis of speech-like and environmental audio.

Two reasons this section synthesises its own audio:

1. **Licensing and consent.** No third-party recordings, no speaker who did not agree
   to be in a teaching corpus. Everything here is generated from code and released
   CC0-1.0.
2. **Controllability.** You can vary pitch, formants, speaking rate, and noise one
   factor at a time, which is exactly what the evaluation modules ask you to do.

The speech is **formant synthesis**: a glottal pulse train filtered by three
resonators whose frequencies encode a vowel. It is intelligible enough to recognise a
six-word vocabulary and not a substitute for a real speech corpus. Every module that
uses it says so.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.signal import lfilter

DEFAULT_SR = 16_000


# ---------------------------------------------------------------------------
# Primitive signals
# ---------------------------------------------------------------------------


def tone(freq: float, duration: float, sample_rate: int = DEFAULT_SR, amplitude: float = 0.3, harmonics: int = 1) -> np.ndarray:
    """Pure tone (or a harmonic stack) with a short fade in/out."""
    n = int(duration * sample_rate)
    t = np.arange(n) / sample_rate
    signal = np.zeros(n, dtype=np.float32)
    for h in range(1, harmonics + 1):
        if freq * h >= sample_rate / 2:
            break
        signal += np.sin(2 * np.pi * freq * h * t).astype(np.float32) / h
    signal *= amplitude / max(1, harmonics)
    return _fade(signal, sample_rate)


def noise(duration: float, sample_rate: int = DEFAULT_SR, amplitude: float = 0.1, seed: int = 0, colour: str = "white") -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(duration * sample_rate)
    signal = rng.standard_normal(n).astype(np.float32)
    if colour == "pink":
        signal = _onepole(signal, alpha=0.98)
    elif colour == "brown":
        signal = _onepole(_onepole(signal, 0.995), 0.99)
    signal /= max(np.max(np.abs(signal)), 1e-9)
    return (signal * amplitude).astype(np.float32)


def chirp(start_hz: float, end_hz: float, duration: float, sample_rate: int = DEFAULT_SR, amplitude: float = 0.3) -> np.ndarray:
    """Linear frequency sweep - the basis of the birdsong class."""
    n = int(duration * sample_rate)
    t = np.arange(n) / sample_rate
    freq = np.linspace(start_hz, end_hz, n)
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    return _fade((amplitude * np.sin(phase)).astype(np.float32), sample_rate)


def impulse_train(f0: float, duration: float, sample_rate: int = DEFAULT_SR, jitter: float = 0.0, seed: int = 0) -> np.ndarray:
    """Glottal source: one impulse per pitch period, with optional jitter."""
    rng = np.random.default_rng(seed)
    n = int(duration * sample_rate)
    out = np.zeros(n, dtype=np.float32)
    period = sample_rate / max(f0, 20.0)
    pos = 0.0
    while pos < n:
        idx = int(pos)
        if idx < n:
            out[idx] = 1.0 + 0.3 * rng.standard_normal()
        pos += period * (1.0 + jitter * rng.standard_normal())
    return out


def _fade(signal: np.ndarray, sample_rate: int, ms: float = 5.0) -> np.ndarray:
    n = int(sample_rate * ms / 1000.0)
    if n <= 1 or len(signal) < 2 * n:
        return signal.astype(np.float32)
    ramp = np.linspace(0.0, 1.0, n, dtype=np.float32)
    out = signal.astype(np.float32).copy()
    out[:n] *= ramp
    out[-n:] *= ramp[::-1]
    return out


def _onepole(signal: np.ndarray, alpha: float) -> np.ndarray:
    """Cheap low-pass: y[n] = alpha*y[n-1] + (1-alpha)*x[n]."""
    out = np.empty_like(signal, dtype=np.float32)
    acc = 0.0
    for i, value in enumerate(signal):
        acc = alpha * acc + (1.0 - alpha) * float(value)
        out[i] = acc
    return out


# ---------------------------------------------------------------------------
# Formant speech synthesis
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Phoneme:
    """One speech sound: either a vowel (formants) or a consonant (noise/burst)."""

    kind: str  # "vowel", "fricative", "plosive", "sonorant"
    duration: float  # seconds at rate 1.0
    formants: tuple[float, float, float] = (500.0, 1500.0, 2500.0)
    bandwidths: tuple[float, float, float] = (80.0, 100.0, 140.0)
    voiced: bool = True
    burst_hz: float = 2000.0


# Formant values are approximate male averages; speaker profiles scale them.
PHONEMES: dict[str, Phoneme] = {
    "i": Phoneme("vowel", 0.11, (280.0, 2250.0, 2950.0)),
    "e": Phoneme("vowel", 0.10, (420.0, 2000.0, 2600.0)),
    "a": Phoneme("vowel", 0.12, (730.0, 1090.0, 2440.0)),
    "o": Phoneme("vowel", 0.12, (500.0, 900.0, 2400.0)),
    "u": Phoneme("vowel", 0.11, (330.0, 700.0, 2200.0)),
    "l": Phoneme("sonorant", 0.07, (360.0, 1300.0, 2700.0)),
    "r": Phoneme("sonorant", 0.07, (330.0, 1200.0, 1600.0)),
    "n": Phoneme("sonorant", 0.07, (250.0, 1700.0, 2600.0)),
    "y": Phoneme("sonorant", 0.06, (250.0, 2200.0, 3000.0)),
    "s": Phoneme("fricative", 0.09, voiced=False, burst_hz=6000.0),
    "f": Phoneme("fricative", 0.08, voiced=False, burst_hz=3000.0),
    "h": Phoneme("fricative", 0.07, voiced=False, burst_hz=1500.0),
    "t": Phoneme("plosive", 0.06, voiced=False, burst_hz=4000.0),
    "p": Phoneme("plosive", 0.06, voiced=False, burst_hz=1200.0),
    "g": Phoneme("plosive", 0.06, voiced=True, burst_hz=1800.0),
}

# The recognised vocabulary. Transcript = the word itself; phonemes drive synthesis.
WORDS: dict[str, tuple[str, ...]] = {
    "yes": ("y", "e", "s"),
    "no": ("n", "o"),
    "stop": ("s", "t", "o", "p"),
    "start": ("s", "t", "a", "r", "t"),
    "left": ("l", "e", "f", "t"),
    "right": ("r", "i", "t"),
}


@dataclass(frozen=True)
class VoiceProfile:
    """A synthetic speaker. ``name`` is an identifier, not a person."""

    name: str
    f0: float = 120.0
    formant_scale: float = 1.0
    rate: float = 1.0
    breathiness: float = 0.02
    gain_db: float = -3.0
    seed: int = 0


VOICES: tuple[VoiceProfile, ...] = tuple(
    VoiceProfile(
        name=f"voice_{i:02d}",
        f0=float(f0),
        formant_scale=scale,
        rate=rate,
        breathiness=0.02 + 0.01 * (i % 3),
        seed=i,
    )
    for i, (f0, scale, rate) in enumerate(
        [
            (95.0, 1.06, 0.92),
            (110.0, 1.00, 1.00),
            (125.0, 0.97, 1.06),
            (145.0, 0.95, 0.96),
            (165.0, 0.92, 1.02),
            (185.0, 0.90, 1.08),
            (105.0, 1.08, 0.88),
            (135.0, 0.98, 1.12),
            (155.0, 0.94, 0.94),
            (200.0, 0.88, 1.00),
            (100.0, 1.10, 1.04),
            (175.0, 0.91, 0.90),
        ]
    )
)


def _resonator(freq: float, bandwidth: float, sample_rate: int) -> tuple[np.ndarray, np.ndarray]:
    r = float(np.exp(-np.pi * bandwidth / sample_rate))
    theta = 2 * np.pi * freq / sample_rate
    a = np.array([1.0, -2.0 * r * np.cos(theta), r * r], dtype=np.float64)
    b = np.array([1.0 - r], dtype=np.float64)
    return b, a


def _apply_formants(source: np.ndarray, formants: tuple[float, float, float], bandwidths: tuple[float, float, float], sample_rate: int) -> np.ndarray:
    out = source.astype(np.float64)
    for freq, bw in zip(formants, bandwidths):
        if freq >= sample_rate / 2:
            continue
        b, a = _resonator(min(freq, sample_rate / 2 - 100.0), bw, sample_rate)
        out = lfilter(b, a, out)
    return out.astype(np.float32)


def _phoneme_audio(phoneme: Phoneme, profile: VoiceProfile, sample_rate: int) -> np.ndarray:
    duration = phoneme.duration / max(profile.rate, 0.2)
    n = max(1, int(duration * sample_rate))
    rng = np.random.default_rng(profile.seed + int(1000 * duration) + len(phoneme.kind))

    if phoneme.kind == "fricative":
        hiss = rng.standard_normal(n).astype(np.float32)
        centre = min(phoneme.burst_hz, sample_rate / 2 - 200.0)
        hiss = _apply_formants(hiss, (centre, centre * 1.5, centre * 2.0), (900.0, 1400.0, 1800.0), sample_rate)
        hiss /= max(np.max(np.abs(hiss)), 1e-9)
        return _fade(hiss * 0.18, sample_rate)

    if phoneme.kind == "plosive":
        silence = np.zeros(int(0.02 * sample_rate), dtype=np.float32)
        burst_n = max(1, int(0.012 * sample_rate))
        burst = rng.standard_normal(burst_n).astype(np.float32)
        burst = _apply_formants(burst, (min(phoneme.burst_hz, sample_rate / 2 - 200.0), 2000.0, 3000.0), (1200.0, 1500.0, 1800.0), sample_rate)
        burst /= max(np.max(np.abs(burst)), 1e-9)
        return np.concatenate([silence, (burst * 0.22).astype(np.float32)])

    # Voiced: glottal pulse train through three formant resonators.
    source = impulse_train(profile.f0, duration, sample_rate, jitter=0.01, seed=profile.seed)
    if profile.breathiness > 0:
        source = source + profile.breathiness * rng.standard_normal(n).astype(np.float32)
    scaled = tuple(f * profile.formant_scale for f in phoneme.formants)
    voiced = _apply_formants(source, scaled, phoneme.bandwidths, sample_rate)
    peak = float(np.max(np.abs(voiced))) if voiced.size else 0.0
    if peak > 0:
        voiced = voiced / peak
    return _fade((voiced * 0.45).astype(np.float32), sample_rate)


def speak(
    text: str,
    profile: VoiceProfile | None = None,
    sample_rate: int = DEFAULT_SR,
    seed: int = 0,
) -> np.ndarray:
    """Render a word from ``WORDS`` (or a space-separated sequence of them)."""
    profile = profile or VOICES[0]
    pieces: list[np.ndarray] = []
    words = [w for w in text.lower().strip().split() if w]
    if not words:
        return np.zeros(int(0.2 * sample_rate), dtype=np.float32)
    for wi, word in enumerate(words):
        phonemes = WORDS.get(word)
        if phonemes is None:
            raise KeyError(f"{word!r} is not in the synthetic vocabulary: {sorted(WORDS)}")
        for ph in phonemes:
            pieces.append(_phoneme_audio(PHONEMES[ph], profile, sample_rate))
            pieces.append(np.zeros(int(0.008 * sample_rate), dtype=np.float32))
        if wi < len(words) - 1:
            pieces.append(np.zeros(int(0.06 * sample_rate), dtype=np.float32))
    signal = np.concatenate(pieces) if pieces else np.zeros(0, dtype=np.float32)
    gain = 10.0 ** (profile.gain_db / 20.0)
    return (signal * gain).astype(np.float32)


def word_phonemes(word: str) -> tuple[str, ...]:
    return WORDS[word.lower()]


# ---------------------------------------------------------------------------
# Environmental sounds
# ---------------------------------------------------------------------------


def env_alarm(duration: float, sample_rate: int = DEFAULT_SR, seed: int = 0) -> np.ndarray:
    """Two-tone alarm: 1 kHz and 1.4 kHz beeps at ~3 Hz."""
    rng = np.random.default_rng(seed)
    n = int(duration * sample_rate)
    out = np.zeros(n, dtype=np.float32)
    beep = 0.18
    period = 0.30
    t = 0.0
    freq = 1000.0 if seed % 2 == 0 else 1400.0
    while t + beep < duration:
        start = int(t * sample_rate)
        stop = min(n, start + int(beep * sample_rate))
        seg = tone(freq, (stop - start) / sample_rate, sample_rate, amplitude=0.5, harmonics=2)
        out[start:stop] += seg[: stop - start]
        t += period * float(rng.uniform(0.95, 1.05))
    return out


def env_rain(duration: float, sample_rate: int = DEFAULT_SR, seed: int = 0) -> np.ndarray:
    """Low-passed noise plus sparse droplet impulses."""
    rng = np.random.default_rng(seed)
    n = int(duration * sample_rate)
    base = noise(duration, sample_rate, amplitude=0.18, seed=seed, colour="pink")[:n]
    droplets = np.zeros(n, dtype=np.float32)
    for _ in range(int(duration * 30)):
        pos = int(rng.integers(0, max(1, n - 400)))
        length = int(rng.integers(80, 400))
        freq = float(rng.uniform(900, 4000))
        droplets[pos : pos + length] += tone(freq, length / sample_rate, sample_rate, amplitude=float(rng.uniform(0.02, 0.08)))[:length]
    return (base + droplets).astype(np.float32)


def env_footsteps(duration: float, sample_rate: int = DEFAULT_SR, seed: int = 0) -> np.ndarray:
    """Periodic low-frequency thumps with irregular timing."""
    rng = np.random.default_rng(seed)
    n = int(duration * sample_rate)
    out = np.zeros(n, dtype=np.float32)
    t = 0.1
    while t < duration - 0.1:
        length = int(0.09 * sample_rate)
        start = int(t * sample_rate)
        t_axis = np.arange(length) / sample_rate
        thump = (np.sin(2 * np.pi * 90 * t_axis) * np.exp(-t_axis * 40)).astype(np.float32)
        thump += 0.3 * rng.standard_normal(length).astype(np.float32) * np.exp(-t_axis * 60)
        out[start : start + length] += thump * 0.7
        t += float(rng.uniform(0.35, 0.55))
    return out


def env_birdsong(duration: float, sample_rate: int = DEFAULT_SR, seed: int = 0) -> np.ndarray:
    """Ascending and descending FM chirps with silence between phrases."""
    rng = np.random.default_rng(seed)
    n = int(duration * sample_rate)
    out = np.zeros(n, dtype=np.float32)
    t = 0.05
    while t < duration - 0.15:
        length = float(rng.uniform(0.06, 0.14))
        start_hz = float(rng.uniform(2000, 3500))
        end_hz = start_hz + float(rng.choice([-1, 1])) * float(rng.uniform(600, 1800))
        seg = chirp(start_hz, max(400.0, end_hz), length, sample_rate, amplitude=0.35)
        start = int(t * sample_rate)
        stop = min(n, start + len(seg))
        out[start:stop] += seg[: stop - start]
        t += length + float(rng.uniform(0.08, 0.2))
    return out


ENV_CLASSES: tuple[str, ...] = ("alarm", "rain", "footsteps", "birdsong")
ENV_RENDERERS = {
    "alarm": env_alarm,
    "rain": env_rain,
    "footsteps": env_footsteps,
    "birdsong": env_birdsong,
}


def env_sound(kind: str, duration: float = 1.0, sample_rate: int = DEFAULT_SR, seed: int = 0, gain_db: float = -6.0) -> np.ndarray:
    """One environmental clip, peak-normalised then attenuated by ``gain_db``."""
    if kind not in ENV_RENDERERS:
        raise KeyError(f"unknown class {kind!r}; expected one of {ENV_CLASSES}")
    signal = ENV_RENDERERS[kind](duration, sample_rate, seed)
    peak = float(np.max(np.abs(signal))) if signal.size else 0.0
    if peak > 0:
        signal = signal / peak
    return (signal * (10.0 ** (gain_db / 20.0))).astype(np.float32)
