# F09 lab submission - Riverside early-warning comparison

**Lab brief:** [F09 lab](../../docs/lessons/f09-tree-ensembles/lab.md)  
**Starter file:** copy this file to `f09-classifier-comparison/README.md` or use it
as your submission checklist.

This is a template. The lab is not complete until you fill it with your own run
evidence. Do not submit the template unchanged.

## Scenario summary

Riverside Community College can make about 120 early-support calls per 500
learners. A missed failing learner costs about 4 staff hours; an unnecessary call
costs 0.25 hours. Your task is to compare at least four classifiers under one
cross-validation protocol, choose a model and threshold inside the 24% capacity
limit, score the test set once, and justify the metric and decision in a memo.

## Constraints

| Constraint | Your value |
| --- | --- |
| Data file and SHA-256 | |
| Label | `at_risk = 1 - passed` (1 = did not pass) |
| Available features | `study_hours`, `attendance`, `prior_score`, `sleep_hours`, `tutoring`, `course` |
| Forbidden features | `final_score`, `passed`, `at_risk` |
| Train / validation / test rows | 300 / 100 / 100 |
| Cost of a missed failing learner | 4.0 staff hours |
| Cost of an unnecessary call | 0.25 staff hours |
| Capacity | At most 120 flags per 500 learners (24%) |
| Chosen model | |
| Chosen threshold | |

## Required artifacts

```text
f09-classifier-comparison/
  README.md
  f09_classifier_comparison.ipynb
  outputs/model_comparison.csv
  outputs/metrics.json
  decision_memo.md
  reflection.md
```

- [ ] Notebook executed top to bottom.
- [ ] `model_comparison.csv` has CV mean and standard deviation for every model and
      metric.
- [ ] `metrics.json` contains validation and test metrics, threshold, expected
      hours, hash, and the test-scored-once flag.
- [ ] `decision_memo.md` has all ten headings and a recommendation.
- [ ] Reflection is 200-300 words and answers all three prompts.

## Decision memo headings

```markdown
# Riverside early-warning decision memo

## 1. Recommendation
## 2. Decision context
## 3. Data and prediction time
## 4. Candidate models and protocol
## 5. Metric justification
## 6. Threshold and cost analysis
## 7. Test result
## 8. Error analysis
## 9. Risks and limitations
## 10. What would change my recommendation
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
| CV object and folds | |
| Models compared | |
| Metric used for ranking | |
| Chosen threshold | |
| Flag rate at the threshold | |
| Validation expected hours per 1,000 | |
| Test expected hours per 1,000 | |
| Test precision / recall / PR-AUC | |
| Test-scored-once flag | |

## Justification checklist

- [ ] I stated the metric before looking at the test set.
- [ ] I explained why the 16:1 cost ratio favors recall, but why recall alone
      ignores capacity.
- [ ] I reported uncertainty across folds, not just a mean.
- [ ] I described at least five false negatives and five false positives.
- [ ] I did not use `final_score` anywhere in the model or the error analysis.
- [ ] I framed the model as support, not punishment or admission.
- [ ] I removed personal paths, secrets, and generated data files.
