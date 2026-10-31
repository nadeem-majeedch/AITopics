# F08 lab - A valuation screen under a latency budget

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Weight** | 40% of the F08 assessment |
| **Time** | About 3 hours |
| **Hardware** | CPU-only, one core; no network at inference time |
| **Starter file** | `labs/foundations/f08_house_prices.md` in the repository |
| **Prerequisite** | A completed run of the [guided notebook](notebook.md) |

## The scenario

**Cedarline Property Partners** is a small fund that buys mid-market homes. Each
week it receives about 2,500 listings from partner agencies. A single analyst
reviews every shortlisted listing, so the cutoff also controls the workload.

The tool must answer two questions for every listing:

1. What will this home sell for?
2. Should it go to the analyst's review queue?

The review rule is fixed by the fund's mandate: **shortlist a listing when the
predicted sale price is at least 325,000 USD**. The fund does not pursue homes
below that band. You may adjust the predicted-price cutoff around that value to
control errors, but you must state the cutoff you use and why.

The vendor's earlier attempt was accurate but unusable: it loaded a 700 MB model,
called a remote service, and took 1.8 seconds per listing. Cedarline needs a local
model that scores 2,500 listings in **under 2.0 seconds total** (0.8 ms per
listing) on one CPU core, with an artifact **under 2 MB**. A model that misses the
budget is not a candidate, however accurate it is.

## Why it matters

This lab is the smallest realistic version of a deployment decision. You must:

- turn a regression output into a business action with a threshold;
- separate the cost of a missed opportunity from the cost of wasted analyst time;
- prove that the model fits an operational budget, not only a metrics table;
- document intended use and limitations in a model card that another person can
  challenge.

The data is synthetic, so no real seller, buyer, or address is involved. The
reasoning is the same as with real listings.

This is not the notebook again. The notebook fits linear, ridge, and logistic
models and prints metrics. The lab adds an operational latency budget, a
cost-sensitive cutoff, a reload check, and a model card that a reviewer can
challenge.

## Constraints

| Constraint | Value |
| --- | --- |
| Data | `datasets/foundations/generated/house_prices.csv`, 600 rows, generated with seed 42 |
| Target | `sale_price` in USD |
| Decision | Shortlist when predicted price is at or above the chosen cutoff, near 325,000 USD |
| Features | Only fields available when the listing arrives; never `sale_price` |
| Split | 60% train, 20% validation, 20% test, fixed seed |
| Latency | 2,500 listings in under 2.0 s on one CPU core, measured after warm-up |
| Artifact | Serialized model under 2 MB |
| Missed shortlist-worthy home | 8,000 USD in lost expected margin |
| Unnecessary review | 400 USD of analyst time |
| Interpretability | A one-page model card; the analyst must be able to explain the main drivers |

If the generated CSV is absent, run `python scripts/make_foundation_data.py` from
the repository root. Record the SHA-256 of `house_prices.csv` from
`datasets/foundations/generated/manifest.json`. The
[dataset card](../../technical/foundation-assets.md#foundation-datasets) states the license (CC0-1.0)
and the limitations you must repeat in your model card.

## Required steps

### Step 1 - Establish provenance

Load the CSV with pandas. Assert that it has 600 rows and 7 columns. Record the
generator seed, the manifest hash, your Python version, and the pandas and
scikit-learn versions. If you regenerate the data, the hash changes; report the
hash you actually used.

### Step 2 - Define the decision and split the data

Create the target `sale_price` and the binary outcome `shortlist_worthy =
sale_price >= 325000`. Split the rows 60/20/20 with a fixed `random_state`. Keep
the test rows untouched until Step 8.

**Validation check 1 - split integrity.** Assert that the three index sets are
disjoint, that their sizes are 360/120/120, and that the positive rate in each
split is within 0.05 of the full table. Save the index arrays so a reviewer can
reproduce the split.

### Step 3 - Audit the features

List every feature and state when it becomes available. Encode `neighbourhood`
with one-hot encoding fitted on training rows only. Create at least one derived
feature if you can justify it, for example `area_per_bedroom`. Drop `sale_price`
from the feature matrix.

**Validation check 2 - no target leakage.** Assert that `sale_price` and
`shortlist_worthy` are absent from the feature columns, and that no column is
computed from the sale outcome. Record a correlation table between each numeric
feature and the target as a sanity check, not as proof of causality.

### Step 4 - Build the baselines

Report two baselines on the validation rows:

- a mean predictor for price (MAE and RMSE);
- a rule that shortlists nothing, and a rule that shortlists everything, scored
  with the decision confusion matrix and expected cost.

The "shortlist nothing" rule catches no worthy home but wastes no analyst time.
Its expected cost is the number to beat.

### Step 5 - Fit and compare candidates

Fit at least three candidates on the training rows:

1. linear regression on standardized numeric features plus encoded location;
2. ridge regression with at least two `alpha` values, standardized;
3. one additional model of your choice, clearly labeled as exploratory if it is a
   tree or ensemble from F09.

Compare them on validation MAE, RMSE, and R-squared. Do not use the test set to
choose a model. Report the table, not a single winner sentence.

### Step 6 - Choose a decision cutoff and compute cost

Convert each validation prediction into a shortlist decision at cutoffs from
300,000 to 350,000 USD in 5,000 steps. For each cutoff, compute the confusion
matrix, precision, recall, and expected cost:

```text
expected cost = 8,000 * false negatives + 400 * false positives
```

Plot or tabulate cost against the cutoff. Choose the cutoff with the lowest
validation cost, and report the flag rate so the analyst can judge the workload.
State the chosen cutoff and the cost per 1,000 listings.

**Validation check 3 - decision arithmetic.** Recompute the expected cost for your
chosen cutoff directly from the four confusion-matrix counts. It must match the
number in your report. An error here usually means the positive class was
flipped.

### Step 7 - Measure latency and artifact size

Serialize the full pipeline (preprocessing and estimator) with `joblib`. Measure
the file size and assert it is under 2 MB.

Build a batch of 2,500 rows by sampling with replacement from the validation
features. Set `OMP_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1` before the timing
run so the measurement matches the one-core constraint. Warm up with one batch,
then time five batches with `time.perf_counter()` and report the median total time
and milliseconds per listing. Assert the median total is under 2.0 seconds on your
machine. Record the CPU model; timings on another machine will differ.

**Validation check 4 - reload and budget.** Reload the artifact in a fresh Python
process, predict the same batch, and assert the predictions are identical. Report
the measured latency and file size, not the target values.

### Step 8 - Evaluate once on the test set

Apply the frozen model and frozen cutoff to the 120 test rows. Report MAE, RMSE,
R-squared, the decision confusion matrix, precision, recall, and expected cost
per 1,000 listings. Compare with the validation numbers and with the baselines.
If the test result is much worse, report it; do not tune and re-report.

**Validation check 5 - test discipline.** Keep a timestamped note or a flag in
your metrics file showing that the test set was scored once, after all choices
were fixed.

### Step 9 - Write the model card and report

Use the template below. The model card is a required artifact, not an appendix.
It must state the intended use, the population the data represents, the features,
the metrics, the decision cutoff, the two error costs, and at least three
limitations.

## Deliverables

```text
f08-house-prices/
  README.md                  # how to rerun, in 5-10 lines
  f08_house_prices.ipynb     # executed top to bottom
  outputs/
    metrics.json             # validation and test metrics, cutoff, latency, hash
    model.joblib              # serialized model, under 2 MB
  model_card.md              # one page, required headings below
  report.md                  # the investigation and decision
  reflection.md              # 200-300 words
```

Do not commit the generated CSV, the virtual environment, or the `outputs/`
directory. Copy the files you need into the submission folder outside the
repository, or keep the folder private and share it directly.

## Report template

```markdown
# F08 valuation screen report

## 1. Summary
The chosen model, cutoff, test MAE, and test expected cost per 1,000 listings.

## 2. Decision and constraints
The review rule, the 2,500-listing latency budget, the 2 MB artifact limit, and
the two error costs.

## 3. Data and features
Rows, split sizes, seed, SHA-256, features, encoding, and the leakage audit.

## 4. Baselines and candidates
Validation table for the mean, no-shortlist, linear, ridge, and exploratory model.

## 5. Decision analysis
Cost versus cutoff table, chosen cutoff, confusion matrix, and cost arithmetic.

## 6. Operational check
Median latency for 2,500 listings, milliseconds per listing, artifact size, and
reload check.

## 7. Test result
One-time test metrics and a comparison with validation.

## 8. Limitations and fairness
Synthetic data, omitted variables, neighborhood as a proxy for protected
characteristics, and what the model must not be used for.

## 9. Reproduction
Exact commands, seeds, versions, and the files a reviewer needs.
```

## Model card headings

```markdown
# Model card - Cedarline valuation screen

## Intended use
## Out-of-scope use
## Training data and provenance
## Features and preprocessing
## Metrics and decision cutoff
## Error costs and expected performance
## Limitations and fairness risks
## Maintenance and retraining
```

## Rubric

The lab is scored out of 100 points. A component with no evidence scores zero,
regardless of effort.

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Technical correctness | 30 | Model runs from a clean clone, beats both baselines, meets the latency and size budgets, and the reload check passes | Model runs but misses a budget or has no baseline comparison |
| Evaluation and diagnosis | 25 | Cost-aware cutoff chosen on validation, test scored once, error counts and costs reconcile, failure modes discussed | Metrics reported but cutoff is arbitrary or test is reused for tuning |
| Reproducibility | 15 | Seed, hash, split indices, versions, commands, and timings let another student rebuild the result | Missing hash or commands; results cannot be rebuilt |
| Data and ethics | 15 | Leakage audit, CC0 provenance, fair-housing discussion, honest model card, no personal data | Weak or missing limitations; ignores proxy risk |
| Communication | 15 | Clear report and model card, readable tables, precise language, honest uncertainty | Disorganized or overclaims deployment readiness |

## Privacy and safety constraints

- The data is synthetic and carries no personal information. Do not add real
  listings, addresses, or seller details.
- `neighbourhood` can act as a proxy for protected characteristics in real
  housing data. Discuss this risk in the model card and state whether you would
  keep, transform, or drop the feature in a real deployment.
- Do not present the screen as an automated valuation or a lending decision. It
  prioritizes human review.
- Do not commit datasets, model binaries, credentials, or local absolute paths.
- Do not claim a production deployment, a real customer result, or a latency
  figure from a machine you did not measure.

## Self-check before submission

- [ ] The CSV hash, seed, split sizes, and package versions are recorded.
- [ ] Train, validation, and test rows are disjoint, and test was scored once.
- [ ] The feature matrix contains no target or post-sale column.
- [ ] Both baselines are reported and the chosen model beats them.
- [ ] The cutoff was selected on validation and its expected cost reconciles with
      the confusion matrix.
- [ ] Median latency for 2,500 listings is under 2.0 s, with the CPU named.
- [ ] The serialized artifact is under 2 MB and reproduces identical predictions
      after reload.
- [ ] The model card contains all eight headings and at least three limitations.
- [ ] No personal data, secrets, or generated data files are in the submission.

Next: use the [assessment page](assessment.md) to score your evidence and write
the reflection.

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)
