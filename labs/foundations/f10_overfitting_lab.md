# F10 lab submission - Harborline complexity investigation

**Lab brief:** [F10 lab](../../docs/lessons/f10-metrics-validation/lab.md)  
**Starter file:** copy this file to `f10-overfitting/README.md` or use it as your
submission checklist.

This is a template. The lab is not complete until you fill it with your own run
evidence. Do not submit the template unchanged.

## Scenario summary

Harborline Realty plans a direct-mail campaign for premium homes, defined as a
sale price of at least 350,000 USD. A correct premium contact is worth about 900
USD; an unnecessary contact wastes about 150 USD. Your task is a controlled
complexity sweep over decision trees and random forests, followed by a memo that
recommends one model and one threshold. The memo must be readable by a marketing
lead who will not open the notebook.

## Constraints

| Constraint | Your value |
| --- | --- |
| Data file and SHA-256 | |
| Target | `premium = sale_price >= 350000` |
| Features | Five numeric fields, `area_per_bedroom`, one-hot `neighbourhood` |
| Forbidden feature | `sale_price` |
| Train / validation / test rows | 360 / 120 / 120 |
| Depth sweep | 1-20 |
| Forest leaf sweep | `min_samples_leaf` 1, 2, 5, 10, 25, 50; 300 trees |
| Cost of a missed premium home | 900 USD |
| Cost of an unnecessary contact | 150 USD |
| Chosen model | |
| Chosen threshold | |

## Required artifacts

```text
f10-overfitting/
  README.md
  f10_overfitting.ipynb
  outputs/complexity_sweep.csv
  outputs/complexity_curve.png
  outputs/metrics.json
  recommendation_memo.md
  reflection.md
```

- [ ] Notebook executed top to bottom.
- [ ] `complexity_sweep.csv` has one row per depth and per leaf size, with train
      and validation scores.
- [ ] `metrics.json` contains the chosen model, threshold, validation and test
      costs, hash, and the test-scored-once flag.
- [ ] `recommendation_memo.md` has all nine headings and rejects one alternative.
- [ ] Reflection is 200-300 words and answers all three prompts.

## Memo headings

```markdown
# Harborline premium-listing recommendation

## 1. Recommendation
## 2. Decision and costs
## 3. Data and features
## 4. Protocol
## 5. Results
## 6. Threshold and expected cost
## 7. Test result
## 8. Limitations and fairness
## 9. What would change my recommendation
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
| Data SHA-256 | |
| Random seed | |
| Split sizes and prevalence | |
| Best validation tree depth | |
| Best forest `min_samples_leaf` | |
| Training and validation gap at depth 20 | |
| Chosen model | |
| Chosen threshold | |
| Validation expected cost per 1,000 | |
| Test expected cost per 1,000 | |
| Test precision / recall / PR-AUC | |
| Test-scored-once flag | |

## Honesty check

- [ ] I selected the model on validation, not on test.
- [ ] I did not keep `sale_price` in the feature matrix.
- [ ] I reported the test cost even if it was worse than validation.
- [ ] I discussed the 350,000 cutoff as a business rule, not a natural boundary.
- [ ] I discussed the fairness risk of using `neighbourhood` for marketing.
- [ ] I removed personal paths, secrets, and generated data files.
