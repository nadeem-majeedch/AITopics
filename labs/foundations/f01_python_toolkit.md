# F01 lab - toolkit submission template

Use this file as the starting point for the report required by the
[F01 lab brief](../../docs/lessons/f01-python-ai/lab.md). Replace every bracketed
prompt with your own evidence and delete prompts you did not answer.

Save your completed copy outside the course repository, for example:

```text
portfolio/f01-python-ai/memo.md
```

## 1. Scenario summary

[Two or three sentences: who recorded the pilot data, how many rows there were,
which two rows could not be used, and what decision the coordinator needs.]

## 2. Constraints

- Synthetic nine-row table only; no real inbox content or personal data.
- Drop no row silently: every rejected row is reported with its raw value.
- Recommendation must respect the 5.0 ms latency budget and the 0.05 accuracy
  lift over the keyword baseline.
- Latency is reported with the machine it was measured on.
- `outputs/` is not committed; copies live in the portfolio folder.

## 3. Required artifacts

| Artifact | Path | Present? |
| --- | --- | --- |
| Toolkit module | `toolkit.py` | [yes/no] |
| Validation checks | `selfcheck.py` | [yes/no] |
| Pilot data | `data/pilot_runs.csv` | [yes/no] |
| Machine-readable summary | `outputs/summary.json` | [yes/no] |
| Per-model table | `outputs/summary.csv` | [yes/no] |
| Decision memo | `memo.md` | [yes/no] |
| Reflection | `reflection.md` | [yes/no] |

## 4. Environment and commands

| Field | Value |
| --- | --- |
| Operating system | [e.g., Windows 11 23H2] |
| Python version | [output of `python --version`] |
| Hardware | [CPU model or core count] |
| Seed | [20261030, or the value you used] |
| Data file | [relative path, e.g., `data/pilot_runs.csv`] |

Commands that rebuild the outputs from a clean state:

```text
[Paste the two commands, for example:
 python selfcheck.py
 python -c "from toolkit import main; main()"]
```

## 5. Data and validation

| Check | Expected | Observed | Passed? |
| --- | --- | --- | --- |
| CSV data rows | 9 | [value] | [yes/no] |
| Runs loaded | 7 | [value] | [yes/no] |
| Rows rejected | 2 | [value] | [yes/no] |
| `accuracy(201, 200)` | raises `ValueError` | [value] | [yes/no] |
| `accuracy(5, 0)` | raises `ValueError` | [value] | [yes/no] |
| `mean([])` | raises `ValueError` | [value] | [yes/no] |

Rejected rows, with the raw value and the reason:

| run_id | Field | Raw value | Why it cannot be used |
| --- | --- | --- | --- |
| [id] | [field] | [raw] | [reason] |

## 6. Results by model

| Model | Runs | Mean accuracy | Mean latency (ms) | Accuracy range |
| --- | --- | --- | --- | --- |
| keywords | [n] | [value] | [value] | [min-max] |
| naive_bayes | [n] | [value] | [value] | [min-max] |
| linear_svm | [n] | [value] | [value] | [min-max] |

## 7. Decision

- **Latency budget:** 5.0 ms per 200-message batch
- **Minimum lift over the keyword baseline:** 0.05 accuracy
- **Eligible models:** [names and the numbers that qualify them]
- **Excluded models:** [name the constraint that excluded each one]
- **Recommendation:** [model, with the two numbers that justify it]

## 8. Risks and limitations

[Batch-to-batch spread, hand-recorded timings, two missing measurements, the
synthetic data, and one measurement you would want before deployment.]

## 9. Reproduction and privacy check

- [ ] `README.md` contains the version, hardware, seed, and both commands.
- [ ] Every number in this report appears in `outputs/summary.json` or
      `outputs/summary.csv`.
- [ ] No real inbox content, personal data, tokens, or absolute personal paths
      are included.
- [ ] `outputs/` is not committed to Git; copies live in the portfolio folder.

## Rubric reminder

| Dimension | Points |
| --- | --- |
| Technical correctness | 30 |
| Evaluation and diagnosis | 25 |
| Reproducibility | 15 |
| Data and ethics | 15 |
| Communication | 15 |
| **Total** | **100** |

The full descriptors and the self-check list are in the
[lab brief](../../docs/lessons/f01-python-ai/lab.md#rubric).
