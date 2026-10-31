# F03 guided notebook

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)

**Notebook file:** `notebooks/foundations/f03_numpy_pandas.ipynb`  
**Hardware:** CPU-only; NumPy and pandas  
**Time:** 2-3 hours including reading the explanations

The notebook builds its own 400-row synthetic table, so there is no download and
no data file to find. Everything it prints is deterministic for seed `42`.

## What the notebook does

| Section | What you do | Evidence produced |
| --- | --- | --- |
| 1. Build a table with a known shape | Generate 400 students and inspect the head | `shape: (400, 9)`, dtypes, three printed rows |
| 2. NumPy arrays: shape, dtype, vectorization | Convert `study_hours` to an array; time a loop mean against a vectorized mean | `(400,)` `float64`; two equal means and two timings |
| 3. Broadcasting and boolean masks | Center `final_score`; compute the pass rate; compare study hours by outcome | Mean-centered array near `0`; pass rate `0.507`; `4.73` vs `3.25` |
| 4. Indexing with `loc` and `iloc` | Select the same row by label and by position | Two agreeing values |
| 5. Grouping and aggregation | Summarize by course, then by tutoring | Three course rows whose counts sum to 400 |
| 6. Merge tables on a key | Join a three-row course catalog with `validate="many_to_one"` | `merged shape: (400, 11)`; department means |
| 7. Prepare a numeric feature matrix | Select four columns, standardize, assert the moments | `X shape: (400, 4)`; means `0`, standard deviations `1` |
| 8. Save and reload a table | Write the CSV, read it back, compare | `outputs/students.csv` with `(400, 9)` after reload |

Each section ends with an assertion on shape, membership, or a numeric tolerance.
The assertions are the specification: if `df.shape` is not `(400, 9)`, the
generator or your edit changed the data, and later numbers cannot be trusted.

## Run it locally

```powershell
cd C:\ai-course\AITopics
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/notebooks.txt
python -m jupyter lab notebooks/foundations/f03_numpy_pandas.ipynb
```

If NumPy or pandas is missing, confirm the kernel first:

```powershell
python -c "import sys, numpy, pandas; print(sys.executable); print(numpy.__version__, pandas.__version__)"
```

The path printed by `sys.executable` must be inside your environment. Installing
packages with a different interpreter is the most common reason a working install
still fails to import.

With Visual Studio Code:

1. Open the repository folder.
2. Open `notebooks/foundations/f03_numpy_pandas.ipynb`.
3. Select the `.venv` interpreter as the kernel.
4. Use **Restart Kernel and Run All Cells**.

The notebook takes a few seconds to run. If it takes much longer, check that you
did not add a loop over 400 rows inside another loop.

## Run it on Google Colab

Colab is optional for F03; it ships NumPy and pandas already, usually at newer
versions than your local environment.

1. Open [Google Colab](https://colab.research.google.com/) and choose **File >
   Upload notebook**.
2. Select `notebooks/foundations/f03_numpy_pandas.ipynb`.
3. Choose **Runtime > Run all** on a standard CPU runtime.
4. Download `outputs/students.csv` from the **Files** pane if you want the
   artifact; `/content` is temporary.

Colab was not executed in the authoring environment, and no Colab result is
reported here. Different pandas versions can change a printed warning or the exact
`to_string` layout, but the asserted shapes and values should hold.

## What a healthy run looks like

These are the verified results from the Windows 11 CPU run with Python 3.12.10.
Timings vary by machine; asserted values do not.

| Check | Verified result | What to expect |
| --- | --- | --- |
| Initial shape | `shape: (400, 9)` | Exactly `(400, 9)` |
| Array shape and dtype | `(400,)` `float64` | Exactly; an `int64` array means you selected a different column |
| Loop versus vector mean | Two equal means | Equal to several decimal places; timings differ |
| Centered mean | `0.0` (within `1e-9`) | Assertion passes |
| Pass rate | `0.507` | About `0.50-0.51`; must equal the mean of the mask |
| Study hours by outcome | passed `4.73`, failed `3.25` | Passed higher; exact values depend on the seed |
| Merged shape | `(400, 11)` | Exactly; anything else means a join problem |
| Feature matrix | `X shape: (400, 4)` | Exactly `(400, 4)` |
| Standardized means | Zeros to 8 decimals | All zero within `1e-9`; a printed `-0.` is also fine |
| Standardized stds | `[1. 1. 1. 1.]` | All one within `1e-9` |
| Reloaded CSV | `reloaded shape: (400, 9)` | Same shape as the table |
| File written | `outputs/students.csv` | Exists, about 25 KB |

The pass rate and the group means describe this synthetic sample. They are not
estimates from a real student population and must not be reported as such.

## Artifacts

| File | Size | Keep it? |
| --- | --- | --- |
| `outputs/students.csv` | About 25 KB | Yes; copy it into your submission folder |
| `outputs/` directory | One file | No; it is regenerated by a rerun |

The repository `.gitignore` excludes `outputs/`, so the CSV is never committed.
That is intentional: the table is generated by the notebook, and a committed copy
would drift from the code. If you need the file in your portfolio, copy it out of
`outputs/` into your own folder.

## Troubleshooting

| Symptom | Diagnosis | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: numpy` | Kernel is not the environment from M01 | Print `sys.executable`; select the right kernel |
| `ModuleNotFoundError: pandas` | pandas is not installed in this environment | `python -m pip install -r requirements/notebooks.txt` |
| Assertion fails on `(400, 9)` | The generator was edited or `n` was changed | Restore `make_students()` defaults and seed `42` |
| `pass rate` is not `0.507` | The `passed` column was modified, or a different seed was used | Rerun from a clean kernel; do not edit the assertion |
| `merged shape` is not `(400, 11)` | Duplicate course rows in the catalog, or a different join type | Use `how="left"` and `validate="many_to_one"`; check `course_info` has 3 unique rows |
| Standard deviations print `1.0012` or similar | pandas' `.std()` was used instead of NumPy's default | Use `X_scaled.std(axis=0)` or pass `ddof=0` |
| `FileNotFoundError: outputs` | Wrong working directory | The first cell creates `outputs/` relative to the kernel's directory; print `Path.cwd()` |
| Reloaded CSV has 10 columns | `to_csv` ran without `index=False` | Rerun the save cell after restoring `index=False` |
| `SettingWithCopyWarning` | A filter result was modified in place | Use `.loc[mask, "col"] = value` on the original table |

If a shape is wrong after an edit of your own, undo the edit before doing anything
else. Debugging a modified table against the notebook's assertions is slower than
starting again.

## Submission checkpoint

Before starting the lab, confirm:

- [ ] The notebook ran top to bottom in a fresh kernel.
- [ ] `outputs/students.csv` exists with a header and 400 data rows.
- [ ] You can explain why the pass rate equals the mean of a boolean mask.
- [ ] You can explain why the merge produced 11 columns.
- [ ] You can state the `ddof` convention behind the standardized standard
      deviations.

Next: the [F03 lab brief](lab.md) asks you to audit a different table and decide
whether it is fit for modeling. Score the result with the
[assessment](assessment.md), then continue to
[F04 - Data cleaning](../f04-data-cleaning/index.md).

---

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)
