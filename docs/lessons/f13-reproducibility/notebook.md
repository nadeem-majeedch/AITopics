# F13 guided notebook

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)

**Notebook file:** `notebooks/foundations/f13_reproducibility.ipynb`
**Open notebook:** [F13 guided notebook](../../notebooks/foundations/f13_reproducibility.ipynb)
**Hardware:** CPU-only core. A GPU, if present, is used automatically for timing
and training; the notebook does not require one.
**Time:** About 3 hours including the explanations; the code runs in about a
minute.
**Execution status:** Verified on Windows 11 CPU with Python 3.12.10 and
PyTorch 2.4.1+cpu. The GPU display branch was **not** executed in the authoring
environment.

## What the notebook does

| Notebook section | What you do | Evidence produced |
| --- | --- | --- |
| 1. A seed controls sequences | Draw two tensors from seed 123 | Identical values, for example `-0.1115, 0.1204, -0.3696, -0.2404` |
| 2. CPU versus GPU timing | Warm up, then time five 512 x 512 products | `device: cpu`, mean `0.95 ms` |
| 3. Determinism is a spectrum | Request deterministic algorithms | Flag enabled; prints `deterministic algorithms requested` |
| 4. A tiny tracker | Append one JSONL record and read it back | `outputs/f13_runs.jsonl` with a start record |
| 5. Three seeds | Train the same model with seeds 7, 17, 27 | Three accuracies and losses, appended to the log |
| 6. Read back and report | Parse the log, compute mean and spread, write the report | `outputs/f13_environment_report.json` |
| Check your work | Review the five-item checklist | Your notes |

## Run it locally

```powershell
cd C:\ai-course\AITopics
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/cpu.txt
python -m jupyter lab notebooks/foundations/f13_reproducibility.ipynb
```

For the optional GPU comparison, read
[requirements/gpu.txt](../../technical/foundation-assets.md#cpu-and-gpu-requirements) and install the CUDA wheel
that matches your driver. The CPU path finishes this notebook without changes.
The CPU-only package list is in
[requirements/cpu.txt](../../technical/foundation-assets.md#cpu-and-gpu-requirements).

### Visual Studio Code

1. Open the repository folder.
2. Open `notebooks/foundations/f13_reproducibility.ipynb`.
3. Select the `.venv` kernel.
4. Use **Restart Kernel and Run All Cells** and save with outputs.

### Thread setting

The notebook calls `torch.set_num_threads(2)`. On a small machine this keeps
timings stable; on a large one it deliberately leaves cores idle. If you change
it, record the value with your timing, because thread count changes matrix
multiplication performance and can change floating-point reduction order.

## Run it on Google Colab

Colab is optional. A GPU runtime is useful only if you want to see the device
branch and a GPU timing row.

1. Upload the notebook.
2. Choose **Runtime > Change runtime type**: CPU for the standard path, GPU only
   for comparison.
3. Run all cells.
4. Download `outputs/f13_runs.jsonl` and `outputs/f13_environment_report.json`
   before the session ends; `/content` is temporary.

Colab was **not** executed while writing this page. A Colab run is a different
environment with different versions, so its numbers are a comparison point, not a
reproduction of the verified result.

## What a healthy run looks like

Values from the verified Windows 11 CPU run:

| Check | Verified result | What to expect |
| --- | --- | --- |
| Python | 3.12.10 | 3.10-3.12; record yours |
| PyTorch | 2.4.1+cpu | Any 2.4.x |
| CUDA available | `False` | `True` only with a working GPU build |
| Seeded tensors | Identical | Assertion enforces equality |
| Device for timing | `cpu` | `cuda` only on the optional path |
| 512 x 512 matmul | 0.95 ms | Machine-dependent; report yours |
| Determinism flag | Enabled | Assertion enforces it |
| Log after first record | 1 record | Must be 1 before training |
| Seed 7 | accuracy 0.848, loss 0.314 | Close |
| Seed 17 | accuracy 0.872, loss 0.257 | Close |
| Seed 27 | accuracy 0.904, loss 0.246 | Close |
| Mean accuracy | 0.875 | Rounded to three decimals |
| Standard deviation | 0.023 | Must exceed 0.005 for the assertion |
| Run records | 3 | Must be 3 |
| Environment report | `outputs/f13_environment_report.json` | Must exist |

The notebook asserts that the standard deviation exceeds 0.005. That assertion
guards against a broken seed loop: if all three runs are identical, the model is
probably not being reinitialized.

## Artifacts

| File | Contents | Keep it? |
| --- | --- | --- |
| `outputs/f13_runs.jsonl` | One JSON object per line: start record plus one record per seed | Yes; copy it into your submission |
| `outputs/f13_environment_report.json` | Versions, platform, device, seed list, mean and standard deviation | Yes; copy it into your submission |

Both files are generated under `outputs/`, which is **not committed** to Git.
Rerunning the notebook recreates them. The notebook deletes an old run log at the
start, so a clean run always produces exactly three `run` records. If you copy
the log into a submission folder, keep the JSON Lines format intact; do not
pretty-print it into a single JSON array.

## Troubleshooting

| Symptom | Diagnosis | Fix |
| --- | --- | --- |
| `cuda available: False` | No GPU, CPU wheel, or driver mismatch | Expected on many machines; the CPU path is complete |
| `ModuleNotFoundError: torch` | PyTorch is not installed in this kernel | Install `requirements/cpu.txt` and reselect the kernel |
| Timing is far above 1 ms | Background load, many threads, or no warm-up | Close other work, keep the warm-up loop, record the device |
| `are_deterministic_algorithms_enabled` assertion fails | Older PyTorch or the call was removed | Check the version; keep the call before the assertion |
| Standard deviation assertion fails | Seeds not applied, or the model built once outside the loop | Rebuild the model inside the loop; keep `set_seed(seed)` first |
| JSONL has 6 run records | The log was appended without the cleanup line | Delete `outputs/f13_runs.jsonl` and rerun from the top |
| JSON decode error when reading the log | A partial line from an interrupted run | Delete the file and rerun; do not hand-edit timestamps |
| Report is missing | Kernel started in another directory | Search for `f13_environment_report.json`; rerun from the notebook folder |
| GPU timing looks slower than CPU | Small matrix and transfer overhead | Expected; test a larger matrix before drawing conclusions |

If a failure is not listed, record the exact message, `sys.executable`,
`torch.__version__`, the device, and the cell that failed.

## Submission checkpoint

- [ ] The notebook ran top to bottom in a fresh kernel.
- [ ] Both seeded tensors are identical.
- [ ] The device used for timing is recorded.
- [ ] The three accuracies and losses match the table above within rounding.
- [ ] Mean and standard deviation are 0.875 and 0.023.
- [ ] `f13_runs.jsonl` has one start record and three run records.
- [ ] `f13_environment_report.json` exists and contains no personal paths.

Next: the [F13 lab brief](lab.md) turns this into a hardware and reproducibility
audit with an explicit CPU-only completion path. Then check the
[assessment](assessment.md).

---

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)
