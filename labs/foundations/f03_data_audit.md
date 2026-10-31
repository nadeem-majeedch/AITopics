# F03 lab - data audit submission template

Use this file as the starting point for the audit required by the
[F03 lab brief](../../docs/lessons/f03-numpy-pandas/lab.md). Replace every
bracketed prompt with your own evidence and delete prompts you did not answer.

Save your completed copy outside the course repository, for example:

```text
portfolio/f03-data-audit/audit_report.md
```

## 1. Scenario summary

[Two or three sentences: the institution (fictional), the table, the proposed use,
and the verdict you reached.]

## 2. Constraints

- Generated synthetic table only; no real enrollment export.
- No individual risk score, ranking, or per-student output.
- Groups under 30 rows are flagged, never compared as if they were large.
- Clipped values, the missing key, and outcome columns are findings to report.
- The SHA-256 in this report matches the CSV you audited.

## 3. Required artifacts

| Artifact | Path | Present? |
| --- | --- | --- |
| Audit script or notebook | `audit.py` | [yes/no] |
| Program catalog | `data/program_catalog.csv` | [yes/no] |
| Column audit | `outputs/audit.csv` | [yes/no] |
| Group summary | `outputs/group_summary.csv` | [yes/no] |
| Audit report | `audit_report.md` | [yes/no] |
| Reflection | `reflection.md` | [yes/no] |

## 4. Environment, seed, and hash

| Field | Value |
| --- | --- |
| Operating system | [value] |
| Python version | [output of `python --version`] |
| NumPy / pandas versions | [two values] |
| Generator seed | [42, or the value you used] |
| Generator command | `python scripts/make_foundation_data.py` |
| CSV SHA-256 | [64 hex characters] |
| Table shape | [(500, 8)] |

## 5. Column audit

| Column | dtype | Non-null | Missing | Unique | Min | Max | Mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [name] | [dtype] | [n] | [n] | [n] | [value] | [value] | [value] |

Clipped or boundary values:

| Column | Count at min | Count at max | Interpretation |
| --- | --- | --- | --- |
| [name] | [n] | [n] | [what a pile-up implies] |

## 6. Keys and duplicates

- Exact duplicate rows: [count]
- Columns where `is_unique` is `True`: [list, or "none"]
- What the missing row key blocks: [one or two sentences]

## 7. Target and leakage

- Pass rate: [value] over [n] rows
- Majority-class baseline: [value]
- Excluded from features for a `passed` model: [columns and why]
- Correlation of `final_score` with `passed`: [value]

## 8. Groups and baseline

| Group | Rows | Pass rate | Mean `final_score` | Beats majority baseline? |
| --- | --- | --- | --- | --- |
| [course or tutoring value] | [n] | [value] | [value] | [yes/no] |

Groups with fewer than 30 rows: [list, or "none"].

## 9. Merge check

- Catalog rows: [3]
- Merge arguments: [`how="left"`, `validate="many_to_one"`, `on="course"`]
- Rows before / after: [value] / [value]
- Assertion used: [paste the line]

## 10. Verdict and conditions

**Verdict:** [fit for a group-level pilot / fit with conditions / not fit]

[One paragraph naming the findings that decide it, followed by the conditions as a
numbered list.]

## 11. Reproduction and privacy check

- [ ] `README.md` contains the generator command, seed, and audit command.
- [ ] Deleting `outputs/` and rerunning reproduces `audit.csv` and
      `group_summary.csv`.
- [ ] The hash in this report matches the CSV on disk.
- [ ] No real student data, names, emails, or identifiers appear anywhere.
- [ ] No individual risk score is produced or implied.

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
[lab brief](../../docs/lessons/f03-numpy-pandas/lab.md#rubric).
