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
| `llm.txt` | Optional UI and embedding extras for the conversational AI section: Streamlit and sentence-transformers | Available |
| `vision.txt` | CPU-only PyTorch, torchvision, Pillow, and NumPy for the computer vision section; runs every lab offline with synthetic data | Available |
| `audio.txt` | CPU-only PyTorch, NumPy, SciPy, and Pillow for the speech and audio section; no librosa, torchaudio, soundfile, or matplotlib, so every lab runs offline with synthesised audio | Available |
| `video.txt` | CPU-only PyTorch, torchvision, OpenCV (headless), NumPy, and SciPy for the video AI section; runs every lab offline on generated video, and only Lab 2/4 fetch a 13 MB COCO checkpoint on first run | Available |
| `ci.txt` | The union of `cpu.txt`, `vision.txt`, `audio.txt`, and `video.txt`; the CPU-only environment used by the validation workflow | Available |
| `agents.txt` | Agent framework, schema validation, tracing, and API clients | Planned, Phase 6 |
| `dev.txt` | Optional linting and type-checking tools; the current unit suite uses `unittest` and notebook checks use `nbclient` | Not required for CI |

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

`ci.txt` is a CI composition file, not a fourth application environment. It
exists so the validation workflow installs the packages imported by the unit
suite instead of silently skipping the vision, audio, or video tests.
