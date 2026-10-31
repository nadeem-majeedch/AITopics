# F06 assessment

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**

F06 uses the course's standard module weights. There is no proctored exam. You
check your own understanding, keep the evidence, and decide whether you are ready
for F07.

| Component | Weight | Evidence |
| --- | --- | --- |
| Knowledge check | 20% | Answers to the eight questions below |
| Guided notebook | 30% | Executed notebook, three figures, short interpretation |
| Independent lab | 40% | Market brief, quality log, group table, figures |
| Reflection | 10% | 200-300 word reflection |

## Part A - Knowledge check (20%)

Answer before opening the answer. Name the mechanism, not just the term.

**1. Why does EDA start with integrity checks before distributions and relationships?**

??? note "Answer"
    Because a shape, a correlation, or a group comparison computed on duplicated,
    mis-typed, or impossible rows describes a table that does not exist. Integrity
    checks establish the row count, types, missingness, duplicates, and plausible
    ranges first. If those are wrong, later summaries are misleading no matter how
    good the plot looks.

**2. Calculation: a column has Q1 = 250,000 and Q3 = 350,000. Apply the 1.5 x IQR rule. What are the bounds, and is a value of 520,000 flagged?**

??? note "Answer"
    IQR = 350,000 - 250,000 = 100,000. The lower bound is
    250,000 - 1.5 x 100,000 = 100,000. The upper bound is
    350,000 + 1.5 x 100,000 = 500,000. The value 520,000 is above the upper bound,
    so it is flagged. Flagged means "investigate", not "delete".

**3. Read the code. What does the output tell you, and why is the count column essential?**

```python
summary = (
    df.groupby("neighbourhood")["sale_price"]
      .agg(["count", "median", "mean"])
      .sort_values("median")
)
```

??? note "Answer"
    It produces one row per neighborhood with the number of sales, the median
    price, and the mean price, sorted from lowest to highest median. The count
    matters because a median from a small group is unstable and should not drive a
    recommendation. In the house table the smallest group has 103 rows, which is
    usable but still less stable than a group with 180. Without counts, a reader
    cannot judge how much weight the median deserves.

**4. The area-price correlation is 0.749. Interpret it, including what it does not prove.**

??? note "Answer"
    It is a strong positive linear association: houses with more area tend to sell
    for more. Squared, it is about 0.56, so a linear model using area alone
    accounts for roughly 56% of the variance in price. It does not prove that area
    causes price, it does not capture nonlinearity, and it can be inflated or
    hidden by group structure and outliers. The scatter plot must be inspected
    before acting on the number.

**5. Calculation: the median price is 337,716 in north and 297,218 in south. What is the absolute gap and the gap as a percentage of the south median?**

??? note "Answer"
    The absolute gap is 337,716 - 297,218 = 40,498 USD. As a percentage of the
    south median, 40,498 / 297,218 is about 0.136, or 13.6%. The gap describes this
    synthetic table. It is not evidence about a real housing market or about why
    prices differ.

**6. The IQR rule flags four rows and there are no negative prices. What do you do with the four rows, and why is deleting them a decision rather than a cleanup?**

??? note "Answer"
    Inspect them and classify each as impossible, rare but valid, or a unit error.
    Here two are unusually cheap and two unusually expensive, and all are valid
    sales. Deleting them changes the question from "what do houses sell for" to
    "what do typical houses sell for" and can change a group ranking. Keep them in
    the main analysis, report a sensitivity check without them, and state which
    question your recommendation answers.

**7. Which plot would you choose for each question, and why? (a) Is price skewed? (b) Does area predict price? (c) Do neighborhoods differ in median price?**

??? note "Answer"
    (a) A histogram or ECDF, because it shows the shape and tail of one numeric
    column. (b) A scatter plot, because it shows the relationship and reveals
    nonlinearity, clusters, and outliers that a correlation hides. (c) A box plot
    with a companion count table, because it compares median and spread across
    categories; the counts are needed to judge stability.

**8. Read the code. Why does no plot appear in the notebook, and where does the figure go?**

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.hist(df["sale_price"], bins=25)
fig.savefig("outputs/price_hist.png", bbox_inches="tight")
plt.close(fig)
```

??? note "Answer"
    `Agg` is a non-interactive backend: it renders to a file buffer instead of a
    screen or notebook output. The figure is written to
    `outputs/price_hist.png`, relative to the current working directory.
    `plt.close(fig)` releases the figure so memory does not grow across many
    plots. To see the plot, open the PNG file.

**Self-score:** 2.5 points per question, 20 points total. Full credit requires the
mechanism, the calculation, or the diagnostic step, not only the vocabulary.

## Part B - Guided notebook (30%)

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Completeness | 10 | All five sections executed; three figures saved |
| Correctness | 10 | Shape `(600, 7)`, correlation 0.749, four outliers, zero negative prices |
| Interpretation | 10 | Five observation-evidence-decision sentences, including one modeling implication |

Add a short markdown cell stating your matplotlib and pandas versions, the three
figure file names, and one thing the plots do not prove. Outputs without
interpretation are incomplete.

## Part C - Independent lab (40%)

The lab is scored with the five-dimension rubric on the
[lab brief](lab.md#rubric): technical correctness 30, evaluation and diagnosis 25,
reproducibility 15, data and ethics 15, communication 15; the weights total 100. The lab score converts
to 40% of the F06 total.

Common reasons for losing marks:

- Recommending a neighborhood without applying the eligibility rule.
- Using mean price instead of median price per square foot, or omitting the
  derived metric entirely.
- Deleting the four IQR-flagged rows without a sensitivity check.
- Reporting a correlation as a causal effect.
- A group table without counts or definitions.
- Figures with no units, no title, or no saved file.
- Inventing demographics or presenting synthetic medians as market advice.

## Part D - Reflection (10%)

Write 200-300 words in `reflection.md`. Answer all three prompts:

1. Which summary statistic in this module was most misleading before you plotted
   the data, and why?
2. The board's decision rule fixed the threshold and tie-break in advance. How did
   that constraint change the way you explored the table?
3. What will you check first the next time someone hands you a table and a
   conclusion?

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
| 90-100 | Ready for F07; evidence is complete and readable |
| 75-89 | Ready, but strengthen the weakest rubric dimension |
| 60-74 | Rerun the notebook and revise the brief's evidence |
| Below 60 | Repeat the module; practice integrity checks and group summaries |

These bands support planning. They are not a university grade and do not confer
credit.

## Academic integrity and AI assistance

- You may use an AI assistant to explain a plot or review a caption.
- You must compute every statistic yourself and verify it against the table.
- Disclose substantive assistance in your reflection: what you asked, what you
  used, and what you checked independently.
- Do not submit figures you did not generate or numbers you cannot trace to a
  cell.

The full policy is in [Academic integrity](../../course/assessments.md#academic-integrity)
and [How to study](../../course/how-to-study.md#academic-integrity-and-ai-assistants).

## Completion checklist

- [ ] I answered all eight questions before opening the answers.
- [ ] My notebook ran from a clean kernel and saved three figures.
- [ ] I can explain the 0.749 correlation and its limits.
- [ ] My lab applies the eligibility rule and the tie-break as written.
- [ ] My group table has counts, medians, and a documented derived metric.
- [ ] My sensitivity check reports whether the recommendation changed.
- [ ] My brief states that the data is synthetic and descriptive.
- [ ] My reflection addresses all three prompts.
- [ ] I saved the package under `f06-house-eda/` in my portfolio.

**Next:** [F07 - Supervised and unsupervised learning](../f07-supervised-unsupervised/index.md).
Bring one group difference from your brief that a clustering method might
rediscover without labels.

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**
