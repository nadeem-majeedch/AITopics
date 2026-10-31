# F08 lab submission - Cedarline valuation screen

**Lab brief:** [F08 lab](../../docs/lessons/f08-regression-classification/lab.md)  
**Starter file:** copy this file to `f08-house-prices/README.md` or use it as your
submission checklist.

This is a template. The lab is not complete until you fill it with your own run
evidence. Do not submit the template unchanged.

## Scenario summary

Cedarline Property Partners reviews about 2,500 listings per week with one
analyst. Your task is a local price model that predicts `sale_price` and
shortlists listings at or above a fixed cutoff near 325,000 USD. The model must
score 2,500 listings in under 2.0 seconds on one CPU core and serialize to an
artifact under 2 MB. A missed shortlist-worthy home costs 8,000 USD in expected
margin; an unnecessary review costs 400 USD.

## Constraints

| Constraint | Your value |
| --- | --- |
| Data file and SHA-256 | |
| Generator seed | 42 |
| Train / validation / test rows | 360 / 120 / 120 |
| Features used | |
| Decision cutoff (USD) | |
| Latency budget | 2,500 rows in under 2.0 s, median of 5 timed batches |
| Artifact budget | Under 2 MB |
| Error costs | 8,000 USD per false negative; 400 USD per false positive |

## Required artifacts

```text
f08-house-prices/
  README.md
  f08_house_prices.ipynb
  outputs/metrics.json
  outputs/model.joblib
  model_card.md
  report.md
  reflection.md
```

- [ ] Notebook executed top to bottom.
- [ ] `metrics.json` contains validation and test metrics, cutoff, latency, hash,
      and a test-scored-once flag.
- [ ] `model.joblib` reloads and reproduces identical predictions.
- [ ] Model card has all eight required headings.
- [ ] Report follows the headings below.

## Report headings

```markdown
# F08 valuation screen report

## 1. Summary
## 2. Decision and constraints
## 3. Data and features
## 4. Baselines and candidates
## 5. Decision analysis
## 6. Operational check
## 7. Test result
## 8. Limitations and fairness
## 9. Reproduction
```

## Rubric reminder

| Dimension | Points |
| --- | --- |
| Technical correctness | 30 |
| Evaluation and diagnosis | 25 |
| Reproducibility | 15 |
| Data and ethics | 15 |
| Communication | 15 |
| **Total** | **100** |

A dimension with no evidence scores zero. The lab counts for 40% of the module
score.

## Commands and seeds

Record the exact values from your run, not from memory.

| Item | Value |
| --- | --- |
| Operating system | |
| Python version | |
| pandas / scikit-learn versions | |
| CPU model | |
| Data SHA-256 | |
| Random seed | |
| Split command or code cell | |
| Chosen model and `alpha` | |
| Median latency for 2,500 rows (s) | |
| Milliseconds per listing | |
| Artifact size (MB) | |
| Validation MAE / RMSE / R-squared | |
| Test MAE / RMSE / R-squared | |
| Test precision / recall | |
| Test expected cost per 1,000 listings | |

## Honesty check

- [ ] I did not tune on the test set.
- [ ] I did not claim a real deployment or a real customer result.
- [ ] I named the fairness risk of using `neighbourhood`.
- [ ] I removed personal paths, secrets, and generated data files from the
      submission.
