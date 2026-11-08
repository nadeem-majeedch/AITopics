# F10 guided notebook

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)

**Notebook file:** `notebooks/foundations/f10_metrics_validation.ipynb`
**Open notebook:** [F10 guided notebook](../../notebooks/foundations/f10_metrics_validation.ipynb)
**Hardware:** CPU-only; matplotlib uses the non-interactive `Agg` backend
**Time:** 2-3 hours including reading the explanations
**Execution status:** verified on Windows 11 CPU with Python 3.12.10. Colab and GPU paths were not executed.

The notebook generates its own 500-row student table and writes one figure. It
needs no download and no GPU.

## What the notebook does

| Section | What you do | Evidence produced |
| --- | --- | --- |
| 1. An imbalanced target | Derive `at_risk` from `final_score < 70`; compute the base rate | Positive rate 0.212; majority accuracy 0.788 |
| 2. Confusion matrix and metrics | Split 70/30, fit logistic regression, label at 0.5 | Matrix `[[114, 4], [8, 24]]`; accuracy 0.920, precision 0.857, recall 0.750, F1 0.800, ROC-AUC 0.963, PR-AUC 0.892 |
| 3. Threshold selection | Sweep 0.3, 0.4, 0.5, 0.6 | Precision/recall/F1 table; 0.3 gives recall 0.906 |
| 4. Cross-validation | Stratified 5-fold CV with PR-AUC | Fold scores 0.736-0.898; mean 0.852 ± 0.059 |
| 5. Overfitting curve | Sweep tree depth 1-15 on a train/validation split | Best validation depth 4; depth 15 train 1.000, validation 0.820; saved figure |
| 6. Target leakage | Add `final_score`, fit, then remove it | Accuracy 1.000 with leakage versus 0.860 without |
| Check your work | Review the five closing claims | Your notes |

Sections 2 and 3 use the test set for both headline metrics and threshold
selection. That is a teaching shortcut, not a recommended protocol. The lab
separates validation from test.

## Run it locally

```powershell
cd C:\ai-course\AITopics
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/notebooks.txt
python -m jupyter lab notebooks/foundations/f10_metrics_validation.ipynb
```

With Visual Studio Code:

1. Open the repository folder.
2. Open `notebooks/foundations/f10_metrics_validation.ipynb`.
3. Select the `.venv` interpreter as the kernel.
4. Choose **Restart Kernel and Run All Cells**.

The first cell sets `matplotlib.use("Agg")` so the notebook can save a figure
without a display. If you want to see plots inline, comment that line out after
the run; do not change it before saving your final evidence, because headless
environments need it.

## Run it on Google Colab

Colab is optional and works for this notebook because everything is CPU-only.

1. Open [Google Colab](https://colab.research.google.com/).
2. Choose **File > Upload notebook** and select
   `notebooks/foundations/f10_metrics_validation.ipynb`.
3. Keep the runtime as **CPU**.
4. Choose **Runtime > Run all**.
5. Download `outputs/f10_overfitting_curve.png` before the session ends if you
   want the figure.

Colab was not executed in the authoring environment. `/content` is temporary, and
package versions may differ. Record what you observe instead of assuming the
authoring environment.

## What a healthy run looks like

| Check | Verified result | What to expect |
| --- | --- | --- |
| Positive rate | 0.212 | 0.19-0.23 |
| Majority accuracy | 0.788 | 0.77-0.81 |
| Test rows | 150 | Same |
| Confusion matrix | `[[114, 4], [8, 24]]` | Counts may shift by a few |
| Accuracy | 0.920 | 0.89-0.94 |
| Precision | 0.857 | 0.82-0.89 |
| Recall | 0.750 | 0.70-0.80 |
| F1 | 0.800 | 0.76-0.84 |
| ROC-AUC | 0.963 | Above 0.93 |
| PR-AUC | 0.892 | Above 0.85 |
| Threshold 0.3 | precision 0.763, recall 0.906 | Recall above 0.85 |
| Threshold 0.6 | precision 0.909, recall 0.625 | Recall near 0.63 |
| CV PR-AUC | 0.852 ± 0.059 | Mean above 0.80 |
| Best validation depth | 4 | 3-6 |
| Depth 15 | train 1.000, validation 0.820 | Train must be 1.000 |
| Leakage accuracy | 1.000 versus 0.860 | The gap must be large |

If the leakage comparison does not separate sharply, check that `final_score` was
added to the correct rows before the split. A misaligned column can produce a
plausible but meaningless result.

## Artifacts

| Path | What it is | Keep it? |
| --- | --- | --- |
| `notebooks/foundations/outputs/f10_overfitting_curve.png` | Training and validation accuracy versus tree depth | Optional; include it if your report discusses the curve |
| Executed `.ipynb` | Code, printed metrics, and your notes | Yes; this is the notebook evidence |

The figure is a small PNG. The repository `.gitignore` excludes `outputs/`, so the
notebook never commits it. Regenerate it by rerunning the notebook rather than
copying it between machines. This notebook does not save a model or a CSV.

## Troubleshooting

| Symptom | Diagnosis | Fix |
| --- | --- | --- |
| `AssertionError` on `0.1 < y.mean() < 0.35` | The generator changed, or `at_risk` was defined differently | Restart and run all cells; check the `< 70` cutoff |
| ROC-AUC assertion fails | Probabilities were taken from the wrong column | Use `predict_proba(...)[:, 1]`, not `[:, 0]` |
| `average_precision_score` returns a strange value | Arguments are reversed or labels are not 0/1 | Signature is `(y_true, y_score)`; print `np.unique(y)` |
| Figure file is missing | Backend or working-directory problem | Keep `matplotlib.use("Agg")`; confirm the kernel starts in the notebook folder |
| Best depth is far from 4 | A different split or seed was used | Check `random_state=SEED` and the 70/30 split |
| Leakage model does not reach 1.000 | `final_score` was not added, or rows were misaligned | Rebuild `X_leaky = X.copy()` from the same frame, then add the column |
| Threshold table assertion fails | The threshold values or comparison were edited | The assertion checks that recall at 0.3 is at least recall at 0.6 |
| `ModuleNotFoundError: matplotlib` | The kernel uses another interpreter | Print `sys.executable`; install `requirements/notebooks.txt` |

Record the error message, the cell number, and your package versions. That record
is what the lab asks you to diagnose.

## Submission checkpoint

Before starting the lab, confirm:

- [ ] The notebook ran top to bottom in a fresh kernel with no failed cell.
- [ ] You can compute the majority baseline from 0.212 without the notebook.
- [ ] You can explain why 0.920 accuracy still misses 8 at-risk students.
- [ ] You can read the threshold table and state which threshold you would choose
      for a given cost ratio.
- [ ] You can explain why the 1.000 leakage score is the worse model.
- [ ] `outputs/f10_overfitting_curve.png` exists if you plan to use it.

Next: the [lab brief](lab.md) applies these ideas to a new target and a controlled
complexity sweep, ending in a memo that recommends a model. The
[assessment](assessment.md) scores the notebook, the lab, and your reflection.

---

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)
