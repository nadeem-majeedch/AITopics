# Evaluation report

**Project:** [replace]  
**Version evaluated:** [replace: checksum or tag]  
**Checkpoint:** 3

## Frozen test declaration

| Item | Value |
| --- | --- |
| Test set | [replace: path, digest, and n] |
| Frozen on | [replace: date, before the final run] |
| Scoring rule | [replace: metric definitions and threshold] |
| Opened | [replace: once, date] |
| Changes after opening | [replace: none, or list and explain] |

No number below was used to choose a hyperparameter, threshold, or model. If a
result is from validation, label it as validation.

## Headline results

| Metric | Candidate | Baseline | Difference | n | 95% interval |
| --- | ---: | ---: | ---: | ---: | --- |
| [replace: primary] | | | | | |
| [replace: secondary] | | | | | |

State how the interval was computed (bootstrap resamples, Wilson, paired
difference) and what it covers.

## Per-class or per-slice results

| Class / slice | n | Precision | Recall | F1 | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| [replace] | | | | | |

If a class has too few examples for a meaningful interval, say so instead of
reporting a precise-looking number.

## Confidence, calibration, and abstention

| Measure | Raw | Calibrated | Fitted on |
| --- | ---: | ---: | --- |
| ECE | [replace] | [replace] | validation only |
| Accuracy at threshold | [replace] | [replace] | validation only |
| Coverage | [replace] | [replace] | test |

Explain what abstention means to the user and what happens to an abstained case.

## Robustness

| Condition | Ordinary | Test-time augmentation | Change |
| --- | ---: | ---: | ---: |
| clean | | | |
| [replace] | | | |
| [replace] | | | |
| [replace] | | | |

State whether augmentation was used in training, and whether the comparison is
fair (same images, same model, no retuning on test).

## Qualitative evaluation and failure cases

Quote outputs exactly; do not clean them up.

1. **Success:** [replace: input, output, why it is correct]
2. **Fluent but wrong:** [replace: input, output, the specific error]
3. **Unusable:** [replace: input, output, what makes it unusable]

Failure taxonomy, with counts:

| Failure type | Count | Share of errors | Likely cause | Evidence |
| --- | ---: | ---: | --- | --- |
| [replace] | | | | |

## Interpretation

- What the result supports: [replace]
- What it does not support: [replace: e.g. real-world accuracy, model intelligence]
- The condition that causes the worst failure: [replace]
- What would change the conclusion: [replace: more data, a different tokenizer, a larger model]

## Reproduce this table

```bash
[replace: one command that writes outputs/metrics.json]
```

The command reads [replace: data digest] and [replace: config], and writes
[replace: output paths]. Expected runtime: [replace].
