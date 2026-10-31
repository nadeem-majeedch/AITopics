# F04 assessment

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**

F04 uses the course's standard module weights. There is no proctored exam. You
check your answers, score your evidence against published criteria, and decide
whether you are ready for F05.

| Component | Weight | Evidence |
| --- | --- | --- |
| Knowledge check | 20% | Answers to the eight questions below |
| Guided notebook | 30% | Executed notebook with `outputs/students_clean.csv` |
| Independent lab | 40% | Cleaning specification, ablation, threshold rule, and report |
| Reflection | 10% | 200-300 word reflection |

## Part A - Knowledge check (20%)

Answer each question in writing before opening the answer.

**1. Calculation: a raw table has 328 rows and 8 exact duplicates. After deduplication, complete-case analysis keeps 248 of the 320 rows. What share of the unique rows was dropped, and why is that loss not automatically harmless?**

??? note "Answer"
    Deduplication leaves `328 - 8 = 320` rows. Complete-case keeps 248, so
    `320 - 248 = 72` rows are dropped, which is `72 / 320 = 22.5%`. The loss is
    harmless only if the values are missing completely at random. If missingness is
    related to attendance or prior score, the 248 remaining rows are a biased
    sample, and the model learns from a group that differs systematically from the
    students who were excluded.

**2. Define MCAR, MAR, and MNAR, and give one consequence for each.**

??? note "Answer"
    **MCAR** (missing completely at random): the probability of missing does not
    depend on any value. Dropping rows is unbiased in expectation, at the cost of
    sample size. **MAR** (missing at random): missingness depends on other observed
    columns, not on the missing value itself. Imputation using those columns is
    defensible. **MNAR** (missing not at random): missingness depends on the
    unobserved value, such as students who skipped class also skipping the survey.
    No simple fix is safe, and the limitation must be reported.

**3. Code reading: `OneHotEncoder(handle_unknown="ignore")` was fit on `course` values `Math`, `Physics`, `CS`. A new batch contains `Biology`. What happens, and what would happen with the default `handle_unknown="error"`?**

??? note "Answer"
    With `"ignore"`, the row is transformed successfully and gets zeros in all
    course columns, so the model sees no course information for it. With the
    default `"error"`, `transform` raises `ValueError: Found unknown categories`,
    and the whole batch fails. The first behavior is required in production; the
    second is a useful failure during development, when an unexpected category
    usually means a data problem.

**4. Why must exact duplicates be removed before the train/test split?**

??? note "Answer"
    If two identical rows land on opposite sides of the split, the model can
    reproduce a test row it has already seen. The test score then measures
    memorization rather than generalization, and it is inflated. Removing
    duplicates first guarantees that no test row has a twin in training, which is
    also the concern that F05 addresses for groups and time.

**5. Code reading: the transformed matrix is `(320, 9)`. The table has 4 numeric columns, `course` with 3 levels, and `tutoring` with 2 levels. Show the arithmetic, and state the shape if a fourth course level `Unknown` appears.**

??? note "Answer"
    One-hot encoding replaces each categorical column with one binary column per
    level, so the width is `4 + 3 + 2 = 9`. If `Unknown` becomes a fourth course
    level, the width becomes `4 + 4 + 2 = 10`, and the shape is `(320, 10)`. Any
    change in category cardinality changes `p`, which is why the report must
    explain the count rather than quote it.

**6. Why does imputing before `cross_val_score` inflate the score, even though imputation never looks at the label?**

??? note "Answer"
    Imputation learns a statistic, such as the median, from the data it is fit on.
    If it is fit on all rows, the training fold's filled values already contain
    information about the validation rows. That is leakage of feature information,
    not label information, and it still makes the validation score optimistic.
    Keeping the imputer inside the pipeline makes each fold fit its own statistic.

**7. Calculation: a column has 79 missing cells spread over 72 incomplete rows. What does the difference between those two numbers tell you, and how many complete rows remain in a 320-row table?**

??? note "Answer"
    The gap means some rows have more than one missing field: if every incomplete
    row had exactly one, the count would be 72 cells, not 79. At least seven rows
    carry two or more missing values. Complete rows are `320 - 72 = 248`, which is
    `77.5%` of the table. A per-cell missingness summary therefore hides how much
    of the table is affected row-wise.

**8. Calculation: a column contains `[1, 2, 3, 4, 1000]`. Compute the mean and the median, and say which you would use to impute and why.**

??? note "Answer"
    The mean is `(1 + 2 + 3 + 4 + 1000) / 5 = 1010 / 5 = 202`. The median is `3`,
    the middle of the sorted values. Use the median: one extreme value moves the
    mean by 200 units and would produce an imputed value that no real observation
    resembles. The mean is acceptable when the column is roughly symmetric and has
    no extreme values, which you should check rather than assume.

**Self-score:** 2.5 points per question, 20 points total. Award full credit only
when the answer includes the mechanism, the arithmetic, or the diagnostic step.

## Part B - Guided notebook (30%)

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Completeness | 10% | All five sections plus the decision table reviewed; no required cell skipped |
| Correctness | 10% | `(328, 7)` and `(320, 9)` assertions pass; 320 rows and 248 complete rows reported |
| Interpretation | 10% | A short markdown note stating your scikit-learn version, which strategy you would choose, and one limitation |

A saved notebook without interpretation is incomplete. The limitation can be one
sentence, for example: "the missing values were injected at random, so this run
cannot show how the strategies differ when missingness is informative."

## Part C - Independent lab (40%)

The lab is scored with the five-dimension rubric on the
[lab brief](lab.md#rubric).

| Dimension | Points | What earns full marks |
| --- | --- | --- |
| Technical correctness | 30 | Specification applied in order; count, value-set, and shape assertions pass; ablation uses one fold object |
| Evaluation and diagnosis | 25 | Each decision has a measured effect; the cutoff follows from the 120-student capacity; missed students are named |
| Reproducibility | 15 | Seed, hash, versions, and commands reproduce all four CSVs |
| Data and ethics | 15 | Aggregate-only outputs, no outcome leakage, group sizes reported, synthetic limits stated |
| Communication | 15 | Decision-first report whose sections agree with each other |
| **Total** | **100** | Converted to 40% of the module score |

Common reasons for losing marks:

- A specification written after the code, listing steps rather than decisions.
- An ablation table where the four variants use different folds or row sets.
- Reporting `0.79` without the row count behind it.
- A threshold of `0.5` that flags 40 or 250 students against a capacity of 120.
- A per-student flag file included "for transparency."
- A group table without group sizes, or a 20-row group compared with a 300-row
  group.

## Part D - Reflection (10%)

Write 200-300 words in `reflection.md`. Answer all three prompts:

1. Which cleaning decision in your lab had the largest measured effect, and did
   that match what you expected before running it?
2. The 95% row floor forced imputation. What would you tell the director if the
   missing values were concentrated among students with low attendance?
3. What will you write in a data preparation note so that a reviewer can disagree
   with a decision without having to reverse-engineer your code?

Reflection is about reasoning and trade-offs, not a summary of steps.

## Scoring worksheet

| Component | Maximum | Your score | Notes |
| --- | --- | --- | --- |
| Knowledge check | 20 | | |
| Guided notebook | 30 | | |
| Independent lab | 40 | | |
| Reflection | 10 | | |
| **Total** | **100** | | |

| Score | Interpretation |
| --- | --- |
| 90-100 | Ready for F05; your cleaning decisions are measured and documented |
| 75-89 | Ready, but tighten the weakest dimension, usually the ablation or ethics |
| 60-74 | Rerun the notebook and rewrite the specification before the code |
| Below 60 | Rebuild sections 1-3 of the notebook, then retry the lab on the notebook's own table |

These bands are self-study guidance. They are not a university grade and do not
confer credit.

## Academic integrity and AI assistance

- You may use an AI assistant to explain a scikit-learn parameter or a warning.
- You must run the generator, the cleaning, and the ablation yourself; submitted
  CSV files must come from your run.
- Disclose substantive assistance in your reflection: what you asked, what you
  used, and what you verified independently.
- Do not submit a specification written after the results, and do not invent an
  ablation row.

The course policy is in [Academic integrity](../../course/assessments.md#academic-integrity)
and [How to study](../../course/how-to-study.md#academic-integrity-and-ai-assistants).

## Completion checklist

- [ ] I answered all eight knowledge questions before opening the answers.
- [ ] My notebook ran from a clean kernel and saved `outputs/students_clean.csv`.
- [ ] I can account for 328, 320, and 248 without looking at the notebook.
- [ ] My lab kept at least 95% of unique rows and says so with a number.
- [ ] My ablation used identical folds and reports standard deviations.
- [ ] My cutoff flags no more than 120 students and names who is missed.
- [ ] My lab contains no per-student output.
- [ ] My reflection addresses all three prompts and discloses AI assistance.
- [ ] I saved the package in my portfolio under `f04-student-cleaning/`.

**Next:** [F05 - Train, validation, and test splits](../f05-splits/index.md). The
[M02 plan](../../syllabus/level-1-foundations.md#m02) and
[M05 plan](../../syllabus/level-1-foundations.md#m05) show how cleaning connects to
dataset preparation.

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**
