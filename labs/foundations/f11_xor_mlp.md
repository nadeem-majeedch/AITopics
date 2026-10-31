# F11 lab submission - noisy XOR capacity

Use this file as the front page of your submission. Replace each bracketed
section with your own content. The full task is in the
[F11 lab brief](../../docs/lessons/f11-neural-networks/lab.md).

## Scenario summary

Two noisy binary sensors must detect odd parity (XOR). I generated a labeled
dataset, trained candidate multilayer networks, and chose the smallest hidden
width that meets a stated reliability bar across five seeds.

## My decision

- Reliability bar: mean test accuracy >= [0.90] and standard deviation <= [0.02]
  across five seeds.
- Chosen architecture: [(16,)].
- Mean test accuracy: [0.000] +/- [0.000].
- One sentence of justification: [why this width and not the next smaller or
  larger one].

## Constraints I worked within

- CPU only; no GPU used.
- Synthetic data generated from a recorded seed; no real sensor or personal data.
- All model settings except width and seed held fixed.
- Test set touched once per configuration, after the decision rules were written.

## Required artifacts

| Artifact | Present | Notes |
| --- | --- | --- |
| `xor_lab.ipynb` or `xor_lab.py` | [ ] | Runs end to end |
| `xor_noisy.csv` | [ ] | 400 rows, generator seed recorded |
| `results.csv` | [ ] | width, seed, train/val/test accuracy, params, seconds |
| `capacity.png` | [ ] | Accuracy per width with spread |
| `report.md` | [ ] | Follows the report headings below |
| `reflection.md` | [ ] | 200-300 words |

## Commands, seeds, and hardware

```text
Python:            [3.12.x]
scikit-learn:      [version]
NumPy:             [version]
OS:                [Windows 11 / other]
CPU:               [model]
GPU:               [none / model, or "not used"]
Data seed:         [2026]
Training seeds:    [0, 1, 2, 3, 4]
Reproduce with:    [exact command, e.g. python xor_lab.py]
Runtime:           [measured minutes]
```

## Report headings

```markdown
# F11 noisy XOR capacity report
## 1. Question and decision
## 2. Data and split
## 3. Method
## 4. Results
## 5. Diagnosis
## 6. Decision and limits
## 7. Reproduction
## 8. Ethics and privacy
```

## Validation checks

- [ ] Corner counts per split are 60 train / 20 validation / 20 test, shown.
- [ ] Training features after scaling have mean near 0 and standard deviation
      near 1.
- [ ] Repeating seed 0 for `(16,)` gives the same accuracy to four decimals.
- [ ] Parameter counts match the printed weight shapes.

## Rubric reminder

| Dimension | Weight |
| --- | --- |
| Technical correctness | 30 |
| Evaluation and diagnosis | 25 |
| Reproducibility | 15 |
| Data and ethics | 15 |
| Communication | 15 |
| **Total** | **100** |

## Self-check

- [ ] The logistic baseline is near chance and I explained why.
- [ ] I named which widths underfit or overfit, with numbers.
- [ ] My decision follows the bar I stated before looking at results.
- [ ] I acknowledged the noise ceiling below 1.00.
- [ ] No usernames, absolute paths, or hostnames remain.
- [ ] I did not claim a GPU run or a production-ready model.

Next: score the work with the
[F11 assessment](../../docs/lessons/f11-neural-networks/assessment.md).
