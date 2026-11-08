# Assessment - Transformers and small language models (M06-M08) {#assessment}

**Section path:** [Overview](index.md) · **Assessment**

Three labs worth 90% and a reproduction defense worth 10%. Every number must be
traceable to a run.

## Weights

| Item | Weight | Deliverable |
| --- | --- | --- |
| [Lab 1](labs/lab-1-tiny-lm.md) - tiny language model | 30% | loss curve, mask test, samples, parameter table |
| [Lab 2](labs/lab-2-sft-and-lora.md) - SFT and LoRA | 35% | label-shift test, four-metric table, adapter, merge check |
| [Lab 3](labs/lab-3-efficiency-report.md) - efficiency | 25% | size/accuracy/agreement table, QLoRA budget |
| Defense | 10% | explain one metric and one failure |

## Grading bands

| Band | Mark | Descriptor |
| --- | --- | --- |
| Excellent | 85-100 | Every number reproducible; mask and shift tests pass; interpretation explains mechanisms; limitations stated |
| Good | 70-84 | Correct runs and clear tables; limitations thin |
| Pass | 50-69 | Runs, but metrics lack baselines or the mask/shift test is missing |
| Fail | < 50 | Unshifted labels presented as SFT; perplexities compared across tokenizers; efficiency table without agreement |

## What every submission must contain

1. A reproduction command with seed and hardware.
2. A mask test that fails when the causal mask is removed.
3. A label-shift test that fails when labels are not shifted.
4. A baseline row for every fine-tuning claim (base model or full SFT).
5. Per-item agreement for quantized models, not only aggregate accuracy.
6. The tokenizer, chat template, and checkpoint digest for the served artifact.

## Lab 1 - what the marker checks

* The causal mask test inspects weights or logits, not just loss.
* Perplexity is reported with the tokenizer unit.
* Samples at three temperatures are shown, not one cherry-picked string.
* The parameter count is derived and matches the implementation.

## Lab 2 - what the marker checks

* The shift/mask implementation is tested, and the unshifted failure is
  demonstrated.
* Metrics include exact match, first-12, word F1, and answer loss.
* The base model is the baseline.
* The LoRA adapter reports trainable parameters and merge difference.

## Lab 3 - what the marker checks

* Compression is computed from measured bytes, not nominal bit width.
* Accuracy and agreement are both reported.
* The QLoRA memory table states its assumptions and excludes activations.
* No GPU speedup is claimed without a GPU measurement.

## Defense

Bring one metric you trust and one failure you diagnosed. The failure is marked on
the diagnosis, not on being absent.

## Academic integrity

Do not present a run you did not perform. Do not copy benchmark numbers into a
teaching table. If you use an external model or dataset, cite the revision.
