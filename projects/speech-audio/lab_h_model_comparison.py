"""Lab H - Compare inference speed and recognition quality across models.

Goal: measure the trade-off instead of guessing it. Three recognisers of the same
family, trained on the same data for the same number of epochs, differ only in size
and in how much they compress time:

===========  =======  =======  ==========  ==================================
name         stride   width    hidden      what it buys / costs
===========  =======  =======  ==========  ==================================
small        3        12       48          fastest, fewest parameters
baseline     2        16       64          the model the other labs use
accurate     1        24       96          four times the compute per second
===========  =======  =======  ==========  ==================================

``stride`` is temporal subsampling inside the network: with 10 ms frames, stride 3
emits one prediction every 30 ms. That is the single most consequential knob, because
it sets both the compute and the minimum length a transcript can have - a five-letter
word needs six output steps including a blank.

Quality is measured two ways: word error rate on clean audio, and word error rate at
10 dB SNR, because a model that is better on clean audio is not always better in noise.

Speed is measured as a real-time factor (RTF): processing time divided by audio
duration. RTF below 1 means faster than real time. It is measured on this CPU, so the
absolute numbers are specific to the machine; the ordering and the ratios are the
transferable part.

Run:

    python lab_h_model_comparison.py
    python lab_h_model_comparison.py --selftest

Output: ``outputs/lab_h_model_comparison.json``
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lab_support as support
from speech_core import asr, datasets, evaluate, metrics, text

CONFIGS = (
    {"name": "small", "stride_time": 3, "width": 12, "hidden": 48},
    {"name": "baseline", "stride_time": 2, "width": 16, "hidden": 64},
    {"name": "accurate", "stride_time": 1, "width": 24, "hidden": 96},
)


def word_error_rate(rec, records) -> float:
    rows = rec.transcribe(records)
    return float(text.corpus_error_rates([(r["reference"], r["text"]) for r in rows])["wer"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    splits, origin = support.speech_splits()
    epochs = 3 if args.selftest else args.epochs
    test = splits["test"]
    noisy = evaluate.apply_condition(test, next(c for c in evaluate.CONDITIONS if c.name == "snr_10"))
    audio_seconds = sum(r.duration for r in test)

    support.rule("setup")
    print(f"test clips  : {len(test)} ({audio_seconds:.1f}s of audio)")
    print(f"training    : same {len(splits['train'])} clips, {epochs} epochs, identical seed")
    print("Only the architecture varies, so differences are attributable to it.")

    rows = []
    records = {}
    for config in CONFIGS:
        started = time.perf_counter()
        rec = support.recognizer(
            config["name"],
            epochs=epochs,
            stride_time=config["stride_time"],
            width=config["width"],
            hidden=config["hidden"],
            log=False,
            # Train here rather than reuse the cache: the training-time column is part of the
            # comparison, and a cache hit would report 0.0 s for a model that takes 5 s.
            force=True,
        )
        train_seconds = time.perf_counter() - started
        info = rec.as_dict()
        clean_wer = word_error_rate(rec, test)
        noisy_wer = word_error_rate(rec, noisy)

        stats = metrics.benchmark(lambda: rec.transcribe(test), runs=3, warmup=1, label=config["name"], audio_seconds=audio_seconds)
        deadlines = 10 * config["stride_time"]
        rows.append(
            {
                "model": config["name"],
                "params": info["parameters_total"],
                "size MB": round(info["size_mb"], 2),
                "stride": config["stride_time"],
                "step ms": deadlines,
                "train s": round(train_seconds, 2),
                "WER clean": clean_wer,
                "WER 10dB": noisy_wer,
                "median ms": round(stats.median_ms, 1),
                "RTF": round(stats.real_time_factor, 4),
            }
        )
        records[config["name"]] = rec
        print(f"  trained {config['name']:<9} in {train_seconds:.1f}s  ({info['parameters_total']:,} parameters)")

    support.rule("speed and quality")
    support.table(rows, ["model", "params", "size MB", "stride", "step ms", "train s", "WER clean", "WER 10dB", "median ms", "RTF"])

    baseline = next(r for r in rows if r["model"] == "baseline")
    support.rule("relative to the baseline")
    for row in rows:
        if row["model"] == "baseline":
            continue
        print(f"  {row['model']:<9} params x{row['params'] / baseline['params']:.2f}  "
              f"RTF x{row['RTF'] / max(baseline['RTF'], 1e-9):.2f}  "
              f"clean WER {row['WER clean'] - baseline['WER clean']:+.3f}  "
              f"noisy WER {row['WER 10dB'] - baseline['WER 10dB']:+.3f}")

    support.rule("closed-vocabulary decoding on the worst model")
    worst = max(rows, key=lambda r: r["WER 10dB"])
    lex = evaluate.lexicon_ablation(
        [(r["reference"], r["text"]) for r in records[worst["model"]].transcribe(noisy)],
        list(datasets.WORDS),
    )
    print(f"worst model : {worst['model']} at 10 dB SNR (WER {worst['WER 10dB']:.3f})")
    print(f"WER after snapping to the six known words: {lex['wer_after']:.3f} "
          f"({lex['absolute_gain']:+.3f} from {lex['wer_before']:.3f})")
    print(lex["caveat"])

    support.rule("how to read this")
    print("  The fastest model is not the smallest WER, and not every step up in size")
    print("  buys accuracy. Pick the cheapest model that meets the error budget for the")
    print("  audio you actually receive, then re-measure on that audio.")
    print(f"  All timings are CPU-only on this machine; GPU numbers would differ in scale.")

    payload = {
        "lab": "H",
        "title": "model comparison: speed vs recognition quality",
        "corpus_origin": origin,
        "epochs": epochs,
        "test_clips": len(test),
        "audio_seconds": round(audio_seconds, 2),
        "rows": rows,
        "lexicon_on_worst": lex,
        "checks": {},
    }

    fastest = min(rows, key=lambda r: r["RTF"])
    checks = {
        "stride 1 is slower than stride 3": next(r for r in rows if r["stride"] == 1)["RTF"]
        > next(r for r in rows if r["stride"] == 3)["RTF"],
        "every model produces WER in [0, 2]": all(0.0 <= r["WER clean"] <= 2.0 and 0.0 <= r["WER 10dB"] <= 2.0 for r in rows),
        "at least one model is faster than real time": any(r["RTF"] < 1.0 for r in rows),
        "lexicon decoding does not hurt": lex["wer_after"] <= lex["wer_before"] + 1e-9,
    }
    failures = 0
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
        failures += 0 if passed else 1
    payload["checks"] = checks

    path = support.write_report("lab_h_model_comparison.json", payload)
    print(f"\nreport written to {path.relative_to(support.HERE)}")
    print(f"fastest: {fastest['model']} at RTF {fastest['RTF']:.3f}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
