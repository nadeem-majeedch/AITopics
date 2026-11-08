# F08 guided notebook

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)

**Notebook file:** `notebooks/foundations/f08_regression_classification.ipynb`
**Open notebook:** [F08 guided notebook](../../notebooks/foundations/f08_regression_classification.ipynb)
**Hardware:** CPU-only
**Time:** 2-3 hours including reading the explanations
**Execution status:** verified on Windows 11 CPU with Python 3.12.10. Colab and GPU paths were not executed.

The notebook is a repository file, not a web page. You run it from your clone in
JupyterLab or Visual Studio Code. It generates both datasets in code, so it needs
no download and no GPU.

## What the notebook does

| Section | What you do | Evidence produced |
| --- | --- | --- |
| 1. Regression data and a baseline | Generate 600 houses, split 450/150, predict the training mean | Baseline MAE 51,734 and RMSE 66,281 |
| 2. Fit linear regression and ridge | Standardize on training rows; fit `LinearRegression` and `Ridge(alpha=10)` | MAE, RMSE, and R-squared for both models |
| 3. Inspect coefficients | Rank the standardized coefficients by absolute value | Area, bedrooms, age, distance, and garage coefficients |
| 4. Classification data and a majority baseline | Generate 500 students, split 375/125 with `stratify=y`, predict the majority class | Baseline accuracy 0.512 and class balance 0.509/0.491 |
| 5. Logistic regression and the confusion matrix | Fit the classifier, label at 0.5, print the matrix and four metrics | Confusion matrix `[[51, 13], [21, 40]]`; accuracy 0.728 |
| 6. Metric guidance | Read the decision-to-metric table | Your notes on which metric fits which decision |
| Check your work | Review the closing checklist | Your notes |

Every code section ends with an `assert`. The assertion is part of the lesson: it
turns a claim such as "the model beats the baseline" into a check that fails
loudly when the data or the code changes.

## Run it locally

These commands assume you cloned the repository to `C:\ai-course\AITopics` and
created `.venv` as described in
[M01](../m01-environment/index.md#1-interpreter-packages-and-virtual-environments).

```powershell
cd C:\ai-course\AITopics
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/notebooks.txt
python -m jupyter lab notebooks/foundations/f08_regression_classification.ipynb
```

With Visual Studio Code:

1. Open the repository folder.
2. Open `notebooks/foundations/f08_regression_classification.ipynb`.
3. Select the `.venv` interpreter as the kernel.
4. Choose **Restart Kernel and Run All Cells**.

Run the cells in order. The notebook creates an `outputs/` directory in
`notebooks/foundations/`, but this notebook writes no files into it. If you
experimented, restart the kernel before your final run so the saved outputs come
from one clean pass.

## Run it on Google Colab

Colab is optional. Upload only the notebook file; the data is generated in the
first code cells, so no CSV upload is needed.

1. Open [Google Colab](https://colab.research.google.com/).
2. Choose **File > Upload notebook** and select
   `notebooks/foundations/f08_regression_classification.ipynb`.
3. Keep the runtime type as **CPU**. The notebook has no GPU code.
4. Choose **Runtime > Run all**.
5. Record the pandas and scikit-learn versions Colab reports if you plan to quote
   the results.

Colab was not executed in the authoring environment. Its package versions may
differ, so treat small differences in the metrics as environment evidence, not as
a failure. The authoring run used Windows 11, Python 3.12.10, and CPU only.

## What a healthy run looks like

These are the results from the verified authoring run. Your values should match
closely because the data is generated from a fixed seed; a different scikit-learn
version can still move the last digit.

| Check | Verified result | What to expect |
| --- | --- | --- |
| House rows and split | 600 rows; 450 train / 150 test | Same, unless you edit `make_houses` |
| Baseline MAE / RMSE | 51,734 / 66,281 | Within a few hundred dollars |
| Linear MAE / RMSE / R-squared | 21,708 / 27,354 / 0.829 | R-squared roughly 0.82-0.84 |
| Ridge MAE / RMSE / R-squared | 21,699 / 27,382 / 0.829 | Nearly identical to linear |
| Top coefficients (standardized) | area 46,020; bedrooms 25,913; age -14,158; distance -14,062; garage 7,129 | Same order and signs |
| Student rows and split | 500 rows; 375 train / 125 test | Same |
| Majority baseline | 0.512 | Close to 0.51 |
| Class balance | 0.509 / 0.491 | Close to even |
| Confusion matrix | `[[51, 13], [21, 40]]` | Same shape; counts may shift by a few |
| Logistic metrics | accuracy 0.728; precision 0.755; recall 0.656; F1 0.702 | Each within about 0.03 |

If a metric is far outside these ranges, check the kernel state and the seed
before you change the model. The most common cause is a modified generator cell
that ran before the original one.

## Artifacts

| Path | What it is | Keep it? |
| --- | --- | --- |
| `notebooks/foundations/outputs/` | Directory created by the first cell | No; it is empty for this notebook |
| Executed `.ipynb` | Code, outputs, and your notes | Yes; this is the evidence for the notebook component |

This notebook writes no CSV, model, or figure files. The two tables exist only in
memory, which is why the lab loads or regenerates the CSV explicitly. The
repository `.gitignore` excludes `outputs/` and generated data, so no run output
is committed. Copy anything you need into a submission folder outside the
repository.

## Troubleshooting

| Symptom | Diagnosis | Fix |
| --- | --- | --- |
| `AssertionError` on `r2_score(...) > 0.5` | Cells ran out of order or the generator was edited | Restart the kernel and run all cells |
| Baseline MAE is not about 51,734 | Different data because the seed or generator changed | Check `SEED = 42` and compare `make_houses` with the repository version |
| `ValueError: could not convert string to float` | `neighbourhood` was added to `feature_columns` without encoding | One-hot encode it, or keep the five numeric features |
| `UndefinedMetricWarning` for precision or recall | The model predicted one class only | Print `np.unique(pred)` and the confusion matrix; check the threshold |
| `ModuleNotFoundError: sklearn` | The kernel uses a different interpreter | Print `sys.executable` and select the `.venv` kernel |
| Results change on every run | The kernel kept old variables or the seed was removed | Restart, run all, and confirm `random_state=SEED` on the split and models |
| Confusion matrix has the wrong shape | Labels are not 0/1 or the matrix was read transposed | Print `np.unique(y_test_c)`; rows are actual, columns are predicted |

When a cell fails, record the exact message, the cell number, `sys.executable`,
and the package versions. That record is lab evidence.

## Submission checkpoint

Before starting the lab, confirm:

- [ ] The notebook ran top to bottom in a fresh kernel with no failed cell.
- [ ] The baseline and model metrics match the healthy-run table within the stated
      tolerance.
- [ ] You can explain why the ridge result is almost identical to linear here.
- [ ] You can compute precision and recall from the printed confusion matrix
      without the notebook's help.
- [ ] You can name one feature the notebook leaves out and one consequence of that
      choice.

Next: the [lab brief](lab.md) uses the same house table in a new business
scenario with a latency budget, a fixed decision threshold, and a required model
card. The [assessment](assessment.md) scores the notebook, the lab, and your
reflection.

---

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)
