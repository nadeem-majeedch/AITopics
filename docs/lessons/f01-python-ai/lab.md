# F01 lab - Build a scoring toolkit for an inbox triage pilot

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Weight** | 40% of the F01 assessment |
| **Time** | About 2 hours |
| **Hardware** | CPU-only; standard library only |
| **Starter file** | `labs/foundations/f01_python_toolkit.md` in the repository |
| **Prerequisite** | A completed run of the [guided notebook](notebook.md) |

## The task

A volunteer team at a neighborhood resource center wants to filter the shared
`help@` inbox into "needs a person today" and "can wait". Three candidate
filters were tested on the same 600 historical messages, in three batches of 200.
The pilot coordinator recorded the results by hand in a spreadsheet, which is why
two latency cells contain text instead of a number.

Your job is to turn those nine raw rows into a **verified run log** and a
**recommendation** the coordinator can defend at the next volunteer meeting. The
rules for the recommendation are fixed in advance: the filter must keep the
average latency for a 200-message batch under 5.0 ms, and it must beat the keyword
baseline by at least 5 percentage points of accuracy. Accuracy alone is not
enough, and speed alone is not enough.

This is not the notebook. The notebook used three clean numeric records and one
metric. Here the raw values are text, two are unusable, there are nine rows
instead of three, and the deliverable is a decision under two constraints.

!!! note "This lab was not completed by the course author"
    The scenario, the data table, and the checks below are designed to be
    solvable. The numbers in the table are synthetic and were chosen so that the
    decision is not obvious from the accuracy column alone. No solution is
    published.

## The pilot data

Create `data/pilot_runs.csv` with exactly this content, including the quotes
around the two non-numeric values and the empty cell:

```csv
run_id,model,correct,total,latency_ms
r01,keywords,148,200,1.9
r02,keywords,151,200,2.0
r03,keywords,146,200,n/a
r04,naive_bayes,171,200,3.1
r05,naive_bayes,169,200,
r06,naive_bayes,174,200,3.3
r07,linear_svm,176,200,6.8
r08,linear_svm,178,200,7.1
r09,linear_svm,175,200,6.9
```

Notes on the data:

- `correct` and `total` are read as text by `csv.DictReader`. Convert them.
- `n/a` and the empty cell are **missing measurements**, not zeros. A latency of
  `0` would make a model look infinitely fast.
- The three batches are disjoint thirds of the same 600 messages, so the per-model
  mean covers all 600 evaluations. The spread across batches shows how much a
  score depends on which messages happened to land in a batch.

## What to build

A small importable module `toolkit.py` with these four public functions. Names and
signatures are part of the contract; your lab grader imports them.

| Function | Contract |
| --- | --- |
| `parse_float(raw: str \| None, field: str) -> float \| None` | Returns a float, `None` for empty or non-numeric input, and prints one warning naming the field and the raw value |
| `accuracy(correct: int, total: int) -> float` | Raises `ValueError` if `total <= 0` or `correct` is outside `[0, total]` |
| `mean(values: list[float]) -> float` | Raises `ValueError` on an empty list |
| `summarize(runs: list[Run]) -> dict` | Returns per-model `mean_accuracy`, `mean_latency_ms`, `n_runs`, and `accuracy_range`, rounded to 3 decimals |

Also define `Run` as a frozen dataclass with fields `run_id`, `model`,
`accuracy`, and `latency_ms`, and with invariants that reject an empty run id or
model name, accuracy outside `[0, 1]`, and non-positive latency. Keep rows with a
missing latency out of `Run` and record them separately: a sentinel such as
`latency_ms=0` would pass a naive invariant and then corrupt every mean.

## Required steps

1. **Set up the workspace.** Create `f01-python-ai-lab/` outside the course
   repository. Record the Python version (`python --version`), the operating
   system, and the date in `README.md`. Note the seed `20261030` you will use for
   any sampling; this lab needs no randomness, so the seed is a placeholder for
   future extensions and must still be recorded.
2. **Create the data file.** Paste the nine rows into `data/pilot_runs.csv` with a
   header. Check it with `python -c "import csv; print(len(list(csv.DictReader(open('data/pilot_runs.csv')))))"`
   and confirm it prints `9`.
3. **Write the parser and metrics.** Implement the four functions in `toolkit.py`.
   Keep `parse_float` free of bare `except:` clauses.
4. **Load and validate.** Write `load_runs(path)` that reads the CSV, converts
   `correct` and `total`, parses latency, and returns `(runs, rejected)`. Then add
   **validation check 1**: a `selfcheck.py` script that asserts the number of
   loaded runs and the number of rejected rows, prints both raw rejected values,
   and fails with a clear message if either count is wrong. Two of the nine rows
   must be rejected, and the run count must be seven.
5. **Reject impossible input.** In `selfcheck.py`, assert that `accuracy(201, 200)`
   and `accuracy(5, 0)` each raise `ValueError`, and that `mean([])` raises
   `ValueError`. This is **validation check 2**: the module refuses bad input
   instead of returning a wrong number.
6. **Summarize per model.** Group the seven valid runs by model and compute mean
   accuracy, mean latency, run count, and the accuracy range. Assert that the
   three model names appear exactly once each in the summary and that the run
   counts sum to seven. Decide whether the mean accuracy uses the valid runs only
   or all three batches, and state the choice: for the two models with a rejected
   row, the two answers differ.
7. **Persist the evidence.** Write `outputs/summary.json` with a `created_utc`
   timestamp, the seed, the platform string, the rejected rows, and the per-model
   summary. Write `outputs/summary.csv` with one row per model. Read both files
   back and assert the model count and one known value. **Validation check 3**:
   the mean accuracy recomputed from the CSV must equal the JSON value to three
   decimals.
8. **Apply the decision rule.** Implement a function that takes the summary, a
   latency budget of `5.0`, and a minimum lift of `0.05` over the keyword
   baseline, and returns the recommended model plus the reason. Print the
   eligible and ineligible models with the number that excluded each one.
9. **Write the memo.** `memo.md` of 400-600 words using the headings in the report
   template below. State the recommendation, the two constraints, the accuracy
   spread across batches, and what you would still want to measure before
   deployment (for example, errors on urgent messages, or performance on a new
   month of mail).
10. **Run the whole thing from a clean state.** Delete `outputs/`, run
    `python selfcheck.py`, then run the summarizer, and confirm the files reappear
    with the same values. Record the two commands in `README.md`.

## Required report headings

Use the starter file content or copy this structure into `memo.md`:

```markdown
# F01 toolkit memo

## 1. Summary
The recommendation in two sentences, with the numbers that support it.

## 2. Data and validation
Rows read, rows rejected, why each rejected row cannot be used, and the checks run.

## 3. Results by model
The per-model table: mean accuracy, mean latency, run count, accuracy range.

## 4. Decision
Which model passes both constraints, which fail and on which constraint.

## 5. Risks and limitations
Batch-to-batch spread, hand-recorded timings, synthetic data, missing measurements.

## 6. Reproduction
The exact commands, the Python version, and the file list.
```

## Deliverables

```text
f01-python-ai-lab/
  README.md               # how to rerun, in 5-10 lines, plus environment details
  toolkit.py              # parser, accuracy, mean, Run, summarize, decision rule
  selfcheck.py            # validation checks 1-3
  data/
    pilot_runs.csv        # exactly nine data rows
  outputs/
    summary.json          # machine-readable results, including rejected rows
    summary.csv           # one row per model
  memo.md                 # 400-600 words, headings above
  reflection.md           # 200-300 words, see the assessment page
```

Do not commit `outputs/` to Git. Copy the two files into your portfolio folder
when you assemble the submission.

## Constraints and safety

- Use only the synthetic table above. Do not substitute real emails, real
  addresses, or screenshots of a real inbox, even with names removed.
- Do not record personal information about volunteers, senders, or staff. The
  `help@` inbox in this scenario is fictional.
- Report latency as measured on your machine, and name the machine. A timing
  without hardware is not reproducible.
- Do not silently drop a row. Every rejected row must appear in the JSON with its
  raw value and the reason.
- Accuracy on three batches of 200 messages is not evidence that the filter is
  safe for urgent mail. Say so in the memo instead of implying a guarantee.
- You may use an AI assistant to debug, but you must run the checks yourself and
  disclose substantive help in `reflection.md`.

## Rubric

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Technical correctness | 30 | All four functions match the contracts; the two unusable rows are rejected for the right reason; counts and summaries are internally consistent | Code runs but returns a wrong count, treats a missing latency as zero, or silently passes bad input |
| Evaluation and diagnosis | 25 | The recommendation follows the two constraints, cites the numbers, explains the batch spread, and names one measurement that would change the decision | A model is recommended on accuracy alone, or the constraints are mentioned but not applied |
| Reproducibility | 15 | README, Python version, hardware, seed, and two commands rebuild the outputs exactly; JSON records the rejected rows | Missing commands or environment details; a rerun produces different artifacts |
| Data and ethics | 15 | Synthetic data only, rejected rows disclosed, no personal data, limitations stated plainly | Minor disclosure gaps, or a memo that overstates what the pilot proves |
| Communication | 15 | Memo is decision-first, tables are readable, numbers agree with the artifacts | Memo is a code walkthrough or contradicts its own table |

A dimension with no evidence scores zero, regardless of effort. The lab total is
converted to 40% of the module score on the [assessment](assessment.md) page.

## Self-check before submission

- [ ] `python selfcheck.py` exits with code 0 and prints both rejected raw values.
- [ ] Seven runs loaded, two rejected, and the three models each appear once.
- [ ] `outputs/summary.json` and `outputs/summary.csv` agree to three decimals.
- [ ] The recommendation names the constraint that excluded each rejected model.
- [ ] Every number in `memo.md` appears in an artifact.
- [ ] `README.md` contains the Python version, hardware, seed, and two commands.
- [ ] No real inbox content, personal data, tokens, or absolute personal paths
      appear in the submission.
- [ ] `reflection.md` is 200-300 words and discloses AI assistance.

Next: score your work with the [F01 assessment](assessment.md), then continue to
[M01 - Python and AI development environment](../m01-environment/index.md).

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)
