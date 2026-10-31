# M01 - Python and AI development environment

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Level** | 0 - Orientation and environment |
| **Study time** | 12 hours: 3 h theory, 5 h guided notebook, 3 h lab, 1 h assessment |
| **Hardware** | CPU-only. A GPU check is optional and never required. |
| **Prerequisites** | [M00 plan](../../syllabus/level-0-start.md#m00) and basic Python |
| **You will produce** | An executed notebook, a two-environment report, a dependency lock file, and a short reflection |

## Why this module exists

Most beginners do not abandon AI because the mathematics is too hard. They
abandon it because a notebook imports a package that is installed in a different
Python environment, because CUDA reports "not available" on a machine that has a
GPU, or because yesterday's result cannot be reproduced today.

An **environment** is everything around your code: the Python interpreter, the
installed libraries, the operating system, the hardware, and the settings that
influence execution. This module teaches you to build that environment
deliberately, inspect it, and prove that it works. Every later module depends on
this skill.

!!! note "What this module is not"
    This is not a general Python course. You should already be able to write
    functions, use lists and dictionaries, read a file, and run a command in a
    terminal. If those are shaky, complete a short Python refresher first; the
    [roadmap](../../course/roadmap.md#prerequisites-and-readiness) lists the
    expected level.

## Learning objectives

By the end of this module, you can:

1. Create and activate an isolated Python environment with `venv` or `uv`.
2. Install CPU or CUDA builds of PyTorch that match your machine.
3. Detect available hardware and explain the driver/CUDA/PyTorch relationship.
4. Run and troubleshoot a Jupyter notebook locally and on Google Colab.
5. Apply reproducibility basics: seeds, pinned versions, and recorded hardware.
6. Use Git to clone the course, create a branch, and commit your work.
7. Diagnose the five most common environment failures on Windows 11.

## Before you start

| Requirement | Why it matters |
| --- | --- |
| Python 3.10-3.12 installed | The course is tested on Python 3.12; newer unsupported versions may lack wheels |
| A terminal (PowerShell, Windows Terminal, or Bash) | You will run environment commands, not only notebook cells |
| 8 GB RAM and 10 GB free disk | Enough for the CPU path and a small notebook environment |
| A GitHub account | Clone the course and keep a portfolio |
| A Google account (optional) | Use Colab for the second environment or later GPU labs |

A dedicated GPU is **not** required for M01. If you have an NVIDIA GPU, this
module helps you determine whether your driver and PyTorch build agree. If you
do not, the notebook records that fact and continues on the CPU.

## The concepts you need

### 1. Interpreter, packages, and virtual environments

The **interpreter** is the program that runs Python code (`python.exe` on
Windows). A **package** is a reusable library installed for a particular
interpreter. If you install a package into one interpreter and run a notebook
with another, the import fails even though `pip install` reported success.

A **virtual environment** is a private directory containing its own interpreter
link and its own `site-packages`. It prevents project A's NumPy version from
breaking project B. Create one per course or per project.

=== "Windows PowerShell"

    ```powershell
    cd C:\ai-course
    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    ```

=== "Linux or macOS"

    ```bash
    cd ~/ai-course
    python3.12 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    ```

=== "uv (optional, faster)"

    ```bash
    uv venv --python 3.12 .venv
    # Windows: .venv\Scripts\activate
    source .venv/bin/activate
    uv pip install -r requirements/notebooks.txt
    ```

`uv` is a fast, open-source installer. It is optional; `pip` and `venv` are
enough. Avoid mixing installers inside the same environment unless you
understand the consequences.

**Check which interpreter you are using** before installing anything:

```powershell
python -c "import sys; print(sys.executable)"
```

The output should point inside your `.venv` directory. If it points to
`C:\Users\...\AppData\Local\Programs\Python\...`, the environment is not
activated.

### 2. Dependency resolution and pinning

`pip install scikit-learn` does not install one package. It resolves a graph of
dependencies and picks versions that satisfy every constraint. Two installs made
on different days can therefore produce different environments.

A **requirements file** lists direct dependencies. A **lock file** records the
exact versions that were installed, including indirect dependencies. The course
uses compatible ranges in `requirements/` and asks you to produce a lock file
for each lab.

```powershell
pip install -r requirements/notebooks.txt
pip freeze > requirements.lock
```

Review the lock file before sharing it. It may contain packages you did not
intend to install, and it must never contain credentials or local paths.

### 3. The GPU stack: four layers that must agree

| Layer | What it is | How to check it |
| --- | --- | --- |
| NVIDIA driver | Operating-system software that talks to the GPU | `nvidia-smi` |
| CUDA runtime | GPU programming runtime; PyTorch wheels bundle a compatible copy | `torch.version.cuda` |
| cuDNN | Accelerated deep-learning primitives used by PyTorch | Installed with the PyTorch wheel |
| PyTorch build | CPU-only or CUDA-enabled wheel | `torch.cuda.is_available()` |

The **driver** must be new enough for the CUDA version bundled in the PyTorch
wheel. You usually do **not** need to install the full CUDA toolkit system-wide.
Install the PyTorch wheel that matches your driver from the official PyTorch
installation selector.

**VRAM** is memory on the GPU. A model, its gradients, optimizer state, and
activations must fit in VRAM during training. When they do not, you get an
out-of-memory error even though system RAM is free. Later modules teach memory
reduction techniques; for M01 you only need to record the available VRAM.

### 4. CPU versus GPU

A GPU is not automatically faster for every operation. Small matrices, small
batches, and frequent transfers between CPU and GPU can make a GPU slower than a
well-used CPU. GPUs become valuable for large parallel workloads such as training
neural networks.

For this course:

- **CPU-only** work includes environment setup, classical machine learning,
  data preparation, small-model inference, RAG with small embedding models, and
  most evaluation and deployment exercises.
- **GPU-recommended** work includes deep-learning foundations and vision or
  speech inference.
- **GPU-required** work includes fine-tuning and training at useful speed.

Always label your results with the hardware you used. "It took 20 minutes" is
not reproducible; "20 minutes on an RTX 4060 Ti with 16 GB VRAM" is.

### 5. Notebooks versus scripts

A **notebook** interleaves code, output, and explanation. It is excellent for
learning, exploration, and showing evidence. A **script** is a plain `.py` file
that runs from top to bottom and is easier to test, review, schedule, and deploy.

Use notebooks for guided work and experiments. Move stable logic into modules
under `src/` or a small script when you need repeatable execution, testing, or
deployment. A notebook that only works when cells are run out of order is not a
reproducible artifact.

### 6. Reproducibility

Reproducibility means another person can rerun your work and obtain results
close enough to support the same conclusion. It requires more than a seed:

| Record | Example |
| --- | --- |
| Code version | Git commit hash and branch |
| Interpreter | Python 3.12.10 |
| Direct and indirect dependencies | `requirements.lock` |
| Hardware | CPU model, RAM, GPU name, VRAM |
| Operating system | Windows 11 build or Colab image |
| Random seeds | Python, NumPy, framework seeds |
| Data version | Dataset name, version, checksum |
| Commands | Exact notebook or script entry point |

Seeds make pseudo-random sequences repeatable on the **same** software and
hardware. They do not guarantee bit-identical results across different GPUs,
CUDA versions, or BLAS implementations. Report the variation instead of hiding
it.

### 7. Git basics for a self-study course

Git records snapshots of your work and lets you experiment without losing a
working version.

```bash
git clone https://github.com/nadeem-majeedch/AITopics.git
cd AITopics
git switch -c m01-work
git status
git add notebooks/foundations/m01_environment_check.ipynb
git commit -m "Complete M01 environment check"
```

If your cohort uses a private or renamed repository, use the clone URL provided
by your instructor. Never commit virtual environments, datasets, model weights,
tokens, or `.env` files; the course `.gitignore` already excludes the usual
offenders.

### 8. Google Colab constraints

Colab gives you a temporary Linux machine in a browser. It is excellent for a
second environment and for free GPU time, but it has rules:

- `/content` is temporary. Save notebooks to Git or Drive before the session ends.
- The installed package versions may differ from your local machine.
- Free GPU type and availability vary; a GPU runtime is not guaranteed.
- Secrets must not be pasted into cells that you share or commit. Use Colab
  secrets or environment variables.
- A notebook that runs on Colab is not automatically reproducible locally. That
  is exactly why the M01 lab asks you to compare two environments.

### 9. Windows 11 specifics

| Issue | What happens | Practical fix |
| --- | --- | --- |
| Long paths | Deep folder names break installs or imports | Work in `C:\ai-course`, not a deeply nested OneDrive folder |
| OneDrive sync | Files lock or change during installs | Keep environments and datasets outside synced folders |
| PowerShell execution policy | `Activate.ps1` is blocked | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` for the current shell only |
| `python` opens the Microsoft Store | The Windows alias shadows your install | Use `py -3.12` or disable the alias in Settings |
| Antivirus scanning | Slow installs or locked DLLs | Add the project folder to exclusions only if your policy allows it |

Do not change machine-wide security settings to make one lab work. Prefer a
short path and a per-process policy change.

## Guided walkthrough

The full practical is the
[guided notebook](notebook.md). It performs these steps and writes an
`environment_report.json` file:

1. Print the platform, Python interpreter, and package versions.
2. Detect CPU cores, RAM, and free disk space.
3. Query `nvidia-smi` and PyTorch for optional GPU information.
4. Seed Python and NumPy, then demonstrate repeatable random sequences.
5. Train logistic regression on the bundled scikit-learn digits dataset.
6. Save the model, reload it, and compare predictions.
7. Time a matrix multiplication on the CPU and, if available, the GPU.
8. Export the data to CSV, write a SHA-256 checksum, and verify it.
9. Assemble a machine-readable environment report.

The notebook is CPU-only. If PyTorch is absent or CUDA is unavailable, the GPU
section records that fact and continues. A skipped optional section is not a
failure.

## Common failures and how to diagnose them

| Symptom | Likely cause | First check |
| --- | --- | --- |
| `ModuleNotFoundError` after a successful install | Notebook kernel uses a different interpreter | `import sys; print(sys.executable)` inside the notebook |
| `Activate.ps1 cannot be loaded` | PowerShell execution policy | Use a per-process bypass, then activate again |
| `torch.cuda.is_available()` is `False` | CPU-only wheel, driver issue, or no NVIDIA GPU | Compare `nvidia-smi` with `torch.version.cuda` |
| `CUDA out of memory` | Model or batch does not fit VRAM | Reduce batch size; record VRAM; use Colab |
| `pip` is not recognized | Environment not activated or Python not on PATH | Use `python -m pip`, and check `sys.executable` |
| Notebook works only after running cells out of order | Hidden state | Restart the kernel and run all cells |
| Downloads fail behind a campus network | Proxy or firewall | Use the institution's proxy settings; do not disable TLS checks |

A useful debugging protocol:

1. Reproduce the failure with the smallest possible command.
2. Read the **last** line of the error, then the first line that names your file.
3. Check the interpreter, working directory, and package version.
4. Change one variable at a time.
5. Record what you tried and what happened. That record becomes lab evidence.

## Checkpoint

You are ready for the lab when you can:

- [ ] Activate your environment and show that `sys.executable` points inside it.
- [ ] Run the guided notebook from a clean kernel without errors.
- [ ] Explain why `nvidia-smi` can find a GPU while `torch.cuda.is_available()` is false.
- [ ] Locate the generated `environment_report.json`.
- [ ] State one result that would change if a package version changed.

## Next step

1. Run the [guided notebook](notebook.md).
2. Complete the [lab brief](lab.md) in a second environment.
3. Check your evidence against the [assessment](assessment.md).
4. Continue to M02 - Machine learning foundations, whose plan is in
   [Level 1](../../syllabus/level-1-foundations.md#m02).

---

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)
