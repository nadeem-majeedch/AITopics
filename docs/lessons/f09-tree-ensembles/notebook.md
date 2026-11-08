# F09 guided notebook

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)

**Notebook file:** `notebooks/foundations/f09_tree_ensembles.ipynb`
**Open notebook:** [F09 guided notebook](../../notebooks/foundations/f09_tree_ensembles.ipynb)
**Hardware:** CPU-only; the forest uses all available cores through `n_jobs=-1`
**Time:** 2-3 hours including reading the explanations
**Execution status:** verified on Windows 11 CPU with Python 3.12.10. Colab and GPU paths were not executed.

The notebook generates its own 500-row student table. You do not need the CSV,
a download, or a GPU to run it.

## What the notebook does

| Section | What you do | Evidence produced |
| --- | --- | --- |
| 1. Data and preprocessing | Generate 500 students; build a `ColumnTransformer` for scaling and one-hot encoding | Shape `(500, 6)` and positive rate 0.49 |
| 2. A single tree and the depth trade-off | Fit trees at depth 2, 5, and unlimited | Train/test table 0.659/0.656, 0.811/0.696, 1.000/0.664 |
| 3. Random forest | Fit 200 trees with `min_samples_leaf=5` | Test accuracy 0.76 |
| 4. Gradient boosting | Fit 200 histogram rounds at learning rate 0.05 | Test accuracy 0.736 |
| 5. Cross-validation | Re-score four models on identical stratified 5-fold splits | Mean and standard deviation per model |
| 6. Feature importance | Rank the forest's impurity importances | Study 0.267, attendance 0.256, prior 0.233, sleep 0.126 |
| Check your work | Review the five closing claims | Your notes |

Section 5 is the one to quote in a report. Sections 2-4 each use a single
train/test split, which is useful for teaching but noisy for ranking.

## Run it locally

```powershell
cd C:\ai-course\AITopics
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/notebooks.txt
python -m jupyter lab notebooks/foundations/f09_tree_ensembles.ipynb
```

With Visual Studio Code:

1. Open the repository folder.
2. Open `notebooks/foundations/f09_tree_ensembles.ipynb`.
3. Select the `.venv` interpreter as the kernel.
4. Choose **Restart Kernel and Run All Cells**.

The forest uses `n_jobs=-1`, so it will use multiple cores. That changes speed,
not results, because `random_state` is fixed. If you edited cells, restart before
your final run.

## Run it on Google Colab

Colab is optional and useful if your laptop is slow. Upload only the notebook; the
data is generated in the first code cells.

1. Open [Google Colab](https://colab.research.google.com/).
2. Choose **File > Upload notebook** and select
   `notebooks/foundations/f09_tree_ensembles.ipynb`.
3. Keep the runtime as **CPU**. No GPU is needed or used.
4. Choose **Runtime > Run all**.
5. Record the scikit-learn version if you quote the CV numbers.

Colab was not executed in the authoring environment. Colab may ship a different
scikit-learn version, which can change tree construction at the last decimal.
Record the version instead of forcing it to match.

## What a healthy run looks like

| Check | Verified result | What to expect |
| --- | --- | --- |
| Data shape | `(500, 6)` | Same |
| Positive rate | 0.49 | 0.47-0.51 |
| Depth 2 train / test | 0.659 / 0.656 | Test within about 0.02 |
| Depth 5 train / test | 0.811 / 0.696 | Gap about 0.10-0.13 |
| Unlimited train / test | 1.000 / 0.664 | Train must be 1.000 |
| Depth 5 leaves | 25 | Close; depends on ties |
| Unlimited leaves | 86 | Close |
| Random forest test | 0.76 | 0.72-0.79 |
| Gradient boosting test | 0.736 | 0.70-0.77 |
| CV logistic | 0.742 ± 0.027 | Mean within 0.02 |
| CV random forest | 0.714 ± 0.033 | Mean within 0.02 |
| CV gradient boosting | 0.678 ± 0.044 | Mean within 0.02 |
| CV depth-5 tree | 0.662 ± 0.044 | Mean within 0.02 |
| Top importances | study 0.267, attendance 0.256, prior 0.233, sleep 0.126 | Same order |

The notebook asserts that the unlimited tree reaches 1.000 training accuracy and
that the best CV mean exceeds 0.65. A failure means the data or the split changed,
not that the lesson is wrong.

## Artifacts

| Path | What it is | Keep it? |
| --- | --- | --- |
| `notebooks/foundations/outputs/` | Directory created by the first cell | No; this notebook writes no files |
| Executed `.ipynb` | Code, printed tables, and your notes | Yes; this is the notebook evidence |

No model, CSV, or figure is saved. If you want a record of the CV table, copy it
into a markdown cell or your lab notes. The repository `.gitignore` excludes
`outputs/`, so generated files are never committed.

## Troubleshooting

| Symptom | Diagnosis | Fix |
| --- | --- | --- |
| `AssertionError` on `X.shape == (500, 6)` | The generator cell was edited or skipped | Restart and run all cells in order |
| Unlimited tree does not reach 1.000 training accuracy | `max_depth` was not `None`, or the tree was fitted on the wrong rows | Print `tree.named_steps["model"].get_depth()` and the training row count |
| CV numbers differ from the table by more than 0.02 | Different folds, different `X`/`y`, or a changed seed | Reuse one `cv = StratifiedKFold(5, shuffle=True, random_state=42)` for all models |
| `InvalidParameterError` for `HistGradientBoostingClassifier` | Very old scikit-learn version | Install `requirements/notebooks.txt`; the notebook targets a current release |
| `NotFittedError` on `forest.named_steps["pre"]` | The pipeline was not fitted before reading feature names | Read names only after `.fit` |
| Forest training takes a long time | `n_jobs=-1` competing with other work, or many more trees than 200 | Close other notebooks; keep 200 trees for the comparison |
| Feature importance sums to less than 1 | The notebook prints only the top eight rows | Print the full series with `.to_string()` |

Record the error, the cell number, your scikit-learn version, and the output of
`python -c "import sys; print(sys.executable)"` when asking for help.

## Submission checkpoint

Before starting the lab, confirm:

- [ ] The notebook ran top to bottom in a fresh kernel with no failed cell.
- [ ] You can explain why the unlimited tree has a 1.000 training score and a
      0.664 test score.
- [ ] You can explain why the forest's single-split 0.76 is not proof that it beats
      logistic regression.
- [ ] You can state the CV mean and standard deviation for all four models.
- [ ] You can explain why preprocessing sits inside the pipeline.

Next: the [lab brief](lab.md) turns this comparison into a cost-sensitive decision
with a written justification. The [assessment](assessment.md) scores the notebook,
the lab, and your reflection.

---

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)
