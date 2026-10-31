# F01 assessment

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**

F01 uses the course's standard module weights. There is no proctored exam. You
check your answers, score your own evidence against published criteria, and
decide whether you are ready to continue.

| Component | Weight | Evidence |
| --- | --- | --- |
| Knowledge check | 20% | Answers to the eight questions below |
| Guided notebook | 30% | Executed notebook with the two output files |
| Independent lab | 40% | Toolkit module, checks, summary artifacts, and memo |
| Reflection | 10% | 200-300 word reflection |

## Part A - Knowledge check (20%)

Answer each question in writing before opening the answer. A correct answer in
your own words, with the mechanism, is worth more than a memorized sentence.

**1. What do `41 / 50` and `41 // 50` evaluate to, and why does the difference matter for a metric?**

??? note "Answer"
    `41 / 50` is `0.82`, a float. `41 // 50` is `0`, because `//` is floor
    division and the remainder is discarded. A metric computed with `//` reports
    zero for every model that does not exceed 100 percent, which looks like a
    broken model rather than a broken line of code.

**2. Compute the MAE for actual `[10, 20, 30]` and predicted `[12, 18, 33]`. Show the arithmetic.**

??? note "Answer"
    The absolute errors are `|10 - 12| = 2`, `|20 - 18| = 2`, and
    `|30 - 33| = 3`. Their sum is `7` over `3` observations, so the MAE is
    `7 / 3 = 2.333` (in the units of the target). A loop-free version is
    `sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual)`.

**3. Code reading: given
`records = [{'model': 'baseline', 'correct': 30, 'total': 50}, {'model': 'logistic', 'correct': 41, 'total': 50}, {'model': 'tree', 'correct': 43, 'total': 50}]`,
what does `[r['model'] for r in records if r['correct'] / r['total'] > 0.80]` return, and in what order?**

??? note "Answer"
    `['logistic', 'tree']`. The accuracies are `0.60`, `0.82`, and `0.86`; the
    comprehension keeps the last two in their original list order. It does not
    sort, so a model added later appears where it was appended.

**4. What does `@dataclass(frozen=True)` prevent, and why is that useful in a run log?**

??? note "Answer"
    It makes instances read-only: assigning to a field after construction raises
    `FrozenInstanceError`. A run log is evidence, so a later cell must not be able
    to overwrite a recorded accuracy with a recomputed one. Freezing turns an
    accidental overwrite into an immediate error instead of a silently altered
    result.

**5. When should you use `assert` and when should you use `raise ValueError`?**

??? note "Answer"
    Use `raise ValueError` for input you do not control: user input, CSV values,
    API responses. Assertions document and check your own assumptions during
    development, and they disappear under `python -O`. Validating untrusted data
    with `assert` means the check can be switched off in exactly the environment
    where it matters.

**6. Code reading: `parse_float("n/a", "latency")` prints a warning and returns `None`. Why is `None` a better return value than `0`, and what does the warning add?**

??? note "Answer"
    `0` is a legitimate measurement, so a missing latency recorded as `0` would
    make the model look infinitely fast and would silently drag the mean down.
    `None` is distinguishable from a real value and forces the caller to decide.
    The warning makes the data loss visible, so a run that rejected two rows does
    not look identical to a clean run.

**7. A baseline reaches accuracy `0.60` at `2.1` ms; a tree reaches `0.86` at `4.8` ms. Compute the extra accuracy per extra millisecond and interpret it.**

??? note "Answer"
    The gain is `0.86 - 0.60 = 0.26` accuracy for `4.8 - 2.1 = 2.7` ms, so
    `0.26 / 2.7 = 0.096` accuracy points per millisecond. Adding the logistic run
    (`0.82` at `3.4` ms) gives `0.22 / 1.3 = 0.169`, so the first increment buys
    more than the second. Diminishing returns like this is why a latency budget
    changes the recommendation.

**8. You wrote `run_log.csv`, reloaded it, and `rows[0]['params']` is the string `'0'`. Is the file corrupt? How do you verify the round trip correctly?**

??? note "Answer"
    The file is fine. CSV stores text and does not preserve Python types, so every
    field returns as a string. Verify the round trip by comparing counts
    (`len(rows) == len(runs)`), comparing a field after explicit conversion
    (`int(rows[0]['params']) == 0`), and comparing one value you know exactly,
    such as the model name. Compare parsed values, not raw strings to numbers.

**Self-score:** 2.5 points per question, 20 points total. Award full credit only
when the answer includes the mechanism, the arithmetic, or the diagnostic step.

## Part B - Guided notebook (30%)

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Completeness | 10% | All eight sections plus the checklist ran top to bottom; no skipped required cell |
| Correctness | 10% | Assertions pass; `run_log.json` has three runs with seed 42; the CSV has three data rows |
| Interpretation | 10% | A short markdown note under the summary cell stating your Python version, the best-accuracy and fastest model, and one limitation |

A notebook with saved outputs and no interpretation is incomplete. The
limitation can be one sentence, for example: "three runs on 50 items is too small
to distinguish a 0.82 model from a 0.86 model."

## Part C - Independent lab (40%)

The lab is scored with the five-dimension rubric on the
[lab brief](lab.md#rubric).

| Dimension | Points | What earns full marks |
| --- | --- | --- |
| Technical correctness | 30 | Contracts met; two rows rejected for the right reason; counts consistent across code, JSON, and CSV |
| Evaluation and diagnosis | 25 | Recommendation follows both constraints and cites the numbers; batch spread discussed |
| Reproducibility | 15 | README, version, hardware, seed, and commands rebuild the artifacts |
| Data and ethics | 15 | Synthetic data only; rejected rows disclosed; limits of a 600-message pilot stated |
| Communication | 15 | Decision-first memo whose numbers match its own table |
| **Total** | **100** | Converted to 40% of the module score |

Common reasons for losing marks:

- Treating `n/a` or a blank cell as `0` ms.
- Recommending the most accurate model without checking the latency budget.
- A summary table that reports means but not the number of runs behind each mean.
- A `selfcheck.py` that prints "ok" without asserting anything.
- A memo that says "the model is accurate" without the numbers or the two
  constraints.
- Rejected rows that appear nowhere in the artifacts.

## Part D - Reflection (10%)

Write 200-300 words in `reflection.md`. Answer all three prompts:

1. Which mistake in this unit would have produced a plausible but wrong number
   rather than an error, and how would you catch it next time?
2. Your lab recommendation depends on a 5.0 ms budget measured by hand. What would
   you change about the measurement before trusting that budget in production?
3. What is one thing you will always write to a run log from now on, and why?

Reflection is not a summary of the steps. It is your reasoning about evidence,
uncertainty, and what you will change.

## Scoring worksheet

| Component | Maximum | Your score | Notes |
| --- | --- | --- | --- |
| Knowledge check | 20 | | |
| Guided notebook | 30 | | |
| Independent lab | 40 | | |
| Reflection | 10 | | |
| **Total** | **100** | | |

Use this scale for your own planning:

| Score | Interpretation |
| --- | --- |
| 90-100 | Ready for M01; your results are verified and your reasoning is explicit |
| 75-89 | Ready, but fix the weakest dimension, usually reproducibility or diagnosis |
| 60-74 | Reread the lesson and rerun the notebook; the lab checks have gaps |
| Below 60 | Rebuild the toolkit from the notebook, section by section, before moving on |

These bands are self-study guidance. They are not a university grade and do not
confer credit.

## Academic integrity and AI assistance

- You may use an AI assistant to explain an error, review a function, or suggest a
  test.
- You must run the code and the checks yourself, and the submitted outputs must
  come from your run.
- Disclose substantive assistance in your reflection: what you asked, what you
  used, and what you verified independently.
- Do not submit a toolkit or memo you cannot explain line by line. The goal is the
  skill, not the file.

The course policy is in [Academic integrity](../../course/assessments.md#academic-integrity)
and [How to study](../../course/how-to-study.md#academic-integrity-and-ai-assistants).

## Completion checklist

- [ ] I answered all eight knowledge questions before opening the answers.
- [ ] My notebook ran from a clean kernel and contains saved outputs.
- [ ] `outputs/run_log.json` and `outputs/run_log.csv` exist and agree.
- [ ] My lab `selfcheck.py` asserts counts and rejected values, not just prints.
- [ ] My lab memo cites the two constraints and the numbers behind its decision.
- [ ] My reflection addresses all three prompts and discloses AI assistance.
- [ ] I removed personal paths and any real inbox content from the submission.
- [ ] I saved the package in my portfolio under `f01-python-ai/`.

**Next:** [M01 - Python and AI development environment](../m01-environment/index.md),
where this toolkit gets a reproducible environment. The unit overview is in the
[Level 0 plan](../../syllabus/level-0-start.md).

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**
