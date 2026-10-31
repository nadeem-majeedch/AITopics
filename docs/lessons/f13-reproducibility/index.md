# F13 - CPU/GPU basics, seeds, reproducibility, and experiment tracking {#f13}

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Level** | 1 - Foundations (implements [M03](../../syllabus/level-1-foundations.md#m03)) |
| **Study time** | 8 hours: 2 h theory, 3 h guided notebook, 2 h lab, 1 h assessment |
| **Hardware** | CPU-only core. A GPU comparison is optional and never required. |
| **Prerequisites** | [F12 - Backpropagation](../f12-backpropagation/index.md); environment setup from [M01](../m01-environment/index.md) |
| **You will produce** | An executed notebook, a run log, an environment report, an independent reproducibility audit, and a short reflection |

## Why this module exists

Three runs of the same script, same data, same model, three different seeds:

| Seed | Validation accuracy | Validation loss |
| --- | --- | --- |
| 7 | 0.848 | 0.314 |
| 17 | 0.872 | 0.257 |
| 27 | 0.904 | 0.246 |

The best run is 0.904. The worst is 0.848. Reporting "0.904" is not a lie, but it
is not a result either: it is the maximum of three samples. The honest summary is
**0.875 with a standard deviation of 0.023**, plus a record of what varied.

This module separates three ideas that beginners merge:

- a **random seed**, which resets a pseudo-random sequence;
- **determinism**, which asks whether the same operations run in the same order
  and produce bit-identical numbers;
- a **reproducible experiment record**, which lets another person rerun your work
  and interpret small differences.

It also covers the hardware question honestly. This course runs on CPUs. A GPU
is an optimization for some workloads, not a requirement, and a CPU-only result
is a valid result when it is labeled as such.

## Learning objectives

By the end of this module, you can:

1. Explain what a CPU and a GPU are each good at, and name one workload where a
   GPU is slower than a CPU.
2. Seed Python, NumPy, and PyTorch and demonstrate that the same seed reproduces
   a tensor sequence on the same device.
3. Distinguish bitwise reproducibility, statistical reproducibility, and a run
   record.
4. Measure a matrix multiplication with warm-up and synchronization, and report
   the device alongside the time.
5. Compute the mean and standard deviation of repeated runs and explain why the
   best run is not the result.
6. Write a JSON Lines run log and an environment report that contain no personal
   data and are readable by another person.
7. Complete a hardware comparison on CPU alone when no GPU is available, and
   state clearly what was not executed.

## Before you start

| Requirement | Why it matters |
| --- | --- |
| F12 completed | The notebook trains a small model and reads its metrics |
| PyTorch installed from `requirements/cpu.txt` | The timing and training cells need `torch` |
| A CPU with at least 2 cores | Thread-count comparisons need more than one |
| Optional: an NVIDIA GPU with a matching driver and CUDA wheel | Needed only for the optional GPU comparison |
| 500 MB free disk and about 10 minutes | Logs and reports are small; training is short |

Install the CPU stack with:

```powershell
python -m pip install -r requirements/cpu.txt
```

The files are in the repository: [requirements/cpu.txt](../../technical/foundation-assets.md#cpu-and-gpu-requirements)
for the CPU-only stack and [requirements/gpu.txt](../../technical/foundation-assets.md#cpu-and-gpu-requirements)
for the optional GPU stack. Read both before installing. The GPU file warns you
not to use it on a CPU-only machine.

## The concepts you need

### 1. CPU and GPU: different shapes of parallelism

A **CPU** has a few powerful cores optimized for sequential work, branchy code,
and low latency. A **GPU** has thousands of simpler arithmetic units optimized
for throughput on large, regular operations such as matrix multiplication.

| Workload | Better device | Why |
| --- | --- | --- |
| Loading and cleaning a CSV | CPU | Branchy code, disk latency, small data |
| 512 x 512 matrix multiply | Either; CPU is fine | Small enough that launch overhead matters |
| 4096 x 4096 matrix multiply | GPU | Much more parallel arithmetic per transfer |
| Training a small MLP on 500 rows | CPU | Data is tiny; the GPU sits idle between launches |
| Training a vision model on 100,000 images | GPU | Large batches, repeated convolutions |

Two costs erase GPU gains on small work:

- **Launch overhead:** each kernel launch has a fixed cost, often tens of
  microseconds.
- **Transfer overhead:** data must move between system RAM and GPU memory. For a
  small operation, the transfer can cost more than the computation.

**VRAM** is GPU memory. Model weights, gradients, optimizer state, and
activations must fit during training. Running out produces an out-of-memory
error even when system RAM is free.

In the verified CPU run, a 512 x 512 matrix multiplication took about **0.95 ms**
after warm-up. That number is machine-dependent and is useful only alongside the
device name.

### 2. Where randomness enters a training run

Training is not one random draw. Randomness enters at several points:

| Source | Example | Controlled by |
| --- | --- | --- |
| Weight initialization | Starting values of each layer | Framework seed, before model creation |
| Data order | Shuffling batches each epoch | Framework or DataLoader seed |
| Data splitting | Which rows land in train or test | NumPy or pandas seed |
| Dropout | Which units are dropped | Framework seed |
| Augmentation | Random crops, flips, noise | Framework or library seed |
| Sampling | Mini-batch selection, bootstraps | NumPy or framework seed |

If you seed only one source, the others still vary. That is why the notebook's
`set_seed` seeds all three libraries.

### 3. Three generators, one function

Python, NumPy, and PyTorch each maintain an independent pseudo-random generator.
A **pseudo-random generator** is a deterministic algorithm that produces a
sequence that looks random; the seed selects the starting state.

```python
def set_seed(seed: int) -> None:
    random.seed(seed)          # Python's random module
    np.random.seed(seed)       # NumPy global generator
    torch.manual_seed(seed)    # PyTorch CPU and CUDA generators
```

| Call | Controls | Common mistake |
| --- | --- | --- |
| `random.seed` | `random.random`, `random.shuffle` | Forgetting it when Python shuffles a list |
| `np.random.seed` | Legacy NumPy global functions | Assuming it also seeds `default_rng()` instances |
| `torch.manual_seed` | Torch tensor creation, dropout, initialization | Calling it after the model is built |
| `torch.cuda.manual_seed_all` | All CUDA devices | Needed for multi-GPU code; not for CPU |

Order matters: seed first, then build the model, then create the split. A seed
applied after initialization does not undo the initialization that already
happened.

### 4. What a seed guarantees, and what it does not

A seed makes a pseudo-random sequence repeatable **on the same software stack and
device**. It does not guarantee identical results everywhere.

| Question | Answer |
| --- | --- |
| Same seed, same code, same machine, same versions? | Usually bit-identical for CPU training |
| Same seed, different library version? | May differ; algorithms and defaults change |
| Same seed, CPU versus GPU? | Frequently differs; reduction order and precision differ |
| Same seed, two different GPU models? | May differ; kernel implementations and atomics differ |
| Same seed, different thread count? | May differ; parallel reductions change summation order |

Reproducibility is therefore a spectrum. **Bitwise reproducibility** means
identical numbers. **Statistical reproducibility** means conclusions hold within
reported variation. The second is what most experiments actually need, and it
requires reporting the spread.

### 5. Determinism settings and their cost

PyTorch can be asked to prefer deterministic algorithms:

```python
torch.use_deterministic_algorithms(True, warn_only=True)
```

With `warn_only=True`, PyTorch uses a deterministic implementation when one
exists and warns instead of raising when it does not. The setting can reduce
speed and does not make every GPU operation bitwise reproducible. Record whether
you enabled it, and report variation rather than promising identical numbers.

On CUDA, `torch.backends.cudnn.benchmark = True` lets cuDNN pick the fastest
convolution algorithm for your input shapes. It is fast but can select different
algorithms between runs, which changes results. Choose speed or determinism
deliberately; do not set both and hope.

### 6. Reporting variation instead of a best run

The notebook's three seeds produce accuracies 0.848, 0.872, and 0.904:

```text
mean = (0.848 + 0.872 + 0.904) / 3 = 0.8747  -> 0.875
```

The standard deviation is about **0.023**. With only three runs, this estimate is
rough; it is still far more informative than a single number.

| Practice | Better alternative |
| --- | --- |
| Report the best of three seeds | Report mean and standard deviation across seeds |
| Report one run and call it "the accuracy" | State the number of runs and the seed list |
| Compare two models with different seeds | Use the same seed set for both |
| Hide a failed seed | Include it, or explain why it was excluded |
| Claim a 1-point improvement from one run each | Check whether it exceeds the seed-to-seed spread |

If the improvement is smaller than the spread, you have not shown an improvement.
You have shown noise.

### 7. Experiment tracking without a server

An **experiment tracker** records what you ran and what happened. It does not need
a database. A **JSON Lines** file (`.jsonl`) stores one JSON object per line, so a
crashed run still leaves valid earlier records.

```python
with path.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(record, sort_keys=True) + "\n")
```

| Field | Example | Why it is needed |
| --- | --- | --- |
| `seed` | `17` | Separates initialization noise from real effects |
| `model` | `mlp_2_12_1` | Identifies the architecture unambiguously |
| `optimizer`, `lr`, `epochs` | `adam`, `0.05`, `80` | Defines the training recipe |
| `val_accuracy`, `val_loss` | `0.872`, `0.2572` | The measured outcome |
| `device` | `cpu` | Makes performance and determinism interpretable |
| Environment versions | `torch 2.4.1+cpu` | Explains differences across machines |

An **environment report** adds Python, PyTorch, NumPy, platform, device name, and
the seed list. The notebook writes both `outputs/f13_runs.jsonl` and
`outputs/f13_environment_report.json`.

!!! warning "No personal data in logs"
    A platform string can contain a hostname, and an error trace can contain a
    home directory. Review logs before sharing. Remove usernames, absolute paths,
    hostnames, and tokens.

## Guided walkthrough

The [guided notebook](notebook.md) runs six short sections:

1. **Seeds** - two sequences from seed 123 are identical.
2. **CPU versus GPU timing** - warm-up, then five timed 512 x 512 multiplications;
   about 0.95 ms on the verified CPU.
3. **Determinism** - requests deterministic algorithms and asserts the flag.
4. **A tiny tracker** - writes one JSONL record and reads it back.
5. **Three seeds** - trains the same model with seeds 7, 17, 27 and logs each run.
6. **Read back and report** - prints the three records and writes the environment
   report.

What each part proves: section 1 proves the seed resets the sequence; section 2
proves timing needs warm-up; section 3 proves the determinism request is active;
sections 4-6 prove the record is machine-readable and complete. The GPU branch is
present in the code but was not executed in the authoring environment.

## Practical exercise

This exercise stays inside the notebook and is not the independent lab.

1. Rerun the notebook unchanged and confirm the two tensors from seed 123 match.
2. Edit `set_seed` to remove the `torch.manual_seed(seed)` line, leaving only the
   Python and NumPy seeds. Rerun the three-seed training cell twice and record
   both sets of accuracies.
3. Restore `torch.manual_seed(seed)` and rerun. Confirm the original accuracies
   return.
4. Change the seed list to `[7, 17, 27, 37, 47]`, rerun, and compute the new mean
   and standard deviation.

Expected observations:

| Step | Expected | Why |
| --- | --- | --- |
| Same seed twice | Identical tensors | One generator, one sequence |
| Torch seeding removed | Accuracies change between reruns and no longer match the seed labels | Weight initialization and training noise come from PyTorch's generator |
| Full seeding restored | 0.848, 0.872, 0.904 return | Every generator is reset in the same order |
| Five seeds | A similar center with a spread that may grow or shrink | Five samples estimate the spread better than three, but do not guarantee a higher mean |

A subtlety worth noticing: in this notebook the data split and the dataset both
use a fixed `random_state=42`, so the NumPy global seed does not change them.
Seeding NumPy matters in pipelines that call NumPy's global functions for splits
or augmentation; seeding PyTorch matters here because the model lives there. The
point of the exercise is to know which generator controls which part of your
pipeline.

## Common mistakes and how to diagnose them

| Symptom | Likely cause | How to diagnose | Fix |
| --- | --- | --- | --- |
| Same seed gives different accuracy | The model was built before seeding, or data order changed | Print the seed calls and move them to the top | Seed first, then split, then build the model |
| `cuda available: False` and you expected `True` | CPU wheel, missing driver, or no NVIDIA GPU | Check `torch.version.cuda` and `nvidia-smi` | Install the correct wheel or continue on CPU |
| GPU is slower than CPU | Small operation, launch and transfer overhead dominate | Time larger matrices and include a warm-up | Use CPU for small work; batch more work per transfer |
| Timing varies wildly between runs | No warm-up, or missing `torch.cuda.synchronize()` | Compare first and later iterations | Warm up, synchronize, report the median |
| Standard deviation is 0.000 across seeds | The model is reinitialized with the same state, the task is saturated, or accuracies were copied | Print the accuracy per seed and the seed before each run | Rebuild the model after `set_seed(seed)`; check that the data split actually varies |
| Warning that an operation is not deterministic | The operation has no deterministic implementation | Read the warning text and identify the operation | Accept the warning with `warn_only=True`, or change the operation |
| JSONL has 6 records instead of 3 | The file was appended by a previous run | Count lines and inspect timestamps | Delete or archive the log before a fresh run |
| Report contains `C:\Users\...` | Platform or traceback captured a home path | Search the JSON for your username | Redact paths before sharing |
| Accuracy claim cannot be compared | Different seeds or epochs per model | Read the log fields | Hold the recipe fixed and vary one factor |

## Checkpoint

- [ ] I can name one workload where a GPU helps and one where it does not.
- [ ] I can explain the difference between a seed and determinism.
- [ ] I can seed Python, NumPy, and PyTorch in the correct order.
- [ ] I can compute a mean and standard deviation for three runs by hand.
- [ ] I can explain why 0.904 is not "the result" of three seeds.
- [ ] I ran the notebook and both output files exist.
- [ ] I can describe what my run log contains and what it omits.

## Next step

1. Run the [guided notebook](notebook.md) and check the run log against the
   expected results.
2. Complete the [lab brief](lab.md): a CPU/GPU and reproducibility audit with a
   CPU-only completion path.
3. Score your evidence with the [assessment](assessment.md).
4. Continue to [M04 - Training models from scratch](../../syllabus/level-1-foundations.md#m04),
   the next approved module after M03.

This unit completes the foundation sequence F01-F13.

---

**Module path:** **Lesson** · [Guided notebook](notebook.md) · [Lab brief](lab.md) · [Assessment](assessment.md)
