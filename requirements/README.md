# Dependency files

The course uses separate dependency sets so that a CPU-only student, a GPU
student, and a documentation maintainer do not install the same environment.

| File | Purpose | Status |
| --- | --- | --- |
| `docs.txt` | Build and preview the MkDocs site | Available |
| `base.txt` | Shared CPU utilities used by early notebooks and labs (NumPy, scikit-learn, matplotlib, joblib) | Available |
| `notebooks.txt` | JupyterLab, ipykernel, and nbclient on top of `base.txt`; runs the M01 notebook | Available |
| `cpu.txt` | CPU-only PyTorch on top of `notebooks.txt`; runs F11-F13 on a laptop | Available |
| `gpu.txt` | Same Python stack with a version constraint for a CUDA PyTorch wheel; install the wheel for your driver | Available |
| `llm.txt` | Transformers, PEFT, TRL, datasets, bitsandbytes, vector stores | Planned, Phase 4 |
| `agents.txt` | Agent framework, schema validation, tracing, and API clients | Planned, Phase 6 |
| `dev.txt` | pytest, ruff, mypy, pre-commit, and notebook smoke-test tooling | Planned, Phase 1 |

## Rules

- Pin direct dependencies to compatible ranges, not unbounded versions.
- Never put secrets or personal tokens in a requirements file.
- Record the exact environment used for every verified notebook in its header.
- GPU wheels must not be installed on CPU-only machines by default.
- Changes to dependency sets require a note in `docs/technical/maintainer-guide.md`.

The first vertical-slice notebook (M01 environment check) was executed
top-to-bottom on Windows 11 with Python 3.12.10 and the versions recorded in
`notebooks/foundations/m01_environment_check.ipynb`. A Google Colab run is
still required before the module is marked fully verified on both supported
environments. `base.txt` and `notebooks.txt` are intentionally CPU-only.
