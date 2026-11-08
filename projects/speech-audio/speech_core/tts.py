"""Text-to-speech: a rule-based formant synthesiser, plus an honest account of what
production TTS actually is.

The synthesiser speaks the six-word vocabulary taught in this section and spells
unknown words letter by letter using approximate letter sounds. That is enough to
build the voice-assistant loop end to end on a CPU with no download, and it is not a
neural TTS system: the prosody is flat, the voice is synthetic, and intelligibility
drops on any word outside the vocabulary.

For a real system you would use a neural vocoder plus an acoustic model (VITS,
Tacotron, Piper, or a hosted service). Those need model weights, usually a few
hundred megabytes and often a GPU. ``neural_tts_available`` reports why that path is
not available here rather than failing at import.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np

from . import audio, datasets, synth


#: Rough letter-to-sound map for spelling unknown words.
LETTER_SOUNDS: dict[str, str] = {
    "a": "a",
    "b": "p",
    "c": "s",
    "d": "t",
    "e": "e",
    "f": "f",
    "g": "g",
    "h": "h",
    "i": "i",
    "j": "s",
    "k": "t",
    "l": "l",
    "m": "n",
    "n": "n",
    "o": "o",
    "p": "p",
    "q": "t",
    "r": "r",
    "s": "s",
    "t": "t",
    "u": "u",
    "v": "f",
    "w": "y",
    "x": "s",
    "y": "y",
    "z": "s",
}


@dataclass
class SynthesisResult:
    samples: np.ndarray
    sample_rate: int
    text: str
    spoken_words: list[str]
    in_vocabulary: bool
    note: str = ""

    @property
    def duration(self) -> float:
        return len(self.samples) / float(self.sample_rate)

    def as_dict(self) -> dict:
        return {
            "text": self.text,
            "words": self.spoken_words,
            "duration": round(self.duration, 3),
            "in_vocabulary": self.in_vocabulary,
            "note": self.note,
        }


class FormantTTS:
    """Deterministic, offline "speech generation" for the assistant loop."""

    def __init__(self, voice_index: int = 1, sample_rate: int = 16_000, word_gap: float = 0.08):
        self.profile = datasets.voice_for(voice_index)
        self.sample_rate = sample_rate
        self.word_gap = word_gap

    def speak_word(self, word: str) -> np.ndarray:
        normalised = word.lower().strip()
        if normalised in synth.WORDS:
            return synth.speak(normalised, self.profile, self.sample_rate)
        return self._spell(normalised)

    def _spell(self, word: str) -> np.ndarray:
        pieces: list[np.ndarray] = []
        for char in word:
            phoneme = LETTER_SOUNDS.get(char)
            if phoneme is None:
                continue
            pieces.append(synth._phoneme_audio(synth.PHONEMES[phoneme], self.profile, self.sample_rate))
            pieces.append(np.zeros(int(0.02 * self.sample_rate), dtype=np.float32))
        return np.concatenate(pieces) if pieces else np.zeros(int(0.1 * self.sample_rate), dtype=np.float32)

    def synthesize(self, text: str) -> SynthesisResult:
        words = [w for w in str(text).lower().replace(",", " ").replace(".", " ").split() if w]
        if not words:
            return SynthesisResult(np.zeros(int(0.2 * self.sample_rate), dtype=np.float32), self.sample_rate, text, [], True)
        pieces: list[np.ndarray] = []
        spoken: list[str] = []
        gap = np.zeros(int(self.word_gap * self.sample_rate), dtype=np.float32)
        for word in words:
            pieces.append(self.speak_word(word))
            pieces.append(gap)
            spoken.append(word)
        samples = np.concatenate(pieces).astype(np.float32)
        unknown = [w for w in words if w not in synth.WORDS]
        note = "" if not unknown else f"spelled {len(unknown)} word(s) outside the vocabulary: {', '.join(unknown[:4])}"
        return SynthesisResult(
            samples=samples,
            sample_rate=self.sample_rate,
            text=text,
            spoken_words=spoken,
            in_vocabulary=not unknown,
            note=note,
        )

    def save(self, text: str, path: str | Path) -> Path:
        result = self.synthesize(text)
        return audio.write_wav(path, result.samples, self.sample_rate)


def neural_tts_available() -> tuple[bool, str]:
    """Report whether a neural TTS stack is importable, and why not if it is not."""
    for module, label in (("piper", "Piper"), ("TTS", "Coqui TTS"), ("torchaudio", "torchaudio pipelines")):
        if importlib.util.find_spec(module) is not None:
            return True, f"{label} is installed"
    return False, (
        "No neural TTS package is installed (checked piper, TTS, torchaudio). "
        "The formant synthesiser is used instead; a neural system needs weights "
        "(hundreds of MB) and often a GPU."
    )


def describe_synthesis(text: str, result: SynthesisResult) -> str:
    """One-line summary for a log or a student report."""
    return (
        f"'{text}' -> {result.duration:.2f}s at {result.sample_rate} Hz "
        f"({len(result.spoken_words)} word(s), in-vocabulary={result.in_vocabulary})"
        + (f" | {result.note}" if result.note else "")
    )
