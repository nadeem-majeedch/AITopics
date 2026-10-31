# F03 assessment

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**

F03 uses the course's standard module weights. There is no proctored exam. You
check your answers, score your evidence against published criteria, and decide
whether you are ready for F04.

| Component | Weight | Evidence |
| --- | --- | --- |
| Knowledge check | 20% | Answers to the eight questions below |
| Guided notebook | 30% | Executed notebook with `outputs/students.csv` |
| Independent lab | 40% | Audit table, group summary, and verdict report |
| Reflection | 10% | 200-300 word reflection |

## Part A - Knowledge check (20%)

Answer each question in writing before opening the answer.

**1. A table has shape `(400, 9)`. What do the two numbers mean, and why check `dtypes` before doing any arithmetic?**

??? note "Answer"
    `400` is the number of rows (observations) and `9` the number of columns
    (variables). `dtypes` tells you whether each column is numeric or text. A
    numeric-looking column stored as text (`"83.2"`) will fail arithmetic or
    concatenate instead of adding, so the failure appears far from its cause if
    you skip the check.

**2. Calculation: a boolean mask over 400 rows sums to 198. What is `mask.mean()`, and what is the accuracy of a model that always predicts the majority class?**

??? note "Answer"
    `mask.mean()` is `198 / 400 = 0.495`, the proportion of `True`. The majority
    class is `False` at `1 - 0.495 = 0.505`, so an always-predict-the-majority
    model scores `0.505`. That is the baseline any classifier must beat; on a
    balanced target it is close to `0.5`, which is why accuracy alone can look
    flattering.

**3. Code reading: `X` has shape `(400, 4)`. What are the shapes and meanings of `X.mean(axis=0)` and `X.mean(axis=1)`?**

??? note "Answer"
    `X.mean(axis=0)` has shape `(4,)`: one mean per column, collapsing the 400
    rows. `X.mean(axis=1)` has shape `(400,)`: one mean per row, collapsing the 4
    columns. Standardization uses `axis=0`. Using `axis=1` by mistake produces a
    per-row average that looks plausible and scales nothing.

**4. Why pass `validate="many_to_one"` to `merge`, and what is a row explosion?**

??? note "Answer"
    It declares that the right table has at most one row per key. If the data
    violates that, pandas raises instead of silently duplicating left rows. A row
    explosion happens when both sides have duplicate keys, so a 400-row table
    joined to a catalog with a duplicated course becomes 800 rows. Every
    downstream count is then wrong, and the error is easy to miss because the
    merge "succeeded".

**5. After `df = df.sort_values("final_score", ascending=False)`, why can `df.loc[0]` and `df.iloc[0]` return different students?**

??? note "Answer"
    `loc` selects by index label, and label `0` still belongs to the student who
    was first before sorting. `iloc` selects by position, so position `0` is now
    the highest-scoring student. The two agree only when the index happens to be
    in sorted order.

**6. Calculation: a column has mean `70` and standard deviation `10`. What is the z-score of a value of `85`, and what does it mean?**

??? note "Answer"
    `z = (85 - 70) / 10 = 1.5`. The value is one and a half standard deviations
    above the column mean. Because z-scores are unitless, a z-score of `1.5` in
    `attendance` and in `prior_score` represent the same relative position, which
    is what lets a model compare coefficients across columns.

**7. NumPy reports a standardized column's standard deviation as `1.0`, but pandas' `.std()` reports about `1.00125`. Is one of them wrong?**

??? note "Answer"
    Neither is wrong. NumPy's `std()` divides by `n` (`ddof=0`, population
    standard deviation); pandas' `.std()` divides by `n - 1` (`ddof=1`, sample
    standard deviation). For `n = 400` the ratio is
    `sqrt(400 / 399) = 1.00125`. Pick one convention, state it, and verify with the
    same function you used to scale.

**8. You saved a table with `to_csv(path)` and the reloaded file has 10 columns instead of 9. What happened, and what else should you verify after a round trip?**

??? note "Answer"
    The default writes the row index as an unnamed column, which reappears as
    `Unnamed: 0`. Use `index=False`. After any round trip, verify the shape, at
    least one known value, and the dtypes you depend on, because CSV stores text
    and pandas re-infers types on read.

**Self-score:** 2.5 points per question, 20 points total. Award full credit only
when the answer includes the mechanism or the arithmetic.

## Part B - Guided notebook (30%)

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Completeness | 10% | All eight sections ran top to bottom; no required cell skipped |
| Correctness | 10% | `(400, 9)`, `(400, 11)`, and `(400, 4)` assertions pass; CSV reloads at `(400, 9)` |
| Interpretation | 10% | A short markdown note stating your pandas version, the pass rate you observed, and one limit of the table |

A saved notebook without interpretation is incomplete. The limit can be one
sentence, for example: "the table is synthetic and the relationships are additive
by construction, so it cannot show whether these features matter for real
students."

## Part C - Independent lab (40%)

The lab is scored with the five-dimension rubric on the
[lab brief](lab.md#rubric).

| Dimension | Points | What earns full marks |
| --- | --- | --- |
| Technical correctness | 30 | Eight-row audit with accurate statistics; duplicate, shape, and merge assertions pass; summaries carry counts |
| Evaluation and diagnosis | 25 | Verdict follows from named findings; leakage, clipping, and the missing key are explained with consequences |
| Reproducibility | 15 | Seed, SHA-256, commands, and a clean rerun reproduce both CSVs |
| Data and ethics | 15 | No individual scoring, small groups flagged, provenance stated, no causal claims |
| Communication | 15 | Verdict first; every number traceable to an artifact |
| **Total** | **100** | Converted to 40% of the module score |

Common reasons for losing marks:

- An audit table that copies `df.describe()` and omits missing counts or unique
  counts.
- Reporting a group mean without the group size.
- A verdict of "fit" while the report also lists a target-derived feature.
- A merge check that only prints the shape without asserting it.
- A hash that does not match the file because the generator was rerun with a
  different seed.
- Language such as "students who study more pass more, so studying works."

## Part D - Reflection (10%)

Write 200-300 words in `reflection.md`. Answer all three prompts:

1. Which audit finding would have been hardest to notice by reading the CSV in a
   spreadsheet, and why?
2. The table has no student identifier. What would you ask the coordinator for,
   and what would that unlock?
3. What is one rule you will apply to every table before modeling, and what
   failure does it prevent?

Reflection is about reasoning, not a summary of commands.

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
| 90-100 | Ready for F04; your audit is reproducible and your verdict is defended |
| 75-89 | Ready, but tighten the weakest dimension, often reproducibility |
| 60-74 | Rerun the notebook and redo the audit table with all seven fields |
| Below 60 | Rebuild sections 1-5 of the notebook before attempting the lab again |

These bands are self-study guidance. They are not a university grade and do not
confer credit.

## Academic integrity and AI assistance

- You may use an AI assistant to explain an API, a warning, or a statistic.
- You must run the generator, the audit, and the checks yourself; the submitted
  CSVs must come from your run.
- Disclose substantive assistance in your reflection: what you asked, what you
  used, and what you verified independently.
- Do not submit an audit of a table you did not generate, and do not invent a
  SHA-256.

The course policy is in [Academic integrity](../../course/assessments.md#academic-integrity)
and [How to study](../../course/how-to-study.md#academic-integrity-and-ai-assistants).

## Completion checklist

- [ ] I answered all eight knowledge questions before opening the answers.
- [ ] My notebook ran from a clean kernel and saved `outputs/students.csv`.
- [ ] My audit covers all eight columns with missing, unique, and range statistics.
- [ ] I named both outcome columns and excluded them from features.
- [ ] Every group summary in my report includes a count.
- [ ] My hash, seed, and commands reproduce the audit CSVs.
- [ ] My verdict is one of the three allowed options.
- [ ] My reflection addresses all three prompts and discloses AI assistance.
- [ ] I saved the package in my portfolio under `f03-data-audit/`.

**Next:** [F04 - Data cleaning, missing values, categorical features, and
normalization](../f04-data-cleaning/index.md). The
[M02 plan](../../syllabus/level-1-foundations.md#m02) shows how this unit and F04
fit together.

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**
