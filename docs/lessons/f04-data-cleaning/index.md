# F04 - Data cleaning, missing values, categorical features, and normalization {#f04}

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Level** | 1 - Foundations (implements M02 and M05) |
| **Study time** | 10 hours: 3 h reading, 4 h guided notebook, 2 h lab, 1 h assessment |
| **Hardware** | CPU-only. pandas and scikit-learn; no GPU. |
| **Prerequisites** | [F03 - NumPy and pandas](../f03-numpy-pandas/index.md) |
| **You will produce** | An executed notebook, `outputs/students_clean.csv`, a cleaning specification, and a comparison table of cleaning strategies |

## Why this module exists

You have a table with 328 rows. Eight rows are exact duplicates. Three columns
have missing values. The `course` column contains `" math "`, `"MATH"`,
`"physics"`, and `"CS "` — four spellings of three courses. A model will not
accept any of this as-is.

The obvious fixes are also the dangerous ones. Drop every row with a missing
value and you lose 72 of 320 rows, a fifth of the data. Fill missing values with
zero and you invent students who never attended. Impute using the whole table and
you leak information from the rows you will later call "test". One-hot encode
every category and the matrix quietly grows to hundreds of columns.

This module teaches cleaning as a **sequence of documented decisions**, each with a
measured effect. By the end you will be able to defend every transformation with a
number and a reason, which is what separates data preparation from data damage.

## Learning objectives

By the end of this module, you can:

1. Profile a table before changing it: shapes, duplicate counts, missing counts per
   column, and the raw value set of every categorical column.
2. Remove exact duplicates and explain why deduplication must happen before
   splitting data into train and test.
3. Distinguish MCAR, MAR, and MNAR missingness and choose between dropping rows,
   imputing, and adding a missing indicator.
4. Normalize inconsistent category labels, route unseen values to an explicit
   `Unknown` bucket, and justify one-hot versus ordinal encoding.
5. Compare complete-case analysis with imputation on identical cross-validation
   folds and report both the score and the number of rows behind it.
6. Build a scikit-learn `Pipeline` with a `ColumnTransformer` so imputation and
   scaling are fit on training folds only.
7. Produce a transformed `(n, p)` matrix, explain how `p` was computed, and save a
   cleaned table whose missing values are resolved.

## Before you start

| Requirement | Why it matters |
| --- | --- |
| A working environment with pandas and scikit-learn | The notebook imports `ColumnTransformer`, `SimpleImputer`, and `LogisticRegression` |
| F03 skills: `groupby`, `merge`, boolean masks | Cleaning decisions are verified with those operations |
| About 5 MB of free disk | One small CSV is written |
| Familiarity with cross-validation at a high level | Section 4 compares two strategies on the same 5 folds |
| Willingness to write decisions down | A transformation you cannot explain is not finished |

Check the imports before you start:

```powershell
python -c "import pandas, sklearn; print(pandas.__version__, sklearn.__version__)"
```

## The concepts you need

### 1. Cleaning is an ordered plan, not a series of fixes

"Clean the data" is not a plan. A cleaning **specification** is a list of
decisions in a fixed order, each with a reason and a check:

| Order | Decision | Reason | Check |
| --- | --- | --- | --- |
| 1 | Remove exact duplicates | Duplicates inflate counts and can leak across splits | Row count falls by the duplicate count |
| 2 | Normalize category labels | `"MATH"` and `" math "` are the same course | Value set shrinks to the intended categories |
| 3 | Handle missing values | Models need numbers; dropping loses rows | No missing values remain, or the drop is counted |
| 4 | Encode categories | Models consume numbers | Column count `p` is explained |
| 5 | Scale numeric features | Comparable units for linear models | Means near `0`, standard deviations near `1` |

The order matters. Deduplicate first, because duplicates interact with every count
that follows. Normalize labels before imputing categorical columns, because
`" yes"` and `"yes"` would otherwise be imputed as separate categories. Scale
last, and fit the scaler on training data only.

### 2. Duplicates: exact, near, and where they leak

An **exact duplicate** is a row identical to another in every column. A **near
duplicate** differs in one field, often a timestamp or a spelling, and requires a
judgment call. Start with exact duplicates because the decision is mechanical.

The notebook's raw table has 328 rows and 8 duplicate rows, so deduplication leaves
320. Both numbers appear in the outputs, and the difference is the evidence that
the step ran.

Why deduplicate *before* splitting? If the same row appears twice and one copy
lands in train while the other lands in test, the test score measures memorization,
not generalization. That is a form of **leakage** — test information reaching
training — and F05 examines it in detail.

```python
clean = df.drop_duplicates().copy()
assert len(clean) < len(df)
```

`df.duplicated().sum()` counts duplicates *after* the first occurrence, which is
why 8 duplicate rows remove 8 rows and not 16.

### 3. Missing data: mechanisms and the cost of dropping

Missing values are not all alike. The **mechanism** determines which fix is
defensible:

| Mechanism | Meaning | Example | Safe default |
| --- | --- | --- | --- |
| MCAR | Missing completely at random | A sensor dropped a random reading | Impute or drop; either is unbiased in expectation |
| MAR | Missing depends on other observed columns | Older records lack the attendance field | Impute using other columns; consider an indicator |
| MNAR | Missing depends on the missing value itself | Students who skipped class also skipped the survey | Neither fix is safe; report the limitation |

The notebook's table is missing 26 `attendance` values, 19 `prior_score` values,
and 34 `sleep_hours` values. Those are **79 missing cells** spread over **72
incomplete rows**, so at least seven rows have more than one missing field.

**Complete-case analysis** keeps only rows with no missing values. It is simple and
unbiased only under MCAR, and it throws away data:

| Quantity | Value | Consequence |
| --- | --- | --- |
| Clean rows | 320 | Starting point after deduplication |
| Complete rows | 248 | What dropping every incomplete row leaves |
| Rows lost | 72 | `320 - 248` |
| Share lost | 22.5% | `72 / 320` |

A fifth of the sample disappearing is a real cost, and it is not random if the
missing mechanism is MAR or MNAR. The notebook measures this cost instead of
assuming it away.

### 4. Imputation: pick a statistic, fit it on training data

**Imputation** replaces a missing value with an estimate. The two common choices
for numeric columns:

| Strategy | Strength | Weakness | Use when |
| --- | --- | --- | --- |
| Median | Robust to skew and outliers | Ignores the rest of the row; shrinks variance | The column is skewed or has extreme values |
| Mean | Simple, familiar | Pulled by outliers | The column is roughly symmetric and clean |
| Constant (`0`) | Preserves "none" semantics | Invents a real value where none was measured | Only when `0` means "none", such as a count |
| Model-based | Uses other columns | More complex, can overfit | MAR with strong predictors |

`SimpleImputer(strategy="median")` **learns one value per column** during `fit`
and applies it during `transform`. That two-step design is what makes leakage
avoidable: fit on the training fold, transform the validation fold with the
training median.

A **missing indicator** is an extra binary column that records "this value was
missing". It preserves information when missingness itself is predictive. The cost
is one more column per imputed field and a model that is harder to explain.

### 5. Categorical labels: normalize, bucket, then encode

A **categorical feature** is a column of labels rather than numbers. Raw exports
routinely contain `" math "`, `"MATH"`, `"CS "`, and `"physics"` — four strings for
three courses, plus whatever a future export adds.

Normalize before encoding:

```python
clean["course"] = (
    clean["course"].str.strip().str.lower()
    .map({"math": "Math", "physics": "Physics", "cs": "CS"})
    .fillna("Unknown")
)
```

`.str.strip()` removes the spaces, `.str.lower()` removes case differences, `.map`
applies the canonical spelling, and `.fillna("Unknown")` gives every unrecognized
value an explicit home. Silently dropping unknown labels is worse: the row
survives with a missing category and the failure appears later.

Then **encode**, because models need numbers:

| Encoding | Output | Use when | Risk |
| --- | --- | --- | --- |
| One-hot | One binary column per category | Nominal categories with no order | Wide matrix for high cardinality |
| Ordinal | One integer per category | Genuine order, such as low/medium/high | Implies an order that may not exist |
| Target | One number derived from the target | High cardinality, carefully validated | Leakage if fit outside the fold |

`OneHotEncoder(handle_unknown="ignore")` keeps the pipeline alive when a future
batch contains a category that training never saw: the row gets zeros instead of
an exception. That is a production requirement, not a nicety.

Worked example of the column count: 4 numeric columns, `course` with 3 observed
levels, and `tutoring` with 2 levels give `4 + 3 + 2 = 9` columns. The notebook's
transformed matrix is `(320, 9)`. If `course` had contained an unrecognized value,
the count would have been 10, because `Unknown` would be a fourth level.

### 6. Normalization and standardization

**Feature scaling** puts numeric columns on comparable ranges. Two common methods:

| Method | Formula | Output range | Sensitive to outliers? |
| --- | --- | --- | --- |
| Standardization (z-score) | `(x - mean) / std` | Unbounded, mean `0`, std `1` | Yes, through the mean and std |
| Min-max normalization | `(x - min) / (max - min)` | `[0, 1]` | Yes, strongly |

Standardization is the default for linear models and neural networks. Min-max is
useful when a bounded range matters, such as image pixels, and it is fragile when
a single outlier sets the maximum.

The rule that matters more than the choice: **fit the scaler on training data
only, then transform validation and test data with those training statistics**.
Fitting on the full table lets the scaler see test values, which is leakage even
though no label is involved.

### 7. Pipelines: the mechanism that prevents leakage

A scikit-learn **pipeline** chains steps so that `fit` calls `fit_transform` on
each step in order, and `predict` calls `transform` on each step. A
**`ColumnTransformer`** applies different pipelines to different column groups.

```python
numeric_pipe = Pipeline([
    ("impute", SimpleImputer(strategy="median")),
    ("scale", StandardScaler()),
])
categorical_pipe = Pipeline([
    ("impute", SimpleImputer(strategy="most_frequent")),
    ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
])
preprocess = ColumnTransformer([
    ("num", numeric_pipe, numeric_columns),
    ("cat", categorical_pipe, categorical_columns),
])
```

Wrapped inside `cross_val_score`, the entire preprocessing chain is refit on each
training fold. That is the difference between "I imputed the data" and "I imputed
each training fold and applied the result to its validation fold".

The notebook compares two strategies on identical folds, which is the only fair
comparison:

| Strategy | Rows available | Mean CV accuracy |
| --- | --- | --- |
| Median imputation + scaling | 320 | 0.791 |
| Complete-case (drop incomplete rows) | 248 | 0.770 |

Imputation wins here, by about two points, while using 72 more rows. The gain is
modest, and that is the honest finding: on this synthetic table the missing values
are injected at random, so imputation mainly buys sample size. The comparison is
still worth running, because on a different table the same code could show a large
difference in either direction.

## Guided walkthrough

The full practical is the [guided notebook](notebook.md). It runs in five
sections plus a decision table:

1. **Inspect before cleaning** — counts missing values, duplicates, and raw
   category spellings. Proves that you measure the problems before fixing them.
2. **Remove duplicates and normalize labels** — deduplicates to 320 rows and maps
   four spellings onto three courses plus `Unknown`. Proves that the value set is
   now controlled.
3. **Numeric imputation** — builds the numeric and categorical pipelines and the
   `ColumnTransformer`. Proves that preprocessing is a reusable object, not a
   sequence of one-off assignments.
4. **Compare dropping with imputation** — runs the same 5-fold split for both
   strategies and prints rows and scores. Proves that the decision has a measured
   cost.
5. **Fit the final preprocessing** — fits on the cleaned table and asserts the
   transformed shape and finiteness. Proves that the matrix is model-ready.
6. **Common decisions** — a table of trade-offs for imputation, encoding, and
   scaling. Read it as a checklist for your own specification.

The notebook fits the final preprocessing on all 320 rows because it demonstrates
the transformation rather than evaluating a model. When you evaluate, wrap the
pipeline in cross-validation and let each fold fit its own preprocessing.

## Practical exercise

This exercise is yours to run; it is not the graded lab, and it is not in the
notebook. Work in a scratch notebook and keep the notebook's assertions intact.

1. Add a missing indicator for `sleep_hours` using
   `SimpleImputer(strategy="median", add_indicator=True)` in the numeric pipeline.
   Report the new transformed shape.
2. Run the same 5-fold comparison for four strategies: median, mean,
   median plus indicator, and complete-case. Use one `StratifiedKFold` object with
   `random_state=42` for all four.
3. Add a `dropna` variant that drops only rows missing `prior_score`, and compare
   its row count with the full complete-case variant.
4. Write a four-line table of strategy, rows, mean accuracy, and standard
   deviation across folds.

Expected observations:

- The indicator adds one column, so the matrix becomes `(320, 10)` instead of
  `(320, 9)`.
- Median and mean scores differ by less than about `0.01`. These columns are close
  to symmetric, so the robustness argument for the median does not show up as a
  score difference here. Choose the median anyway, and say why in one sentence.
- The indicator changes the score very little, because missingness in this table
  was injected at random and carries no signal.
- Dropping only `prior_score` rows keeps more data than full complete-case. Row
  count, not just accuracy, is the point of the comparison.
- Fold standard deviations are around `0.02-0.05`; a score difference smaller than
  that is not a real difference.

## Common mistakes and how to diagnose them

| Symptom | Likely cause | How to diagnose and fix |
| --- | --- | --- |
| CV score far above what a rerun gives | Imputation or scaling fit before the split | Move all preprocessing inside the pipeline passed to `cross_val_score` |
| Row count silently shrinks after a merge or join | Inner join or `dropna()` in a helper | Print `len()` before and after every step; use `how="left"` and check |
| `ValueError: could not convert string to float` | A categorical column reached the numeric branch | Check the column lists in `ColumnTransformer` |
| Unknown category crashes `predict` | `OneHotEncoder` was built without `handle_unknown="ignore"` | Rebuild the encoder; confirm the encoder was fit, not only constructed |
| Transformed matrix has far more columns than expected | High-cardinality column one-hot encoded | Print `preprocess.get_feature_names_out()` and count levels first |
| Mean equals `0` for a column that should have a value | Missing values were filled with `0` | Check `df[col].isna().sum()` and the imputer strategy |
| Category counts do not match the raw file | Labels normalized without an `Unknown` bucket | Compare `value_counts()` before and after; count the mapped-to-unknown rows |
| `(320, 9)` assertion fails with `(320, 10)` | An extra category such as `Unknown` appeared | Print the encoder's categories; fix the mapping or accept the extra column and document it |
| Good score but the report cannot say why | No specification and no comparison | Write the decision table first; rerun each strategy on the same folds |

Diagnostic protocol for cleaning:

1. Print shape, missing count, and category value counts before each step.
2. After each step, assert exactly the change you intended — one row count, one
   column count, or one value set.
3. When a score is surprising, recheck the fold definition before the model.
4. Never compare two strategies on different splits, row sets, or fold seeds.

## Checkpoint

You are ready for the lab when you can:

- [ ] State how many rows were lost to deduplication and how many to
      complete-case analysis.
- [ ] Explain why `" math "` and `"MATH"` must be normalized before encoding.
- [ ] Explain why imputation is fit inside each cross-validation fold.
- [ ] Account for all 9 columns of the transformed matrix.
- [ ] Describe one case where dropping rows is better than imputing.
- [ ] Read `outputs/students_clean.csv` back and confirm no missing values remain
      in the imputed columns.

## Next step

1. Run the [guided notebook](notebook.md) from a clean kernel.
2. Complete the [lab brief](lab.md): an independent cleaning task for a different
   school and term, with a specification and an ablation table.
3. Score your evidence with the [assessment](assessment.md).
4. Continue to [F05 - Train, validation, and test splits](../f05-splits/index.md),
   where the leakage you avoided here becomes the main topic. The
   [M02 plan](../../syllabus/level-1-foundations.md#m02) and
   [M05 plan](../../syllabus/level-1-foundations.md#m05) show where cleaning and
   dataset preparation sit. The messy table comes from the
   [foundation dataset card](../../technical/foundation-assets.md#foundation-datasets) and the
   [data generator](../../technical/foundation-assets.md#data-generator).

---

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)
