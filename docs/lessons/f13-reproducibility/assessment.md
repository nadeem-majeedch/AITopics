# F13 assessment

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**

F13 completes the foundation sequence. It is self-assessed: no proctored exam, no
credit awarded. Keep your run logs and cards as evidence.

| Component | Weight | Evidence |
| --- | --- | --- |
| Knowledge check | 20% | Answers to the eight questions below |
| Guided notebook | 30% | Executed notebook, JSONL log, environment report |
| Independent lab | 40% | Hardware audit with reproducibility card |
| Reflection | 10% | 200-300 words |

## Part A - Knowledge check (20%)

Each question is worth 2.5 points. Answer before opening the answer.

**1. Three seeds give validation accuracies 0.848, 0.872, and 0.904. Compute the
mean and the population standard deviation. Which number would you report in a
summary, and with what caveat?**

??? note "Answer"
    Mean: `(0.848 + 0.872 + 0.904) / 3 = 2.624 / 3 = 0.8747`, about **0.875**.
    Deviations are `-0.0267`, `-0.0027`, `+0.0293`; their squares sum to about
    `0.00158`; dividing by 3 gives `0.000526`; the square root is **0.023**.
    Report "0.875 with a standard deviation of 0.023 across three seeds". The
    caveat: three runs give a rough spread estimate, and the best run (0.904)
    should not be presented as the result.

**2. Code reading. What does this call do, and what does `warn_only=True` change?**

```python
torch.use_deterministic_algorithms(True, warn_only=True)
```

??? note "Answer"
    It asks PyTorch to use deterministic implementations for operations where one
    exists, so repeated runs on the same hardware and software are more likely to
    produce identical results. `warn_only=True` makes PyTorch emit a warning and
    continue when an operation has no deterministic implementation, instead of
    raising an error. It can slow training and does not guarantee bitwise
    equality on GPUs.

**3. Why does the notebook seed Python, NumPy, and PyTorch separately?**

??? note "Answer"
    Each library has its own pseudo-random generator with its own state. Seeding
    only PyTorch leaves NumPy-driven splits or augmentations and Python-level
    shuffles uncontrolled. Seeding all three makes the whole pipeline repeatable;
    the order must be seed first, then build data and models.

**4. `torch.cuda.is_available()` returns `False` on a machine that has an NVIDIA
GPU. Name three possible causes and the first check for each.**

??? note "Answer"
    Any three of: a CPU-only PyTorch wheel is installed (check `torch.version.cuda`);
    the driver is too old for the bundled CUDA runtime (check `nvidia-smi`);
    PyTorch is installed in a different environment (check `sys.executable`);
    the GPU is disabled, in use exclusively, or hidden from the process; a
    container or remote session has no GPU passthrough. Continue on CPU while
    diagnosing; the notebook does not require a GPU.

**5. Why must a GPU timing include `torch.cuda.synchronize()`, and why does the
CPU benchmark need a warm-up?**

??? note "Answer"
    CUDA operations are asynchronous: the Python call returns before the GPU
    finishes, so stopping the clock immediately measures launch time rather than
    compute time. `synchronize()` blocks until the work completes. Warm-up runs
    move one-time costs (memory allocation, kernel selection, cache population)
    out of the measured loop so the reported time reflects steady-state
    execution.

**6. Code reading. The tracker opens the log with mode `"a"` and flushes each
record. What are the consequences for a run that crashes, and what happens if you
forget to delete an old log?**

??? note "Answer"
    Append mode means earlier records survive a crash, and flushing writes each
    record to disk immediately, so completed runs are not lost. The downside is
    that rerunning without deleting the file accumulates duplicate records, and a
    later reader may count six runs instead of three. The notebook deletes the
    log at the start of a clean run for exactly this reason.

**7. A classmate reports "0.904 accuracy" from the three-seed experiment. What is
wrong with that claim, and what should replace it?**

??? note "Answer"
    0.904 is the best of three runs, so it overstates expected performance and
    hides the spread. The claim also omits the seed list, the device, and the
    exact model recipe. Replace it with the mean and standard deviation across a
    stated seed set, plus the configuration and device, for example "0.875 +/- 0.023
    over seeds 7, 17, 27 on CPU".

**8. Give one workload where a GPU is likely slower than a CPU and explain why.**

??? note "Answer"
    A small matrix multiplication or a tiny model on a few hundred rows. Kernel
    launch overhead and the cost of copying data to and from GPU memory can exceed
    the computation itself, so the GPU spends most of its time waiting. Larger
    matrices or batches amortize those fixed costs and let the GPU's parallelism
    pay off.

**Self-score:** 2.5 points each. Full credit requires the mechanism, not only the
term.

## Part B - Guided notebook (30%)

| Criterion | Weight | Evidence |
| --- | --- | --- |
| Completeness | 10% | All six sections executed; both output files exist |
| Correctness | 10% | Identical seeded tensors, device reported, three run records, mean 0.875 and standard deviation 0.023 |
| Interpretation | 10% | A short note stating the device, the seed set, and what the spread implies |

A notebook with a log but no interpretation scores at most 20 of 30.

## Part C - Independent lab (40%)

Scored with the five-dimension rubric on the [lab brief](lab.md#rubric):
technical correctness 30%, evaluation and diagnosis 25%, reproducibility 15%,
data and ethics 15%, communication 15%.

| Dimension | Points |
| --- | --- |
| Technical correctness | 30 |
| Evaluation and diagnosis | 25 |
| Reproducibility | 15 |
| Data and ethics | 15 |
| Communication | 15 |
| **Total** | **100** |

Common reasons for losing marks:

- Timings without warm-up, or GPU timings without synchronization.
- A speedup claim with no matrix size or device name.
- A missing or fabricated GPU row instead of an honest `not executed` entry.
- Repeating a seed without rebuilding the model, then claiming determinism.
- Reporting the best run rather than mean and spread.
- An environment card that a reader could not use to rebuild the setup.

## Part D - Reflection (10%)

Write 200-300 words and answer all three prompts:

1. Which source of randomness in your own work had you not considered before this
   module, and how will you control it?
2. If you completed the CPU-only path, what did the thread or dtype comparison
   teach you that a GPU comparison would also have shown?
3. What belongs in a one-paragraph "how to rerun this" note, and why is a seed
   alone insufficient?

Reflection is reasoning about evidence and limitations, not a summary of steps.

## Scoring worksheet

| Component | Maximum | Your score | Notes |
| --- | --- | --- | --- |
| Knowledge check (8 x 2.5) | 20 | | |
| Guided notebook | 30 | | |
| Independent lab | 40 | | |
| Reflection | 10 | | |
| **Total** | **100** | | |

Self-study bands:

| Score | Interpretation |
| --- | --- |
| 90-100 | Ready for M04; evidence is complete and reproducible |
| 75-89 | Ready, but fix the weakest rubric dimension first |
| 60-74 | Reread the lesson and rerun the notebook; lab evidence has gaps |
| Below 60 | Repeat the module before starting M04 |

These bands are for planning. They are not a university grade and confer no
credit.

## Academic integrity and AI assistance

- You may use an AI assistant to explain an error or suggest a diagnostic step.
- You must run the benchmarks and training yourself and record the real device.
- Disclose substantive assistance in your reflection: what you asked, what you
  used, and what you verified independently.
- Never report a GPU or Colab run you did not perform. "Not executed" is an
  acceptable and expected result.

The course policy is in
[Academic integrity](../../course/assessments.md#academic-integrity) and
[How to study](../../course/how-to-study.md#academic-integrity-and-ai-assistants).

## Completion checklist

- [ ] I answered all eight questions before opening the answers.
- [ ] My notebook ran from a clean kernel and both output files exist.
- [ ] My lab includes timings with warm-up and a stated repeat count.
- [ ] My GPU row is either measured or marked `not executed` with a reason.
- [ ] My repeated seed-7 runs match to four decimals.
- [ ] My mean and standard deviation were recomputed independently.
- [ ] My reflection addresses all three prompts.
- [ ] No personal identifiers remain in the submission.

**Next:** [M04 - Training models from scratch](../../syllabus/level-1-foundations.md#m04),
the next approved module after M03. This unit completes the foundation sequence.

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · [Lab brief](lab.md) · **Assessment**
