# F06 - Exploratory data analysis and visualization {#f06}

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Level** | 1 - Foundations (M02) |
| **Study time** | 8 hours: 2 h theory, 3 h guided notebook, 2 h lab, 1 h assessment |
| **Hardware** | CPU-only; plotting runs on the CPU |
| **Prerequisites** | [F05 - Train, validation, and test splits](../f05-splits/index.md) |
| **You will produce** | An executed notebook, a neighborhood EDA brief with three figures, a data-quality log, and a short reflection |

## Why this module exists

A team receives a table of 600 house sales. Someone computes the average price,
317,661 USD, and writes in a slide that "the typical home costs about 317,700".
The number is arithmetically correct and still hides the facts that matter for a
decision: neighborhood medians range from 297,218 to 337,716, the smallest group
has only 103 sales, and four houses fall outside the interquartile range.

The summary is not a lie. It is an **unexamined summary**. Exploratory data
analysis (EDA) is the disciplined habit of looking at the data before you model
it: distributions, relationships, groups, and anomalies, each tied to a sentence
that changes a decision.

The cost of skipping EDA is concrete. You miss a feature that carries most of the
signal, you trust a group with too few rows, you fit squared-error metrics to a
target with a long tail, and you ship a model whose behavior surprises you on the
first unusual row.

## Learning objectives

By the end of this module, you can:

1. Run an EDA pass in a fixed order: integrity, univariate, relationships,
   groups, anomalies.
2. Choose a plot type that answers a specific question and label it with units.
3. Interpret a correlation coefficient, including what it does not tell you.
4. Compare group medians with group counts and decide whether the sample supports
   a claim.
5. Apply the interquartile range rule, separate a rare value from an impossible
   one, and choose a metric accordingly.
6. Save figures reproducibly with a non-interactive backend and fixed settings.
7. Write five observations that each change a modeling or reporting decision.

## Before you start

| Requirement | Why it matters |
| --- | --- |
| Completed [F05](../f05-splits/index.md) | Splitting first protects the test set from EDA-driven choices |
| pandas, NumPy, and matplotlib installed | The notebook imports all three |
| The synthetic house table, or the generator | The notebook builds the table itself |
| About 8 GB of RAM | Ample; the table is small |
| A folder you can write to | The notebook saves three figures under `outputs/` |

The notebook generates its own 600-row table, so no download is required. To work
from CSV instead, run `python scripts/make_foundation_data.py` and read
`datasets/foundations/generated/house_prices.csv`. The
[dataset card](../../technical/foundation-assets.md#foundation-datasets) lists the columns and the
CC0-1.0 license; the generator is
[`scripts/make_foundation_data.py`](../../technical/foundation-assets.md#data-generator).

## The concepts you need

### 1. EDA is a sequence of questions, not a gallery of plots

A **univariate** summary describes one column. A **bivariate** summary describes
the relationship between two. A **grouped** summary compares subsets. Do them in
that order, because a relationship can be hidden or created by a distribution you
have not inspected yet.

| Question | Check | Typical view |
| --- | --- | --- |
| Is the table what it claims to be? | Shape, dtypes, missingness, duplicates, impossible values | Printed summary, not a plot |
| What shape does each column have? | Center, spread, skew, gaps, spikes | Histogram or ECDF |
| Do two columns move together? | Scatter, correlation, binned means | Scatter plot |
| Do groups differ? | Count, median, spread per group | Box plot plus a count table |
| Which rows are unusual? | IQR rule, domain limits, exact duplicates | Sorted table of flagged rows |

**Skew** means one tail is longer than the other. A right-skewed column such as
`distance_km` has a few large values that pull the mean above the median. When
mean and median disagree, report both and say which one answers the question.

### 2. Univariate distributions

Start with the target. For the house table, price has a long upper tail: most
sales cluster in a broad middle range, and a small number are much more
expensive. That shape has consequences: a histogram with too few bins hides the
tail, and a squared-error metric will be dominated by the expensive rows.

| Statistic | What it tells you | Trap |
| --- | --- | --- |
| Mean | Arithmetic average | Sensitive to skew and outliers |
| Median | Middle value | Ignores the size of extreme values |
| Standard deviation | Typical distance from the mean | Assumes a roughly symmetric spread |
| Min and max | Range and impossible values | One bad row can set the max |
| Quartiles | Spread of the middle 50% | Needs enough rows to be stable |
| Missing count | Whether the column is usable | Missingness can be informative |

**Bin width** is a modeling choice. A histogram with 10 bins and one with 60 bins
are both "the data"; they answer different questions. Choose a width that shows
the shape without turning noise into structure, and say what you chose.

```python
fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(df["sale_price"] / 1000, bins=25, edgecolor="white")
ax.set_xlabel("Sale price (thousand USD)")
ax.set_ylabel("Houses")
fig.savefig(OUTPUT_DIR / "price_hist.png", bbox_inches="tight")
plt.close(fig)
```

Dividing by 1,000 is not cosmetic. An axis labeled in thousands is easier to read
than one with six-digit tick labels, and the unit belongs in the axis label.

### 3. Relationships and correlation

A **scatter plot** shows one point per row. **Correlation** summarizes the
strength of a linear relationship between two numeric columns, from -1 to 1.
Zero correlation means no *linear* association; it does not mean independence.

In the verified run, the correlation between `area_sqft` and `sale_price` is
**0.749**. Squaring it gives about 0.56: a linear model using area alone accounts
for roughly 56% of the variance in price. That is a strong signal and still leaves
44% for other features, noise, and nonlinearity.

| Correlation | Rough reading | Check before acting |
| --- | --- | --- |
| 0.0 to 0.2 | Little linear signal | Look for a nonlinear pattern |
| 0.2 to 0.5 | Weak to moderate | Inspect groups and outliers |
| 0.5 to 0.8 | Moderate to strong | Confirm with a scatter plot |
| 0.8 to 1.0 | Strong | Ask whether one column is derived from the other |

Correlation is not causation. A correlation between `age_years` and price may
reflect location, renovation history, or the age of the housing stock in a
neighborhood. Plot the points, color by group if you can, and describe the pattern
rather than the number alone.

### 4. Groups, counts, and medians

A **grouped summary** compares subsets. Always print the count beside the median.
A median from 103 rows and a median from 200 rows are not equally stable, and a
group with 8 rows should not drive a recommendation.

Verified medians for the house table:

| Neighborhood | Median sale price (USD) | Note |
| --- | --- | --- |
| South | 297,218 | Lowest median |
| West | 301,761 | Close to south |
| East | 323,728 | Middle |
| North | 337,716 | Highest median |

The gap between north and south is 40,498 USD. That is a real difference in this
table, but it is a description of 600 synthetic sales, not a claim about a
housing market. The smallest group has **103** rows, which is large enough to
report a median and small enough that a few sales can move it.

A **box plot** shows the median, the middle 50%, and points beyond the whiskers.
It is good for comparing several groups at once. It hides the number of rows, so
pair it with the count table, and it can make a small group look as important as
a large one.

### 5. Outliers and impossible values

The **interquartile range (IQR)** is the distance between the 25th and 75th
percentiles. The IQR rule flags values below `Q1 - 1.5 * IQR` or above
`Q3 + 1.5 * IQR`. It is a convention for starting an investigation, not a verdict.

Worked example: for the values 10, 12, 13, 14, 15, 16, 17, 18, 19, 40, the first
quartile is 13 and the third is 18, so the IQR is 5. The bounds are 5.5 and 25.5.
The value 40 is flagged. It may be a data-entry error, a different unit, or a
genuine extreme case. You cannot tell from the rule alone.

Distinguish three cases:

| Case | Example | Action |
| --- | --- | --- |
| Impossible value | Negative price, age of 300 years | Fix or remove with a documented rule |
| Rare but valid value | A mansion in a normal market | Keep; consider a robust metric or a transformed target |
| Unit or parsing error | Price stored in cents | Correct the unit, then recheck the distribution |

In the house table, the IQR rule flags **four** rows and there are **no negative
prices**. Two flagged rows are unusually cheap and two are unusually expensive;
all four look like plausible sales, not corruption. Removing them would change
the question from "what do houses sell for" to "what do typical houses sell for",
which may be the right question, but it must be stated.

### 6. Visual design that does not mislead

A figure is an argument. Make the argument readable and honest.

| Choice | Good practice | Why |
| --- | --- | --- |
| Axis range | Start bar charts at zero; show the range that matters for scatter plots | Truncated axes exaggerate differences |
| Units | Put them in the label: "thousand USD", "sq ft", "km" | A number without a unit is ambiguous |
| Scale | Consider a log scale for a long-tailed positive column | Compresses the tail without deleting it |
| Overplotting | Use small points, transparency, or binning | 600 points can hide a dense center |
| Color | Use a colorblind-safe palette and label categories | Color alone should not carry meaning |
| Title | State the comparison, not "Figure 1" | The reader should not guess |
| Saving | `bbox_inches="tight"`, fixed DPI, `plt.close(fig)` | Reproducible files and no memory growth |

In a headless environment, set a non-interactive backend before importing
pyplot:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
```

`Agg` writes files without opening a window. If you use it in a notebook and see
no inline plot, that is expected: open the saved PNG instead.

### 7. From observation to decision

An EDA note is not a list of plots. Each observation should name the evidence and
the decision it supports.

| Observation | Evidence | Decision |
| --- | --- | --- |
| Price has a long upper tail | Histogram; maximum 507,728 against Q3 356,400 | Report the median; check sensitivity to expensive rows |
| Area is the strongest linear signal | Correlation 0.749 | Keep area; check for nonlinearity |
| Neighborhood medians differ by about 40k | Group table | Include neighborhood as a feature |
| One group has only 103 rows | Count table | Avoid strong claims about that group |
| Four IQR flags, two low and two high; no negative prices | IQR check | Keep them; report sensitivity to removal |

The template is deliberately blunt: **observation, evidence, decision**. If you
cannot fill the third column, the plot is decoration.

## Guided walkthrough

The [guided notebook](notebook.md) runs five sections on the house table:

1. **Univariate distributions.** Plots price, area, and distance, and saves
   `outputs/f06_distributions.png`. It shows the price tail and the right-skewed
   distance column.
2. **Relationships and correlation.** Prints the correlation of every numeric
   column with price and saves a scatter plot of area against price. The
   area-price correlation is 0.749.
3. **Groups and sample sizes.** Prints count, median, and mean per neighborhood,
   saves a box plot, and asserts that the smallest group has at least 50 rows. The
   smallest group has 103.
4. **Outliers and impossible values.** Applies the IQR rule and checks for
   non-positive prices. It finds four outliers and no negative prices.
5. **Write observations.** Converts the findings into five sentences with
   modeling implications.

The notebook saves three figures under `outputs/`: `f06_distributions.png`,
`f06_area_price.png`, and `f06_price_by_neighbourhood.png`.

## Practical exercise

This exercise stays inside the notebook's table and is smaller than the lab. Work
in a scratch notebook.

1. Summarize `age_years` and `garage`: count, median, mean, min, and max for each
   level of `garage`.
2. Compute the median sale price for `garage = 0` and `garage = 1`. State the
   difference and whether it matches the generator's documented +12,000 effect.
3. Plot a histogram of `distance_km` and decide whether the mean or the median is
   the better summary. Justify it from the shape.
4. Write three observation-evidence-decision sentences about these two columns.

Expected observations:

- `age_years` is roughly uniform between 0 and 59 because the generator draws it
  uniformly. A flat histogram is the expected shape, not a bug.
- `garage = 1` should show a higher median price. The generator adds 12,000 for a
  garage, but other features also differ between the groups, so the raw difference
  is not a causal effect.
- `distance_km` is drawn from a gamma distribution and clipped, so it is
  right-skewed. The mean sits above the median; report both.
- Your three sentences should each end in a decision, such as "keep the column",
  "report the median", or "check the group sizes before comparing".

## Common mistakes and how to diagnose them

| Mistake | Symptom | Diagnosis and fix |
| --- | --- | --- |
| Using the mean for a skewed target | "Typical price" is higher than most prices | Compare mean and median; report both; plot the distribution |
| Reading correlation as causation | Confident claim about what raises price | Check for confounders and group structure; describe association only |
| Ignoring group counts | A tiny group drives the conclusion | Print count beside every group statistic; set a minimum |
| Too few or too many histogram bins | Shape looks flat or noisy | Try several widths; state the choice |
| Treating every flagged outlier as an error | Rows deleted without evidence | Inspect the rows; classify impossible, rare, or unit error |
| Plot without units or title | Reader cannot interpret the axis | Add labels with units and a sentence title |
| Saving figures without closing them | Memory grows; files missing in headless runs | Use `savefig`, then `plt.close(fig)`; set `Agg` |
| Doing EDA on the test set | Modeling choices quietly fit the test rows | Explore training data; keep test untouched until evaluation |

## Checkpoint

You are ready for the lab when you can:

- [ ] Name the five EDA questions in order and the check used for each.
- [ ] Explain why the median price is a better "typical" value than the mean for
      this table.
- [ ] Interpret the area-price correlation of 0.749 without claiming causation.
- [ ] Read the neighborhood table and state the north-south gap and the smallest
      group size.
- [ ] Apply the IQR rule by hand to a small list.
- [ ] Explain why the four flagged rows are not automatically errors.
- [ ] Produce a labeled figure and save it without opening a window.

## Next step

1. Run the [guided notebook](notebook.md) and open the three saved figures.
2. Complete the [lab brief](lab.md): build a neighborhood market brief from the
   same table, with a recommendation and a limitations section.
3. Score your work with the [assessment](assessment.md).
4. Continue to [F07 - Supervised and unsupervised learning](../f07-supervised-unsupervised/index.md).

---

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)
