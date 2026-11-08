# F06 guided notebook

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)

**Notebook file:** `notebooks/foundations/f06_eda.ipynb`
**Open notebook:** [F06 guided notebook](../../notebooks/foundations/f06_eda.ipynb)
**Hardware:** CPU-only
**Time:** 2-3 hours including reading the figures

The notebook is a repository file. It generates the house table, makes three
figures, prints the numbers behind them, and saves every figure to `outputs/`.
This guide explains what each section proves and what a correct run produces.

## What the notebook does

| Section | What you do | Evidence produced |
| --- | --- | --- |
| Setup | Import pandas, NumPy, matplotlib; set the `Agg` backend and output folder | Library version, `outputs/` created |
| 1. Univariate distributions | Plot price, area, and distance | `f06_distributions.png` |
| 2. Relationships | Correlate numeric columns with price; scatter area against price | Correlation table and `f06_area_price.png` |
| 3. Groups | Count, median, and mean by neighborhood; box plot | Group table, `f06_price_by_neighbourhood.png` |
| 4. Outliers | Apply the IQR rule and check for non-positive prices | Bounds, 4 flagged rows, 0 negative prices |
| 5. Observations | Convert findings into five decision-oriented sentences | Your written observations |

The notebook has no modeling step. That is deliberate: EDA describes the data,
and the next module uses those descriptions to choose a method.

## Run it locally

```powershell
cd C:\ai-course\AITopics
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/notebooks.txt
python -m jupyter lab notebooks/foundations/f06_eda.ipynb
```

With Visual Studio Code:

1. Open the repository folder.
2. Open `notebooks/foundations/f06_eda.ipynb`.
3. Select the `.venv` interpreter as the kernel.
4. Run **Restart Kernel and Run All Cells**.

The notebook sets `matplotlib.use("Agg")`, so plots are written to files rather
than displayed inline. That is expected. Open the PNG files in `outputs/` after
the run; in JupyterLab you can right-click a file and choose **Open With > Image
Viewer**.

## Google Colab (optional)

Upload the notebook, choose a CPU runtime, and run all cells. Matplotlib is
preinstalled. Because the notebook uses `Agg`, no figure appears inline; open the
**Files** pane, find `outputs/`, and download the three PNG files before the
session ends. Colab's temporary disk is erased when the runtime stops.

Colab was **not** executed in the authoring environment. The numbers below come
from Windows 11, Python 3.12.10, CPU-only.

## What a healthy run looks like

| Check | Verified result | What to expect |
| --- | --- | --- |
| Table shape | `(600, 7)` | Exactly 600 rows and 7 columns |
| Missing values | Count is 600 for every numeric column in `describe()` | No missing values in the generated table |
| Area-price correlation | 0.749 | Above 0.5; small changes if the generator changes |
| South median | 297,218 | Lowest median |
| West median | 301,761 | Close to south |
| East median | 323,728 | Middle |
| North median | 337,716 | Highest median |
| Smallest group | 103 | At least 50; the notebook asserts this |
| IQR outlier rows | 4 | Two below the lower bound, two above the upper bound |
| Negative or zero prices | 0 | Must be zero |
| Saved figures | 3 | All three files exist in `outputs/` |

Medians are printed as whole dollars because the table rounds prices to whole
units. If your medians differ by a few dollars, check that you did not filter or
resample the table.

## Artifacts

| File | What it shows | Keep it? |
| --- | --- | --- |
| `outputs/f06_distributions.png` | Histograms of price, area, and distance | Yes, for the lab or portfolio |
| `outputs/f06_area_price.png` | Scatter plot of area against price | Yes |
| `outputs/f06_price_by_neighbourhood.png` | Box plot of price by neighborhood | Yes |
| `outputs/` directory | Created on every run | No; regenerate it |

The repository `.gitignore` excludes `outputs/`, so these files are never
committed. If you need them in a submission, copy them into your portfolio folder
outside the repository.

Figures are rendered at 110 DPI with `bbox_inches="tight"`. File sizes depend on
your matplotlib version and fonts. A zero-byte file means the save failed; check
the working directory.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No plots appear in the notebook | `Agg` is a non-interactive backend | Open the saved PNG files in `outputs/`; this is expected |
| `TypeError: boxplot() got an unexpected keyword argument 'tick_labels'` | matplotlib older than 3.9 | Upgrade matplotlib, or replace `tick_labels=order` with `labels=order` |
| `FileNotFoundError` when saving | The notebook started outside its folder | Run from the repository root or the notebook directory; the first cell creates `outputs/` |
| `KeyError: 'neighbourhood'` | A renamed column or a different CSV | Use the generated table; check `df.columns` |
| Assertion on `df.shape == (600, 7)` fails | The generator was edited or a filter was applied | Restart the kernel and rerun from cell 1 |
| Smallest group assertion fails | The neighborhood probabilities or seed changed | Restore `make_houses()` and `SEED = 42` |
| Correlation is much lower than 0.749 | Rows were filtered or the target column was altered | Print `df.shape` and `df.head()`; compare with the notebook |
| Negative prices reported | Wrong file, wrong unit, or corrupted CSV | Regenerate the data; do not "fix" prices by taking absolute values |

If a cell fails for another reason, record the exact error, the last printed
shape, and your package versions before changing code.

## Submission checkpoint

Before starting the lab, confirm:

- [ ] The notebook ran top to bottom and printed `(600, 7)`.
- [ ] Three PNG files exist in `outputs/` and open correctly.
- [ ] The area-price correlation is about 0.749.
- [ ] You can name the highest and lowest neighborhood medians and the smallest
      group size.
- [ ] You can explain why four rows were flagged and why they were not deleted.
- [ ] You wrote five observation-evidence-decision sentences of your own.

Next: the [lab brief](lab.md) asks for a neighborhood market brief with a
recommendation, not a rerun of these plots.

---

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)
