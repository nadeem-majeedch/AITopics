# F13 lab - A hardware and reproducibility audit

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)

| | |
| --- | --- |
| **Weight** | 40% of the F13 module score |
| **Time** | About 2 hours |
| **Hardware** | CPU-only completion path. A GPU is optional and never required. |
| **Starter file** | `labs/foundations/f13_cpu_gpu_reproducibility.md` |
| **Prerequisite** | A completed run of the [guided notebook](notebook.md) |

## The scenario

Your study group wants to publish a one-page methods note answering a practical
question: **for small models like ours, is a GPU worth the setup cost?**

A draft claim is already circulating: "The GPU is 20x faster." It is based on one
timing on one machine, with no warm-up and no device name. You are the reviewer.
You will produce a measurement card and a reproducibility card that another
student can check, and you will label every claim as measured, estimated, or not
executed.

The lab is designed so that a student without a GPU can complete it fully. The
CPU-only path compares thread counts and repeats a seeded training run; the GPU
path adds a device comparison where hardware permits. **Do not rent, borrow, or
misrepresent hardware to complete this lab.**

## What you must decide

Answer one question with evidence: **for a model of this size, where does a GPU
help, and where does it not?**

Your answer must include:

- at least three matrix sizes, timed with warm-up and a stated repeat count;
- a repeated-seed training comparison (same seed twice, then different seeds);
- an explicit statement of what was measured on which device, and what was not
  executed;
- a recommendation that a reader could apply to their own machine.

## Required steps

### Step 1 - Inventory the machine

Record the operating system, CPU model and core count, RAM, Python version,
PyTorch version, whether CUDA is available, and, if present, the GPU name and
VRAM. On Windows, `nvidia-smi` reports the driver and GPU when one exists.

Write the inventory to `inventory.json`. Do not include hostnames, usernames, IP
addresses, or absolute paths.

**Validation check 1:** every field is either a measured value or the string
`"not available"` with a reason. No field may be blank or guessed.

### Step 2 - Fix the benchmark protocol

Use float32 tensors and square matrices of size 128, 256, 512, and 1024. For each
size:

1. create both matrices once;
2. run three warm-up multiplications;
3. synchronize if the device is CUDA;
4. time ten multiplications;
5. report the median and the minimum in milliseconds.

Fix `torch.set_num_threads(2)` for the main run so the comparison is stable, and
record the value.

### Step 3 - Measure the CPU baseline

Run the protocol on CPU and save a small CSV with columns `size`, `median_ms`,
`min_ms`, `device`, `threads`, `dtype`.

Expected pattern: time grows roughly with `size^3`. A 1024 matrix does about eight
times the arithmetic of a 512 matrix, so expect a substantially larger time, not
a doubling.

**Validation check 2:** median time must increase with size. If 1024 is faster
than 512, something is wrong with the loop, caching, or thread settings.

### Step 4 - Optional GPU comparison

If, and only if, `torch.cuda.is_available()` is true:

1. move the matrices to the GPU once;
2. repeat the protocol with `torch.cuda.synchronize()` before stopping the clock;
3. record the GPU name and VRAM;
4. time a separate transfer of the 1024 matrices from CPU to GPU, so transfer
   cost is visible rather than hidden;
5. report CPU and GPU times side by side.

If CUDA is not available, do **not** invent a GPU row. Record `"gpu": "not
executed"` and one of these reasons: no NVIDIA GPU, no matching driver, or a
CPU-only PyTorch build. Then complete the CPU-only substitution in Step 5.

### Step 5 - CPU-only substitution: threads and dtype

Choose one controlled comparison and run it on the same machine:

- **Threads:** repeat the 512 x 512 and 1024 x 1024 measurements with
  `torch.set_num_threads(1)`, `2`, and the default.
- **dtype:** repeat with `float32` and `float64` at 512 x 512.

Record every configuration. Explain which factor changed the time and by how
much. This is the CPU-only path that replaces the GPU comparison; it is not a
lesser result, it is a different controlled experiment.

### Step 6 - Repeated-seed training comparison

Train the same small model twice with seed 7, then once each with seeds 17 and
27. Use the notebook's model and settings or a comparably small MLP, and keep
everything except the seed fixed.

Log each run to `runs.jsonl` with: run name, seed, repeat index, model,
optimizer, learning rate, epochs, validation accuracy, validation loss, device,
and runtime.

**Validation check 3:** the two seed-7 runs must match to four decimal places. If
they do not, the split, initialization, or data order is not controlled. Explain
which generator you had to seed to make them match.

### Step 7 - Compute the spread and check the arithmetic

Compute mean and standard deviation across the three distinct seeds. Then
recompute them by hand or with a calculator and confirm the card matches. State
whether you used the population or sample standard deviation and why.

With three values, the difference between the two formulas is small but real.
Naming the formula matters more than the number.

### Step 8 - Write the measurement and reproducibility cards

Write `card.md` with the headings below. Every performance claim must point to a
row in your CSV or JSONL. Every claim you did not measure must be labeled
`not executed`, with a reason.

### Step 9 - Run the honesty audit

Read your draft once as a skeptical reviewer and answer:

- Does any sentence imply a GPU was used when it was not?
- Is any speedup stated without the matrix size and device?
- Is the accuracy report a best run or a mean with spread?
- Could a reader rebuild your environment from the card alone?

Fix the draft before submitting.

## Deliverables

```text
f13-repro-audit/
  README.md               # rerun instructions, 5-10 lines
  bench.py                # or bench.ipynb, the benchmark and training script
  inventory.json          # hardware and versions, redacted
  timings.csv             # size, device, threads, dtype, median, min
  runs.jsonl              # four training runs (seed 7 twice, 17 and 27 once)
  environment_report.json # versions, device, seeds, mean, std
  card.md                 # measurement and reproducibility card
  reflection.md           # 200-300 words
```

## Report template

```markdown
# F13 hardware and reproducibility card

## 1. Question
What you set out to determine, in one or two sentences.

## 2. Machine
CPU, RAM, OS, Python, PyTorch, CUDA availability, GPU and VRAM or "not available".

## 3. Benchmark protocol
Sizes, warm-up, repeats, statistic used, threads, dtype, synchronization.

## 4. Results
Table of median and minimum times per size and device.

## 5. GPU status
Measured, or not executed with a specific reason and the CPU-only substitution.

## 6. Reproducibility
Repeated seed result, three-seed mean and standard deviation, formula used.

## 7. Recommendation
When a GPU helps for this size and when it does not, with limits.

## 8. Reproduction
Exact commands, package files, seeds, runtime.

## 9. Honesty and privacy
Claims labeled measured or not executed; personal data removed.
```

## Rubric

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Technical correctness | 30 | Protocol is sound; timings include warm-up and synchronization; all three validation checks pass | Timings lack warm-up, or the repeated-seed check is missing |
| Evaluation and diagnosis | 25 | Speedups and spread are interpreted; GPU and transfer costs separated; recommendation follows evidence | Numbers listed without interpretation, or a speedup claimed without size or device |
| Reproducibility | 15 | Commands, seeds, versions, thread settings, and device reproduce the card | Partial settings; a reader could not rerun it |
| Data and ethics | 15 | Hardware limits stated honestly; no claimed GPU run without one; privacy redaction | Vague device description or an implied GPU result |
| Communication | 15 | Clear cards, labeled claims, readable tables | Disorganized, or measured and estimated claims mixed |

A dimension without evidence scores zero. A fabricated GPU row scores zero on
data and ethics and may invalidate the whole submission.

## Privacy and safety constraints

- Do not include usernames, hostnames, IP addresses, machine names, or absolute
  paths in the inventory, logs, or screenshots.
- Do not disable security software or driver protections to make a GPU appear.
- Do not install a GPU stack on a machine you do not own. Read
  [requirements/gpu.txt](../../technical/foundation-assets.md#cpu-and-gpu-requirements) before any GPU install.
- Do not commit generated logs, virtual environments, or caches.
- If a shared machine is used, ask before running a sustained benchmark; keep the
  total runtime short and report it.

## Self-check before submission

- [ ] `inventory.json` has no blank or guessed fields.
- [ ] Timings include warm-up, a stated repeat count, and a median.
- [ ] Median time increases with matrix size on both devices.
- [ ] The GPU row says either a measured device name or `not executed` with a
      reason.
- [ ] The two seed-7 runs match to four decimals.
- [ ] Mean and standard deviation are recomputed and the formula is named.
- [ ] Every claim in the card is labeled measured or not executed.
- [ ] The recommendation is limited to the sizes actually tested.
- [ ] No personal identifiers remain.
- [ ] I did not claim a GPU or Colab run that I did not perform.

Next: score the work with the [assessment](assessment.md), then continue to
[M04 - Training models from scratch](../../syllabus/level-1-foundations.md#m04).

---

**Module path:** [Lesson](index.md) · [Guided notebook](notebook.md) · **Lab brief** · [Assessment](assessment.md)
