# F01 guided notebook

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)

**Notebook file:** `notebooks/foundations/f01_python_ai.ipynb`  
**Hardware:** CPU-only, standard library only  
**Time:** 2-3 hours including reading the explanations

The notebook is a repository file, not a web page. You run it from your clone in
JupyterLab, Visual Studio Code, or Google Colab. This guide explains what each
section proves, what the verified output looked like, and what to check when a
cell fails.

## What the notebook does

| Section | What you do | Evidence produced |
| --- | --- | --- |
| 1. Values, types, and the cost of a mistake | Print the interpreter, compute `41 / 50`, inspect `7 // 2` and `0.1 + 0.2` | Accuracy `0.82` as a `float`; the `math.isclose` check passes |
| 2. Collections | Build the three-run record list; extract labels and unique latencies | `models: ['baseline', 'logistic', 'tree']` |
| 3. Functions and validation | Define `accuracy`, `mean`, `mae`; call each with bad input | `accuracy: 0.82`, `mae: 2.333`, two printed rejections |
| 4. Comprehensions | Score all runs and keep those above 0.80 | `above 0.80: ['logistic', 'tree']` |
| 5. Dataclass with validation | Construct three frozen `Run` objects | Three printed run records; accuracy `0.86` on the last |
| 6. Parse untrusted values | Feed `"3.5"`, `"n/a"`, and `""` to `parse_float` | `parser checks passed` plus one warning line |
| 7. Persist evidence | Write and reload JSON and CSV | `outputs/run_log.json`, `outputs/run_log.csv`, both verified |
| 8. Experiment summary | Select best accuracy and lowest latency | JSON summary with `tree` and `baseline` |
| Check your work | Review the checklist | Your notes |

Every code section ends with `assert`. The assertions are the point of the
notebook: they turn "the output looked right" into a check that fails loudly.

## Run it locally

These commands assume you cloned the repository to `C:\ai-course\AITopics`. F01
needs no third-party package, so any Python 3.10-3.12 interpreter works. If you
have already completed M01, activate that environment first.

```powershell
cd C:\ai-course\AITopics
python --version
python -m jupyter lab notebooks/foundations/f01_python_ai.ipynb
```

If you have no Jupyter installation, run the notebook from Visual Studio Code
instead:

1. Open the repository folder in VS Code.
2. Open `notebooks/foundations/f01_python_ai.ipynb`.
3. Select a Python 3.10+ interpreter as the kernel; the notebook needs no extra
   packages.
4. Use **Restart Kernel and Run All Cells**.

Run the cells in order. If you experimented, restart the kernel before your final
run so the saved notebook shows a clean top-to-bottom execution.

The notebook creates `outputs/` beside itself with `Path("outputs").mkdir()`, so
the file location depends on the kernel's working directory. It is normally the
notebook's own folder, `notebooks/foundations/outputs/`.

## Run it on Google Colab

Colab is optional for F01. The notebook imports only `csv`, `json`, `math`,
`platform`, `statistics`, `sys`, `pathlib`, `dataclasses`, and `datetime`, all of
which Colab provides.

1. Open [Google Colab](https://colab.research.google.com/) and choose **File >
   Upload notebook**.
2. Select `notebooks/foundations/f01_python_ai.ipynb` from your clone.
3. Choose **Runtime > Run all**.
4. Download `outputs/run_log.json` from the **Files** pane if you want to keep it;
   `/content` is temporary.
5. Save the executed notebook to Drive or GitHub before the session ends.

This Colab path was not executed in the authoring environment. The verified run
described below was local, on Windows 11.

## What a healthy run looks like

These values come from the verified Windows 11 run on Python 3.12.10. Timings and
printed timestamps will differ; the asserted values must not.

| Check | Verified result | What to expect |
| --- | --- | --- |
| Python version | `Python: 3.12.10` | 3.10 or newer; older versions fail the version assertion |
| Platform | Windows 11 | Your own operating system |
| Section 1 accuracy | `accuracy: 0.74 <class 'float'>` | Exactly `0.74`, from `37 / 50` |
| Integer and float demo | `7 // 2 = 3`, `0.1 + 0.2 = 0.30000000000000004` | Identical; this is why `math.isclose` is used |
| Section 3 accuracy | `accuracy: 0.82 <class 'float'>` | Exactly `0.82`, from `accuracy(41, 50)` |
| MAE | `mae: 2.333` | Exactly `7 / 3` |
| Rejected calls | `rejected (51, 50) -> ...` and `rejected (5, 0) -> ...` | Two rejections, no crash |
| Threshold filter | `above 0.80: ['logistic', 'tree']` | Same two names in the same order |
| Run records | `Run(model='baseline', accuracy=0.6, latency_ms=2.1, params=0)` and two more | Three records; the tree run has accuracy `0.86` |
| JSON reload | `seed == 42`, three runs | Both assertions pass |
| CSV reload | Three rows, header `model,accuracy,latency_ms,params` | Three rows, same field order |
| Summary | `best_accuracy: tree`, `fastest: baseline` | Same two names |
| Files written | `outputs/run_log.json`, `outputs/run_log.csv` | Both exist and are non-empty |

The three runs in the summary are:

| Model | Correct / 50 | Accuracy | Latency (ms) |
| --- | --- | --- | --- |
| baseline | 30 | 0.60 | 2.1 |
| logistic | 41 | 0.82 | 3.4 |
| tree | 43 | 0.86 | 4.8 |

The most accurate model is the tree; the fastest is the baseline. The notebook
prints both facts instead of collapsing them into one ranking.

## Artifacts

| File | Size | Keep it? |
| --- | --- | --- |
| `outputs/run_log.json` | About 1 KB | Yes; copy it into your submission folder |
| `outputs/run_log.csv` | Under 1 KB | Yes, if your report quotes the table |
| `outputs/` directory | Two files | No; the whole directory is regenerated by a rerun |

The repository `.gitignore` excludes `outputs/`, so the notebook never adds these
generated files to Git. That is deliberate: outputs are evidence you copy out,
not source files the course ships. If you submit through Git, place your
screenshots or copied JSON in your own portfolio folder, not in `outputs/`.

Expect the JSON to contain a `created_utc` timestamp that changes on every run.
Everything else in the payload should be identical when you rerun on the same
Python version.

## Troubleshooting

| Symptom | Diagnosis | Fix |
| --- | --- | --- |
| `SyntaxError` on `float \| None` | Python older than 3.10 | Install Python 3.10-3.12; do not patch the syntax |
| `AssertionError: Use Python 3.10 or newer` | The kernel is an old interpreter | Select a 3.10+ kernel and rerun the first cell |
| `accuracy: 0` or assertion `accuracy == 0.82` fails | Integer division, or a cell was edited | Section 1 must print `0.74`; section 3 must print `0.82` and `mae: 2.333` |
| `AssertionError` in section 4 | A run was renamed, or the `> 0.80` threshold was edited | Restore the three records and the threshold |
| `TypeError: unsupported operand type(s) for -: 'str' and 'int'` | A value was read from CSV without conversion | CSV reloads everything as text; convert with `float()` or `int()` |
| `FileNotFoundError` when writing the JSON | The kernel's working directory is not writable or not where you expect | Print `Path.cwd()`; the `outputs/` folder is created relative to it |
| The CSV has four or more rows after a rerun | The cell was run twice in append mode, or an old file was edited by hand | Delete `outputs/` and run the persistence cell once more |
| `KeyError: 'params'` in the CSV writer | The `Run` fields were renamed | Keep the dataclass field names; `asdict` derives the header from them |
| A warning line but no error in section 6 | Expected: `"n/a"` is not numeric | Confirm the cell prints `parser checks passed` afterward |

When a failure is not in this table, record four things before changing code: the
exact error, the cell that produced it, the interpreter from
`sys.version`, and the value you expected.

## Submission checkpoint

Before starting the lab, confirm:

- [ ] The notebook ran top to bottom in a fresh kernel with no failed cells.
- [ ] `outputs/run_log.json` and `outputs/run_log.csv` exist.
- [ ] The JSON contains `seed: 42` and three run objects.
- [ ] The CSV has one header and three data rows.
- [ ] You can explain why `mae` returns `2.333` and not `2`.
- [ ] You can state which run is most accurate, which is fastest, and why those
      are different questions.

Next: the [F01 lab brief](lab.md) asks you to build a tested toolkit for a
different scenario and recommend a model. Score the result with the
[assessment](assessment.md), then continue to
[M01 - Python and AI development environment](../m01-environment/index.md).

---

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)
