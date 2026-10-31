# F05 assessment

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**

F05 uses the course's standard module weights. There is no proctored exam. You
check your own understanding, keep the evidence, and decide whether you are ready
for F06.

| Component | Weight | Evidence |
| --- | --- | --- |
| Knowledge check | 20% | Answers to the eight questions below |
| Guided notebook | 30% | Executed notebook with outputs and a short interpretation |
| Independent lab | 40% | Leakage audit report, manifest, and memo |
| Reflection | 10% | 200-300 word reflection |

## Part A - Knowledge check (20%)

Answer in your own words before opening the answer. A correct mechanism is worth
more than a memorized sentence.

**1. What is the difference between the validation set and the test set, and why does the test set get only one look?**

??? note "Answer"
    The validation set is used repeatedly to compare models, features, and
    thresholds. The test set is used once, after all choices are fixed, to
    estimate generalization to unseen rows. Every look at the test set feeds
    information back into your decisions, which turns it into a second validation
    set and makes the final estimate optimistic.

**2. Read the code below. How many rows end up in each set for a 600-row table, and why is the second `test_size` 0.25 rather than 0.20?**

```python
train_val, test = train_test_split(houses, test_size=0.20, random_state=42)
train, validation = train_test_split(train_val, test_size=0.25, random_state=42)
```

??? note "Answer"
    The first call holds out 20% of 600, which is 120 test rows and leaves 480.
    The second call takes 25% of the remaining 480, which is 120 validation rows.
    The training set is the other 360 rows. The second fraction is 0.25 because
    it applies to the already-reduced table: 0.25 x 0.80 = 0.20 of the original
    data. The result is 360/120/120, or 60/20/20.

**3. Calculation: you have 1,000 rows and want a 70/15/15 split. Then you find 40 duplicate pairs (80 rows) and deduplicate to 960 rows. How many rows are in each set before and after deduplication?**

??? note "Answer"
    Before: 700 training, 150 validation, 150 test. After deduplication the table
    has 960 rows: 960 x 0.70 = 672 training, 960 x 0.15 = 144 validation, and 144
    test. If the counts do not add to 960, rounding or an accidental filter has
    changed the table.

**4. In the notebook, fitting the scaler on all rows and fitting it on training rows both produce an R-squared of 0.7976. Does that mean the first approach is acceptable? Explain.**

??? note "Answer"
    No. Fitting the scaler on all rows lets the training process see the mean and
    variance of the test data, which is information it would not have at
    deployment. The measured effect is nearly zero because this table is large,
    clean, and similarly distributed across rows. The defect is procedural and
    would matter more with a small table, a skewed feature, or a transformation
    that learns more than two statistics. Correctness is judged by the procedure,
    not by whether today's number moved.

**5. A model reaches R-squared 1.000 when `price_vs_city_mean` is included and 0.703 without it. What is the feature, and what should you conclude?**

??? note "Answer"
    The feature is the sale price minus the mean sale price of the whole table, so
    it is a deterministic function of the target. A linear model can recover the
    target from it almost exactly. The 1.000 is leakage, not skill. The 0.703
    model is the credible baseline. Any feature computed from the target or from
    the full table, including the current row, must be removed or rebuilt from
    training data only.

**6. You use `GroupShuffleSplit` with `neighbourhood` as the group. Training ends up with east, south, and west; test has only north. What does this estimate tell you, and what does it not tell you?**

??? note "Answer"
    It estimates performance on neighborhoods the model has never seen, which is
    the right question if deployment includes new locations. It does not estimate
    performance on east, south, or west, and it cannot tell you how the model
    behaves on a neighborhood whose price level is outside the training range.
    The estimate is also based on one small group, so it is noisy.

**7. The notebook finds 11 cross-split duplicate matches before deduplication and 0 after. How would you detect the same problem in a table that has no obvious duplicate column?**

??? note "Answer"
    Build a content fingerprint: normalize text columns, select the columns that
    should identify a record, and hash them. Rows with the same hash are exact
    duplicates after normalization. For near-duplicates, compare a stable
    identifier such as patient ID, listing ID, or building address, and group by
    it before splitting. Inspect the largest hash groups manually before deciding
    whether to drop or group them.

**8. A teammate evaluates the same model on the test set after every feature change and keeps the feature set with the best test score. What has gone wrong, and how would you fix the workflow?**

??? note "Answer"
    The test set has become a validation set, so the final score is optimistic and
    no longer estimates performance on unseen data. Fix it by doing all
    comparisons on the validation set or with cross-validation on training data,
    freezing the model and threshold, and evaluating the test set once. Record how
    many times the test set was touched; the answer should be one.

**Self-score:** 2.5 points per question, 20 points total. Award full credit only
when the answer names the mechanism or the diagnostic step, not only the term.

## Part B - Guided notebook (30%)

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Completeness | 10 | All seven sections executed top to bottom; no skipped cell |
| Correctness | 10 | Assertions pass; counts are 360/120/120, overlap is empty, duplicates go 11 to 0 |
| Interpretation | 10 | A short note explains the 1.000 versus 0.703 result and why 0.7976 versus 0.7976 is still a defect |

Add a markdown cell at the end of the notebook stating your Python and
scikit-learn versions, your seed, and one limitation of the demonstration. A
notebook with outputs but no interpretation is incomplete.

## Part C - Independent lab (40%)

The lab is scored with the five-dimension rubric on the
[lab brief](lab.md#rubric): technical correctness 30, evaluation and diagnosis 25,
reproducibility 15, data and ethics 15, communication 15; the weights total 100. The lab score converts
to 40% of the F05 total.

Common reasons for losing marks:

- Reproducing the inherited accuracy without identifying why it is meaningless.
- Listing leaks without measuring the effect of removing them.
- Leaving `final_score` in the feature matrix while claiming a clean model.
- Selecting a threshold on the test set.
- Reporting a held-out-course result without its sample size or uncertainty.
- A manifest without a seed, feature list, or data hash.
- A memo that recommends deployment without stating what the model must not be
  used for.

## Part D - Reflection (10%)

Write 200-300 words in `reflection.md`. Answer all three prompts:

1. Which leak was hardest to see before you measured it, and what made it
   visible?
2. The scaler leak changed nothing measurable in the notebook. How do you decide
   when a procedural defect still matters?
3. What will you record in every future evaluation so that a reviewer can tell
   whether the test set was touched more than once?

Reflection is not a summary of steps. It is your reasoning about evidence,
limits, and what you will change next time.

## Scoring worksheet

| Component | Maximum | Your score | Notes |
| --- | --- | --- | --- |
| Knowledge check | 20 | | |
| Guided notebook | 30 | | |
| Independent lab | 40 | | |
| Reflection | 10 | | |
| **Total** | **100** | | |

Self-study scale:

| Score | Interpretation |
| --- | --- |
| 90-100 | Ready for F06; evidence is complete and reproducible |
| 75-89 | Ready, but fix the weakest rubric dimension first |
| 60-74 | Rerun the notebook and strengthen the lab evidence |
| Below 60 | Repeat the module; focus on the split design before modeling |

These bands support your own planning. They are not a university grade and do not
confer credit.

## Academic integrity and AI assistance

- You may use an AI assistant to explain an error, review a leak inventory, or
  suggest a diagnostic step.
- You must run every command yourself and verify every number in your report.
- Disclose substantive assistance in your reflection: what you asked, what you
  used, and what you checked independently.
- Do not submit an audit of a dataset you did not load or metrics you did not
  compute.

The full policy is in [Academic integrity](../../course/assessments.md#academic-integrity)
and [How to study](../../course/how-to-study.md#academic-integrity-and-ai-assistants).

## Completion checklist

- [ ] I answered all eight questions before opening the answers.
- [ ] My notebook ran from a clean kernel and contains outputs.
- [ ] I can explain the 1.000 versus 0.703 result without notes.
- [ ] My lab quantifies at least three leaks with before/after metrics.
- [ ] My split manifest contains seed, counts, groups, features, and hash.
- [ ] My memo states what the model must not be used for.
- [ ] My reflection addresses all three prompts.
- [ ] I saved the package under `f05-leakage-audit/` in my portfolio.

**Next:** [F06 - Exploratory data analysis and visualization](../f06-eda/index.md).
Read the lesson, run the notebook, and bring one observation from your F05 audit
that a plot would have made easier to see.

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**
