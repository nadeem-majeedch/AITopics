# F10 lab - An overfitting investigation with a recommendation

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Weight** | 40% of the F10 assessment |
| **Time** | About 3 hours |
| **Hardware** | CPU-only |
| **Starter file** | `labs/foundations/f10_overfitting_lab.md` in the repository |
| **Prerequisite** | A completed run of the [guided notebook](notebook.md) |

## The scenario

**Harborline Realty** wants to run a direct-mail campaign for premium homes. The
marketing team has a fixed budget and a simple rule: contact the owner of a listing
when the model predicts the home will sell for **350,000 USD or more**. A correct
premium contact is worth about **900 USD** in expected commission. A contact sent
for a non-premium home wastes about **150 USD** in mailer and staff time.

The team has 600 historical listings with `sale_price` and listing-time features.
Your job is to run a **controlled complexity sweep**, decide how complex the model
should be, and recommend one model and one decision threshold in a written memo.
The memo will be read by a marketing lead who will not open your notebook.

This is not the notebook again. The notebook studies a student target with one
tree sweep. This lab uses a different dataset, a different target, a new feature
set with an engineered ratio, two model families, a cost-sensitive decision, and a
written recommendation.

## Why it matters

Overfitting is easy to see in a textbook curve and easy to miss in a project. A
deep tree with perfect training accuracy looks like progress in a notebook. The
lab forces you to compare complexity under one protocol, quantify the gap, choose
on validation data, and explain the trade-off to someone who cares about mailing
costs, not Gini impurity.

## Constraints

| Constraint | Value |
| --- | --- |
| Data | `datasets/foundations/generated/house_prices.csv`, 600 rows, seed 42 |
| Target | `premium = sale_price >= 350000` |
| Features | `area_sqft`, `bedrooms`, `age_years`, `distance_km`, `garage`, `area_per_bedroom`, and one-hot `neighbourhood` |
| Forbidden feature | `sale_price` |
| Split | 60% train, 20% validation, 20% test, stratified by `premium`, fixed seed |
| Complexity sweep | Decision tree depth 1-20; random forest `min_samples_leaf` at 1, 2, 5, 10, 25, 50 |
| Cost of a missed premium home | 900 USD |
| Cost of an unnecessary contact | 150 USD |
| Deliverable | A memo with a model and threshold recommendation |

Generate the data with `python scripts/make_foundation_data.py` if needed, and
record the SHA-256 of `house_prices.csv` from the manifest. The
[dataset card](../../technical/foundation-assets.md#foundation-datasets) states the CC0 license and
the warning that the table is synthetic, not a real housing market.

## Required steps

### Step 1 - Provenance

Load the CSV with pandas. Assert 600 rows and 7 columns. Record the seed, hash,
Python version, pandas version, and scikit-learn version. State that the data is
synthetic and that the 350,000 cutoff is a business rule, not a natural boundary.

### Step 2 - Define the target

Create `premium` from `sale_price >= 350000`. Report the positive rate and the
majority-class accuracy. Explain in two sentences why the cutoff could reasonably
be 325,000 or 375,000, and why that choice changes the problem.

### Step 3 - Build the feature set

Use the five original numeric features, plus `area_per_bedroom = area_sqft /
bedrooms`, plus one-hot encoded `neighbourhood`. Fit the encoder on the training
rows after the split in Step 4. Drop `sale_price`. Confirm that every remaining
feature is available when the listing arrives.

**Validation check 1 - no target leakage.** Assert that `sale_price` and `premium`
are absent from the feature columns, and that `area_per_bedroom` uses only
listing-time inputs.

### Step 4 - Split and freeze

Split 60/20/20 with `stratify=premium` and a fixed `random_state`. Fit the
one-hot encoder on the training rows, then transform validation and test. Assert
the sizes are 360/120/120 and that the positive rate in each split is within 0.03
of the full rate. Save the index arrays. Do not touch the test rows until Step 8.
Print the correlation of each numeric feature with `premium` on the training rows
as a sanity check.

**Validation check 2 - split integrity.** Assert the three index sets are
disjoint, the sizes match, and the prevalence condition holds.

### Step 5 - Baselines with costs

Compute the expected cost of two constant rules on the validation rows:

- **Contact nobody:** every premium home is a false negative.
- **Contact everybody:** every non-premium home is a false positive.

Use `expected cost = 900 * FN + 150 * FP` and report cost per 1,000 listings. Fit a
logistic regression pipeline as a learned baseline. Report accuracy, precision,
recall, and PR-AUC.

### Step 6 - Sweep tree depth

Fit decision trees at depths 1 through 20 on the training rows. For each depth,
record training accuracy, validation accuracy, validation PR-AUC, and the gap
between training and validation accuracy. Plot depth on the x-axis and both
accuracies on the y-axis.

Identify the depth with the best validation score and the depth where the gap
becomes large. Do not choose a depth because its training accuracy is highest.

**Validation check 3 - sweep sanity.** Assert that the depth-20 training accuracy
is at least the depth-1 training accuracy, and that the depth-20 gap is larger
than the depth-1 gap. A sweep that violates this is not measuring complexity.

### Step 7 - Sweep forest leaf size

Fix `n_estimators=300` and `random_state` to the seed. Fit random forests with
`min_samples_leaf` in 1, 2, 5, 10, 25, and 50 on the same training rows. Record
training accuracy, validation accuracy, validation PR-AUC, and the gap. Explain the
pattern in two or three sentences: small leaves fit noise, large leaves underfit.

### Step 8 - Choose a model and threshold

Shortlist the best tree and the best forest from validation results. For each,
sweep the predicted-probability threshold from 0.05 to 0.95. For every threshold,
compute the confusion matrix, precision, recall, and expected cost per 1,000
listings. Choose the model and threshold with the lowest validation cost. Report
the cost at the default 0.5 for comparison.

**Validation check 4 - cost arithmetic.** Recompute the chosen expected cost from
the four confusion-matrix counts in a separate cell or by hand. It must match the
reported number.

### Step 9 - Test once

Freeze preprocessing, model, and threshold. Score the 120 test rows once. Report
accuracy, precision, recall, PR-AUC, the confusion matrix, and expected cost per
1,000 listings. Compare with validation and with both constant baselines. If the
test cost is higher, report it and discuss why.

**Validation check 5 - test discipline.** Store `"test_scored": true` with a
timestamp in `metrics.json`, and state in the memo that the test set was used once.

### Step 10 - Write the memo

Use the headings below. Recommend one model and one threshold. Reject at least one
alternative with evidence. State the cost assumptions, the uncertainty, and the
conditions under which your recommendation would change.

## Deliverables

```text
f10-overfitting/
  README.md
  f10_overfitting.ipynb
  outputs/
    complexity_sweep.csv
    metrics.json
    complexity_curve.png
  recommendation_memo.md
  reflection.md
```

Do not commit the generated CSV, the virtual environment, or `outputs/`. Copy the
files you need into a submission folder outside the repository.

## Memo template

```markdown
# Harborline premium-listing recommendation

## 1. Recommendation
The model, threshold, validation cost, and test cost, in five sentences or fewer.

## 2. Decision and costs
Who is contacted, the 900/150 cost ratio, and the 350,000 cutoff.

## 3. Data and features
Rows, split sizes, seed, SHA-256, engineered feature, and leakage audit.

## 4. Protocol
The complexity sweeps, the validation split, and why training accuracy is not the
selection metric.

## 5. Results
The depth table, the leaf-size table, and the chosen model.

## 6. Threshold and expected cost
The sweep, the chosen threshold, and the cost arithmetic.

## 7. Test result
One-time test metrics and a comparison with validation and the baselines.

## 8. Limitations and fairness
Synthetic data, arbitrary premium cutoff, neighborhood proxies, and campaign risks.

## 9. What would change my recommendation
The evidence or cost change that would reverse the choice.
```

## Rubric

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Technical correctness | 30 | Sweeps are controlled; models run from a clean clone; the chosen model beats the baselines; arithmetic is correct | Sweeps mix protocols or the model does not run end to end |
| Evaluation and diagnosis | 25 | Gap and PR-AUC interpreted correctly; threshold chosen on validation; test scored once; alternatives rejected with evidence | Curves plotted but not interpreted; threshold chosen by habit |
| Reproducibility | 15 | Seed, hash, split indices, versions, and commands reproduce the sweep and test result | Missing key settings or commands |
| Data and ethics | 15 | Leakage audit, CC0 provenance, cutoff sensitivity, fairness discussion | Weak limitations; ignores proxy risk or campaign harm |
| Communication | 15 | Memo is decision-first, readable by a marketing lead, and honest about uncertainty | Memo is a notebook walkthrough with no recommendation |

A component with no evidence scores zero.

## Privacy and safety constraints

- The data is synthetic. Do not add real addresses, owners, or sale records.
- The 350,000 cutoff is a campaign rule. Do not describe it as a market fact or a
  property valuation.
- `neighbourhood` can proxy for protected characteristics. Discuss whether using it
  for marketing is acceptable, and what you would do in a real deployment.
- Do not claim that the model causes sales or that the campaign will pay for
  itself. The lab evaluates prediction cost, not campaign lift.
- Do not commit datasets, credentials, absolute paths, or generated figures that
  embed personal information.

## Self-check before submission

- [ ] The hash, seed, split sizes, and package versions are recorded.
- [ ] `sale_price` is absent from the feature matrix.
- [ ] The depth and leaf-size sweeps use the same training and validation rows.
- [ ] The selected model is chosen on validation, not training or test.
- [ ] The expected cost reconciles with the confusion matrix.
- [ ] The test set was scored once, and the flag is recorded.
- [ ] The memo rejects at least one alternative with evidence.
- [ ] The memo contains all nine headings and a clear recommendation.
- [ ] Fairness and cutoff sensitivity are discussed.
- [ ] No generated data, secrets, or personal paths are in the submission.

Next: use the [assessment page](assessment.md) to score your evidence and write
the reflection.

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)
