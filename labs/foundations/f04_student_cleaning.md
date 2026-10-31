# F04 lab - cleaning report submission template

Use this file as the starting point for the report required by the
[F04 lab brief](../../docs/lessons/f04-data-cleaning/lab.md). Replace every
bracketed prompt with your own evidence and delete prompts you did not answer.

Save your completed copy outside the course repository, for example:

```text
portfolio/f04-student-cleaning/report.md
```

## 1. Scenario summary

[Two or three sentences: the school (fictional), the term, the export, the
tutoring capacity, and what you were asked to decide.]

## 2. Constraints

- At least 95% of unique rows survive; no row is dropped except an exact
  duplicate.
- `course` and `tutoring` end in exactly the allowed value sets, with every
  remapped row counted.
- Missing indicators exist for all three imputed numeric columns.
- `final_score` is never a feature when predicting `passed`.
- Every submitted output is an aggregate; no per-student list or identifier.

## 3. Required artifacts

| Artifact | Path | Present? |
| --- | --- | --- |
| Cleaning script or notebook | `clean.py` | [yes/no] |
| Specification | `cleaning_spec.md` | [yes/no] |
| Before profile | `outputs/profile_before.csv` | [yes/no] |
| Ablation table | `outputs/ablation.csv` | [yes/no] |
| Cleaned table | `outputs/students_clean.csv` | [yes/no] |
| Group flags | `outputs/group_flags.csv` | [yes/no] |
| Report | `report.md` | [yes/no] |
| Reflection | `reflection.md` | [yes/no] |

## 4. Data and provenance

| Field | Value |
| --- | --- |
| File | `datasets/foundations/generated/student_performance_messy.csv` |
| Generator command | [exact command] |
| Seed | [value] |
| SHA-256 | [64 hex characters] |
| Raw rows | [value] |
| Duplicate rows | [value] |
| Unique rows | [value] |

Missing counts before cleaning:

| Column | Missing | Share of rows |
| --- | --- | --- |
| attendance | [n] | [share] |
| prior_score | [n] | [share] |
| sleep_hours | [n] | [share] |

Raw label spellings: [paste the sorted `unique()` values for `course` and
`tutoring`].

## 5. Cleaning specification

| # | Decision | Reason | Expected effect | Observed effect |
| --- | --- | --- | --- | --- |
| 1 | [decision] | [reason] | [rows, columns, or value set] | [measured] |

Rows kept: [n] of [n] unique rows ([percentage]). Does this meet the 95% floor?
[yes/no].

## 6. Ablation

| Variant | Rows | Mean accuracy | Std accuracy | Meets 95% floor |
| --- | --- | --- | --- | --- |
| Full specification | [n] | [value] | [value] | [yes/no] |
| No missing indicators | [n] | [value] | [value] | [yes/no] |
| Mean instead of median | [n] | [value] | [value] | [yes/no] |
| Complete-case | [n] | [value] | [value] | [yes/no] |

Fold check: [paste the assertion or the line that proves all variants scored on
the same test indices].

Interpretation: [which differences are larger than the fold standard deviation,
and which are noise].

## 7. Flagging rule

- Target: [predicting `passed`]
- Flagged group: [students with the lowest predicted probability of passing]
- Cutoff: [value]
- Students flagged: [n] of [n] (capacity 120)
- Who is missed: [one or two sentences]

## 8. Group check

| Group | Rows | Flagged | Flagged share |
| --- | --- | --- | --- |
| [course] | [n] | [n] | [share] |

Groups differing from the overall share by more than 15 points: [list, with your
explanation of whether the cause is the data or the cutoff].

## 9. Limitations and ethics

[Synthetic provenance, imputation as estimation rather than measurement, missing
indicators, capacity trade-off, and the uses this pilot must never support.]

## 10. Reproduction and privacy check

```text
[Paste the two commands that rebuild every artifact from a clean state.]
```

- [ ] Deleting `outputs/` and rerunning reproduces all four CSVs.
- [ ] No per-student ranking, probability list, or identifier is included.
- [ ] Every group table has a size column.
- [ ] The report states that the table is synthetic and that no tutoring
      intervention was evaluated.

## Rubric reminder

| Dimension | Points |
| --- | --- |
| Technical correctness | 30 |
| Evaluation and diagnosis | 25 |
| Reproducibility | 15 |
| Data and ethics | 15 |
| Communication | 15 |
| **Total** | **100** |

Descriptors and the self-check list are in the
[lab brief](../../docs/lessons/f04-data-cleaning/lab.md#rubric).
