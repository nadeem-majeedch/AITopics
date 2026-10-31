# M01 guided notebook

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)

**Notebook file:** `notebooks/foundations/m01_environment_check.ipynb`  
**Hardware:** CPU-only; optional GPU cells skip themselves  
**Time:** 2-3 hours including reading the explanations

The notebook is a repository file, not a web page. You run it from your clone in
JupyterLab, Visual Studio Code, or Google Colab. This guide explains how to open
it, what each section proves, and what to do when a cell fails.

## What the notebook does

| Section | What you do | Evidence produced |
| --- | --- | --- |
| 1. Runtime and packages | Read the interpreter and library versions | Version table |
| 2. Hardware | Detect CPU cores, RAM, and free disk | Hardware dictionary |
| 3. GPU | Query `nvidia-smi` and PyTorch; skip safely if absent | GPU status and reason |
| 4. Seeded randomness | Draw the same bootstrap sample twice | Identical arrays |
| 5. Classifier | Train logistic regression on scikit-learn digits | Accuracy and classification report |
| 6. Persistence | Save, reload, and compare predictions | Byte-identical predictions |
| 7. Timing | Time a 768 x 768 matrix multiply on CPU and optional GPU | Seconds and GFLOP/s |
| 8. Checksums | Export CSV, write SHA-256, verify it | Verified checksum |
| 9. Report | Assemble and write `environment_report.json` | Machine-readable report |
| 10. Check your work | Review the checklist and reflection prompts | Your notes |

## Run it locally

These commands assume you cloned the repository to `C:\ai-course\AITopics` and
created `.venv` as described in the [lesson](index.md#1-interpreter-packages-and-virtual-environments).

```powershell
cd C:\ai-course\AITopics
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/notebooks.txt
python -m jupyter lab notebooks/foundations/m01_environment_check.ipynb
```

Alternative with Visual Studio Code:

1. Open the repository folder.
2. Open `notebooks/foundations/m01_environment_check.ipynb`.
3. Select the `.venv` interpreter as the kernel.
4. Use **Restart Kernel and Run All Cells**.

Do not run cells out of order. If you experimented, restart the kernel before
your final run so the saved notebook reflects a clean top-to-bottom execution.

## Run it on Google Colab

Colab is optional but recommended for the lab, where you compare two
environments.

1. Open [Google Colab](https://colab.research.google.com/).
2. Choose **File > Upload notebook** and select
   `notebooks/foundations/m01_environment_check.ipynb` from your clone.
3. Choose **Runtime > Change runtime type**. Select **CPU** for the standard
   path. A GPU is optional.
4. Choose **Runtime > Run all**.
5. Open the **Files** pane and download `outputs/environment_report.json`.
6. Before the session ends, save the executed notebook to Drive or GitHub.
   `/content` is temporary.

Colab installs its own versions of NumPy, scikit-learn, and matplotlib. They will
probably differ from your local versions. That difference is useful lab evidence,
not an error. Record it instead of trying to force both environments to match.

!!! warning "Upload the notebook, not your whole repository"
    Do not upload datasets or model weights to Colab. This notebook needs none.
    Do not paste tokens or `.env` contents into cells.

## What a healthy run looks like

These are results from the verified Windows 11 run on 2026-10-30. Your versions,
timings, and accuracy will differ slightly.

| Check | Verified result | What to expect |
| --- | --- | --- |
| Python | 3.12.10 | 3.10-3.12; record your version |
| Seeded arrays | Identical | Must be `True` |
| Test accuracy | 0.9778 | Roughly 0.96-0.99 |
| Reloaded predictions | Identical | Must be `True` |
| CPU matrix time | 1.40 ms | Machine-dependent |
| GPU timing | Skipped, no PyTorch in that environment | Skipped or recorded, never required |
| Checksum verified | `True` | Must be `True` |
| Report | `outputs/environment_report.json` | Must exist and name your runtime |

The notebook raises an assertion if a determinism, reload, or checksum check
fails. Read the assertion message before changing code.

## Artifacts

After a successful run, the notebook writes to an `outputs/` directory beside
the notebook:

| File | Size | Keep it? |
| --- | --- | --- |
| `environment_report.json` | A few KB | Yes; copy it into your portfolio submission |
| `m01_digits_logreg.joblib` | About 8 KB | No; regenerate it by rerunning the notebook |
| `digits.csv` | About 260 KB | No; regenerate it from scikit-learn |
| `digits.csv.sha256` | One line | Yes, if your report quotes the hash |
| `m01_confusion_matrix.png` | About 60 KB | Only if your report needs the figure |

The repository `.gitignore` excludes `outputs/`, so the notebook never adds
these generated files to Git. Copy the report out of `outputs/` only when you
assemble a submission folder outside the repository.

## Troubleshooting

| Symptom | Diagnosis | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: sklearn` | Kernel uses another Python | Print `sys.executable`; select the `.venv` kernel |
| `ModuleNotFoundError: torch` | PyTorch is not installed | Expected. The CPU path continues; GPU timing is skipped |
| `nvidia-smi` works but `torch` is absent | Driver is installed, PyTorch is not | Install PyTorch only if a later module needs it |
| `FileNotFoundError: outputs` | Notebook started from an unexpected directory | Restart from the repository or notebook folder; the first cell creates `outputs/` |
| Plot cell fails | Matplotlib backend problem | The notebook sets the non-interactive `Agg` backend; reinstall matplotlib if the import fails |
| Colab disconnects | Free runtime timeout | Rerun and save artifacts earlier |
| Accuracy is much lower than 0.96 | Wrong cell order or modified data | Restart the kernel and run all cells |
| `PermissionError` on Windows | OneDrive or antivirus lock | Move the repository to a short local path |

If a cell fails for a reason not listed here, record:

1. The exact error message.
2. The output of `python -c "import sys; print(sys.executable)"`.
3. Your operating system and package versions.
4. The cell you ran and the cells before it.

That record is what the lab asks you to diagnose.

## Submission checkpoint

Before starting the lab, confirm:

- [ ] The notebook ran top to bottom in a fresh kernel.
- [ ] `outputs/environment_report.json` exists.
- [ ] The report contains your Python version and hardware.
- [ ] The determinism and checksum checks passed.
- [ ] You can explain why the GPU section was skipped or what it recorded.

Next: the [M01 lab brief](lab.md) asks you to reproduce this notebook in a second
environment and write the comparison report.

---

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)
