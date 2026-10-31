# F05 lab - Audit and rebuild a leakage-prone evaluation

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Weight** | 40% of the F05 assessment |
| **Time** | About 2 hours |
| **Hardware** | CPU-only |
| **Starter file** | `labs/foundations/f05_leakage_audit.md` |
| **Data** | `datasets/foundations/generated/student_performance.csv`, or generate it with `python scripts/make_foundation_data.py` |
| **Prerequisite** | A completed run of the [guided notebook](notebook.md) |

## The scenario

A study-support team wants an **early-warning model**. At the end of week 8 of a
14-week course, the model should flag students who are likely to fail, so an
adviser can offer help. The model will run before the final exam, using only data
the team already has: study hours so far, attendance, prior score, sleep hours,
tutoring, and course.

A colleague has already built an evaluation and reports that it is "almost
perfect". You are asked to audit it before anyone acts on it. The inherited
notebook:

- predicts `passed` using a feature set that includes `final_score`;
- imputes missing values and scales features on the full table, before splitting;
- compares four thresholds on the test set and reports the best one;
- uses a single random 80/20 split with no seed and no group check.

Your job is not to improve the accuracy number. Your job is to decide whether the
number means anything, fix the evaluation, and write a short decision memo.

## Why it matters

An early-warning system that looks accurate because it saw the final exam is
worse than no system. It sends help to students who do not need it, misses
students who do, and gives advisers false confidence. The same pattern appears in
credit scoring, fraud detection, medical triage, and churn prediction: a column
recorded after the outcome quietly becomes the model's best feature.

Data leakage is also an **ethics** problem, not only a technical one. A model that
uses information from the future makes decisions about people based on a
performance that has not happened yet.

## Constraints

- **Target:** `passed`.
- **Allowed predictors:** `study_hours`, `attendance`, `prior_score`,
  `sleep_hours`, `tutoring`, `course`.
- **Forbidden predictors:** `final_score`, `passed`, and any column computed from
  either of them.
- **Split:** 60/20/20, stratified on `passed`, seed `2026`, applied to a table
  with 500 rows.
- **Preprocessing:** every imputer, encoder, and scaler is fitted on training
  rows only.
- **Model selection:** the validation set chooses between a majority-class
  baseline and one logistic regression configuration. The test set is evaluated
  once.
- **Group check:** `course` is the group. Hold out one entire course and report
  the result separately.
- **No new data:** use the repository table. Do not download external data.
- **No individual decisions:** the output is an evaluation and a recommendation,
  never a list of named students.

## Required steps

### Step 1 - Establish provenance and identity

1. Generate the data if needed:

   ```powershell
   python scripts/make_foundation_data.py
   ```

2. Load `student_performance.csv`, print the shape, column types, missing-value
   counts, and duplicate-row count.
3. Add a `student_id` column before any shuffling, for example
   `df.insert(0, "student_id", [f"S{i:04d}" for i in range(len(df))])`. This is a
   synthetic identifier, not a real person.
4. Record the file's SHA-256 and the generator seed.

**Validation check 1:** assert that the table has 500 rows and that
`student_id` is unique. If the row count differs, stop and record why before
continuing.

### Step 2 - Write a data-availability table

For every column, state:

| Column | Known when? | Available at week 8? | Role | Decision |
| --- | --- | --- | --- | --- |
| `student_id` | At enrollment | Yes | Identifier | Exclude from features |
| `study_hours` | Continuously | Yes | Feature | Keep |
| `attendance` | Continuously | Yes | Feature | Keep |
| `prior_score` | Before the course | Yes | Feature | Keep |
| `sleep_hours` | Continuously | Yes | Feature | Keep |
| `tutoring` | Continuously | Yes | Feature | Keep |
| `course` | At enrollment | Yes | Feature and group | Keep; also used for the group split |
| `final_score` | After the final exam | No | Post-outcome | Exclude |
| `passed` | After the final exam | No | Target | Never a feature |

The "known when" column is the audit's core question. A feature that is only
known after the outcome cannot be used, no matter how predictive it is.

### Step 3 - Reproduce the inherited evaluation

Build a small script or notebook that reproduces the colleague's approach:

1. Use all original columns except `passed` as features, including
   `final_score`; exclude the synthetic `student_id`.
2. Fit the scaler on the full table.
3. Split 80/20 without a seed.
4. Fit logistic regression and report accuracy.
5. Try four decision thresholds on the test set and report the best.

Record the accuracy and threshold. If the number looks excellent, treat that as
the claim to investigate, not as success. You are not done: you have reproduced a
flawed result, which is the necessary first step in auditing it.

### Step 4 - Inventory the leaks

Identify at least **three** distinct leaks. For each one, change exactly one thing
and re-evaluate:

| Leak | Evidence | Metric before | Metric after | Fix |
| --- | --- | --- | --- | --- |
| Post-outcome feature | `final_score` is in `X` | | | Remove it |
| Preprocessing before split | Scaler mean uses test rows | | | Fit on train only |
| Test-set tuning | Threshold chosen on test | | | Choose on validation |
| Unseeded split | Counts change per run | | | Fix seed 2026 |
| Group leakage | Courses mixed across splits | | | Hold out a course |

"Metric before" and "metric after" must come from your run, not from this page.
A leak whose removal changes nothing is still a leak; explain why the effect was
small if that happens.

**Validation check 2:** assert that the final feature list and
`{"final_score", "passed"}` are disjoint. Put the assertion in code, not only in
prose.

### Step 5 - Build the clean split

1. Deduplicate and confirm the row count.
2. Create `X` and `y` with the allowed predictors only.
3. Split 60/20/20, stratified on `passed`, `random_state=2026`.
4. Fit the imputer, encoder, and scaler inside a pipeline on the training rows.
   Encode `tutoring` and `course` inside the pipeline so the test rows never
   influence the category list.
5. Compare a majority-class baseline with logistic regression on the validation
   set. Select one model and one threshold.
6. Evaluate the selected configuration on the test set exactly once.

Report accuracy, precision, recall, and the confusion matrix. In an early-warning
setting, **recall** for the failing class usually matters more than accuracy,
because a missed student is a missed intervention. State the trade-off you chose.

**Validation check 3:** assert that the three split sizes sum to 500, that no
`student_id` appears in two splits, and that the scaler's learned mean matches
the training mean within a small tolerance.

### Step 6 - Stress-test with a held-out course

Repeat the clean evaluation with `GroupShuffleSplit`, holding out one entire
`course` as the test set. Keep the same preprocessing rules.

If you one-hot encode `course`, set `handle_unknown="ignore"` on the encoder, or
drop `course` from the feature list for this stress test and say so. Otherwise the
held-out course is an unseen category and the encoder raises an error. Neither
choice is wrong; the point is to make it deliberately and report it.

Answer:

1. How large is the gap between the random-split and held-out-course results?
2. Which course was held out, and how many students were in it?
3. If the gap is large, would you trust the random-split estimate for a new
   course? Why or why not?

With only three courses, a held-out course is a small and noisy test set. Say so.
A wide confidence interval is an honest result, not a failure.

### Step 7 - Check duplicates and identifiers

Compute:

- exact duplicate rows before splitting;
- the number of `student_id` values shared across train and test;
- the number of rows lost to deduplication.

Record all three. A zero duplicate count is a valid finding; report it rather
than skipping the check.

### Step 8 - Write the audit report and memo

Use the report headings below. End with a one-paragraph recommendation to the
study-support team:

- whether the inherited evaluation can support a decision;
- what the leakage-free estimate is;
- what the model should and should not be used for;
- what you would monitor if it were deployed.

## Deliverables

```text
f05-leakage-audit/
  README.md                 # how to rerun, in 5-10 lines
  audit.ipynb               # executed top to bottom, or audit.py plus output log
  leakage_table.csv         # leak, evidence, metric before, metric after, fix
  split_manifest.json       # seed, counts, groups, data hash, feature list
  metrics.json              # baseline, validation, test, held-out-course results
  audit_report.md           # the report described below
  reflection.md             # 200-300 words for the assessment
  figures/                  # optional confusion matrices or bar charts
```

`split_manifest.json` should contain at least: data file name, SHA-256, row
count, seed, fractions, group column, group assignment, feature list, and the
timestamp of the run. Do not include personal paths or usernames.

## Report template

```markdown
# F05 leakage audit

## 1. Summary and recommendation
What you audited, the headline finding, and your recommendation in three sentences.

## 2. Data and provenance
File, row count, columns, hash, generator seed, and the synthetic-data license.

## 3. Data availability
The table from Step 2 and the rule you used to classify each column.

## 4. Inherited evaluation
What the colleague's pipeline did and the metric it reported.

## 5. Leak inventory
The table from Step 4. For each leak: mechanism, evidence, effect, and fix.

## 6. Rebuilt evaluation
Split design, preprocessing, model selection, test metrics, and confusion matrix.

## 7. Held-out course result
The group split, the gap, and your interpretation of its uncertainty.

## 8. Limitations
Sample size, synthetic data, single split, and anything you could not test.

## 9. Reproduction
Exact commands, seeds, package versions, and where each artifact is stored.
```

## Rubric

The lab is scored on five dimensions. The weights total 100%.

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Technical correctness | 30 | Clean split, train-only preprocessing, correct metrics, assertions pass | Split exists but preprocessing or feature rules are violated |
| Evaluation and diagnosis | 25 | At least three leaks quantified one at a time; test used once; group gap interpreted | Leaks listed without measurement or mixed together |
| Reproducibility | 15 | Seed, hashes, versions, commands, and manifest reproduce every number | Missing manifest or seed; results cannot be rebuilt |
| Data and ethics | 15 | Availability rule applied consistently; no individual predictions; limits stated | Ethics mentioned but not reflected in the design |
| Communication | 15 | Memo is clear, tables are readable, recommendation follows the evidence | Report is a step log without a decision |

A dimension with no evidence scores zero, regardless of effort.

## Privacy and safety

- The student table is synthetic and CC0-1.0. It contains no real people. Still,
  treat it as if it did: do not invent names, emails, or student numbers.
- Never produce a ranked list of "students likely to fail" in your submission.
  Report aggregate metrics only.
- Do not use the model, or your audit, to make decisions about real students.
  The data is a teaching artifact, not a measurement of any course.
- Do not upload the table to a public service. It is small enough to keep local.
- Remove absolute personal paths and usernames from logs before submitting.
- If you use an AI assistant, verify every number it suggests against your own
  run and disclose the assistance in your reflection.

## Self-check before submission

- [ ] The table has 500 rows, unique `student_id` values, and a recorded hash.
- [ ] The feature list excludes `final_score` and `passed`, enforced by an
      assertion.
- [ ] At least three leaks are quantified with before/after metrics from my run.
- [ ] The scaler and imputer are fitted on training rows only.
- [ ] The test set was evaluated once; the threshold came from validation.
- [ ] The held-out-course result is reported with its sample size.
- [ ] `split_manifest.json` contains the seed, counts, groups, and feature list.
- [ ] The memo states what the model must not be used for.
- [ ] No personal paths or identifiers appear in the submission.

Next: score the work with the [assessment](assessment.md), then continue to
[F06 - Exploratory data analysis and visualization](../f06-eda/index.md).

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)
