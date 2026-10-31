# Troubleshooting

This page covers the failures most likely to stop a learner or maintainer. Start
with the diagnostics, then find the matching section.

## First diagnostics

Run these before asking for help.

```bash
python --version
python -c "import sys; print(sys.executable)"
python -m pip --version
python -m pip list
```

For GPU checks:

```bash
nvidia-smi
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

For documentation:

```bash
python -m mkdocs --version
python -m mkdocs build --strict
```

Record the exact command, error, versions, and hardware. Most issues are
environment mismatches, not model bugs.

## Windows 11

### PowerShell blocks virtual environment activation

Symptom:

```text
cannot be loaded because running scripts is disabled on this system
```

Fix for your user account:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

Do not change machine-wide policy without administrator approval. In Git Bash,
use `source .venv/Scripts/activate` instead.

### `python` is not found or the wrong Python runs

- Try the Windows launcher: `py -0p` to list interpreters, then
  `py -3.12 -m venv .venv`.
- Check `where python` and `python -c "import sys; print(sys.executable)"`.
- Prefer `python -m pip` over bare `pip` to avoid installing into a different
  interpreter.
- Avoid installing packages globally. Use a virtual environment.

### Long paths or OneDrive cause failures

- Keep projects in a short path such as `C:\ai-course`.
- Avoid OneDrive-synced folders for environments, datasets, and checkpoints.
- If long paths are required, enable long path support in Windows with
  administrator approval.

### A package needs a C++ compiler

Some packages require Microsoft C++ Build Tools. Install them only if the
package documentation requires it. Prefer prebuilt wheels.

### Port 8000 is already in use

```bash
python -m mkdocs serve --dev-addr 127.0.0.1:8001
```

Or stop the process using the port. Do not kill unknown processes without
checking what they are.

## Python environments

### Packages install but imports fail

- Confirm the kernel uses the same environment:

```bash
python -c "import sys; print(sys.executable)"
```

- In Jupyter, check the selected kernel.
- Restart the kernel after installation.
- Reinstall with `python -m pip install ...`.

### Dependency conflicts

- Create a fresh virtual environment.
- Install from the course requirements file, not ad hoc.
- Do not mix Conda and pip in the same environment unless necessary.
- Record the working versions.

### CUDA PyTorch installed on a CPU-only machine

Uninstall and install the CPU wheel, or use the CPU requirements set once it is
available. A CUDA wheel without a GPU will fail at runtime or run on CPU with
warnings.

## GPU and CUDA

### `torch.cuda.is_available()` is False

Check in this order:

1. `nvidia-smi` works and shows a driver.
2. The installed PyTorch build matches the driver's CUDA capability.
3. You are not in a CPU-only environment or container.
4. The GPU is visible to the process (WSL2 and containers can hide it).

Install the PyTorch wheel recommended by the official PyTorch selector. Do not
install the full CUDA toolkit just to run PyTorch; the wheel bundles the runtime.
Update the NVIDIA driver if needed, with administrator approval.

### Out of memory (OOM)

Try, in order:

1. Reduce batch size.
2. Reduce sequence length, image resolution, or clip length.
3. Use gradient accumulation to keep an effective batch size.
4. Enable gradient checkpointing.
5. Use a smaller model or a quantized model.
6. Free memory: delete unused tensors, clear the cache, restart the kernel.

Record peak VRAM. "It ran on my machine" is not enough if the lab targets a 16 GB
free GPU.

### GPU is idle during training

- Move the model and batches to the device.
- Check that the DataLoader is not the bottleneck (`num_workers`, disk speed).
- Avoid transferring data to CPU every step.
- Use mixed precision where appropriate.

### Loss becomes NaN

- Lower the learning rate.
- Check labels and input ranges.
- Add gradient clipping.
- Check for division by zero or log of zero.
- Disable mixed precision temporarily.
- Verify that the loss is computed on the correct logits.

### `bitsandbytes` fails on Windows

Use Google Colab or WSL2 if the native Windows build does not work. Document the
workaround; do not present an unverified Windows path as supported.

## Google Colab

### Session disconnects or restarts

- Save notebooks to GitHub or Drive.
- Checkpoint models every epoch.
- Treat `/content` as temporary.
- Re-run the setup cells after a restart.

### GPU quota unavailable

- Try again later; free quotas vary.
- Use Kaggle as a backup.
- Use the CPU-feasible variant of the lab.
- Reduce model size and dataset size.

### Disk full

- Delete old checkpoints and datasets in `/content`.
- Use `!df -h` and `!du -sh /content/*`.
- Mount Drive only when needed.
- Do not download multiple large models in one session.

### Secrets and tokens

Use Colab's Secrets manager or environment variables. Never paste a token into a
notebook cell that will be committed. Revoke any token that leaks.

## Hugging Face

### Gated model or 401/403

- Accept the model's terms on the Hugging Face website.
- Authenticate with the current Hugging Face CLI or `HF_TOKEN` environment
  variable.
- Verify the token has the right permissions.
- Do not share tokens.

### Download fails or fills the disk

- Check the cache location and free space.
- Remove unused models from the cache.
- Prefer smaller models for the lab.
- Use a stable mirror only if it is official.

### Model license restricts use

This is not a bug. Choose a permissively licensed model or restrict the use to
learning. Record the license in the model card.

## Datasets and media

### Link rot

- Check the dataset card for an official alternate source.
- Open an issue with the module code and the failing URL.
- Do not replace a dataset with an unlicensed mirror.

### Checksum mismatch

- Re-download from the official source.
- Confirm the dataset version.
- Do not bypass checksum verification silently.
- Report persistent mismatches.

### `ffmpeg` not found

Install FFmpeg using the official instructions for your platform, or use a
Colab environment that includes it. Verify:

```bash
ffmpeg -version
```

### OpenCV cannot open a video

- Check the codec and file path.
- Try `cv2.VideoCapture` with a different backend.
- Convert the clip with FFmpeg.
- Confirm the file is not corrupted.

### Dataset license is unclear

Do not use it. Choose a dataset with a clear license or ask the instructor.

## Jupyter

### Kernel does not see installed packages

- Select the correct kernel.
- Install into the environment that the kernel uses.
- Restart the kernel.
- Avoid mixing system Python and virtual environments.

### Notebook behaves differently after restart

- Run all cells from top to bottom.
- Remove hidden state.
- Check that file paths are relative or configured in one cell.
- Set seeds in one place.

### Outputs are too large

- Clear outputs before committing.
- Save large artifacts outside Git.
- Keep only representative plots and logs.

## MkDocs

### `No module named mkdocs`

Activate the virtual environment and install documentation requirements:

```bash
python -m pip install -r requirements/docs.txt
```

### Strict build fails

Read the first error, not the last. Common causes:

- A page in `nav` does not exist.
- A page exists but is not in `nav` and strict mode treats the info as a problem.
- A relative link points to a missing file.
- A malformed Markdown table or code fence.

Fix the source; do not disable strict mode to hide the problem.

### Page returns 404 locally

- Check the file path and navigation entry.
- Confirm the URL uses the directory style generated by MkDocs.
- Rebuild after adding a page.
- Check for a stale `site/` directory.

### Mermaid diagram shows as text

- The fence language must be `mermaid`.
- `pymdownx.superfences` must include the custom fence configuration in
  `mkdocs.yml`.
- Check the browser console for script errors.

### Anchor link does not work

- Confirm the heading text and generated anchor.
- Prefer linking to the page and the exact heading.
- Strict mode does not validate every anchor; click the link.

## Git and GitHub

### Large file rejected

The repository does not use Git LFS. Remove the file from the commit, add it to
`.gitignore`, and store it externally. Do not rewrite public history without
approval.

### Line-ending warnings

Windows may convert line endings. Use a consistent Git configuration and avoid
committing entire files with only line-ending changes.

### Authentication fails

Use a personal access token or GitHub CLI authentication. Never commit tokens.
Check the remote URL and your account permissions.

## When to open an issue

Open an issue if:

- The problem persists after the checks above.
- The fix requires changing course content.
- A dataset or model license is unclear.
- A notebook fails on a supported environment.
- A link is broken.

Include the module code, exact command, full error, versions, hardware, and a
minimal reproduction. Do not include secrets or personal data.

## Recovery rule

Before deleting an environment, cache, or branch, confirm that it contains no
unique work. When in doubt, move it aside or back it up instead of deleting it.
Most build artifacts can be regenerated; student work and uncommitted notebooks
cannot.
