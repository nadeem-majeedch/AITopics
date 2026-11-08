"""Lab D - Evaluate speech recognition with word error rate.

Goal: measure a recogniser properly, and see why one number is never enough.

Word error rate is the edit distance between reference and hypothesis, counted in
words: substitutions + insertions + deletions, divided by the number of reference
words. It can exceed 1.0 when the system inserts extra words.

The recogniser reaches WER 0.000 on this clean six-word corpus. That is not a good
system, it is an easy task: six words, isolated utterances, and voices built from the
same synthesiser. So the lab evaluates three corpora instead of one:

* **clean** - the saturated case, included so you can see saturation;
* **5 dB SNR** - the same clips with heavy noise, where WER, per-word accuracy, and the
  confusion list have something to report;
* **seven conditions** - noise, gain, rate, and bandwidth, because "works on my test
  set" is not a deployment claim.

It also measures the difference between corpus WER (total errors / total reference
words) and the mean of per-utterance WERs. They are different numbers and quoting the
lower one is a common way to look better than you are. Finally it runs the lexicon
ablation: snapping output to the six known words helps a closed vocabulary and would
be cheating on an open one.

Run:

    python lab_d_wer_evaluation.py
    python lab_d_wer_evaluation.py --selftest

Output: ``outputs/lab_d_wer.json``
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lab_support as support
from speech_core import datasets, evaluate, metrics, text

LEXICON = list(datasets.WORDS)


def analyse(rec, records) -> dict:
    """Everything this lab reports about one corpus."""
    rows = rec.transcribe(records)
    pairs = [(row["reference"], row["text"]) for row in rows]
    report = text.corpus_error_rates(pairs)
    per_word: dict[str, dict] = {}
    for reference, hypothesis in pairs:
        bucket = per_word.setdefault(reference, {"n": 0, "correct": 0})
        bucket["n"] += 1
        bucket["correct"] += int(text.normalize_text(reference) == text.normalize_text(hypothesis))
    for bucket in per_word.values():
        bucket["accuracy"] = bucket["correct"] / bucket["n"]
    return {
        "rows": rows,
        "wer": report["wer"],
        "cer": report["cer"],
        "sentence_accuracy": report["sentence_accuracy"],
        "substitutions": report["substitutions"],
        "insertions": report["insertions"],
        "deletions": report["deletions"],
        "reference_words": report["reference_words"],
        "mean_per_clip_wer": float(np.mean([text.word_error_rate(r, h)["wer"] for r, h in pairs])),
        "per_word": per_word,
        "confusions": [{"reference": a, "recognised": b, "count": c} for a, b, c in text.confusion_pairs(pairs)],
        "lexicon": evaluate.lexicon_ablation(pairs, LEXICON),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    splits, origin = support.speech_splits()
    epochs = 4 if args.selftest else args.epochs
    rec = support.recognizer("base", epochs=epochs, log=False)

    support.rule("corpus")
    print(f"origin      : {origin}")
    print(f"train       : {len(splits['train'])} clips, {len({r.source_id for r in splits['train']})} speakers")
    print(f"test        : {len(splits['test'])} clips, {len({r.source_id for r in splits['test']})} unseen speakers")

    clean = analyse(rec, splits["test"])
    support.rule("clean test set (saturated - do not quote this as a capability)")
    print(f"corpus WER        : {clean['wer']:.3f}")
    print(f"mean of per-clip  : {clean['mean_per_clip_wer']:.3f}")
    print(f"character error   : {clean['cer']:.3f}")
    print(f"sentence accuracy : {clean['sentence_accuracy']:.3f}")
    print(f"errors            : {clean['substitutions']} substitutions, {clean['insertions']} insertions, "
          f"{clean['deletions']} deletions over {clean['reference_words']} reference words")

    noisy_records = evaluate.apply_condition(splits["test"], next(c for c in evaluate.CONDITIONS if c.name == "snr_5"))
    noisy = analyse(rec, noisy_records)
    support.rule("5 dB SNR (the same clips, heavily noisier)")
    for row in noisy["rows"][:6]:
        mark = "ok " if row["reference"] == row["text"] else "err"
        print(f"  {mark} ref {row['reference']:<6} hyp {row['text']!r:<10} conf {row['confidence']:.2f}")
    print(f"\ncorpus WER        : {noisy['wer']:.3f}")
    print(f"mean of per-clip  : {noisy['mean_per_clip_wer']:.3f}")
    print(f"character error   : {noisy['cer']:.3f}")
    print(f"sentence accuracy : {noisy['sentence_accuracy']:.3f}")
    print(f"errors            : {noisy['substitutions']} substitutions, {noisy['insertions']} insertions, "
          f"{noisy['deletions']} deletions over {noisy['reference_words']} reference words")
    if abs(noisy["wer"] - noisy["mean_per_clip_wer"]) > 1e-9:
        print("The two WERs differ because every clip here has one word: reporting the")
        print("lower of the two across corpora is how a system gets described as better than it is.")

    support.rule("per-word accuracy at 5 dB SNR")
    support.table(
        [{"word": w, "accuracy": v["accuracy"], "n": v["n"]} for w, v in sorted(noisy["per_word"].items())],
        ["word", "accuracy", "n"],
    )
    support.rule("confusions at 5 dB SNR")
    if noisy["confusions"]:
        support.table(noisy["confusions"][:6], ["reference", "recognised", "count"])
    else:
        print("no whole-word confusions: the errors are insertions and deletions inside words")

    support.rule("lexicon ablation (closed vocabulary only)")
    lex = noisy["lexicon"]
    print(f"threshold          : normalised edit distance <= {lex['max_ratio']}")
    print(f"WER before         : {lex['wer_before']:.3f}")
    print(f"WER after          : {lex['wer_after']:.3f}  ({lex['absolute_gain']:+.3f})")
    print(f"utterances changed : {lex['utterances_changed']} of {len(noisy['rows'])}")
    print(lex["caveat"])

    support.rule("all conditions")
    condition_rows = []
    for condition in evaluate.CONDITIONS:
        perturbed = evaluate.apply_condition(splits["test"], condition)
        result = analyse(rec, perturbed)
        condition_rows.append(
            {
                "condition": condition.name,
                "wer": result["wer"],
                "cer": result["cer"],
                "sentence_accuracy": result["sentence_accuracy"],
                "needs_lexicon": result["lexicon"]["wer_after"],
            }
        )
    support.table(condition_rows, ["condition", "wer", "cer", "sentence_accuracy", "needs_lexicon"])
    worst = max(condition_rows, key=lambda r: r["wer"])
    print(f"worst: {worst['condition']} at WER {worst['wer']:.3f}")
    print("`needs_lexicon` is the WER if you are allowed to snap to the six known words.")
    print("That is legitimate here and would be dishonest on open-vocabulary speech.")

    payload = {
        "lab": "D",
        "title": "word error rate evaluation",
        "corpus_origin": origin,
        "test_clips": len(splits["test"]),
        "clean": {k: v for k, v in clean.items() if k not in {"rows", "per_word", "confusions", "lexicon"}},
        "snr_5_detail": {
            **{k: v for k, v in noisy.items() if k not in {"rows", "per_word", "confusions", "lexicon"}},
            "per_word": noisy["per_word"],
            "confusions": noisy["confusions"],
            "lexicon": noisy["lexicon"],
            "utterances": noisy["rows"],
        },
        "conditions": condition_rows,
        "checks": {},
    }

    checks = {
        "corpus WER in [0, 2]": 0.0 <= clean["wer"] <= 2.0 and 0.0 <= noisy["wer"] <= 2.0,
        "counts add up to the reported errors": noisy["substitutions"] + noisy["insertions"] + noisy["deletions"]
        == int(round(noisy["wer"] * noisy["reference_words"])),
        "noise does not improve WER": noisy["wer"] >= clean["wer"] - 1e-9,
        "lexicon does not make WER worse": noisy["lexicon"]["wer_after"] <= noisy["lexicon"]["wer_before"] + 1e-9,
        "per-word accuracy covers every word": len(noisy["per_word"]) == len(datasets.WORDS),
        "every condition was measured": len(condition_rows) == len(evaluate.CONDITIONS),
    }
    failures = 0
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
        failures += 0 if passed else 1
    payload["checks"] = checks

    path = support.write_report("lab_d_wer.json", payload)
    print(f"\nreport written to {path.relative_to(support.HERE)}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
