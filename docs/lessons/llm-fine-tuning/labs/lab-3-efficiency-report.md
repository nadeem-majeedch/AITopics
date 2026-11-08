# Lab 3 - Efficiency and quantization report {#lab-3}

**Section:** [Language models](../index.md) · **Module:** M08 · **Time:** 5 hours

## Goal

Measure the memory and quality cost of three serving strategies and produce a
budget a reviewer can check.

## Steps

1. Measure the fp32 checkpoint size in bytes. Compute bytes per parameter.
2. Quantize to int8 and int4. Report the actual file size, compression ratio, exact
   match, and per-item agreement with fp32.
3. Find three items where int4 and fp32 disagree. Inspect the outputs and classify
   the difference (same meaning, different wording, wrong answer).
4. Train LoRA at `r=4`, `8`, and `16`. Report trainable parameters and exact match
   at a fixed step budget.
5. Build a QLoRA memory table for a 1B-parameter model: fp32 full fine-tune, LoRA on
   fp32 base, 4-bit base plus LoRA. State bytes-per-parameter assumptions and
   exclude activations explicitly.
6. Recommend one configuration for a device with a stated memory limit. Justify the
   choice with the table, not with a slogan.

## Deliverables

| File | Contents |
| --- | --- |
| `report.md` | Tables, disagreement examples, recommendation, assumptions |
| `sizes.csv` | format, bytes, compression, accuracy, agreement |
| `lora_sweep.csv` | rank, trainable params, exact match, seconds |
| `budget.md` | Memory arithmetic with units and exclusions |

## Required table

| Format | Bytes | Compression | Exact match | Agreement |
| --- | --- | --- | --- | --- |
| fp32 | | 1.00x | | 1.000 |
| int8 | | | | |
| int4 | | | | |

## Marking

* **30%** sizes are measured, not inferred from nominal bits.
* **25%** accuracy and agreement are both reported and interpreted.
* **25%** QLoRA budget states assumptions and excludes activations.
* **20%** recommendation follows from the table and names the device limit.

## Stretch

Measure latency for fp32 and int8 on CPU with batch size 1. Does quantization help
latency, or only memory? Report medians after warmup.

## Rules

No GPU is required. If you use one, report the device and whether the quantized
path actually ran on it. Do not claim a speedup you did not measure.
