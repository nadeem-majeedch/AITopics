# Level 0 - Orientation and environment

**Modules:** M00-M01 | **Hours:** 15 | **Hardware:** CPU-only

Level 0 turns a motivated learner into a prepared one. You will choose a learning
path, set a realistic schedule, build a reproducible environment, and verify that
you can run the same notebook on Windows 11 and Google Colab.

!!! note "Level outcome"
    You can create, document, and reproduce an AI development environment, and
    you know exactly what your hardware can and cannot do.

## Readiness check

Before starting, you should be able to:

- Write and call Python functions.
- Use lists, dictionaries, and files.
- Run commands in PowerShell or Bash.
- Install a Python package and activate a virtual environment (or learn it in M01).

If your Python is weak, complete a free refresher before M01. The level is not a
programming course.

---

## M00 - Course orientation and study plan {#m00}

**Level 0 | 3 hours | CPU-only | Prerequisite: none**

### Learning objectives

By the end of this module, you can:

1. Explain the course structure, levels, and assessment model.
2. Map your goals to one of the five learning paths.
3. Build a weekly study plan that matches your available time and hardware.
4. Set up a portfolio structure for lab artifacts.
5. State the course rules for collaboration, AI assistance, and data ethics.

### Prerequisites

- None. Curiosity and a realistic schedule are enough.

### Study time

| Theory | Practical | Assessment | Total |
| --- | --- | --- | --- |
| 1 h | 1 h | 1 h | 3 h |

### Required theory

- Course map and the theory-to-lab learning loop.
- Learning science basics: spaced practice, retrieval, and deliberate practice.
- Portfolio-based learning and evidence of capability.
- Academic integrity and the AI-assistant policy.
- Hardware and software expectations, including CPU/GPU labels.

### Guided practical

- Planned worksheet: `labs/foundations/m00_study_plan.md`.
- Complete a self-assessment of Python, math, hardware, and available time.
- Choose a learning path and list the modules you will take.
- Draft a 26-week schedule with buffer weeks.
- Create a portfolio repository with one folder per module.

### Independent lab

**Brief:** Produce a personal study plan that survives contact with your real
week. It must include:

- Your target path, start date, and weekly hours.
- A week-by-week schedule with at least 20% buffer.
- Primary and backup hardware plans.
- Accounts and software you still need.
- Two foreseeable blockers and your mitigation.
- A portfolio link or local folder plan.

**Constraints:** No more than two pages. Hours must be honest, not aspirational.

### Assessment criteria

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Plan completeness | 30% | Path, schedule, hardware, accounts, risks |
| Realism | 30% | Hours match your stated commitments |
| Prerequisite planning | 20% | Gaps identified with concrete actions |
| Portfolio setup | 20% | Usable structure and naming |

### Deliverables

- Personal study plan.
- Portfolio skeleton with a README.
- Accounts and hardware checklist.

### Next step

M01 - Python and AI development environment.

### Risks and notes

- Do not plan 30 hours per week if you have a full course load. Burnout is the
  most common reason learners stop.
- Choosing the full program on day one is fine, but schedule only the first
  level in detail.

---

## M01 - Python and AI development environment {#m01}

**Level 0 | 12 hours | CPU-only (GPU check optional) | Prerequisite: M00 and basic Python**

**Status:** Published. The lesson, executable notebook, lab brief, starter file,
and assessment are available.

### Learning objectives

By the end of this module, you can:

1. Create and activate isolated Python environments with `venv` or `uv`.
2. Install CPU and CUDA builds of PyTorch correctly for your machine.
3. Detect available hardware and explain the driver/CUDA/PyTorch relationship.
4. Run and troubleshoot Jupyter notebooks locally and on Google Colab.
5. Apply reproducibility basics: seeds, pinned versions, recorded hardware.
6. Use Git to clone the course, create a branch, and commit your work.
7. Diagnose the five most common environment failures on Windows 11.

### Prerequisites

- M00.
- Basic Python syntax and command-line navigation.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 3 h | 5 h | 3 h | 1 h | 12 h |

### Required theory

- Python versions, interpreters, virtual environments, and dependency resolution.
- `pip`, `uv`, and when (not) to use Conda.
- GPU stack: NVIDIA driver, CUDA runtime, cuDNN, and PyTorch wheels.
- CPU vs GPU execution, VRAM, and the cost of data transfer.
- Notebooks vs scripts: when each is appropriate.
- Reproducibility: seeds, determinism, version pinning, hardware logs.
- Git basics: clone, status, diff, commit, branch, pull request.
- Colab constraints: ephemeral sessions, mounted Drive, GPU quotas, secrets.
- Windows path, long-path, and PowerShell execution-policy issues.

### Guided notebook

**Published notebook:** `notebooks/foundations/m01_environment_check.ipynb`  
**Lesson:** [M01 - Python and AI development environment](../lessons/m01-environment/index.md)  
**Run guide:** [Guided notebook page](../lessons/m01-environment/notebook.md)

The notebook will:

1. Print platform, Python, and package versions.
2. Detect CPU, RAM, CUDA availability, GPU name, and VRAM.
3. Set seeds and demonstrate determinism on a small computation.
4. Train a logistic regression on the bundled scikit-learn digits dataset.
5. Save and reload the model, then verify predictions match.
6. Time a small matrix operation on CPU and, if available, GPU.
7. Export the digits data to CSV and verify a SHA-256 checksum.
8. Write a machine-readable environment report.

**Dataset:** bundled scikit-learn digits data; no external download required.
The checksum exercise exports that data to CSV, so the core path works offline.
The same `verify_sha256` function applies to files downloaded from a dataset
publisher.

**Hardware:** CPU-only. GPU cells are optional and skipped automatically when
CUDA is unavailable.

### Independent lab

**Published brief:** [M01 lab - Reproduce the environment in two places](../lessons/m01-environment/lab.md)  
**Starter file:** `labs/foundations/m01_environment_report.md`

Reproduce the guided notebook in a second environment and write an environment
report.

- Environment A: your local Windows 11 machine.
- Environment B: Google Colab (CPU or GPU) or a second machine.
- Compare Python and package versions, hardware, runtime, and any failures.
- Provide a `requirements.txt` or lock file that reproduces Environment A.
- Explain one failure you hit and how you diagnosed it.
- Include a screenshot or text log of GPU detection, if available.

**Constraints:** Do not install the full CUDA toolkit unless a specific need is
documented. Do not commit large wheels or secrets. The notebook must run
top-to-bottom from a clean kernel.

### Assessment criteria

The lab is 40% of the module mark and uses the course's five lab dimensions.
The module also scores the knowledge check (20%), guided notebook (30%), and
reflection (10%); see the [M01 assessment](../lessons/m01-environment/assessment.md).

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Technical correctness | 30% | Both environments run the notebook |
| Evaluation and diagnosis | 25% | Differences and one failure explained with evidence |
| Reproducibility | 15% | Pinned dependencies, seeds, recorded hardware, commands |
| Data and ethics | 15% | Privacy redaction, safe installs, no secrets |
| Communication | 15% | Readable report and run instructions |

### Deliverables

- Executed environment-check notebook.
- Environment report comparing local and Colab.
- Dependency file that reproduces the local environment.
- Short reflection on hardware limits.

### Next step

[M01 lesson](../lessons/m01-environment/index.md) and
[M01 assessment](../lessons/m01-environment/assessment.md), then
M02 - Machine learning foundations.

### Risks and notes

- **CUDA mismatch:** install the PyTorch wheel that matches your driver; do not
  install a random CUDA toolkit.
- **Windows:** long paths and OneDrive-synced folders cause avoidable failures.
  Work in a short path such as `C:\ai-course`.
- **Colab:** `/content` is temporary. Save work to Git and data to Drive.
- **bitsandbytes** and some quantization tools are easier on Linux/Colab than
  native Windows. M08 documents workarounds.
- If you cannot install a local GPU stack, use Colab for GPU labs and keep a
  local CPU environment for development.

---

## Level 0 completion checklist

- [ ] I chose a learning path and wrote a realistic schedule.
- [ ] I created a portfolio structure.
- [ ] I can create and activate a Python environment.
- [ ] I can detect CPU/GPU and explain the CUDA relationship.
- [ ] I ran the environment notebook on two environments.
- [ ] I recorded versions, seeds, hardware, and one diagnosed failure.
- [ ] I know my primary and backup environment for GPU labs.

Proceed to [Level 1 - Foundations](level-1-foundations.md).
