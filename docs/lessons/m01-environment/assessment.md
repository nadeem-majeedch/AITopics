# M01 assessment

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**

M01 uses the course's standard module weights. There is no proctored exam. You
assess yourself against published criteria, keep the evidence, and decide whether
you are ready for M02.

| Component | Weight | Evidence |
| --- | --- | --- |
| Knowledge check | 20% | Answers to the ten questions below |
| Guided notebook | 30% | Executed notebook with outputs and report |
| Independent lab | 40% | Two-environment comparison and diagnosis |
| Reflection | 10% | 200-300 word reflection |

## Part A - Knowledge check (20%)

Answer first, then open the answer to check. A correct answer in your own words
is worth more than a memorized sentence.

??? question "1. What problem does a virtual environment solve?"
    It isolates a project's interpreter and installed packages from other
    projects and from the system Python. This prevents version conflicts and makes
    the project's dependencies reproducible.

??? question "2. `pip install scikit-learn` succeeds, but the notebook still reports `ModuleNotFoundError`. What is the most likely cause?"
    The notebook kernel is using a different Python interpreter from the one where
    `pip` installed the package. Check `sys.executable` inside the notebook and
    compare it with the interpreter used for installation.

??? question "3. `nvidia-smi` lists a GPU, but `torch.cuda.is_available()` returns `False`. Name three possible causes."
    Any three of: a CPU-only PyTorch wheel is installed; the NVIDIA driver is too
    old for the CUDA version bundled with PyTorch; PyTorch is not installed; the
    process runs in a container or remote session without GPU access; the GPU is
    disabled or unavailable to the current user.

??? question "4. Why can the same random seed produce different results on two different GPUs?"
    A seed controls the pseudo-random number sequence, but GPU operations can run
    in a nondeterministic order, use different cuDNN algorithms, or differ in
    floating-point behavior across hardware and library versions. Reproducibility
    also requires recording the hardware, software, and framework settings.

??? question "5. What is VRAM, and why can training fail even when system RAM is free?"
    VRAM is memory on the graphics card. Training stores model parameters,
    gradients, optimizer state, and activations in VRAM. If those exceed capacity,
    the process fails with an out-of-memory error even though the CPU's RAM is
    available.

??? question "6. What does a SHA-256 checksum tell you about a dataset file?"
    It is a fingerprint of the file's contents. If your computed hash matches the
    publisher's expected hash, the file is almost certainly complete and
    unmodified. A mismatch means corruption, an incomplete download, or a
    different version.

??? question "7. Why should you not treat `/content` in Google Colab as permanent storage?"
    Colab provides a temporary virtual machine. Files under `/content` are lost
    when the session ends or is reset. Save work to Git, Drive, or another
    persistent location.

??? question "8. What is the difference between a requirements file and a lock file?"
    A requirements file lists direct dependencies, often with version ranges. A
    lock file records the exact versions of direct and indirect dependencies that
    were actually installed, so the environment can be recreated more precisely.

??? question "9. List five facts you should record for a reproducible experiment."
    Any five of: code version or commit, Python version, package versions, operating
    system, hardware (CPU, RAM, GPU, VRAM), random seeds, dataset version and
    checksum, exact run command, and relevant framework settings.

??? question "10. Why does the course label every exercise CPU-only, GPU recommended, or GPU required?"
    The label tells you whether the work is feasible on your hardware before you
    start, helps you plan access to free or local GPUs, and makes performance
    claims interpretable. It also prevents learners without a GPU from assuming
    they cannot take the course.

**Self-score:** 2 points per question, 20 points total. Award full credit only
when your answer includes the mechanism or the diagnostic step, not just the
term.

## Part B - Guided notebook (30%)

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Completeness | 10% | All sections executed top to bottom; no skipped required cell |
| Correctness | 10% | Assertions pass; accuracy and reload checks are plausible |
| Interpretation | 10% | You can explain what the report proves and what it does not |

A notebook with saved outputs but no interpretation is incomplete. Add a short
markdown note under the report cell stating your Python version, whether CUDA was
available, and one limitation of the run.

## Part C - Independent lab (40%)

The lab is scored with the five-dimension rubric on the
[lab brief](lab.md#rubric): technical correctness 30%, evaluation and diagnosis
25%, reproducibility 15%, data and ethics 15%, and communication 15%. The module
weight converts that lab score to 40% of the M01 total.

Common reasons for losing marks:

- Reporting "both environments worked" without artifacts.
- Copying the report JSON without explaining the differences.
- A lock file that contains local paths or cannot rebuild the environment.
- A diagnosis with no evidence, hypothesis, or prevention step.
- Screenshots that expose a username, hostname, token, or private path.
- Claiming a GPU result that the report shows was skipped.

## Part D - Reflection (10%)

Write 200-300 words in `reflection.md`. Answer all four prompts:

1. Which environment difference surprised you most, and what did it teach you
   about reproducibility?
2. If `cuda_available` was false, how did you determine whether that was a fault,
   a missing driver, or a CPU-only PyTorch build?
3. What did the timing result show that a simple "it works" claim would hide?
4. What will you record in every future lab report so another student can rerun
   your result?

Reflection is not a summary of the steps. It is your reasoning about evidence,
limitations, and what you will change next time.

## Scoring worksheet

| Component | Maximum | Your score | Notes |
| --- | --- | --- | --- |
| Knowledge check | 20 | | |
| Guided notebook | 30 | | |
| Independent lab | 40 | | |
| Reflection | 10 | | |
| **Total** | **100** | | |

Use this scale for self-study:

| Score | Interpretation |
| --- | --- |
| 90-100 | Ready for M02; evidence is complete and reproducible |
| 75-89 | Ready, but fix the weakest rubric dimension before moving on |
| 60-74 | Revisit the lesson and rerun the notebook; the lab evidence has gaps |
| Below 60 | Repeat the module with a simpler second environment (Colab CPU) |

These bands are for your own planning. They are not a university grade and do
not confer credit.

## Academic integrity and AI assistance

- You may use an AI assistant to explain an error or suggest a diagnostic step.
- You must run the commands yourself and verify the output.
- Disclose substantive AI assistance in your reflection: what you asked, what you
  used, and what you verified independently.
- Do not submit a generated environment report that describes a machine you did
  not use.

The full policy is in [Academic integrity](../../course/assessments.md#academic-integrity)
and [How to study](../../course/how-to-study.md#academic-integrity-and-ai-assistants).

## Completion checklist

- [ ] I answered all ten knowledge questions before opening the answers.
- [ ] My notebook ran from a clean kernel and contains outputs.
- [ ] My lab includes two environment reports and a comparison table.
- [ ] My lock file rebuilds Environment A.
- [ ] My diagnosis names a failure or warning, a hypothesis, a test, and a fix.
- [ ] My reflection addresses all four prompts.
- [ ] I redacted personal information.
- [ ] I saved the package in my portfolio under `m01-environment/`.

**Next:** M02 - Machine learning foundations. Read the
[M02 plan](../../syllabus/level-1-foundations.md#m02) and continue with the
[Level 1 syllabus](../../syllabus/level-1-foundations.md).

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**
