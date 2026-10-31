# F03 lab - Audit a table before anyone models it

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Weight** | 40% of the F03 assessment |
| **Time** | About 2 hours |
| **Hardware** | CPU-only |
| **Starter file** | `labs/foundations/f03_data_audit.md` in the repository |
| **Prerequisite** | A completed run of the [guided notebook](notebook.md) |

## The scenario

Harborview Adult Learning Center runs evening preparation courses in math,
physics, and computer science. Its coordinator has exported one term of records
(500 enrollments) and a vendor has offered to build a "student risk score" from
it. Before signing, the coordinator asks you for an independent audit: what is
actually in this table, what could break a model, and is it fit for the proposed
use?

You are not building the model. You are producing the evidence that decides
whether modeling should start, and on what conditions.

The table is `datasets/foundations/student_performance.csv`, produced by the
course's synthetic data generator. Treat it as if it were a real institutional
export: the same audit steps apply, and the same privacy rules would apply to real
records.

!!! warning "This table has two outcome columns"
    `final_score` and `passed` are both results of the term. A model that uses
    either one to predict the other will look excellent and mean nothing. Part of
    the audit is naming every column that must be excluded from features.

## Why this matters

Most modeling failures that reach production were visible in the table before any
model was trained: an identifier used as a feature, a group with 12 rows treated
like a group with 300, a target that is a deterministic function of another
column, or a table with no key that can keep one person's rows together.

An audit is cheap. It takes an afternoon and produces a document that survives
staff changes. Skipping it produces a model nobody can defend.

## What the data is

The generator writes four CSV files to `datasets/foundations/generated/`. They
are not committed to Git; you create them:

```powershell
cd C:\ai-course\AITopics
python scripts/make_foundation_data.py
```

The file you need is `datasets/foundations/generated/student_performance.csv`.
Read the [foundation dataset card](../../technical/foundation-assets.md#foundation-datasets) for
provenance, license (CC0-1.0), and known limitations, and keep the card's URL or
path in your report.

The table has 8 columns and no student identifier. That single fact changes what
you can promise: without an identifier you cannot tell whether two rows are the
same person, cannot build a grouped train/test split by student, and cannot
follow a student across terms. Say so in the audit instead of working around it.

## Required steps

1. **Generate and fingerprint the data.** Run the generator with its default seed.
   Record the command, the seed (`42`), and the SHA-256 of the CSV:

   ```powershell
   python -c "import hashlib, pathlib; p=pathlib.Path('datasets/foundations/generated/student_performance.csv'); print(hashlib.sha256(p.read_bytes()).hexdigest())"
   ```

   Put the hash in your report. It is the only way a reviewer can confirm they
   audited the same bytes you did.

2. **Load and describe.** Read the CSV with pandas, then record `shape`, `dtypes`,
   and `df.head(3)`. **Validation check 1:** assert the shape is `(500, 8)` and
   that the eight expected column names are present in order. Print the assertion
   result, not just "loaded".

3. **Build a column audit table.** One row per column with: dtype, non-null count,
   missing count, unique count, minimum, maximum, and mean (numeric columns only).
   Write it to `outputs/audit.csv`. Assert that the audit has exactly 8 rows and
   that the missing counts sum to `df.isna().sum().sum()`.

4. **Look for clipped values.** Count how many values sit exactly at each column's
   minimum and maximum. The generator clips several columns to plausible ranges,
   so values pile up at the bounds. Report the counts and explain what a pile-up
   implies: the true value may be outside the recorded range, and a model cannot
   learn what the file never contains.

5. **Check duplicates and keys.** Count exact duplicate rows. Then test each column
   with `is_unique`. **Validation check 2:** assert that there are zero exact
   duplicates and that no single column is unique. The second result is the
   finding, not a failure: this table has no row key. Write one sentence on what
   that blocks.

6. **Review the target and leakage.** Compute the pass rate (`passed.mean()`) with
   its count. Compute the correlation between `final_score` and `passed`, and
   between `final_score` and each numeric feature. Produce an explicit exclusion
   list for a model that predicts `passed`, and one for a model that predicts
   `final_score`. Name the columns that are outcomes rather than inputs.

7. **Check categories and group sizes.** Print the value counts for `tutoring` and
   `course`. Flag every group with fewer than 30 rows, and state whether any
   planned comparison would rest on a group that small. Convert `tutoring` to a
   boolean mask and confirm the two counts sum to 500.

8. **Merge a catalog and prove the row count.** Create
   `data/program_catalog.csv` with three rows and these columns:
   `course,department,credits` — `Math,Sciences,3`; `Physics,Sciences,4`;
   `CS,Computing,3`. Merge with `how="left"` and `validate="many_to_one"`.
   **Validation check 3:** assert the merged row count equals the original and
   that `credits` has no missing values. Report the merged shape.

9. **Compare group summaries with a baseline.** Report pass rate and mean
   `final_score` by `course` and by `tutoring`, each with a count. Compare each
   group's pass rate with the always-predict-the-majority baseline
   (`max(pass_rate, 1 - pass_rate)`). Any group that does not beat the baseline is
   a finding about the feature, not about a model.

10. **Write the verdict.** `audit_report.md` of 500-700 words using the headings
    below. End with one of three verdicts: **fit for a group-level pilot**,
    **fit with conditions** (list them), or **not fit** (say what the coordinator
    must supply first). Then delete `outputs/` and rerun your script once to prove
    it reproduces.

## Report headings

```markdown
# Harborview data audit

## 1. Verdict
One of the three verdicts, in one sentence, with the two findings that decide it.

## 2. What the table is
Rows, columns, what one row means, provenance, license, SHA-256, seed.

## 3. Column audit
The table from `outputs/audit.csv`, summarized; call out clipped columns.

## 4. Keys and duplicates
Duplicate count, uniqueness test per column, and what the missing key blocks.

## 5. Target and leakage
Pass rate with count, the exclusion lists, and the correlation you found.

## 6. Groups and baseline
Pass rate by course and tutoring with counts, compared with the majority baseline.

## 7. Conditions and risks
What must be true before modeling starts; what the table can never support.

## 8. Reproduction
Commands, seed, hash, and the two reruns you performed.
```

## Deliverables

```text
f03-data-audit/
  README.md                 # 5-10 lines: what to run, in what order
  audit.py                  # or audit.ipynb, top-to-bottom runnable
  data/
    program_catalog.csv     # three rows, created by you
  outputs/
    audit.csv               # one row per column
    group_summary.csv       # pass rate by course and by tutoring, with counts
  audit_report.md           # 500-700 words, headings above
  reflection.md             # 200-300 words, see the assessment page
```

Do not commit `outputs/`. Copy the two CSV files into your portfolio folder when
you assemble the submission.

## Constraints and safety

- The table is synthetic and CC0. Do not replace it with a real institutional
  export, and do not add real names, emails, or student numbers.
- Do not build or report an individual risk score. The audit may discuss whether
  a group-level pilot is defensible; it must not rank people.
- Report group results only when the group has at least 30 rows, and say when a
  group is too small to compare.
- Do not "fix" the table silently. Clipped values, missing keys, and outcome
  columns are findings to report, not problems to hide before the audit.
- A correlation in this table is a property of a synthetic generator. Do not write
  that studying causes a pass, or that any number here describes real students.
- Keep the SHA-256 in the report so a reviewer can confirm the data version.

## Rubric

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Technical correctness | 30 | Audit table is complete and accurate; shape, duplicate, and merge assertions pass; group summaries include counts | Missing columns in the audit, a merge that changes the row count, or summaries without counts |
| Evaluation and diagnosis | 25 | Verdict follows from named findings; leakage, clipping, and the missing key are explained with their consequences | Findings are listed but not interpreted, or the verdict contradicts the evidence |
| Reproducibility | 15 | Seed, hash, commands, and a clean rerun reproduce both CSVs exactly | Commands or hash missing; outputs cannot be regenerated |
| Data and ethics | 15 | No individual scoring, small groups flagged, synthetic provenance stated, no causal claims | Group results reported without size warnings, or causal language used |
| Communication | 15 | Verdict first, tables readable, every claim traceable to an artifact | Report is a code walkthrough or buries the verdict |

A dimension with no evidence scores zero. The lab total converts to 40% of the
module score on the [assessment](assessment.md) page.

## Self-check before submission

- [ ] The generator ran and the SHA-256 in the report matches the file on disk.
- [ ] `outputs/audit.csv` has exactly 8 rows, one per column.
- [ ] Zero duplicate rows; no unique column; the consequence is written down.
- [ ] Both outcome columns are on the exclusion list for a `passed` model.
- [ ] Every group summary has a count, and groups under 30 are flagged.
- [ ] The merge preserved 500 rows and the assertion is visible in the code.
- [ ] The verdict is one of the three allowed options.
- [ ] Deleted `outputs/`, reran, and got the same two files.
- [ ] No real student data, names, or identifiers anywhere in the submission.

Next: score the work with the [F03 assessment](assessment.md), then continue to
[F04 - Data cleaning](../f04-data-cleaning/index.md).

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)
