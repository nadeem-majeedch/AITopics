# F05 guided notebook

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)

**Notebook file:** `notebooks/foundations/f05_splits.ipynb`
**Open notebook:** [F05 guided notebook](../../notebooks/foundations/f05_splits.ipynb)
**Hardware:** CPU-only; no GPU cells
**Time:** 2-3 hours including the explanations

The notebook is a repository file. You run it from your clone in JupyterLab or
Visual Studio Code. This guide explains what each section proves, what a correct
run prints, and what to check when a cell fails.

## What the notebook does

| Section | What you do | Evidence produced |
| --- | --- | --- |
| 1. Build a table | Generate 600 houses with a neighborhood group and a price target | Shape `(600, 7)`, positive prices |
| 2. 60/20/20 split | Hold out test, then split the remainder | 360/120/120 rows and fractions 0.6/0.2/0.2 |
| 3. Stratified split | Bin price into quartiles, stratify, compare bands | Test band shares near 0.25 each |
| 4. Group split | Hold out whole neighborhoods | Train east/south/west, test north, zero overlap |
| 5. Target leakage | Add `price_vs_city_mean` and compare models | R-squared 1.000 versus 0.703 |
| 6. Scaler leakage | Fit the scaler on all rows, then on train only | R-squared 0.7976 versus 0.7976 |
| 7. Duplicate leakage | Inject duplicates, split, deduplicate, split again | 11 matches, then 0 |
| Check your work | Review the five properties | Your notes |

Every section ends with an assertion. The assertions are the contract: the
notebook refuses to continue quietly when a property stops holding.

## Run it locally

These commands assume the repository is at `C:\ai-course\AITopics` and the
environment is the one you built in [M01](../m01-environment/index.md).

```powershell
cd C:\ai-course\AITopics
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/notebooks.txt
python -m jupyter lab notebooks/foundations/f05_splits.ipynb
```

With Visual Studio Code:

1. Open the repository folder.
2. Open `notebooks/foundations/f05_splits.ipynb`.
3. Select the `.venv` interpreter as the kernel.
4. Run **Restart Kernel and Run All Cells**.

The notebook has no external data dependency: it generates the table with
`numpy.random.default_rng(42)`. Running it twice in the same environment therefore
produces the same rows, counts, and scores.

## Google Colab (optional)

The notebook runs on Colab without extra installs because pandas, NumPy, and
scikit-learn are preinstalled. Upload the `.ipynb`, choose a CPU runtime, and run
all cells. Colab resets its filesystem when the session ends, so download anything
you want to keep before closing the tab.

Colab was **not** used to verify this notebook. The results below come from a
Windows 11 CPU run. If your Colab versions of scikit-learn or pandas differ, the
printed version line will differ; the split counts and the leakage pattern should
not.

## What a healthy run looks like

These results were verified on Windows 11, Python 3.12.10, CPU-only. Your
versions may differ; the structural results should not.

| Check | Verified result | What to expect |
| --- | --- | --- |
| House table | `(600, 7)` | `(600, 7)`; a different shape means the generator changed |
| Split sizes | train `(360, 7)`, validation `(120, 7)`, test `(120, 7)` | 60/20/20 of 600 |
| Split fractions | 0.6, 0.2, 0.2 | Rounded to two decimals |
| Test band shares | About 0.25 per quartile | Each band present; values near 0.25 |
| Group split train | east, south, west | Order in the printout may differ |
| Group split test | north | One held-out group |
| Group overlap | `set()` | Must be empty |
| R-squared with target feature | 1.000 | Above 0.95 |
| R-squared without it | 0.703 | Clearly lower |
| Scaler fitted on all rows | 0.7976 | Close to the clean value |
| Scaler fitted on train only | 0.7976 | Close to the leaky value |
| Duplicate matches before dedupe | 11 | Greater than zero |
| Duplicate matches after dedupe | 0 | Must be zero |

The last two rows are the ones students most often misread. The scaler leak
produced no measurable change here. That is a property of this large, clean,
well-scaled table, not evidence that the leak is acceptable.

## Artifacts

This notebook is a demonstration, not a report generator. It creates an
`outputs/` directory beside the notebook but writes no data files into it.

| Path | Written by the notebook? | Keep it? |
| --- | --- | --- |
| `outputs/` | Yes, an empty directory | No; it is recreated on each run |
| Printed split counts | No, console output only | Copy the numbers into your notes |
| Screenshots of key cells | No | Optional; useful in the lab report |

The repository `.gitignore` excludes `outputs/`. If you save figures or notes
there, copy them out before packaging a submission. Generated files are never
committed.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AssertionError` on `houses.shape == (600, 7)` | The generator or its arguments were edited | Restore `make_houses()` and rerun from a clean kernel |
| `KeyError: 'neighbourhood'` | You loaded a CSV whose column was renamed | Use the notebook's generated table or the documented column names |
| Group overlap is not empty | `groups=` received the wrong column or row indices | Pass `groups=houses["neighbourhood"]` to `GroupShuffleSplit.split` |
| Leaky R-squared prints 0.703 | The target-derived column was dropped before fitting | Keep `price_vs_city_mean` in `X_leaky` for the demonstration |
| `assert abs(leaky - clean) < 0.05` fails | The table or seed changed, so the scaler statistics moved more | Rerun from cell 1; do not weaken the assertion to make it pass |
| Duplicate matches print 0 before dedupe | A different seed produced no cross-split duplicates | Restore `random_state=42`; 42 yields 11 |
| `Bin edges must be unique` from `qcut` | The target became constant or nearly constant | Check that you did not filter the table to a single price |
| `ModuleNotFoundError: sklearn` | The kernel is not the course environment | Run `import sys; print(sys.executable)` and select the `.venv` kernel |

If a failure is not in this table, record the full error, the cell that produced
it, and the printed shapes from the cells above it. That record is exactly what
the lab asks you to produce for a leak you diagnose.

## Submission checkpoint

Before starting the lab, confirm:

- [ ] The notebook ran top to bottom in a fresh kernel.
- [ ] The split counts are 360/120/120 and the fractions are 0.6/0.2/0.2.
- [ ] The group split shows zero overlap.
- [ ] You can explain the 1.000 versus 0.703 result in one sentence.
- [ ] You can explain why 0.7976 versus 0.7976 is still a defect.
- [ ] The duplicate count is 11 before deduplication and 0 after.
- [ ] You have written your seed and your package versions in your notes.

Next: the [lab brief](lab.md) asks you to audit a different evaluation on the
student table, find its leaks, and rebuild the split under time-of-prediction
constraints.

---

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)
