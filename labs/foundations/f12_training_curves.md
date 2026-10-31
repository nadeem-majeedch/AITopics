# F12 lab submission - training-curve diagnosis

Use this file as the front page of your submission. Replace each bracketed
section with your own content. The full task is in the
[F12 lab brief](../../docs/lessons/f12-backpropagation/lab.md).

## Scenario summary

A tutoring program has a 150-student pilot table and wants a small neural network
to flag students who may need support. I trained a model on the pilot rows,
diagnosed its training curves, applied two controlled changes, and froze one
configuration with an early-stopping rule.

## My decision

- Recommended configuration: [architecture, learning rate, weight decay].
- Stopping rule: [lowest validation loss at epoch N / fixed 300 epochs].
- Validation accuracy at the chosen epoch: [0.000].
- Test accuracy (evaluated once): [0.000].
- One-sentence justification: [what the curves showed and why this rule].

## Constraints I worked within

- CPU only; device used: [cpu].
- Only the synthetic repository dataset; no real student records.
- `final_score` excluded from all final features.
- Test set evaluated once, after freezing the configuration.
- Three seeds for the final recipe: [yes / no, with reason].

## Required artifacts

| Artifact | Present | Notes |
| --- | --- | --- |
| `train_curves.ipynb` or `.py` | [ ] | Runs end to end |
| `runs.jsonl` | [ ] | One record per run |
| `curves_baseline.png` | [ ] | Train and validation loss and accuracy |
| `curves_changed.png` | [ ] | After both controlled changes |
| `results.csv` | [ ] | Per-run metrics |
| `report.md` | [ ] | Follows the headings below |
| `reflection.md` | [ ] | 200-300 words |

## Commands, seeds, and hardware

```text
Python:            [3.12.x]
torch:             [2.4.x]
NumPy:             [version]
OS:                [Windows 11 / other]
CPU:               [model]
GPU:               [none / model, or "not used"]
Data file:         datasets/foundations/generated/student_performance.csv
Split seed:        [42]
Pilot subset:      [150 rows, indices saved at ...]
Training seeds:    [list]
Reproduce with:    [exact command]
Runtime:           [measured minutes]
```

## Report headings

```markdown
# F12 training-curve diagnosis
## 1. Question and decision
## 2. Data and split
## 3. Method
## 4. Baseline
## 5. Curves and diagnosis
## 6. Controlled changes
## 7. Final evaluation
## 8. Reproduction
## 9. Ethics and limits
```

## Validation checks

- [ ] Feature matrix has no `final_score` and every column is named.
- [ ] Standardized pilot features have mean near 0 and standard deviation near 1.
- [ ] Repeating the first 20 epochs with the same seed gives identical losses to
      four decimals.
- [ ] `runs.jsonl` has one record per run and parses as JSON Lines.

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

- [ ] My diagnosis names a best epoch and a train-validation gap.
- [ ] Each controlled change altered exactly one factor.
- [ ] I did not tune the stopping epoch on the test set.
- [ ] I report mean and spread across seeds, or explain the single run.
- [ ] I state that the model must not be used for real student decisions.
- [ ] No names, IDs, absolute paths, or hostnames remain.
- [ ] I did not claim a GPU run that I did not perform.

Next: score the work with the
[F12 assessment](../../docs/lessons/f12-backpropagation/assessment.md).
