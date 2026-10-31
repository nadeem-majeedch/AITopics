# F03 - NumPy and pandas for datasets {#f03}

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Level** | 1 - Foundations (implements M02) |
| **Study time** | 8 hours: 2 h reading, 3 h guided notebook, 2 h lab, 1 h assessment |
| **Hardware** | CPU-only. NumPy and pandas; no GPU. |
| **Prerequisites** | [M01 - Python and AI development environment](../m01-environment/index.md) and [F01 - Python essentials](../f01-python-ai/index.md) |
| **You will produce** | An executed notebook, `outputs/students.csv`, a column-audit table, and a short fitness-for-use memo |

## Why this module exists

A colleague sends you a file called `students_final_v3.csv`. It opens in Excel
and looks fine. You load it into a model and get an error about a missing column,
then a warning about a conversion, then a shape that does not match the
documentation.

Almost every real dataset arrives like this. The columns are text, one column has
trailing spaces in its name, two tables must be joined on a course code, and
nobody wrote down how many rows to expect. The work of an AI engineer starts with
answering three questions about any table: **what shape is it, what does each
column actually contain, and what does one row represent?**

This module teaches the two libraries that answer those questions: **NumPy** for
arrays and fast numeric operations, and **pandas** for labeled tables. Both are
CPU-only and both are prerequisites for every later dataset module. You will work
with a synthetic table of 400 students, but the operations are the ones you will
run on real data.

## Learning objectives

By the end of this module, you can:

1. Report the shape, dtypes, and missing-value count of a table and say what one
   row represents.
2. Convert a column to a NumPy array, state its shape and dtype, and explain when
   a two-dimensional `(n, 1)` array is required.
3. Replace a Python loop with a vectorized operation and a boolean mask, and
   compute a rate as the mean of a mask.
4. Select data correctly with `loc` and `iloc`, and explain why chained indexing
   is unsafe.
5. Summarize a table with `groupby` and check group sizes before trusting a mean.
6. Merge two tables on a key with `validate=`, and prove the merge preserved the
   row count.
7. Build a standardized `(n, p)` feature matrix from selected columns, verify its
   column means and standard deviations, and save the table to CSV with a verified
   round trip.

## Before you start

| Requirement | Why it matters |
| --- | --- |
| A working Python environment from M01 | The notebook imports NumPy and pandas |
| NumPy and pandas installed | Both are in `requirements/notebooks.txt` |
| F01 skills: functions, dicts, lists of records | Every pandas operation returns objects you must inspect and explain |
| About 5 MB of free disk | The notebook writes one small CSV |
| A calculator or Python REPL | Several checkpoints ask you to verify an arithmetic claim |

Check the versions before you start:

```powershell
python -c "import numpy, pandas; print(numpy.__version__, pandas.__version__)"
```

If the import fails, the kernel is not using the environment from M01. Fix that
first; installing a second copy of pandas rarely helps.

## The concepts you need

### 1. The DataFrame: a table you can inspect

A **DataFrame** is a two-dimensional labeled table: columns have names, rows have
an **index**, and each column has a **dtype** (the type pandas inferred for its
values). A **Series** is one column, including its index.

```python
df = make_students()
print(df.shape)        # (400, 9)
print(df.dtypes)
print(df.head(3))
```

For any new table, answer these five questions in order:

| Question | Code | Why it matters |
| --- | --- | --- |
| How many rows and columns? | `df.shape` | Expected `(400, 9)`; a different shape means a different file |
| What type is each column? | `df.dtypes` | `object` means text; arithmetic on it fails or silently concatenates |
| What does one row mean? | Read the column names and a few rows | "One row per student" is an assumption you must verify |
| What is missing? | `df.isna().sum()` | Every model needs a decision about missing values (F04) |
| Are rows unique? | `df["student_id"].is_unique` | Duplicate rows inflate every count and leak across splits (F05) |

The notebook's table has 400 rows and 9 columns: `student_id`, `study_hours`,
`attendance`, `prior_score`, `sleep_hours`, `tutoring`, `course`, `passed`, and
`final_score`. One row is one student. `passed` is a binary **target** (the value
you would predict); the rest are **features** (inputs), except `student_id`,
which is an identifier and must never be a feature.

### 2. NumPy arrays and vectorization

A **NumPy array** is a fixed-size block of one dtype with a shape. A
one-dimensional array of 400 values has shape `(400,)`; a matrix of 400 rows and
4 columns has shape `(400, 4)`.

| Object | Shape | Meaning |
| --- | --- | --- |
| `df["study_hours"].to_numpy()` | `(400,)` | One value per student |
| `df[["study_hours", "attendance"]].to_numpy()` | `(400, 2)` | Two features per student |
| `X.reshape(400, 1)` | `(400, 1)` | A single feature in matrix form, as scikit-learn expects |

**Vectorization** means applying an operation to a whole array in compiled code
instead of looping in Python:

```python
study = df["study_hours"].to_numpy()
loop_mean = sum(value for value in study) / len(study)
vector_mean = study.mean()          # same value, no Python loop
```

On 400 rows the timing difference is noise. On 40 million rows it is the
difference between seconds and minutes. Learn the vectorized form now, while the
data is small enough to check both results against each other.

### 3. Broadcasting and boolean masks

**Broadcasting** is NumPy's rule for combining arrays whose shapes differ but are
compatible. Subtracting a per-column mean from a `(400, 4)` matrix works because
the `(4,)` vector is stretched across the 400 rows.

A **boolean mask** is an array of `True`/`False` values, one per row. Its mean is
the proportion of `True` values, which makes it a natural way to compute a rate:

```python
passed = df["passed"].to_numpy() == 1
print(passed.sum(), round(passed.mean(), 3))   # number passed, pass rate
```

In the verified run the mask's mean, the **pass rate**, is `0.507`. That number is
the base rate every later model must beat: a model that always predicts "fail"
scores about `0.493`, not zero.

Masks also drive comparisons between groups:

| Group | Mean study hours | What it suggests |
| --- | --- | --- |
| Passed | 4.73 | Students who passed studied more |
| Failed | 3.25 | A difference of about 1.5 hours per week |

This is a description of one synthetic sample, not evidence that studying causes
a pass. F06 and F08 return to that distinction.

### 4. Label and position indexing

Two accessors, two rules:

| Accessor | Selects by | Example | Result |
| --- | --- | --- | --- |
| `.loc[]` | labels (index values, column names) | `df.loc[0, "course"]` | The value in the row labeled `0` |
| `.iloc[]` | integer position | `df.iloc[0, 2]` | The value in the first row, third column |

The notebook uses both and asserts that they agree for the first row, which is
true only because the default index is `0..399`. After `sort_values`, `dropna`,
or a `groupby`, labels and positions diverge.

**Chained indexing** such as `df[df["passed"] == 1]["final_score"] = 0` may modify
a temporary copy. Use one `.loc` call for assignment:
`df.loc[df["passed"] == 1, "final_score"] = 0`.

### 5. Grouping and aggregation

`groupby` implements **split, apply, combine**: split rows into groups, compute
one summary per group, combine the summaries into a new table. It answers "one
row per group" questions.

```python
by_course = (
    df.groupby("course", as_index=False)
      .agg(students=("student_id", "count"),
           mean_score=("final_score", "mean"),
           pass_rate=("passed", "mean"))
      .sort_values("mean_score", ascending=False)
)
```

Always request the count next to the mean. A mean over 3 students and a mean over
300 are printed identically unless you ask for `n`. In the notebook the three
course groups sum to 400 students, and the assertion
`by_course["students"].sum() == len(df)` proves no row was lost or duplicated.

`groupby` also skips missing keys by default. If a column has missing values,
`dropna=False` keeps them as a visible group instead of hiding them.

### 6. Merging tables without changing the row count

A **merge** (a join) combines two tables on a shared key. The dangerous outcome is
a **row explosion**: if the right table has duplicate keys, a many-to-one join
becomes many-to-many and the result grows.

`validate=` makes the intended relationship explicit and raises an error when the
data violates it:

| `validate=` | Meaning | Use when |
| --- | --- | --- |
| `"one_to_one"` | Keys unique on both sides | Joining two per-student tables |
| `"many_to_one"` | Keys unique on the right only | Joining a lookup table such as the course catalog |
| `"one_to_many"` | Keys unique on the left only | Attaching a per-student table to a per-course one |
| `"many_to_many"` | No uniqueness assumed | Rare, and usually a modeling mistake |

```python
merged = df.merge(course_info, on="course", how="left", validate="many_to_one")
assert merged.shape[0] == df.shape[0]
```

The notebook's `df` has 9 columns and the 3-column catalog contributes
`department` and `credits` after the join key is consumed, so the result is
`(400, 11)`. A left merge can add rows or columns; it must never silently drop
students. `assert merged.shape[0] == df.shape[0]` is the check that proves it.

### 7. From table to feature matrix

A **feature matrix** is a two-dimensional numeric array `X` of shape
`(n_samples, n_features)`, plus a target vector `y` of length `n`. Models consume
numbers, so text columns must be encoded (F04) and numeric columns usually
standardized.

**Standardization** subtracts the column mean and divides by the column standard
deviation, producing **z-scores**:

```python
X = df[["study_hours", "attendance", "prior_score", "sleep_hours"]].to_numpy(dtype=float)
X_scaled = (X - X.mean(axis=0)) / X.std(axis=0)
```

| Property | Before | After |
| --- | --- | --- |
| Shape | `(400, 4)` | `(400, 4)` |
| Column means | Different units: hours, percent, points | About `0` |
| Column standard deviations | Different scales | `1` |
| Unit | Mixed | Standard deviations from the mean |

Worked example: a student with `study_hours = 8.0` in a column with mean `4.0`
and standard deviation `2.0` gets `z = (8.0 - 4.0) / 2.0 = 2.0`, meaning two
standard deviations above average for that column.

Two details that cause real bugs:

- **`ddof`**: NumPy's `std()` divides by `n` by default (`ddof=0`); pandas'
  `.std()` divides by `n - 1` (`ddof=1`). The notebook asserts means of `0` and
  standard deviations of `1` with NumPy's default, so use the same convention when
  you verify.
- **Fit on training data only.** Here scaling uses all 400 rows because this is a
  demonstration, not an evaluation. In F05 you will see that fitting the scaler on
  the full table leaks test-set information.

Finally, persist the table: `df.to_csv(path, index=False)`. Without
`index=False`, pandas writes the row index as an unnamed first column, and the
next reader gets a 10-column file. CSV also loses dtypes: `passed` returns as
`int64` but a text column returns as `object`, and missing integers may come back
as floats. Read the file, compare shapes, and check one known value before
trusting it.

## Guided walkthrough

The full practical is the [guided notebook](notebook.md). It runs in eight
sections, each proving one skill:

1. **Build a table with a known shape** — generates 400 students and asserts
   `(400, 9)`. Proves that you check a table before analyzing it.
2. **Arrays: shape, dtype, vectorization** — converts `study_hours` to an array
   and compares a loop mean with the vectorized mean. Proves that both agree.
3. **Broadcasting and masks** — centers `final_score`, computes the pass rate, and
   compares study hours by outcome. Proves that a mask is a rate.
4. **`loc` and `iloc`** — selects the same row two ways and asserts they agree.
   Proves that you know which accessor you are using.
5. **Grouping** — summarizes by course and by tutoring, with counts. Proves that
   you check group sizes.
6. **Merge** — joins a course catalog with `validate="many_to_one"` and asserts
   `(400, 11)`. Proves that the join did not change the row count.
7. **Feature matrix** — selects four numeric columns, standardizes, and asserts
   means near `0` and standard deviations near `1`. Proves that the matrix is
   model-ready.
8. **Save and reload** — writes `outputs/students.csv`, reads it back, and
   compares. Proves that the artifact is usable.

The notebook stops at the first failed assertion by design. A wrong shape early
would make every later number meaningless, so fix the cause rather than editing
the assertion.

## Practical exercise

This exercise is yours to run; it is not the graded lab, and it is not in the
notebook. Work in a scratch notebook or a `.py` script.

1. Compute the pass rate by `tutoring` with counts, and the pass rate by `course`
   with counts. Compare each group with the overall `0.507`.
2. Bin `study_hours` into three bands with `pd.cut` (edges `[0, 3, 6, 20]`) and
   report the pass rate and count per band. Check that the counts sum to 400.
3. Build `X` from the four numeric columns, standardize it with NumPy, then
   compute `X_scaled.std(axis=0)` and `pd.DataFrame(X_scaled).std().to_numpy()`.
   Explain the two results.
4. Sort the table by `final_score` descending, then select the top row with both
   `.loc[0]` and `.iloc[0]`. Explain why they now return different students.

Expected observations:

- Tutored students pass at a higher rate than untutored students, and the
  weighted average of the two rates is the overall `0.507`. If your weighted
  average is not `0.507`, one group's count is wrong.
- Pass rate rises from the lowest study band to the highest. It is a description
  of this sample, not proof of causation.
- NumPy's `std(axis=0)` returns `1.0`; pandas' `.std()` returns about `1.00125`
  because it divides by `n - 1`. Both are correct under their own convention.
- After sorting, `.loc[0]` selects the student whose original index label was
  `0`, while `.iloc[0]` selects the highest-scoring student. This is exactly why
  chained indexing is unsafe.

## Common mistakes and how to diagnose them

| Symptom | Likely cause | How to diagnose and fix |
| --- | --- | --- |
| `KeyError: 'Study Hours'` | Column is `study_hours`; names are case- and space-sensitive | Print `list(df.columns)` and copy the exact name |
| `TypeError: unsupported operand type(s) for -: 'str' and 'int'` | A numeric-looking column is stored as text | Check `df.dtypes`; convert with `pd.to_numeric(..., errors="coerce")` |
| Merge result has more rows than the left table | Duplicate keys on the right side | Use `validate="many_to_one"`; count duplicate keys before merging |
| `SettingWithCopyWarning` or an assignment that does nothing | Chained indexing (`df[mask]["col"] = ...`) | Use one `.loc[mask, "col"] = ...` assignment |
| Mean looks impossible | The group is tiny, or missing values were dropped silently | Add `count` to every `agg`; check `df.isna().sum()` |
| Standardized columns are not exactly mean `0`, std `1` | pandas' `std` uses `ddof=1`, NumPy's default is `ddof=0` | Verify with the same library and convention used to scale |
| Reloaded CSV has an extra `Unnamed: 0` column | `to_csv` was called without `index=False` | Rewrite with `index=False`; never delete the column by hand |
| `ValueError: Expected 2D array, got 1D array` | A single column was passed to a model | Use `df[["col"]].to_numpy()` or `.reshape(-1, 1)` |
| An assertion compares a `(400,)` array to a scalar | Shape mismatch, not a value mismatch | Print `.shape` on both sides before comparing |

A debugging protocol for tables:

1. Print `shape` and `dtypes` before and after every transformation.
2. Print one known row before and after a merge or a sort.
3. When a value is wrong, check the input column, not the formula.
4. Change one operation, rerun, and record the new shape.

## Checkpoint

You are ready for the lab when you can:

- [ ] State the shape of the table and the feature matrix without looking.
- [ ] Explain why `passed.mean()` equals the pass rate.
- [ ] Explain the difference between `loc` and `iloc` after a sort.
- [ ] Prove a merge preserved 400 rows and say which `validate=` value you used.
- [ ] Verify that standardized columns have mean `0` and standard deviation `1`,
      and name the `ddof` convention you used.
- [ ] Read `outputs/students.csv` back and confirm the shape matches.

## Next step

1. Run the [guided notebook](notebook.md) from a clean kernel.
2. Complete the [lab brief](lab.md), which asks you to audit a different table and
   decide whether it is fit for modeling.
3. Score your evidence with the [assessment](assessment.md).
4. Continue to [F04 - Data cleaning, missing values, categorical features, and
   normalization](../f04-data-cleaning/index.md). If you came here from M01, the
   [M02 plan](../../syllabus/level-1-foundations.md#m02) shows where this unit
   sits. The notebook builds its 400-row table inline; the
   [foundation dataset card](../../technical/foundation-assets.md#foundation-datasets) documents the
   related CSV tables, and the [data generator](../../technical/foundation-assets.md#data-generator)
   produces the file you will audit in the lab.

---

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)
