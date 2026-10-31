# F05 leakage audit - submission template

Use this file as the starting point for the lab required by the
[F05 lab brief](../../docs/lessons/f05-splits/lab.md). Replace every bracketed
prompt with your own evidence. Delete prompts you did not answer.

Save your completed copy outside the course repository, for example:

```text
portfolio/f05-leakage-audit/audit_report.md
```

## Scenario summary

[Three sentences: the early-warning task, the colleague's reported result, and
what your audit found.]

## Constraints I worked under

| Constraint | Value I used |
| --- | --- |
| Target | `passed` |
| Allowed predictors | `study_hours`, `attendance`, `prior_score`, `sleep_hours`, `tutoring`, `course` |
| Forbidden predictors | `final_score`, `passed`, and anything derived from them |
| Split | 60/20/20, stratified, seed 2026 |
| Preprocessing | Fitted on training rows only |
| Group check | Hold out one entire `course` |
| Data | `datasets/foundations/generated/student_performance.csv` |

## Commands and seeds

```powershell
# [the exact commands you ran, including data generation]
```

| Item | Value |
| --- | --- |
| Data file and SHA-256 | [value] |
| Rows and columns | [value] |
| Python / pandas / scikit-learn | [versions] |
| Split seed | [value] |
| Model random state | [value] |
| Test-set evaluations | [must be 1] |

## Required artifacts

| Artifact | Path | Present |
| --- | --- | --- |
| Executed notebook or script log | [path] | [yes/no] |
| Leakage table | `leakage_table.csv` | [yes/no] |
| Split manifest | `split_manifest.json` | [yes/no] |
| Metrics | `metrics.json` | [yes/no] |
| Report | `audit_report.md` | [yes/no] |
| Reflection | `reflection.md` | [yes/no] |

## Leak inventory

| Leak | Evidence | Metric before | Metric after | Fix |
| --- | --- | --- | --- | --- |
| [name] | [what proves it] | [value] | [value] | [change] |
| [name] | [what proves it] | [value] | [value] | [change] |
| [name] | [what proves it] | [value] | [value] | [change] |

## Report headings

```markdown
# F05 leakage audit

## 1. Summary and recommendation
## 2. Data and provenance
## 3. Data availability
## 4. Inherited evaluation
## 5. Leak inventory
## 6. Rebuilt evaluation
## 7. Held-out course result
## 8. Limitations
## 9. Reproduction
```

## Results to fill in

| Metric | Baseline | Validation choice | Test | Held-out course |
| --- | --- | --- | --- | --- |
| Accuracy | | | | |
| Precision | | | | |
| Recall | | | | |
| Confusion matrix | | | | |
| Rows evaluated | | | | |

## Validation checks

- [ ] 500 rows and unique `student_id`.
- [ ] Feature list and `{"final_score", "passed"}` are disjoint, enforced in
      code.
- [ ] Split sizes sum to 500 and no `student_id` crosses splits.
- [ ] Scaler mean matches the training mean within tolerance.
- [ ] Test set evaluated once.

## Rubric reminder

| Dimension | Weight |
| --- | --- |
| Technical correctness | 30 |
| Evaluation and diagnosis | 25 |
| Reproducibility | 15 |
| Data and ethics | 15 |
| Communication | 15 |

A dimension with no evidence scores zero. The full descriptors are in the
[lab brief](../../docs/lessons/f05-splits/lab.md#rubric).

## Privacy check

- [ ] No names, emails, or real student identifiers.
- [ ] No ranked list of individual students.
- [ ] No absolute personal paths or usernames in logs.
- [ ] The report states that the model is advisory and not for decisions about
      people.
