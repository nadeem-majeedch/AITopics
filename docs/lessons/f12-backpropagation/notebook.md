# F12 guided notebook

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)

**Notebook file:** `notebooks/foundations/f12_backpropagation.ipynb`  
**Hardware:** CPU by default; uses CUDA only if `torch.cuda.is_available()` is true.  
**Time:** About 3 hours including the explanations; the code runs in under a minute.  
**Execution status:** Verified on Windows 11 CPU with Python 3.12.10 and
PyTorch 2.4.1+cpu. The optional GPU branch was **not** executed in the authoring
environment.

## What the notebook does

| Notebook section | What you do | Evidence produced |
| --- | --- | --- |
| 1. Tensors | Add and multiply tensors; check broadcasting | `a + b` shape `(2, 2)`, `a @ b` shape `(2,)`, batch result `(8, 4)` |
| 2. Automatic differentiation | Differentiate `y = x^2 + 3x` | `dy/dx at x=2: 7.0` |
| 3. Numerical gradient check | Compare autograd with a central difference | autograd `-0.346939`, numeric `-0.346988` |
| 4. Model, loss, optimizer | Build a 337-parameter MLP with `BCEWithLogitsLoss` and Adam | Model summary and `parameters: 337` |
| 5. Train | Run 200 epochs, printing every 50th | Epoch 50/100/150/200 losses; final train 0.948, validation 0.945 |
| 6. Backpropagation summary | Read the shape table and close the loop | `outputs/f12_training_curves.png` |
| Check your work | Review the module checklist | Your notes |

The figure is saved from section 5; section 6 is a written summary, not new code.

## Run it locally

```powershell
cd C:\ai-course\AITopics
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/cpu.txt
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
python -m jupyter lab notebooks/foundations/f12_backpropagation.ipynb
```

The version check matters. If it prints a CPU build, the notebook will run on CPU
and print `device cpu`. That is a supported path, not a degraded one.

### Visual Studio Code

1. Open the repository folder.
2. Open `notebooks/foundations/f12_backpropagation.ipynb`.
3. Select the `.venv` kernel that has PyTorch installed.
4. Use **Restart Kernel and Run All Cells**, then save the notebook with outputs.

### Where the figure goes

`outputs/` is relative to the kernel's working directory. Launch JupyterLab from
the repository root and the figure lands in `E:\AITopics\outputs\`; launch from
`notebooks/foundations/` and it lands beside the notebook. Find it with a file
search for `f12_training_curves.png` if you are unsure. The repository
`.gitignore` excludes both locations.

## Run it on Google Colab

Colab is optional. It provides a GPU on some runtimes, which changes only the
printed device line, not the code.

1. Upload the notebook to Colab.
2. Choose **Runtime > Change runtime type**. CPU is enough; select a GPU only if
   you want to see the device branch.
3. Run all cells.
4. If you selected a GPU, expect `device cuda` and slightly different timings.
   Accuracy may differ in the last decimal place because GPU kernels are not
   bitwise identical to CPU kernels.

Colab was **not** executed while writing this page, and no GPU run is claimed.
If you use Colab, report it as your environment, not as the course baseline.

## What a healthy run looks like

Values from the verified Windows 11 CPU run:

| Check | Verified result | What to expect |
| --- | --- | --- |
| PyTorch version | `2.4.1+cpu` | Any 2.4.x; record yours |
| Device | `cpu`, CUDA `False` | `cuda` only if you have a working GPU build |
| `a + b` | shape `(2, 2)`, values `[[11, 22], [13, 24]]` | Exact |
| `a @ b` | `tensor([50., 110.])` | Exact |
| Batch product | `(8, 3) @ (3, 4)` gives `(8, 4)` | Exact |
| Autograd derivative | `7.0` | Exact, asserted |
| Analytic vs numeric gradient | `-0.346939` vs `-0.346988` | Within `1e-2`; second run may move in the last digits |
| Parameters | 337 | Must be 337 |
| Epoch 50 | train loss 0.146, val loss 0.153, val acc 0.950 | Close |
| Epoch 200 | train loss 0.121, val loss 0.177, val acc 0.945 | Validation loss above its epoch-50 value |
| Final accuracy | train 0.948, validation 0.945 | Validation above 0.90, asserted |
| Figure | `f12_training_curves.png` exists | Assertion enforces it |

The notebook asserts `val_acc > 0.90`. If that fails, check scaling and the number
of epochs before changing the assertion.

!!! note "A naming detail in this notebook"
    The notebook calls its held-out 25% split "validation" because it is used to
    watch for overfitting. In a real project, keep three splits: train, validation
    for tuning and early stopping, and test for the final single evaluation. The
    [lab brief](lab.md) uses all three.

## Artifacts

| File | Produced by | Keep it? |
| --- | --- | --- |
| `outputs/f12_training_curves.png` | Section 5, after training | Yes for the lab discussion; copy it outside the repository |

The generated `outputs/` folder is **not committed**. Rerun the notebook to
recreate the curve. If you compare runs, save each curve under a different name
outside the repository, for example `curves_baseline.png` and `curves_wider.png`.

## Troubleshooting

| Symptom | Diagnosis | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: torch` | PyTorch is not installed in this kernel | `python -m pip install -r requirements/cpu.txt`; reselect the kernel |
| `device cuda` never appears | CPU wheel, no NVIDIA GPU, or driver mismatch | Check `torch.version.cuda` and `nvidia-smi`; the CPU path is fine |
| Assertion on `x.grad == 7.0` fails | `x` created as an integer tensor with no gradient | Use `torch.tensor(2.0, requires_grad=True)` |
| Gradient check is far off | `eps` changed, or a different loss was used | Restore `epsilon = 1e-3` and the mean-squared-error loss |
| `val_acc > 0.90` assertion fails | Features not standardized, or too few epochs | Rerun scaling cells, keep 200 epochs, check the seed |
| Validation loss is below training loss | Normal early in training, or dropout is active during evaluation | Call `model.eval()` and use `torch.no_grad()`; compare later epochs |
| Curves show a flat line at the start | Plot index is a checkpoint counter, not the epoch number | Read the x-axis label; checkpoints are every 10 epochs |
| Figure is not in `notebooks/foundations/outputs/` | JupyterLab started from the repository root | Search for the file, or relaunch from the notebook folder |
| Second `backward()` raises an error | The graph was freed after the first call | Recompute the forward pass; do not reuse a freed graph |

Record the exact error, your `torch.__version__`, the device, and the cell that
failed if the problem is not listed.

## Submission checkpoint

- [ ] The notebook ran top to bottom in a fresh kernel.
- [ ] The device line is recorded, whether `cpu` or `cuda`.
- [ ] The autograd value is 7.0 and the gradient check agrees.
- [ ] The parameter count is 337.
- [ ] Final train and validation accuracies are recorded.
- [ ] You can point to the epoch where validation loss starts rising.
- [ ] `f12_training_curves.png` exists and you can describe both panels.

Next: the [F12 lab brief](lab.md) applies these ideas to a new dataset and asks
for an early-stopping decision. Then check the [assessment](assessment.md).

---

**Module path:** [Lesson](index.md) · **Guided notebook** · [Lab brief](lab.md) · [Assessment](assessment.md)
