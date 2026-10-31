# M01 lab - Reproduce the environment in two places

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Weight** | 40% of the M01 assessment |
| **Time** | About 3 hours |
| **Hardware** | CPU-only; a GPU is optional |
| **Starter file** | `labs/foundations/m01_environment_report.md` in the repository |
| **Prerequisite** | A completed run of the [guided notebook](notebook.md) |

## The task

You have proved that the notebook runs in one environment. Now prove that you can
**reproduce** it somewhere else and explain the differences.

You will run the same notebook in:

- **Environment A:** your local Windows 11 machine (or your primary Linux/macOS
  machine if that is your local setup).
- **Environment B:** Google Colab, a second computer, or a separate virtual
  environment with a different Python version.

Then you will write an environment report that another student could follow to
rebuild Environment A and understand what changed in Environment B.

!!! warning "Do not try to make the two environments identical"
    Different Python versions and package versions are expected. The lab is about
    observing, recording, and explaining differences, not hiding them. A report
    that says "both worked" without evidence earns little credit.

## What to submit

```text
m01-environment/
  README.md                     # how to rerun your work, in 5-10 lines
  m01_environment_check.ipynb   # executed top to bottom in Environment A
  environment_A.json            # report from Environment A
  environment_B.json            # report from Environment B
  requirements.lock             # exact packages from Environment A
  environment_report.md         # the comparison and diagnosis
  reflection.md                 # 200-300 words
  screenshots/                  # optional, redacted logs or GPU screenshots
```

If you use Colab, also keep a link to the executed Colab notebook or export it as
HTML. A link alone is not enough; the notebook file must be in the submission.

## Step 1 - Baseline Environment A

1. Activate your local environment.
2. Confirm the interpreter:

   ```powershell
   python -c "import sys; print(sys.executable)"
   ```

3. Restart the notebook kernel and run all cells.
4. Rename or copy `outputs/environment_report.json` to `environment_A.json`.
5. Record the exact package set:

   ```powershell
   python -m pip freeze > requirements.lock
   ```

6. Check that `requirements.lock` contains no local file paths, tokens, or
   private package indexes. Remove lines that point to a personal filesystem.

## Step 2 - Environment B

Choose one:

- **Google Colab (recommended):** upload the notebook, run all cells, download
  `outputs/environment_report.json`, and save it as `environment_B.json`.
- **Second machine:** clone the repository, create a fresh environment, install
  `requirements/notebooks.txt`, and run the notebook.
- **Separate local environment:** create a second venv with a different supported
  Python version. Do not modify your baseline environment.

Record how you created Environment B in the lab README, including the Python
version and the install command.

## Step 3 - Compare the environments

Build a table with at least these rows. Use values from the JSON reports, not
from memory.

| Item | Environment A | Environment B | Same? | Why it matters |
| --- | --- | --- | --- | --- |
| Operating system | | | | Driver and path behavior differ |
| Python version | | | | Wheel availability and syntax |
| NumPy version | | | | Numerical behavior |
| scikit-learn version | | | | Model defaults and metrics |
| CPU cores | | | | Runtime |
| RAM | | | | Dataset size limits |
| GPU and VRAM | | | | Training feasibility |
| CUDA available | | | | GPU execution |
| Test accuracy | | | | Should be close, not necessarily identical |
| Matrix time | | | | Hardware effect |
| Failures or warnings | | | | Diagnosis evidence |

Then explain, in prose:

1. Which differences are **expected** and harmless.
2. Which differences could change a scientific conclusion.
3. Which environment you will use for the next module, and why.

## Step 4 - Diagnose one failure

If you hit a real failure, document it:

- The exact error message.
- The command or cell that produced it.
- The interpreter and package versions at the time.
- What you suspected, what you tested, and what fixed it.
- How you would prevent it next time.

If both environments ran perfectly, create a **non-destructive** mismatch in a
throwaway copy of the environment, for example:

1. Create a separate venv.
2. Install an older compatible scikit-learn version.
3. Run only the classifier section.
4. Record any warning or metric difference.
5. Delete the throwaway environment afterward.

Do not break your working environment to manufacture a failure. A well-diagnosed
warning is better evidence than a destroyed setup.

## Step 5 - Write the environment report

Use the starter file or copy this structure into `environment_report.md`:

```markdown
# M01 environment report

## 1. Summary
What you ran, where, and the headline result.

## 2. Environment A
Operating system, Python, packages, CPU, RAM, GPU, install command.

## 3. Environment B
The same fields, plus how the environment was created.

## 4. Comparison
The table from Step 3, followed by your interpretation.

## 5. Diagnosis
The failure or warning you investigated, with evidence.

## 6. Reproduction instructions
The exact commands needed to rebuild Environment A, including the lock file.

## 7. Limitations
What another student could not reproduce from your report, and why.

## 8. Privacy check
Confirmation that usernames, hostnames, IP addresses, tokens, and personal paths
were removed from the submission.
```

Keep the report readable. A reviewer should be able to rerun Environment A
without asking you a question.

## Constraints and safety

- Do not install the full CUDA toolkit unless you document a specific need. Most
  PyTorch wheels bundle what they require.
- Do not commit virtual environments, datasets, model weights, executed caches,
  or secrets.
- Do not disable TLS verification, firewall rules, or antivirus to make an
  install succeed.
- Redact personal paths, usernames, hostnames, and IP addresses from screenshots
  and reports.
- If you use a Colab notebook link, set sharing so that it does not expose private
  Drive files.
- The notebook must run top-to-bottom from a clean kernel in both environments.

## Rubric

The lab contributes 40% of the module mark and uses the course's five lab
dimensions.

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Technical correctness | 30% | Both environments run the notebook; evidence is complete and internally consistent | One environment runs; missing artifacts or unexplained gaps |
| Evaluation and diagnosis | 25% | Differences and one failure are explained with evidence and a prevention step | Differences listed but not interpreted; diagnosis is guesswork |
| Reproducibility | 15% | Lock file, seeds, versions, hardware, and commands reproduce Environment A | Partial pins or missing commands; another student could not rebuild it |
| Data and ethics | 15% | Privacy redaction, safe installs, license awareness, no secrets | Minor redaction gaps or unsafe workaround |
| Communication | 15% | Clear report, readable tables, honest limitations | Report is disorganized or omits limitations |

A component with no evidence scores zero, regardless of effort.

## Self-check before submission

- [ ] `environment_A.json` and `environment_B.json` exist and are readable JSON.
- [ ] The executed notebook is saved with outputs.
- [ ] `requirements.lock` reproduces Environment A.
- [ ] The comparison table uses report values, not memory.
- [ ] The diagnosis includes an error or warning, a hypothesis, a test, and a fix.
- [ ] Reproduction instructions are copy-pasteable.
- [ ] Personal information is redacted.
- [ ] You can explain every row in your comparison table.

Next: use the [assessment page](assessment.md) to score your evidence and write
the reflection.

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)
