# F05 - Train, validation, and test splits {#f05}

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Level** | 1 - Foundations (M02) |
| **Study time** | 8 hours: 2 h theory, 3 h guided notebook, 2 h lab, 1 h assessment |
| **Hardware** | CPU-only; no GPU required |
| **Prerequisites** | [F04 - Cleaning, missing values, categories, normalization](../f04-data-cleaning/index.md) |
| **You will produce** | An executed notebook, a leakage audit report, a split manifest, and a short reflection |

## Why this module exists

An analyst is asked to predict house sale prices. The first model reaches an
R-squared of 0.70 (the share of price variance the model explains), which is
reasonable for noisy data. To improve it, the analyst adds a feature called
`price_vs_city_mean`: each house's sale price minus the average sale price in the
table. The score jumps to 1.00, and the report says the model is almost perfect.

It is not. The new feature is computed from the answer. At prediction time, when
a house has not sold yet, that value does not exist. The same report also fit its
scaler on every row before splitting, and it split duplicate listings across
training and test. Three separate leaks produced one confident, wrong number.

A **split** is the assignment of rows to a training set, a validation set, and a
test set. It is the first place where a model evaluation becomes trustworthy or
worthless. This module teaches you to build splits that survive a skeptical
review, and to recognize the leaks that survive a careless one.

## Learning objectives

By the end of this module, you can:

1. Explain what the training, validation, and test sets are each allowed to
   influence, and why the test set is held out until the end.
2. Build a reproducible 60/20/20 split with a fixed seed and report the exact
   row counts.
3. Stratify a continuous target by binning it, then verify that the test set
   preserves the target distribution.
4. Use a group-aware split to keep related rows on one side, and prove that the
   groups do not overlap.
5. Identify a target-derived feature, remove it, and explain the resulting score
   change.
6. Fit every learned preprocessing step on training data only, and explain why a
   small measured effect does not make the leak acceptable.
7. Detect duplicate rows that cross a split boundary and deduplicate before
   splitting.

## Before you start

| Requirement | Why it matters |
| --- | --- |
| Completed [F04](../f04-data-cleaning/index.md) | You need clean, typed columns before splitting makes sense |
| A working Python environment with pandas and scikit-learn | The notebook imports both |
| The synthetic house table or the generator | The notebook builds the table in code, so no download is required |
| About 1 GB of free disk and 8 GB of RAM | The table is small; the headroom is for Jupyter and plots |
| Willingness to read assertions | Every section ends with a check that fails loudly when a leak returns |

The notebook is self-contained: it generates the 600-row house table with a fixed
seed. If you prefer to work from CSV files, run
`python scripts/make_foundation_data.py` and read
`datasets/foundations/generated/house_prices.csv`. The
[dataset card](../../technical/foundation-assets.md#foundation-datasets) documents the columns,
the license, and the generator at
[`scripts/make_foundation_data.py`](../../technical/foundation-assets.md#data-generator).

## The concepts you need

### 1. Three sets, three different jobs

A **training set** is the rows a model learns parameters from. A **validation
set** is the rows you use to compare model choices: feature sets, regularization
strength, tree depth, a decision threshold. A **test set** is touched once, at the
end, to estimate how the chosen model performs on data it has never seen.

| Set | Typical share | What it may influence | May you change the model after looking? |
| --- | --- | --- | --- |
| Training | 60% | Parameters, preprocessing statistics | Yes, that is its purpose |
| Validation | 20% | Model selection, hyperparameters, thresholds | Yes, but record every comparison |
| Test | 20% | The final reported estimate only | No; looking turns it into a validation set |

The shares are conventions, not laws. 60/20/20 is common for small tables
because it leaves enough rows in each set to detect a meaningful difference. With
100,000 rows you can afford 80/10/10; with 120 rows you may need cross-validation
instead of a separate validation set.

```python
from sklearn.model_selection import train_test_split

train_val, test = train_test_split(houses, test_size=0.20, random_state=42)
train, validation = train_test_split(train_val, test_size=0.25, random_state=42)
```

The second call takes 25% **of the remaining 80%**, which is 20% of the original
table. For 600 rows the result is 360 training, 120 validation, and 120 test rows.

A **seed** makes the pseudo-random assignment repeatable. It does not make the
split statistically better; it makes your report reproducible.

### 2. Random splits fail when rows are related

A random row split assumes rows are independent. House listings in the same
neighborhood are not: they share schools, transport, and unmeasured location
effects. If some houses from a neighborhood land in training and others in test,
the model can learn that neighborhood's level and appear to generalize to it.

This is **group leakage**. The fix is a **group-aware split**: every group goes
entirely into one side.

```python
from sklearn.model_selection import GroupShuffleSplit

gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
train_idx, test_idx = next(gss.split(houses, groups=houses["neighbourhood"]))
group_train, group_test = houses.iloc[train_idx], houses.iloc[test_idx]
```

In the verified run, training contains east, south, and west, and the test set
contains north only. The intersection of the two group sets is empty.

The trade-off is real: the test set no longer contains every group, so it cannot
tell you how the model performs on a neighborhood it has seen. That is the point.
If deployment will include new neighborhoods, the honest estimate is the
unseen-group estimate, not the random-row one.

| Split strategy | Keeps together | Use when | Cost |
| --- | --- | --- | --- |
| Random row split | Nothing | Rows are independent and exchangeable | Overstates performance on related rows |
| Stratified split | Target distribution | Classes or target bands are imbalanced | Does not handle group dependence |
| Group split | A group such as patient, user, or region | The same group can appear more than once | Test may omit entire groups |
| Time-based split | Chronology | Data arrives over time | Old data may not represent the future |

### 3. Stratification for a continuous target

**Stratification** preserves the share of a variable across splits. For a
categorical target, scikit-learn can stratify directly. For a continuous target
such as price, you first bin it, then stratify on the bin.

```python
houses["price_band"] = pd.qcut(houses["sale_price"], q=4, labels=["Q1", "Q2", "Q3", "Q4"])
train_s, test_s = train_test_split(
    houses, test_size=0.20, random_state=42, stratify=houses["price_band"]
)
```

`qcut` creates quartile bins with roughly equal counts. With 600 rows, each band
holds about 150 houses; a 120-row test set should hold about 30 per band. Verify
the shares instead of assuming them.

Stratifying on the target itself is standard for classification: it balances the
classes without giving the model any feature values it would not have at
prediction time. Stratifying on a feature derived from the target is different.
It encodes the answer into the split, and it makes the test distribution depend on
information the model is supposed to predict.

### 4. Preprocessing is learned, so it can leak

A `StandardScaler` learns a mean and a standard deviation. An imputer learns a
fill value. A one-hot encoder learns a category list. Each is a **learned
transformation**, and each must be fitted on training data only.

If you fit the scaler on all rows, the training process sees the test set's mean
and variance. The model has received a small summary of data it is supposed to
predict.

```python
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

model = make_pipeline(StandardScaler(), Ridge())
model.fit(X_train, y_train)      # scaler fits on X_train only
score = model.score(X_test, y_test)
```

A **pipeline** chains transformations and a final estimator so that `fit` applies
only to training data and `predict` reuses the stored statistics. This is the
default habit to build; manual `fit_transform` calls are easy to get wrong.

In the notebook, the leaky and clean scaler versions both reach an R-squared of
0.7976. The effect is nearly zero because the table is large and the features are
well behaved. Do not conclude that the leak is harmless. On a small table, a
skewed feature, or a target-encoded column, the same mistake can move a score by
a large amount. The principle is about correctness, not about whether today's
number moved.

### 5. Target leakage

**Target leakage** happens when a feature contains information about the target
that will not be available when the model is used. It is the most damaging leak
because it produces excellent scores and no error message.

Common forms:

- An aggregate computed with the current row included, such as a customer's
  average spend including the purchase being predicted.
- A column recorded after the outcome, such as a discharge code, a refund flag,
  or a final exam score.
- A column computed from the target, such as price per square foot when the
  target is sale price, or a total that includes the outcome being predicted.

The notebook makes the mechanism visible:

```python
leaky["price_vs_city_mean"] = leaky["sale_price"] - leaky["sale_price"].mean()
```

The feature is the target minus a constant, so a linear model can recover the
target almost exactly. The verified run reports R-squared 1.000 with the feature
and 0.703 without it. The second number is the believable one.

Three questions catch most target leaks:

1. Would this value exist at the moment of prediction, before the outcome?
2. Was it computed using rows outside the training set, including this row?
3. Is the score too good for the noise level the problem should have?

### 6. Duplicates and near-duplicates

If the same row appears in training and test, the model can memorize it. The
notebook appends 20 sampled rows to the 600-row table, splits the 620 rows, and
finds **11 cross-split matches**. After `drop_duplicates()` and a fresh split, the
count is **0**.

```python
deduped = with_duplicates.drop_duplicates()
clean_train, clean_test = train_test_split(deduped, test_size=0.2, random_state=42)
```

Exact duplicates are easy. Near-duplicates are harder: the same apartment listed
twice with a slightly different description, or the same patient with two visit
records. When a stable identifier exists, group by it. When it does not, hash a
normalized subset of columns and inspect the largest clusters before splitting.

Order matters: deduplicate **before** splitting. Deduplicating after the split
leaves the test set contaminated and the row counts inconsistent.

### 7. Record the split so someone can rebuild it

A split is an experimental condition. If you cannot rebuild it, your score is an
anecdote.

| Field | Example | Why |
| --- | --- | --- |
| Data version | Generator commit and seed 42 | Different data, different split |
| Row count | 600 | Detects silent filtering |
| Seed | 42 | Reproduces the assignment |
| Fractions | 60/20/20 | Explains the counts |
| Group column | `neighbourhood` | Documents the dependence structure |
| Group assignment | train east/south/west; test north | Proves zero overlap |
| Split hash | SHA-256 of sorted row identifiers per set | Detects accidental changes |
| Code version | Git commit | Ties the report to the code |

For temporal data, split by time rather than at random: train on the past, test on
the future. A random split on time-ordered rows lets the model learn from the
future, which is the same category of mistake as target leakage.

## Guided walkthrough

The [guided notebook](notebook.md) performs seven checks on the synthetic house
table. Each section proves one property:

1. **Build the table.** Confirms the shape `(600, 7)` and that prices are
   positive before any splitting.
2. **60/20/20 split.** Produces 360/120/120 rows and asserts that the parts sum
   to the whole.
3. **Stratified split.** Bins price into quartiles and checks that the test set
   contains all four bands.
4. **Group split.** Holds out whole neighborhoods and asserts that the group
   sets do not intersect.
5. **Target leakage.** Adds a feature computed from the target and shows the
   R-squared rise from 0.703 to 1.000.
6. **Preprocessing leakage.** Compares a scaler fitted on all rows with one
   fitted on training rows; both score 0.7976, and the notebook explains why the
   principle still matters.
7. **Duplicate leakage.** Finds 11 cross-split duplicates, deduplicates, and
   finds 0.

The assertions are part of the lesson. If one fails, the run is not a success
with a different number; something about the data or the split changed.

## Practical exercise

This exercise is smaller than the lab and stays inside the guided notebook's
data. Work in a scratch notebook so you do not overwrite the guided run.

1. Take the first 200 houses with `.iloc[:200]` and make a 70/15/15 split with
   `random_state=7`. Record the three row counts.
2. Fit a `StandardScaler` on all 200 rows, then on the training rows only. Train
   the same linear model both ways and print both test R-squared values.
3. Run a group split on the 200-row subset with `GroupShuffleSplit` and print the
   train and test group sets.
4. Add one duplicate of every tenth row, split at random, count cross-split
   matches, deduplicate, and count again.

Expected observations:

- The counts should be 140, 30, and 30. A different result means the fractions
  were applied twice or the subset changed.
- The two R-squared values should be close. A large gap on 200 rows is a signal
  that the scaler statistic matters for this feature set, not proof of a bug.
- The group split should show no overlap, but the test set may contain only one
  or two neighborhoods. Write down which groups the estimate covers.
- The duplicate count before deduplication should be greater than zero; after
  deduplication it must be zero. If it is zero before, your duplicate injection
  did not survive the split.

## Common mistakes and how to diagnose them

| Mistake | Symptom | Diagnosis and fix |
| --- | --- | --- |
| Fitting the scaler or imputer on all rows | Score slightly or greatly better than a pipeline run | Compare `scaler.fit(X)` with `scaler.fit(X_train)`; move preprocessing into a pipeline |
| Computing an aggregate with the current row included | Near-perfect R-squared, especially with a linear model | Check whether the feature can be derived from the target; rebuild it from training rows only |
| Splitting before deduplicating | Test score drops sharply on a fresh dataset | Merge train and test on all columns; count matches; deduplicate first |
| Using a random split when groups repeat | Validation score much higher than the unseen-group score | Run both splits; if the gap is large, report the group split |
| Reusing the test set to choose features | Test score tracks every change you make | Move all comparisons to validation; touch test once |
| Stratifying on raw continuous values | `ValueError` about bins or continuous targets | Bin with `qcut`, then stratify on the band |
| Forgetting `random_state` | Counts and scores change on every run | Set the seed once at the top and reuse it |
| Splitting time-ordered rows at random | Model performs well offline, poorly in production | Use a cutoff date; train on earlier rows, test on later rows |

## Checkpoint

You are ready for the lab when you can:

- [ ] State the job of each of the three sets without looking at your notes.
- [ ] Reproduce a 60/20/20 split of 600 rows and explain why the second
      `test_size` is 0.25.
- [ ] Show a group split with zero overlap and name the groups on each side.
- [ ] Explain the difference between the R-squared 1.000 and 0.703 results.
- [ ] Explain why the 0.7976 versus 0.7976 scaler result is still a defect.
- [ ] Find the 11 cross-split duplicates and show the count falls to 0.
- [ ] Write a split manifest with seed, counts, groups, and data version.

## Next step

1. Run the [guided notebook](notebook.md) from a clean kernel.
2. Complete the [lab brief](lab.md): audit an inherited evaluation and rebuild a
   leakage-free split for a student early-warning model.
3. Score your evidence with the [assessment](assessment.md).
4. Continue to [F06 - Exploratory data analysis and visualization](../f06-eda/index.md).

---

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)
