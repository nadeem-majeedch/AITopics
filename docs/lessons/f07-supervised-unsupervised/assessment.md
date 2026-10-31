# F07 assessment

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**

F07 uses the course's standard module weights. There is no proctored exam. You
check your own understanding, keep the evidence, and decide whether you are ready
for F08.

| Component | Weight | Evidence |
| --- | --- | --- |
| Knowledge check | 20% | Answers to the eight questions below |
| Guided notebook | 30% | Executed notebook, cluster plot, short interpretation |
| Independent lab | 40% | Segmentation memo, stability table, selection file |
| Reflection | 10% | 200-300 word reflection |

## Part A - Knowledge check (20%)

Answer before opening the answer. Name the mechanism, not just the term.

**1. How do you decide whether a question needs supervised or unsupervised learning? Give one example of each from the same customer table.**

??? note "Answer"
    Look for a target. If a column exists that you want to predict for new rows,
    the problem is supervised: for example, predicting `accepted_offer` from
    customer features. If no target exists and the goal is to discover structure,
    the problem is unsupervised: for example, grouping customers by spend, visits,
    age, and online share. The same table can support both, but the claims and the
    evaluation differ.

**2. The sweep reports silhouette 0.619 at `k=2`, 0.707 at `k=3`, 0.552 at `k=4`, 0.363 at `k=5`, and 0.246 at `k=6`. Which `k` do you choose, and why is the largest `k` not the answer?**

??? note "Answer"
    Choose `k=3`, the maximum silhouette. Larger `k` lowers the score because the
    clusters become less separated. Inertia would keep falling with larger `k`,
    which is why it cannot make the choice alone. A high silhouette is evidence of
    separation, not proof that three is the true number of segments; stability and
    purpose still need checking.

**3. Read the code. What does each argument control, and what happens if `random_state` is removed?**

```python
KMeans(n_clusters=3, n_init=10, random_state=42).fit(X)
```

??? note "Answer"
    `n_clusters=3` sets the number of centroids. `n_init=10` runs the algorithm
    from ten initializations and keeps the best inertia, reducing sensitivity to a
    poor start. `random_state=42` makes those initializations repeatable. Without
    it, the starting centroids can change between runs, so labels and sometimes
    the chosen partition change, which makes the report irreproducible.

**4. Why must the features be standardized before k-means, and what would happen if they were not?**

??? note "Answer"
    K-means uses distance. Unscaled annual spend varies over hundreds or thousands
    of units, while online share varies between 0 and 1 and visits per month is a
    small number. The distance would be dominated almost entirely by spend, so the
    other features would barely influence the clusters. Standardizing puts each
    feature on a mean-0, standard-deviation-1 scale so one standard deviation
    counts equally in every dimension.

**5. Calculation: the cluster sizes are 143, 110, and 167 out of 420. What share of the base does each hold, and what would a perfectly balanced three-cluster solution give?**

??? note "Answer"
    143 / 420 is about 34.0%, 110 / 420 is about 26.2%, and 167 / 420 is about
    39.8%. A perfectly balanced three-cluster solution would give 33.3% each. The
    largest cluster is about 6.5 percentage points above balance, which is a
    moderate imbalance, not a degenerate solution with one tiny cluster.

**6. PCA explains 93.8% of variance on the first component and 3.0% on the second. What does that tell you, and what does the 2D plot still hide?**

??? note "Answer"
    The two components together explain about 96.8% of the variance in the four
    standardized features, so the 2D plot preserves most of the variation. It still
    hides the remaining 3.2% spread across the other components, and it can make
    clusters look more separated than they are in the full feature space. Visual
    separation is not a substitute for silhouette, stability, or held-out
    evaluation.

**7. The clustering reaches ARI 1.0 and the classifier reaches accuracy 1.0. Are these the same result? Explain.**

??? note "Answer"
    No. ARI compares two partitions and is invariant to how clusters are numbered;
    1.0 means the discovered partition matches the withheld segment partition up to
    relabeling. Accuracy compares predicted labels with known labels and depends on
    label alignment and class balance. ARI answers "did we recover the same
    grouping?" Accuracy answers "did we assign the right label to each row?" The
    high values on both are expected because the synthetic groups are well
    separated.

**8. A manager says: "Cluster 2 has the highest spend, so raise prices for everyone in it." Give two reasons this conclusion does not follow from the clustering.**

??? note "Answer"
    First, a cluster is a description of a group of rows, not a causal model: high
    spend in the cluster does not mean members will tolerate a price increase, and
    the clustering did not test any pricing intervention. Second, acting on
    individual customers requires a validated predictive or experimental result,
    not a group mean; the segment may contain customers with very different price
    sensitivity. A responsible next step is a controlled test, reviewed for
    fairness and consent, not a blanket increase.

**Self-score:** 2.5 points per question, 20 points total. Full credit requires the
mechanism, calculation, or diagnostic step.

## Part B - Guided notebook (30%)

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Completeness | 10 | All six sections executed; figure saved |
| Correctness | 10 | Feature matrix `(420, 4)`, silhouette peak at `k=3`, sizes 143/110/167, ARI 1.0 |
| Interpretation | 10 | A short note explains why ARI 1.0 and accuracy 1.0 are expected and what neither proves |

Add a markdown cell stating your seed, package versions, the chosen `k`, and one
limitation of the synthetic data. Outputs without interpretation are incomplete.

## Part C - Independent lab (40%)

The lab is scored with the five-dimension rubric on the
[lab brief](lab.md#rubric): technical correctness 30, evaluation and diagnosis 25,
reproducibility 15, data and ethics 15, communication 15; the weights total 100. The lab score converts
to 40% of the F07 total.

Common reasons for losing marks:

- Using `latent_segment` as a clustering input.
- Choosing `k` from inertia or from the nicer-looking chart.
- Reporting one silhouette value without the five-seed variation.
- Skipping pairwise ARI, so stability is asserted rather than shown.
- Profiling only in z-scores, with no original-unit interpretation.
- Naming segments with judgments about customer worth.
- Mixing ARI and accuracy into a single "score".
- Recommending individual targeting or differential pricing.

## Part D - Reflection (10%)

Write 200-300 words in `reflection.md`. Answer all three prompts:

1. What changed in your reading of the three-segment solution once you saw the
   five-seed stability results?
2. The selection rule limited you to four segments for operational reasons. How
   did a business constraint change a statistical decision?
3. Where is the line between describing a segment and making a judgment about the
   people in it, and how will you keep on the right side of it?

Reflection is reasoning about evidence and limits, not a step log.

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
| 90-100 | Ready for F08; evidence is complete and reproducible |
| 75-89 | Ready, but strengthen the weakest rubric dimension |
| 60-74 | Rerun the notebook and revise the stability evidence |
| Below 60 | Repeat the module; focus on scaling, k selection, and ARI |

These bands support planning. They are not a university grade and do not confer
credit.

## Academic integrity and AI assistance

- You may use an AI assistant to explain a metric or review a segment description
  for judgmental language.
- You must run every experiment yourself and verify every number.
- Disclose substantive assistance in your reflection: what you asked, what you
  used, and what you checked independently.
- Do not submit a memo describing clusters you did not fit.

The full policy is in [Academic integrity](../../course/assessments.md#academic-integrity)
and [How to study](../../course/how-to-study.md#academic-integrity-and-ai-assistants).

## Completion checklist

- [ ] I answered all eight questions before opening the answers.
- [ ] My notebook ran from a clean kernel and saved the cluster plot.
- [ ] I can explain why inertia cannot choose `k`.
- [ ] My lab reports silhouette variation across five seeds.
- [ ] My lab reports pairwise ARI and applies the selection rule.
- [ ] My segment names describe behavior, not worth.
- [ ] My memo separates ARI from cross-validated accuracy.
- [ ] My reflection addresses all three prompts.
- [ ] I saved the package under `f07-customer-segments/` in my portfolio.

**Next:** [F08 - Regression and classification](../f08-regression-classification/index.md).
Bring one segment description from your memo and ask what a supervised model would
need in order to predict it for a new customer.

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**
