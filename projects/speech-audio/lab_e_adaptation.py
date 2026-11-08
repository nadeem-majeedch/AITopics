"""Lab E - Adapt a pretrained recogniser to a small permitted dataset.

Goal: take the recogniser trained on clean speech, show that it degrades on noisy
input, and adapt it with eighteen noisy clips from speakers it has never heard.

What "pretrained" means here, honestly: the base model was trained in this course on
synthetic voices, not downloaded. The mechanics match adapting Whisper or wav2vec2 to
a new language, accent, or channel - freeze a feature front end, fine-tune a small
head, keep an untouched evaluation set - but the numbers belong to this corpus. A real
adaptation starts from a checkpoint that already knows English.

The adaptation protocol, which is the part that matters:

* adapt on utterance 0 of each new speaker, evaluate on utterance 1 - never the same
  clips, or the result measures memorisation;
* report the "before" number first, from the unmodified model, on identical clips;
* compare a frozen front end with full fine-tuning, because on 18 clips a full update
  often destroys what the model already knew;
* check the model still works on clean audio afterwards. Adapting to noise and losing
  clean accuracy is a regression, not an improvement.

Consent: the "new speakers" are synthetic voice profiles, so there is nothing to
consent to. With real speakers you need documented permission, a stated purpose, and
a deletion path before fine-tuning on anyone's voice.

Run:

    python lab_e_adaptation.py
    python lab_e_adaptation.py --selftest

Output: ``outputs/lab_e_adaptation.json``
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lab_support as support
from speech_core import asr, audio, datasets, text, training
from speech_core.datasets import AudioRecord


def add_noise(records, snr_db: float, seed: int = 0):
    """Same clips, white noise at a fixed SNR - a stand-in for a noisier channel."""
    out = []
    for i, record in enumerate(records):
        out.append(
            AudioRecord(
                samples=audio.add_noise(record.samples, snr_db, seed=seed + i),
                sample_rate=record.sample_rate,
                label=record.label,
                source_id=record.source_id,
                meta={**record.meta, "snr_db": snr_db},
            )
        )
    return out


def wer(rec, records) -> float:
    rows = rec.transcribe(records)
    return float(text.corpus_error_rates([(r["reference"], r["text"]) for r in rows])["wer"])


def cache_path(epochs: int) -> Path:
    return support.CACHE / f"base_e{epochs}_lr0.003_s2_w16_h64_seed0.pt"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-epochs", type=int, default=12)
    parser.add_argument("--adapt-epochs", type=int, default=8)
    parser.add_argument(
        "--snr",
        type=float,
        default=5.0,
        help="SNR of the new domain. 5 dB is hard enough that the base model fails and "
        "adaptation has something to fix; 10 dB is too easy for this corpus.",
    )
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    splits, origin = support.speech_splits()
    base_epochs = 4 if args.selftest else args.base_epochs
    adapt_epochs = 3 if args.selftest else args.adapt_epochs

    support.rule("base model (trained on clean audio from 18 speakers)")
    base = support.recognizer("base", epochs=base_epochs, log=False)
    new_speakers = sorted({r.source_id for r in splits["test"]})
    print(f"base data   : {len(splits['train'])} clips, {len({r.source_id for r in splits['train']})} speakers")
    print(f"new domain  : {new_speakers} (never used in training), noise at {args.snr:.0f} dB SNR")
    print(f"base params : {base.as_dict()['parameters_total']:,}")

    # The "new dataset": the same new speakers, but recorded in noise.
    adapt_all = add_noise(splits["test"], args.snr)
    adapt = [r for r in adapt_all if r.meta.get("utterance") == 0]
    eval_set = [r for r in adapt_all if r.meta.get("utterance") == 1]
    clean_eval = [r for r in splits["test"] if r.meta.get("utterance") == 1]
    print(f"adaptation  : {len(adapt)} noisy clips (utterance 0 of each word)")
    print(f"evaluation  : {len(eval_set)} noisy clips (utterance 1 - held out)")
    print(f"clean check : {len(clean_eval)} clean clips, to catch forgetting")

    before = wer(base, eval_set)
    clean_before = wer(base, clean_eval)
    support.rule("before adaptation")
    print(f"WER on noisy new speakers : {before:.3f}")
    print(f"WER on clean new speakers : {clean_before:.3f}")
    for row in base.transcribe(eval_set)[:6]:
        print(f"  ref {row['reference']:<6} hyp {row['text']!r:<10} conf {row['confidence']:.2f}")

    support.rule("frozen-front-end adaptation")
    frozen = asr.Recognizer.load(cache_path(base_epochs))
    frozen_params = asr.freeze_feature_extractor(frozen.model)
    total_params = sum(p.numel() for p in frozen.model.parameters())
    print(f"frozen      : {frozen_params:,} of {total_params:,} parameters ({frozen_params / total_params:.0%})")
    print("The convolution stack keeps the spectral patterns it learned; the GRU and output")
    print("head absorb the new acoustic conditions.")
    started = time.perf_counter()
    history, frozen.model = training.train_ctc(
        frozen.model, adapt, frozen.vocab, eval_set, epochs=adapt_epochs, lr=1e-3, batch_size=8, seed=1, log=False
    )
    frozen.mean, frozen.std = history["mean"], history["std"]
    frozen_seconds = time.perf_counter() - started
    after_frozen = wer(frozen, eval_set)
    clean_after_frozen = wer(frozen, clean_eval)

    support.rule("full fine-tuning (every parameter trains)")
    full = asr.Recognizer.load(cache_path(base_epochs))
    asr.unfreeze_all(full.model)
    history_full, full.model = training.train_ctc(
        full.model, adapt, full.vocab, eval_set, epochs=adapt_epochs, lr=1e-3, batch_size=8, seed=1, log=False
    )
    full.mean, full.std = history_full["mean"], history_full["std"]
    after_full = wer(full, eval_set)
    clean_after_full = wer(full, clean_eval)

    support.rule("results on identical held-out noisy clips")
    support.table(
        [
            {"variant": "no adaptation", "trainable": 0, "noisy WER": before, "clean WER": clean_before, "seconds": 0.0},
            {"variant": "frozen front end", "trainable": _trainable(frozen.model), "noisy WER": after_frozen, "clean WER": clean_after_frozen, "seconds": frozen_seconds},
            {"variant": "full fine-tune", "trainable": _trainable(full.model), "noisy WER": after_full, "clean WER": clean_after_full, "seconds": float(sum(history_full["seconds"]))},
        ],
        ["variant", "trainable", "noisy WER", "clean WER", "seconds"],
    )
    print(f"noise gain, frozen : {before - after_frozen:+.3f} WER")
    print(f"noise gain, full   : {before - after_full:+.3f} WER")
    print(f"clean change, frozen: {clean_before - clean_after_frozen:+.3f} WER")
    print(f"clean change, full  : {clean_before - clean_after_full:+.3f} WER")
    for row in frozen.transcribe(eval_set)[:6]:
        print(f"  ref {row['reference']:<6} hyp {row['text']!r:<10} conf {row['confidence']:.2f}")

    payload = {
        "lab": "E",
        "title": "adapting a pretrained recogniser to a noisy channel",
        "corpus_origin": origin,
        "base": base.as_dict(),
        "new_speakers": new_speakers,
        "adaptation": {
            "clips": len(adapt),
            "evaluation_clips": len(eval_set),
            "epochs": adapt_epochs,
            "lr": 1e-3,
            "snr_db": args.snr,
            "frozen_parameters": frozen_params,
            "total_parameters": total_params,
        },
        "results": {
            "before": {"noisy": before, "clean": clean_before},
            "frozen": {"noisy": after_frozen, "clean": clean_after_frozen, "seconds": round(frozen_seconds, 2)},
            "full": {"noisy": after_full, "clean": clean_after_full, "seconds": round(float(sum(history_full["seconds"])), 2)},
        },
        "predictions_before": base.transcribe(eval_set),
        "predictions_after_frozen": frozen.transcribe(eval_set),
        "checks": {},
    }

    checks = {
        "adaptation and evaluation clips are disjoint": not (
            {(r.source_id, r.meta.get("utterance")) for r in adapt}
            & {(r.source_id, r.meta.get("utterance")) for r in eval_set}
        ),
        "adaptation used unseen speakers": not ({r.source_id for r in adapt} & {r.source_id for r in splits["train"]}),
        "frozen parameters are a strict subset": 0 < frozen_params < total_params,
        "WER in [0, 2] everywhere": all(0.0 <= v <= 2.0 for v in (before, after_frozen, after_full, clean_before, clean_after_frozen, clean_after_full)),
    }
    if not args.selftest:
        checks["adaptation improves the noisy WER"] = after_frozen < before
        # Adaptation is a trade, not a free win: the noise-tuned model can lose some
        # clean accuracy. The check allows a visible regression but not a collapse.
        checks["clean accuracy is not destroyed"] = clean_after_frozen <= max(0.2, clean_before + 0.2)
    failures = 0
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
        failures += 0 if passed else 1
    payload["checks"] = checks

    path = support.write_report("lab_e_adaptation.json", payload)
    print(f"\nreport written to {path.relative_to(support.HERE)}")
    print("Adaptation data must be permitted, documented, and deletable. Synthetic voices")
    print("avoid that question; a real deployment cannot.")
    return 0 if failures == 0 else 1


def _trainable(model) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    raise SystemExit(main())
