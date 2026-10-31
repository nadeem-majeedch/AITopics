# F07 guided notebook

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)

**Notebook file:** `notebooks/foundations/f07_supervised_unsupervised.ipynb`  
**Hardware:** CPU-only  
**Time:** 2-3 hours including the cluster profile reading

The notebook generates 420 synthetic customers, clusters them without using the
withheld segment label, evaluates the clusters against that label, and then trains
a supervised classifier for comparison. This guide maps each section to the
evidence it produces and shows what a correct run prints.

## What the notebook does

| Section | What you do | Evidence produced |
| --- | --- | --- |
| 1. A table with hidden structure | Generate customers, select four features, standardize | Feature matrix `(420, 4)`, means near zero |
| 2. Choose the number of clusters | Fit k-means for `k=2` to `k=6`, record inertia and silhouette | Silhouette peaks at `k=3` |
| 3. Fit and profile | Fit three clusters, print feature means and sizes | Sizes 143/110/167, profile table |
| 4. Evaluate with withheld labels | Compare clusters with `latent_segment` using ARI | ARI 1.0 |
| 5. Visualize with PCA | Project to two components and save a scatter plot | 93.8% + 3.0% variance, `f07_clusters.png` |
| 6. Supervised versus unsupervised | Train logistic regression on a stratified split | Held-out accuracy 1.0 |
| Check your work | Review the five properties | Your notes |

The withheld label is used **only** in section 4 and section 6. It never enters
the clustering feature matrix.

## Run it locally

```powershell
cd C:\ai-course\AITopics
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/notebooks.txt
python -m jupyter lab notebooks/foundations/f07_supervised_unsupervised.ipynb
```

With Visual Studio Code:

1. Open the repository folder.
2. Open `notebooks/foundations/f07_supervised_unsupervised.ipynb`.
3. Select the `.venv` interpreter as the kernel.
4. Run **Restart Kernel and Run All Cells**.

The notebook uses the `Agg` backend, so the cluster plot is saved to a file
instead of displayed inline. Open `outputs/f07_clusters.png` after the run.

## Google Colab (optional)

Upload the notebook, choose a CPU runtime, and run all cells. pandas, NumPy,
scikit-learn, and matplotlib are preinstalled, so no install cell is needed.
Download `outputs/f07_clusters.png` before the session ends; Colab's disk is
temporary.

Colab was **not** executed in the authoring environment. The results below are
from Windows 11, Python 3.12.10, CPU-only.

## What a healthy run looks like

| Check | Verified result | What to expect |
| --- | --- | --- |
| Feature matrix | `(420, 4)` | 420 rows, four standardized features |
| Standardized means | Near 0 | Assertion tolerance 1e-9 |
| Silhouette, `k=2` | 0.619 | Healthy but below `k=3` |
| Silhouette, `k=3` | 0.707 | Maximum in the sweep |
| Silhouette, `k=4` | 0.552 | Lower than `k=3` |
| Silhouette, `k=5` | 0.363 | Weak structure |
| Silhouette, `k=6` | 0.246 | Near the "no substantial structure" band |
| Chosen `k` | 3 | Assertion checks this |
| Cluster sizes | 143, 110, 167 | Sum to 420 |
| Adjusted Rand index | 1.0 | Above 0.5; 1.0 is expected here |
| PCA explained variance | 93.8% and 3.0% | About 96.8% combined |
| Supervised accuracy | 1.0 | Above 0.9; perfect is expected here |
| Saved figure | `outputs/f07_clusters.png` | File exists |

If the silhouette peak moves to a different `k`, the assertion fails. Do not
edit the assertion; check whether the feature list, seed, or standardization
changed.

## Artifacts

| File | What it shows | Keep it? |
| --- | --- | --- |
| `outputs/f07_clusters.png` | Clusters plotted in the first two PCA components | Yes, for the lab or portfolio |
| `outputs/` directory | Created on every run | No; regenerate it |

The repository `.gitignore` excludes `outputs/`, so the figure is not committed.
Copy it into your portfolio folder if you need it in a submission. The notebook
writes no CSV or model file; every table is printed to the notebook output.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: Number of labels is 1` from `silhouette_score` | All rows were assigned to one cluster | Keep `k >= 2`; check that the model actually fitted |
| `ConvergenceWarning: Number of distinct clusters found smaller than n_clusters` | Poor initialization or unscaled features | Increase `n_init`, keep standardization, inspect the data |
| Assertion that the best `k` is 3 fails | Data, feature list, or `k` range changed | Print the score table; restore `make_customers()` and `SEED = 42` |
| ARI is far below 1.0 | `latent_segment` was used as an input, or labels were shuffled | Rebuild `X` from the four features only; never fit on the label |
| `KeyError: 'latent_segment'` | Reading a CSV that omits the withheld column | Use the generated table or the documented dataset version |
| No plot appears in the notebook | `Agg` backend | Open `outputs/f07_clusters.png`; this is expected |
| `FileNotFoundError` when saving the figure | Notebook started outside its folder | Run from the repository root or notebook directory |
| Accuracy prints 1.0 and you distrust it | The synthetic groups are far apart | Check the ARI and the cluster profiles; perfect scores are expected on this table, not on real data |

If a failure is not listed, record the exact error, the printed shape, and your
package versions before changing anything.

## Submission checkpoint

Before starting the lab, confirm:

- [ ] The notebook ran top to bottom and printed `(420, 4)`.
- [ ] You can read the silhouette table and explain why `k=3` was chosen.
- [ ] The cluster sizes are 143, 110, and 167.
- [ ] ARI is 1.0 and you can explain why that is expected here.
- [ ] You can interpret 93.8% plus 3.0% explained variance.
- [ ] `outputs/f07_clusters.png` exists and opens.
- [ ] You can state one thing the supervised accuracy does not prove.

Next: the [lab brief](lab.md) asks you to segment the same customer base under a
stability requirement, choose between three and four segments for a retention
team, and defend the choice.

---

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)
