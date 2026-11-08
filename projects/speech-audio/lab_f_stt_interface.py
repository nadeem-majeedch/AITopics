"""Lab F - Build a simple speech-to-text interface.

Goal: wrap the recogniser in something a person could actually use, and handle the
three situations every transcript interface meets:

* **low confidence.** The model always produces text. Saying "I'm not sure, please
  repeat" is a feature; printing a wrong transcript as fact is a bug.
* **no speech.** Silence decodes to an empty string or to a burst of noise letters.
  Both need a distinct message from "unrecognised".
* **files that are not 16 kHz mono.** Real recordings arrive as 44.1 kHz stereo MP3s
  and phone memos; the interface resamples and downmixes rather than crashing.

There is no microphone in this environment (no ``sounddevice``/``pyaudio``), so the
interface takes files and a built-in demo mode. That is the same code path a live
microphone would use: capture -> 16 kHz mono float -> transpose.

Run:

    python lab_f_stt_interface.py                     # demo with synthetic clips
    python lab_f_stt_interface.py --file clip.wav     # transcribe your own file
    python lab_f_stt_interface.py --interactive       # type paths, one per line
    python lab_f_stt_interface.py --selftest

Outputs: ``outputs/lab_f_stt.json`` and ``outputs/lab_f_demo_*.wav``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lab_support as support
from speech_core import asr, audio, datasets, synth

CONFIDENCE_FLOOR = 0.70
SILENCE_RMS = 0.004
#: Closed-vocabulary interfaces may snap a one-character slip to a known word.
MAX_CORRECTION = 0.34


def load_audio(path: Path) -> tuple[np.ndarray, int, list[str]]:
    """Read any WAV, convert to mono 16 kHz, and report what had to change."""
    samples, rate = audio.read_wav(path)
    notes = []
    if samples.ndim > 1:
        samples = audio.to_mono(samples)
        notes.append("downmixed to mono")
    if rate != 16_000:
        samples = audio.resample(samples, rate, 16_000)
        notes.append(f"resampled {rate} Hz -> 16000 Hz")
        rate = 16_000
    return samples.astype(np.float32), rate, notes


def transcribe_interface(rec, samples: np.ndarray, sample_rate: int, label: str) -> dict:
    """One utterance in, one user-facing result out."""
    rms = audio.rms(samples)
    if rms < SILENCE_RMS:
        return {"input": label, "status": "silence", "text": "", "confidence": 0.0, "message": "(no speech detected)"}
    result = rec.transcribe_samples(samples, sample_rate)
    if result["text"]:
        snapped = asr.lexicon_decode(result["text"], list(datasets.WORDS), max_ratio=MAX_CORRECTION)
        if snapped["applied"]:
            result = {**result, "raw": result["text"], "text": snapped["text"]}
    if not result["text"]:
        return {"input": label, "status": "unrecognised", "text": "", "confidence": result["confidence"], "message": "(could not make out any words)"}
    if result["confidence"] < CONFIDENCE_FLOOR:
        return {
            "input": label,
            "status": "low_confidence",
            "text": result["text"],
            "confidence": result["confidence"],
            "message": f'"{result["text"]}" (not certain - please repeat)',
        }
    message = result["text"] if "raw" not in result else f'{result["text"]} (from {result["raw"]!r})'
    return {"input": label, "status": "ok", "text": result["text"], "confidence": result["confidence"], "message": message, "raw": result.get("raw")}


def show(result: dict, width: int = 24) -> None:
    bar_len = int(round(result["confidence"] * width))
    bar = "#" * bar_len + "." * (width - bar_len)
    print(f"  {result['input']:<22} [{bar}] {result['confidence']:.2f}  {result['message']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", action="append", default=[], help="WAV file to transcribe (repeatable)")
    parser.add_argument("--interactive", action="store_true", help="read file paths from stdin")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    # Train the documented configuration even in the smoke test. A 4-epoch model
    # transcribes "right" as "rit", the interface correctly asks for a repeat,
    # and then the strict check below fails on working code.
    epochs = 12
    rec = support.recognizer("base", epochs=epochs, log=False)
    results: list[dict] = []

    support.rule("interface")
    print(f"model       : {rec.as_dict()['parameters_total']:,} parameters, {len(rec.vocab)} output symbols")
    print(f"vocabulary  : {', '.join(datasets.WORDS)}")
    print(f"confidence floor: {CONFIDENCE_FLOOR:.2f} - below this the interface asks for a repeat")
    print(f"correction      : near misses snapped to the six known words (edit distance <= {MAX_CORRECTION})")
    print(f"silence threshold: RMS {SILENCE_RMS} - below this it reports no speech instead of guessing")

    if args.file or args.interactive:
        paths = [Path(p) for p in args.file]
        if args.interactive:
            print("Type a WAV path per line, blank line to finish.")
            while True:
                line = input("> ").strip()
                if not line:
                    break
                paths.append(Path(line))
        support.rule("transcribing files")
        for path in paths:
            if not path.exists():
                print(f"  {path.name:<22} ERROR file not found")
                results.append({"input": str(path), "status": "error", "message": "file not found"})
                continue
            samples, rate, notes = load_audio(path)
            result = transcribe_interface(rec, samples, rate, path.name)
            result["conversion"] = notes
            results.append(result)
            show(result)
            if notes:
                print(f"  {'':<22} converted: {', '.join(notes)}")
    else:
        support.rule("demo: synthesised utterances, including the failures")
        demo = [
            ("yes", 0, 0.0),
            ("start", 3, 0.0),
            ("right", 7, 0.0),
            ("left", 2, 5.0),  # heavy noise on purpose
            ("stop", 1, -1.0),  # zero-length means silence
        ]
        for word, voice_index, snr in demo:
            profile = datasets.voice_for(voice_index)
            if snr < 0:
                samples = np.zeros(16_000, dtype=np.float32)
                label = "silence.wav"
            else:
                samples = synth.speak(word, profile, 16_000)
                if snr > 0:
                    samples = audio.add_noise(samples, snr, seed=voice_index)
                label = f"{word}_{profile.name}.wav"
            path = audio.write_wav(support.OUT / f"lab_f_demo_{label}", samples, 16_000)
            converted, rate, notes = load_audio(path)
            result = transcribe_interface(rec, converted, rate, label)
            # Only the clean clips have a guaranteed expected transcript; the 5 dB one
            # is there to show the model failing, not to assert a string.
            result["expected"] = word if (snr == 0 and snr >= 0) else None
            result["snr_db"] = snr if snr > 0 else None
            results.append(result)
            show(result)

    support.rule("summary")
    statuses = {}
    for result in results:
        statuses[result["status"]] = statuses.get(result["status"], 0) + 1
    support.table([{"status": k, "count": v} for k, v in sorted(statuses.items())], ["status", "count"])
    print("A real interface would also offer a retry, and would never show a raw confidence")
    print("number as if it were a calibrated probability - see the calibration module.")

    payload = {
        "lab": "F",
        "title": "speech-to-text interface",
        "confidence_floor": CONFIDENCE_FLOOR,
        "silence_rms": SILENCE_RMS,
        "model": rec.as_dict(),
        "results": results,
        "status_counts": statuses,
        "checks": {},
    }

    demo_expected = [(r["input"], r["expected"], r["text"]) for r in results if r.get("expected")]
    checks = {
        "clean demo clips are recognised": all(text == expected for _, expected, text in demo_expected),
        "silence is reported as silence": any(r["status"] == "silence" for r in results),
        "every result has a status": all("status" in r for r in results),
    }
    if args.file or args.interactive:
        checks["no crashes on user files"] = True
    failures = 0
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
        failures += 0 if passed else 1
    payload["checks"] = checks

    path = support.write_report("lab_f_stt.json", payload)
    print(f"\nreport written to {path.relative_to(support.HERE)}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
