# F06 lab - Neighborhood market brief

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Weight** | 40% of the F06 assessment |
| **Time** | About 2 hours |
| **Hardware** | CPU-only |
| **Starter file** | `labs/foundations/f06_house_eda.md` |
| **Data** | `datasets/foundations/generated/house_prices.csv`, or generate it with `python scripts/make_foundation_data.py` |
| **Prerequisite** | A completed run of the [guided notebook](notebook.md) |

## The scenario

A community housing nonprofit has funding for **one** walk-in advice desk. It can
open the desk in one of four neighborhoods: north, south, east, or west. The board
has asked for an evidence brief, not a model.

The board agreed on a decision rule before seeing the data:

1. The desk should go where a typical square foot is most expensive, because that
   is where space affordability pressure is highest.
2. A neighborhood is eligible only if the table contains at least **150** sales
   for it.
3. If the top two neighborhoods are within **3%** on median price per square foot,
   choose the one with more sales, because the desk will see more households.

Your task is to test that rule against the data, report what the data can and
cannot support, and make one recommendation.

## Why it matters

A recommendation is a decision with consequences. If you compare raw median
prices only, you may recommend a neighborhood where large houses make the median
look high, even though space is cheap per square foot. If you ignore counts, a
median built on too few sales can decide where a real desk opens. If you delete
the expensive rows without saying so, you change the question.

EDA is the evidence stage. This lab asks you to produce evidence that a
non-technical board can check, including the parts that weaken your own case.

## Constraints

- **Descriptive only.** No model, no prediction, no causal claim.
- **Decision rule fixed in advance.** Do not change the 150-sale threshold or the
  3% tie-break after seeing the ranking. If you think the rule is wrong, report
  that separately.
- **Use only the repository table.** Do not add external market data,
  neighborhood demographics, or scraped listings.
- **Keep every row in the main analysis.** The IQR-flagged rows stay in; run a
  sensitivity check with them removed and report both results.
- **Three figures minimum**, each saved to `outputs/`, each with a title, axis
  labels, and units.
- **No personal or address-level detail.** The data is synthetic; do not invent
  addresses, owners, or demographics.
- **Reproducible.** Fix the seed where randomness is involved, record package
  versions, and make every number traceable to a cell.

## Required steps

### Step 1 - Provenance and integrity

1. Generate the table if needed:

   ```powershell
   python scripts/make_foundation_data.py
   ```

2. Load `house_prices.csv` and print the shape, dtypes, missing-value counts,
   duplicate-row count, and the minimum and maximum of `sale_price`.
3. Record the file's SHA-256 and the generator seed.

**Validation check 1:** assert that the table has 600 rows and 7 columns, that
`sale_price` is strictly positive, and that there are no duplicate rows. If any
check fails, stop and document the failure instead of cleaning silently.

### Step 2 - Data dictionary and quality log

Write a table with one row per column: name, type, unit, range, missing count, and
a note on plausibility. Then add a quality log with one row per issue found:
issue, how many rows, evidence, decision, and effect on the analysis.

A quality log entry can say "no issue found". Recording a check that passed is
evidence that you ran it.

### Step 3 - Univariate profile

For `sale_price`, `area_sqft`, `bedrooms`, `age_years`, `distance_km`, and
`garage`, report count, mean, median, standard deviation, minimum, maximum, and
the quartiles. State which columns are skewed and which are roughly symmetric.

Plot the target distribution. Choose a bin count and defend it in one sentence.

### Step 4 - Relationships

1. Compute the correlation matrix for the numeric columns and print the
   correlation of each feature with `sale_price`.
2. Make a scatter plot of `area_sqft` against `sale_price`. Describe the shape,
   the spread, and any clusters.
3. Make a second scatter plot of `distance_km` against `sale_price`. Decide
   whether a linear summary is adequate; if not, say what you would check next.

Do not describe a correlation as an effect. "Area and price move together" is
supportable; "area causes price" is not.

### Step 5 - Group comparison

Build a table with one row per neighborhood and these columns:

| Column | Definition |
| --- | --- |
| `count` | Number of sales |
| `median_price` | Median `sale_price` |
| `mean_price` | Mean `sale_price` |
| `q1`, `q3` | Quartiles of `sale_price` |
| `iqr` | `q3 - q1` |
| `median_price_per_sqft` | Median of `sale_price / area_sqft` |
| `eligible` | `count >= 150` |

Make a box plot of price by neighborhood, ordered by median. State the smallest
group and whether every group is eligible under the board's rule. At least one
neighborhood will fall below 150 sales; if every group looks eligible, check that
you compared raw counts rather than shares.

The median of per-house ratios is not the same as total price divided by total
area. The two can rank neighborhoods differently. Use the median of ratios as the
rule specifies, and note the difference in your limitations section.

### Step 6 - Apply the decision rule

1. Filter to eligible neighborhoods.
2. Rank by `median_price_per_sqft`.
3. Apply the 3% tie-break if the top two are close.
4. Write the recommendation in one sentence, naming the neighborhood and the
   numbers behind it.

**Validation check 2:** assert that the recommended neighborhood is eligible, and
that its `median_price_per_sqft` is within the top two of the eligible set. The
recommendation must be computed from the table, not typed as a constant.

### Step 7 - Outlier and sensitivity analysis

1. Apply the IQR rule to `sale_price`. Report the bounds and the number of flagged
   rows.
2. List the flagged rows with the columns that matter for the decision.
3. Recompute the group table and the recommendation with the flagged rows removed.
4. State whether the recommendation changes. If it does, the recommendation is
   fragile and must be reported as conditional.

The flags are not errors by default. The table is synthetic and has no negative
prices; the flagged rows are unusually cheap or expensive sales, not corruption.
Say what you did and why.

### Step 8 - Figures and packaging

Produce at least three figures:

- the target distribution;
- area against price;
- the group comparison, with counts visible in the caption or a companion table.

Save each to `outputs/` with `bbox_inches="tight"`, then close it. Verify that
each file exists and is larger than zero bytes.

### Step 9 - Write the brief

Use the report headings below. The brief must contain:

- five numbered observations, each with evidence and a decision;
- the recommendation and the rule that produced it;
- one finding that weakens or complicates the recommendation;
- limitations of the synthetic table;
- reproduction instructions.

## Deliverables

```text
f06-house-eda/
  README.md                 # how to rerun, in 5-10 lines
  eda.ipynb                 # executed top to bottom, or eda.py plus a log
  quality_log.csv           # one row per check or issue
  group_summary.csv         # the table from Step 5
  recommendation.json       # neighborhood, metric, rule, sensitivity result
  outputs/                  # the three figures
  market_brief.md           # the report described below
  reflection.md             # 200-300 words for the assessment
```

`recommendation.json` should contain the chosen neighborhood, the metric value,
the runner-up, the gap in percent, the eligibility counts, and whether the
recommendation survived the outlier sensitivity check. Do not include personal
paths.

## Report template

```markdown
# F06 neighborhood market brief

## 1. Summary and recommendation
The decision, the rule, and the headline number.

## 2. Data and provenance
File, shape, hash, generator seed, license, and units.

## 3. Data quality
The quality log, including checks that passed.

## 4. Distributions
Shape of the target and the main features; the figures that support it.

## 5. Relationships
Correlations and scatter plots, with the limits of each summary.

## 6. Group comparison
The group table, counts, and eligibility.

## 7. Decision
The ranking, the tie-break if used, and the recommendation.

## 8. Sensitivity and anomalies
IQR flags, what happened when they were removed, and whether the decision changed.

## 9. Limitations
Synthetic data, sample size, one snapshot, no causal claims.

## 10. Reproduction
Commands, seeds, versions, and artifact locations.
```

## Rubric

The lab is scored on five dimensions. The weights total 100%.

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Technical correctness | 30 | Correct statistics, derived metric, eligibility filter, and recommendation; assertions pass | Numbers exist but a definition or filter is wrong |
| Evaluation and diagnosis | 25 | Outliers classified, sensitivity run, conclusion follows evidence, one weakening finding reported | Outliers deleted or ignored; no sensitivity check |
| Reproducibility | 15 | Seed, hash, versions, commands, and saved figures reproduce every number | Missing provenance; figures cannot be regenerated |
| Data and ethics | 15 | Synthetic-data limits stated; no invented demographics; no causal or individual claims | Overclaims about real markets or people |
| Communication | 15 | Brief is readable by a non-technical board; tables and figures are labeled; recommendation is unambiguous | Jargon-heavy or no clear recommendation |

A dimension with no evidence scores zero, regardless of effort.

## Privacy and safety

- The house table is synthetic and CC0-1.0. It does not describe a real housing
  market. Say so in the brief; do not present the medians as market advice.
- Do not invent neighborhood demographics, school quality, crime rates, or
  resident characteristics. The table has none of these, and inventing them
  creates harmful claims.
- Do not include addresses, owner names, or anything that looks like a real
  listing.
- Avoid stigmatizing language about low-price neighborhoods. A low median price
  is a number about houses in a synthetic table, not a statement about the people
  who live there.
- Keep the data local. There is no reason to upload it to a public service.
- Remove absolute personal paths and usernames from logs and screenshots.

## Self-check before submission

- [ ] The table is 600 x 7, with no missing values, duplicates, or non-positive
      prices.
- [ ] Every column in the group table has a stated definition and unit.
- [ ] The recommendation follows the pre-registered rule and names its numbers.
- [ ] The eligibility filter is applied before ranking.
- [ ] The IQR sensitivity check is reported, including whether the decision
      changed.
- [ ] At least three labeled figures exist in `outputs/` and are non-empty.
- [ ] The brief states that the data is synthetic and descriptive only.
- [ ] No invented demographics or addresses appear anywhere.
- [ ] Another student could rerun the analysis from the README and hash.

Next: score the work with the [assessment](assessment.md), then continue to
[F07 - Supervised and unsupervised learning](../f07-supervised-unsupervised/index.md).

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)
