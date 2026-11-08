"""Lab C - Transcribe a short audio clip.

Goal: take one clip all the way from a NumPy array to text, then look inside the step
that turns 30 frames of character probabilities into "stop".

The recogniser is a small convolutional-recurrent network trained with CTC. CTC means
"connectionist temporal classification": the network emits one distribution per frame
and the loss handles alignment, so nobody has to mark where each letter starts. The
decoder then does three things, in this order:

1. take the most likely symbol in each frame;
2. collapse runs of the same symbol ("ssstt" -> "st");
3. drop the blank symbol that separates repeated letters ("st" vs "sst").

Getting any of those wrong produces text that looks almost right, which is why the lab
prints the intermediate frame labels rather than only the final string.

Run:

    python lab_c_transcribe_clip.py
    python lab_c_transcribe_clip.py --selftest

Outputs: ``outputs/lab_c_transcribe.json`` and ``outputs/lab_c_clip.wav``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lab_support as support
from speech_core import asr, audio, features, training


def frame_symbols(rec, samples: np.ndarray, sample_rate: int = 16_000) -> list[str]:
    """The per-frame argmax before collapsing - the raw material the decoder works on."""
    mel = features.mel_spectrogram(samples, sample_rate=sample_rate, n_mels=rec.n_mels)
    usable = mel.shape[0]
    buffer = np.full((1, 1, rec.n_mels, usable), mel.min(), dtype=np.float32)
    buffer[0, 0] = mel.T
    x = training.normalize_inputs(buffer, rec.mean, rec.std)
    import torch

    with torch.no_grad():
        logits = rec.model(torch.from_numpy(x))
    best = logits[0].argmax(dim=1).tolist()
    return [rec.vocab[i] if 0 < i < len(rec.vocab) else "_" for i in best]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    splits, origin = support.speech_splits()
    # The smoke test trains the documented configuration on purpose. Four epochs
    # is not enough for a CTC model to emit every letter of a word, so a shorter
    # run asserts the wrong thing and fails on a correct implementation.
    epochs = args.epochs

    support.rule("corpus and vocabulary")
    vocab = support.vocab_for(splits["train"])
    print(f"origin      : {origin}")
    print(f"splits      : { {k: len(v) for k, v in splits.items()} }  (split by speaker)")
    print(f"vocabulary  : {len(vocab)} symbols {vocab}")
    print("blank is index 0; CTC needs it to separate repeated letters.")

    support.rule(f"training the recogniser ({epochs} epochs)")
    rec = support.recognizer("base", epochs=epochs, log=False)
    info = rec.as_dict()
    print(f"parameters  : {info['parameters_total']:,}  ({info['size_mb']:.2f} MB on disk)")
    print(f"features    : {rec.n_mels} log-Mel bands, normalised mean {rec.mean:.2f} / std {rec.std:.2f}")
    print(f"frame stride: {info['stride_time']} (10 ms frames -> {10 * info['stride_time']} ms per output step)")
    print(f"trained on  : {rec.meta.get('trained_on')} clips in {rec.meta.get('train_seconds')}s")

    clip = next(r for r in splits["test"] if r.transcript == "start")
    support.rule(f"one clip from a speaker the model never heard ({clip.source_id})")
    print(f"reference   : {clip.transcript!r}")
    print(f"duration    : {clip.duration:.2f}s  ({len(clip.samples)} samples at {clip.sample_rate} Hz)")

    symbols = frame_symbols(rec, clip.samples, clip.sample_rate)
    print(f"frame labels: {''.join(symbols)[:80]}")
    print(f"             ({len(symbols)} frames; '_' is the CTC blank)")

    result = rec.transcribe([clip])[0]
    print(f"transcript  : {result['text']!r}   confidence {result['confidence']:.3f}")

    support.rule("the same clip after a round trip through a WAV file")
    path = audio.write_wav(support.OUT / "lab_c_clip.wav", clip.samples, clip.sample_rate)
    info_wav = audio.wav_info(path)
    print(f"file        : {path.relative_to(support.HERE)}  {info_wav}")
    from_file = rec.transcribe_file(path)
    print(f"transcript  : {from_file['text']!r}   confidence {from_file['confidence']:.3f}")

    support.rule("why the frame budget matters")
    frames = training.mel_matrix(clip, n_mels=rec.n_mels).shape[0]
    output_steps = int(np.ceil(frames / info["stride_time"]))
    needed = len(clip.transcript) + 1
    print(f"clip frames {frames} -> {output_steps} output steps after stride {info['stride_time']}")
    print(f"transcript {len(clip.transcript)} characters needs at least {needed} steps (one per character plus a blank)")
    print(f"margin      : {output_steps - needed} steps")

    payload = {
        "lab": "C",
        "title": "transcribe a short clip",
        "corpus_origin": origin,
        "model": info,
        "clip": {"reference": clip.transcript, "speaker": clip.source_id, "duration": clip.duration, "frames": frames},
        "frames": {"output_steps": output_steps, "needed": needed, "margin": output_steps - needed},
        "transcript": result["text"],
        "confidence": result["confidence"],
        "transcript_from_file": from_file["text"],
        "wav_info": info_wav,
        "checks": {},
    }

    checks = {
        "transcript matches the reference": result["text"] == clip.transcript,
        "WAV round trip gives the same text": from_file["text"] == result["text"],
        "confidence above 0.5": result["confidence"] > 0.5,
        "frame budget has positive margin": output_steps - needed > 0,
    }
    failures = 0
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
        failures += 0 if passed else 1
    payload["checks"] = checks

    path = support.write_report("lab_c_transcribe.json", payload)
    print(f"\nreport written to {path.relative_to(support.HERE)}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
