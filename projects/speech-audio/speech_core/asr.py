"""CTC decoding, transcription, and adaptation of a recogniser.

The decoder matters as much as the network. A character-level CTC model emits one
distribution per frame over letters plus a blank; turning that into text requires
three steps - argmax, collapse repeats, drop blanks - and every one of them can be
got wrong in a way that produces plausible garbage ("hhhelllo" or "ssttoopp").

The section also implements **lexicon-constrained** decoding: if the task is known to
be a closed vocabulary, snapping a near-miss to the nearest word is legitimate and is
what production systems do for command words. It is measured separately, because it
hides acoustic errors rather than fixing them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import torch

from . import audio, features, models
from .datasets import AudioRecord
from .text import edit_operations, normalize_text


def ctc_greedy_decode(
    log_probs: np.ndarray,
    vocab: Sequence[str],
    length: int | None = None,
    blank: int = 0,
) -> tuple[str, float]:
    """Collapse a frame-level distribution into text, returning mean confidence.

    ``log_probs`` is ``(T, V)`` - already log-softmaxed. Confidence is the mean
    probability of the emitted (non-blank) symbols, which is a rough confidence, not
    a calibrated probability.
    """
    arr = np.asarray(log_probs, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError("expected a (frames, vocab) matrix")
    if length is not None:
        arr = arr[:length]
    if arr.size == 0:
        return "", 0.0
    best = arr.argmax(axis=1)
    probs = np.exp(arr.max(axis=1))
    collapsed: list[int] = []
    confidences: list[float] = []
    previous = -1
    for frame, token in enumerate(best.tolist()):
        if token != previous and token != blank:
            collapsed.append(token)
            confidences.append(float(probs[frame]))
        previous = token
    text = "".join(vocab[i] for i in collapsed if 0 < i < len(vocab))
    return text, float(np.mean(confidences)) if confidences else 0.0


def decode_output(
    logits: torch.Tensor,
    lengths: torch.Tensor | None,
    vocab: Sequence[str],
) -> list[tuple[str, float]]:
    """Decode a batch of model outputs ``(B, T, V)``."""
    log_probs = logits.log_softmax(2).detach().cpu().numpy()
    results = []
    for i in range(log_probs.shape[0]):
        length = int(lengths[i]) if lengths is not None else None
        results.append(ctc_greedy_decode(log_probs[i], vocab, length=length))
    return results


def transcribe(
    model: torch.nn.Module,
    samples: np.ndarray,
    vocab: Sequence[str],
    sample_rate: int = 16_000,
    n_mels: int = 40,
    mean: float = 0.0,
    std: float = 1.0,
    stride_time: int | None = None,
    max_frames: int | None = None,
) -> dict:
    """Transcribe one clip. Same preprocessing path as training, or the result is noise."""
    mel = features.mel_spectrogram(samples, sample_rate=sample_rate, n_mels=n_mels)
    usable = mel.shape[0]
    frames = usable if max_frames is None else max_frames
    padded = np.full((1, 1, n_mels, frames), mel.min(), dtype=np.float32)
    padded[0, 0, :, : min(usable, frames)] = mel[:frames].T
    x = torch.from_numpy(((padded - mean) / max(std, 1e-6)).astype(np.float32))
    stride = stride_time if stride_time is not None else int(getattr(model, "stride_time", 1))
    with torch.no_grad():
        logits = model(x)
    length = min(logits.shape[1], int(np.ceil(usable / max(stride, 1))))
    text, confidence = decode_output(logits, torch.tensor([length]), vocab)[0]
    return {"text": text, "confidence": confidence, "frames": int(usable)}


def transcribe_records(
    model: torch.nn.Module,
    records: Sequence[AudioRecord],
    vocab: Sequence[str],
    mean: float = 0.0,
    std: float = 1.0,
    n_mels: int = 40,
    max_frames: int | None = None,
) -> list[dict]:
    """Transcribe many clips in one batch (faster, and what the evaluators use)."""
    from . import training

    x, frame_lengths, _ = training.build_inputs(records, n_mels=n_mels, max_frames=max_frames)
    x = training.normalize_inputs(x, mean, std)
    stride = int(getattr(model, "stride_time", 1))
    lengths = training.output_lengths(frame_lengths, stride)
    with torch.no_grad():
        logits = model(torch.from_numpy(x))
    decoded = decode_output(logits, lengths, vocab)
    out = []
    for record, (text, confidence) in zip(records, decoded):
        out.append(
            {
                "text": text,
                "confidence": confidence,
                "reference": record.transcript,
                "speaker": record.meta.get("speaker", record.source_id),
                "source_id": record.source_id,
            }
        )
    return out


# ---------------------------------------------------------------------------
# Lexicon-constrained decoding
# ---------------------------------------------------------------------------


def closest_word(text: str, lexicon: Sequence[str]) -> tuple[str, float, int]:
    """Nearest lexicon entry by character edit distance.

    Returns ``(word, normalised_distance, distance)``. Normalised by the reference
    length so a four-letter miss on a long word is not treated like a four-letter
    miss on a short one.
    """
    normalised = normalize_text(text).replace(" ", "")
    best_word, best_ratio, best_distance = normalised, float("inf"), 10**6
    for word in lexicon:
        candidate = normalize_text(word)
        distance = edit_operations(list(candidate), list(normalised)).errors
        ratio = distance / max(len(candidate), 1)
        if ratio < best_ratio:
            best_word, best_ratio, best_distance = candidate, ratio, distance
    return best_word, best_ratio, best_distance


def lexicon_decode(text: str, lexicon: Sequence[str], max_ratio: float = 0.5) -> dict:
    """Snap ``text`` to the nearest word when it is close enough.

    ``max_ratio`` controls how much correction is allowed. At 0.5 a six-letter word
    can be half wrong; at 0.2 it must be nearly right. Set it to 0.0 to disable
    snapping and see the raw acoustic output - which is what an honest ablation does.
    """
    word, ratio, distance = closest_word(text, lexicon)
    applied = ratio <= max_ratio and normalize_text(text) != word
    return {
        "text": word if applied else normalize_text(text),
        "raw": normalize_text(text),
        "distance": distance,
        "ratio": ratio,
        "applied": applied,
    }


# ---------------------------------------------------------------------------
# Adaptation
# ---------------------------------------------------------------------------


def freeze_feature_extractor(model: torch.nn.Module) -> int:
    """Freeze the convolutional stack, return how many parameters were frozen.

    The convolutions learn spectral patterns that transfer between voices; the
    recurrent layer and output head learn this corpus's vocabulary and timing. On a
    small new speaker set, freezing the front end is the difference between adapting
    and overfitting.
    """
    frozen = 0
    for name, param in model.named_parameters():
        if name.startswith(("conv1", "conv2")):
            param.requires_grad = False
            frozen += param.numel()
    return frozen


def unfreeze_all(model: torch.nn.Module) -> None:
    for param in model.parameters():
        param.requires_grad = True


def adapter_parameters(model: torch.nn.Module) -> list[torch.nn.Parameter]:
    return [p for p in model.parameters() if p.requires_grad]


def load_model(path: str | Path, vocab_size: int, **kwargs) -> models.TinyCRNN:
    model = models.TinyCRNN(vocab_size=vocab_size, **kwargs)
    models.load_checkpoint(model, path)
    return model


def transcribe_file(
    model: torch.nn.Module,
    path: str | Path,
    vocab: Sequence[str],
    **kwargs,
) -> dict:
    samples, rate = audio.read_wav(path)
    return transcribe(model, samples, vocab, sample_rate=rate, **kwargs)


# ---------------------------------------------------------------------------
# A recogniser that cannot forget its own preprocessing
# ---------------------------------------------------------------------------


class Recognizer:
    """A CTC model bundled with the vocabulary and feature statistics it was trained with.

    This exists because of a bug that costs every student an hour: training normalises
    log-Mel features with the training mean and standard deviation, and inference that
    does not apply the same numbers produces confident nonsense. Keeping the three
    together - weights, vocabulary, normalisation - makes the mismatch impossible.

    Typical use::

        rec = Recognizer.train(train, val, vocab, epochs=12)
        print(rec.transcribe(test_records)[0]["text"])
        rec.save("outputs/recogniser.pt")
    """

    def __init__(
        self,
        model: torch.nn.Module,
        vocab: Sequence[str],
        mean: float = 0.0,
        std: float = 1.0,
        n_mels: int = 40,
        meta: dict | None = None,
    ):
        self.model = model
        self.vocab = list(vocab)
        self.mean = float(mean)
        self.std = float(std)
        self.n_mels = int(n_mels)
        self.meta = dict(meta or {})

    # -- construction -------------------------------------------------------
    @classmethod
    def train(
        cls,
        train_records: Sequence[AudioRecord],
        val_records: Sequence[AudioRecord],
        vocab: Sequence[str] | None = None,
        *,
        epochs: int = 12,
        lr: float = 3e-3,
        batch_size: int = 16,
        seed: int = 0,
        n_mels: int = 40,
        stride_time: int = 2,
        width: int = 16,
        hidden: int = 64,
        augment: bool = False,
        log: bool = True,
    ) -> tuple["Recognizer", dict]:
        from . import training

        if vocab is None:
            from .text import build_char_vocab

            vocab = build_char_vocab([r.transcript for r in train_records])
        # Seed before the network is built: initial weights come from the global RNG,
        # so seeding inside train_ctc (which runs after construction) would leave the
        # starting point process-dependent and every reported number would drift.
        models.set_seed(seed)
        model = models.TinyCRNN(
            vocab_size=len(vocab), n_mels=n_mels, stride_time=stride_time, width=width, hidden=hidden
        )
        history, model = training.train_ctc(
            model,
            train_records,
            vocab,
            val_records,
            n_mels=n_mels,
            epochs=epochs,
            lr=lr,
            batch_size=batch_size,
            seed=seed,
            augment=augment,
            log=log,
        )
        meta = {
            "trained_on": len(train_records),
            "validated_on": len(val_records),
            "epochs": epochs,
            "lr": lr,
            "seed": seed,
            "stride_time": stride_time,
            "width": width,
            "hidden": hidden,
            "train_seconds": round(history["total_seconds"], 2),
        }
        return cls(model, vocab, history["mean"], history["std"], n_mels, meta), history

    # -- inference ----------------------------------------------------------
    def transcribe(self, records: Sequence[AudioRecord]) -> list[dict]:
        return transcribe_records(self.model, records, self.vocab, mean=self.mean, std=self.std, n_mels=self.n_mels)

    def transcribe_samples(self, samples: np.ndarray, sample_rate: int = 16_000) -> dict:
        return transcribe(
            self.model,
            samples,
            self.vocab,
            sample_rate=sample_rate,
            n_mels=self.n_mels,
            mean=self.mean,
            std=self.std,
        )

    def transcribe_file(self, path: str | Path) -> dict:
        samples, rate = audio.read_wav(path)
        result = self.transcribe_samples(samples, rate)
        result["path"] = str(path)
        return result

    # -- persistence --------------------------------------------------------
    def save(self, path: str | Path) -> Path:
        payload = {
            "state_dict": self.model.state_dict(),
            "vocab": self.vocab,
            "mean": self.mean,
            "std": self.std,
            "n_mels": self.n_mels,
            "meta": self.meta,
            "stride_time": int(getattr(self.model, "stride_time", 1)),
        }
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(payload, path)
        return path

    @classmethod
    def load(cls, path: str | Path) -> "Recognizer":
        payload = torch.load(Path(path), map_location="cpu", weights_only=False)
        meta = payload.get("meta") or {}
        # Width and hidden have to come back too, or a checkpoint from a smaller or larger
        # model fails to load with a wall of size-mismatch warnings: the architecture is part
        # of the checkpoint, not a detail of whoever happens to load it.
        model = models.TinyCRNN(
            vocab_size=len(payload["vocab"]),
            n_mels=payload.get("n_mels", 40),
            stride_time=payload.get("stride_time", 2),
            width=int(meta.get("width", 16)),
            hidden=int(meta.get("hidden", 64)),
        )
        model.load_state_dict(payload["state_dict"])
        model.eval()
        return cls(model, payload["vocab"], payload["mean"], payload["std"], payload.get("n_mels", 40), meta)

    # -- reporting ----------------------------------------------------------
    def as_dict(self) -> dict:
        info = models.summarize_model(self.model)
        return {
            **info,
            "vocab_size": len(self.vocab),
            "vocab": self.vocab,
            "normalisation": {"mean": round(self.mean, 4), "std": round(self.std, 4)},
            "stride_time": int(getattr(self.model, "stride_time", 1)),
            **self.meta,
        }
