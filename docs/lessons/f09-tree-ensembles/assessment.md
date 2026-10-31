# F09 assessment

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**

F09 uses the course's standard module weights. There is no proctored exam. You
assess yourself against published criteria, keep the evidence, and decide whether
you are ready for F10.

| Component | Weight | Evidence |
| --- | --- | --- |
| Knowledge check | 20% | Answers to the eight questions below |
| Guided notebook | 30% | Executed notebook with outputs and notes |
| Independent lab | 40% | Cost-sensitive comparison and decision memo |
| Reflection | 10% | 200-300 word reflection |

## Part A - Knowledge check (20%)

Answer first, then open the answer to check.

**1. A node has 20 rows, 12 positive and 8 negative. Compute its Gini impurity. A
candidate split sends 10 rows (8 positive, 2 negative) left and 10 rows (4
positive, 6 negative) right. Compute the weighted child impurity and the gain.**

??? note "Answer"
    Parent: `p = 0.6`, Gini = `1 - (0.6^2 + 0.4^2)` = **0.48**.
    Left: `1 - (0.8^2 + 0.2^2)` = 0.32. Right: `1 - (0.4^2 + 0.6^2)` = 0.48.
    Weighted child impurity = `0.5 * 0.32 + 0.5 * 0.48` = **0.40**.
    Gain = `0.48 - 0.40` = **0.08**. The tree prefers the split with the largest
    gain, but the search is greedy and does not guarantee a globally optimal tree.

**2. The notebook reports depth 2 at 0.659 train / 0.656 test, depth 5 at 0.811 /
0.696, and unlimited depth at 1.000 / 0.664. Which model underfits, which overfits,
and which would you choose from this table alone?**

??? note "Answer"
    Depth 2 underfits: training and test scores are almost identical but low. The
    unlimited tree overfits: perfect training accuracy, a 0.336 gap, and a lower
    test score than depth 5. Depth 5 is the best of the three on test (0.696) with a
    moderate gap (0.115). From this table alone, choose depth 5, but confirm the
    choice on validation or cross-validation rather than a single test split.

**3. Compute the train-test gap for the three depths in Question 2. What does the
pattern tell you about variance?**

??? note "Answer"
    Depth 2: `0.659 - 0.656 = 0.003`. Depth 5: `0.811 - 0.696 = 0.115`. Unlimited:
    `1.000 - 0.664 = 0.336`. As depth grows, the model fits training rows more
    closely while test performance stops improving, which is the variance side of
    the bias-variance trade-off. A large gap is a warning, not proof: a model can
    overfit and still be the best available, so compare held-out scores as well.

**4. Explain the difference between bagging in a random forest and boosting in
gradient boosting. Which one is sequential?**

??? note "Answer"
    A random forest fits many trees independently on bootstrap samples with random
    feature subsets, then averages them; this mainly reduces variance. Gradient
    boosting fits trees sequentially, each one to the current errors or negative
    gradient, and adds them with a learning rate; this mainly reduces bias. Boosting
    is sequential because each tree depends on the ensemble built so far. A forest
    can be trained in parallel.

**5. Read this code. What is wrong with the cross-validation score, and how do you
fix it?**

```python
pre = ColumnTransformer([
    ("num", StandardScaler(), numeric),
    ("cat", OneHotEncoder(), categorical),
]).fit(X_train)

X_train_t = pre.transform(X_train)
scores = cross_val_score(LogisticRegression(), X_train_t, y_train, cv=cv)
```

??? note "Answer"
    The scaler and encoder are fitted once on all training rows before the folds are
    created. Inside each fold, the validation rows' scaling statistics and category
    levels have already influenced the transformation, so the score is optimistic.
    This is preprocessing leakage across folds. Fix it by putting the
    `ColumnTransformer` and the model in one `Pipeline` and passing the pipeline to
    `cross_val_score`, so each fold fits its own preprocessing.

**6. The random forest scores 0.76 on the single test split, 0.714 ± 0.033 under
five-fold CV. Logistic regression scores 0.742 ± 0.027 under the same CV. What do
you report, and what can you not claim?**

??? note "Answer"
    Report the CV table with mean and standard deviation: logistic 0.742 ± 0.027,
    forest 0.714 ± 0.033. The forest's single-split 0.76 was a favorable sample.
    The 0.028 CV difference is smaller than one standard deviation and the folds
    overlap, so you cannot claim logistic regression is definitively better; you can
    say it is at least as good on this table, and choose on cost, interpretability,
    and latency. A final held-out test is still needed before deployment.

**7. The forest ranks study hours 0.267, attendance 0.256, prior score 0.233, and
sleep 0.126. A colleague says "study hours cause passing." What is wrong with that
claim, and what would you do instead?**

??? note "Answer"
    Impurity importance measures how much a feature reduced impurity in this fitted
    forest; it is predictive, not causal. It is biased toward high-cardinality and
    correlated features, and one-hot categories split their credit across dummies.
    Study hours may be correlated with prior score, attendance, or motivation.
    Instead, use permutation importance on held-out data, inspect partial
    dependence, or run a controlled experiment before making a causal claim.

**8. An academic director says, "I must be able to explain every flag to an
advisor." The best CV model is a gradient boosting ensemble, 0.01 ahead of logistic
regression with overlapping folds. What do you recommend and why?**

??? note "Answer"
    Recommend logistic regression unless the ensemble shows a meaningful,
    reproducible gain in expected cost. A 0.01 difference within fold noise does not
    justify losing a directly explainable linear model. Logistic coefficients can be
    translated into per-feature contributions for an advisor, and the threshold and
    cost are easy to state. If the ensemble were clearly better, you would need a
    documented explanation method and a review of its failure cases before
    deployment.

**Self-score:** 2.5 points per question, 20 points total. Full credit requires the
mechanism or the arithmetic, not just the conclusion.

## Part B - Guided notebook (30%)

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Completeness | 10% | All six sections executed top to bottom; no skipped required cell |
| Correctness | 10% | Assertions pass; depth table and CV table match the expected ranges |
| Interpretation | 10% | A short note explaining the depth gap, the CV reversal, and one limitation |

Add three or four sentences under the final cell: why the unlimited tree is not
deployable, why the single-split ranking changed under CV, and what the feature
importances do not prove.

## Part C - Independent lab (40%)

The lab is scored with the five-dimension rubric on the
[lab brief](lab.md#rubric): technical correctness 30, evaluation and diagnosis 25,
reproducibility 15, data and ethics 15, and communication 15. That score out of
100 becomes 40% of the module total.

Common reasons for losing marks:

- Comparing models on different folds or different preprocessing.
- Choosing a threshold on the test set, or re-scoring after tuning.
- Ignoring the 24% capacity limit.
- Reporting accuracy as the primary metric when costs are 16:1.
- A memo that walks through the notebook instead of making a recommendation.
- Using `final_score` because it improves the numbers.

## Part D - Reflection (10%)

Write 200-300 words in `reflection.md`. Answer all three prompts:

1. Which result surprised you more: the unlimited tree's 1.000 training accuracy or
   the forest losing to logistic regression under CV? Why?
2. How did the cost ratio change the model or threshold you would recommend?
3. What will you check first in your next comparison so that one lucky split does
   not drive the conclusion?

Reflection is not a summary of the steps. It is your reasoning about evidence and
decisions.

## Scoring worksheet

| Component | Maximum | Your score | Notes |
| --- | --- | --- | --- |
| Knowledge check | 20 | | 2.5 points per question |
| Guided notebook | 30 | | 10 completeness, 10 correctness, 10 interpretation |
| Independent lab | 40 | | Lab rubric out of 100, scaled to 40 |
| Reflection | 10 | | All three prompts, specific evidence |
| **Total** | **100** | | |

| Score | Interpretation |
| --- | --- |
| 90-100 | Ready for F10; evidence is complete and reproducible |
| 75-89 | Ready, but fix the weakest rubric dimension first |
| 60-74 | Rerun the notebook and revise the memo |
| Below 60 | Repeat the module; the comparison protocol or leakage check is missing |

These bands are for your own planning. They are not a university grade and do not
confer credit.

## Academic integrity and AI assistance

- You may use an AI assistant to explain a tree concept, a scikit-learn argument,
  or an error message.
- You must run the comparison and verify every metric and cost yourself.
- Disclose substantive assistance in your reflection: what you asked, what you
  used, and how you checked it.
- Do not submit a memo that describes a comparison you did not run.

The full policy is in [Academic integrity](../../course/assessments.md#academic-integrity)
and [How to study](../../course/how-to-study.md#academic-integrity-and-ai-assistants).

## Completion checklist

- [ ] I answered all eight knowledge questions before opening the answers.
- [ ] My notebook ran from a clean kernel and contains outputs.
- [ ] I can explain the depth gap and the CV reversal without notes.
- [ ] My lab compares at least four models under one protocol.
- [ ] My metric choice is justified before the test result.
- [ ] My threshold respects the capacity limit and the cost arithmetic reconciles.
- [ ] My memo is decision-first and readable by a non-programmer.
- [ ] My reflection addresses all three prompts with specific evidence.
- [ ] I saved the package in my portfolio under `f09-classifier-comparison/`.

**Next:** [F10 - Metrics, overfitting, underfitting, data leakage, and cross-validation](../f10-metrics-validation/index.md).
Read the [M02 plan](../../syllabus/level-1-foundations.md#m02) for module-level
context.

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**
