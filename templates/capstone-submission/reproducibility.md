# Reproducibility

**Project:** [replace]  
**Environment:** [replace: OS, Python version, CPU/GPU]  
**Checkpoint:** 2, verified at 3

The goal is a stranger with your repository and no GPU can reach your headline
result, within its interval, from one command.

## Environment

| Item | Value |
| --- | --- |
| OS | [replace] |
| Python | [replace] |
| Package manager | [replace: pip / uv / conda] |
| Key packages | [replace: name==version for torch, numpy, ...] |
| Hardware | [replace: CPU model and threads; GPU only if used] |
| Disk and memory | [replace] |
| Network needed | [replace: none / downloads named model and licence] |

Pinned dependencies live in `requirements.txt`. Do not write "latest".

## Data

| Item | Value |
| --- | --- |
| Generation command | `[replace]` |
| Seed | [replace] |
| Dataset version | [replace] |
| Manifest or checksum | [replace: path and digest] |
| Verification command | `[replace: e.g. python scripts/make_vision_data.py --check]` |
| Expected result | [replace: e.g. "960 images checked, 0 problems"] |

If the data is downloaded, provide the URL, licence, checksum, and the command.
Never commit raw data.

## Seeds and determinism

- Python, NumPy, and framework seeds: [replace]
- Deterministic dataloader order: [replace: yes/no]
- Nondeterministic operations documented: [replace: which ones, and the observed variation]
- Two runs compared: [replace: metric difference, or "not tested"]

## Commands

Run from the repository root, in order.

```bash
# 1. environment
[replace: python -m venv .venv && ...]

# 2. data
[replace: generation or download command]
[replace: verification command]

# 3. train or build
[replace]

# 4. evaluate
[replace]

# 5. check the headline result
[replace: the command that prints the reported metric]
```

## Expected outputs

| Path | Contents | Runtime |
| --- | --- | ---: |
| `outputs/metrics.json` | [replace: headline metrics with n] | [replace] |
| `outputs/[replace]` | [replace] | [replace] |
| `artifacts/[replace]` | model or adapter, checksum [replace] | - |

Report CPU runtime as measured. If a GPU path exists but was not run, say
"unverified" rather than estimating a speedup.

## Reload and check the artifact

```bash
[replace: command that reloads the saved artifact and reproduces 3 stored predictions]
```

Expected: [replace: e.g. "the reloaded adapter reproduces the stored generations
exactly" or the measured difference].

## Known non-reproducibility

- [replace: GPU kernel nondeterminism, library version drift, service dependency]
- [replace: anything a reader cannot reproduce offline, and why it is not needed
  for the headline result]

## Reproduction record

| Date | Who | Command | Result | Difference from reported |
| --- | --- | --- | --- | --- |
| [replace] | [replace] | [replace] | [replace] | [replace] |
