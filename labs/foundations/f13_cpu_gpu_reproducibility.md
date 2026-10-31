# F13 lab submission - hardware and reproducibility audit

Use this file as the front page of your submission. Replace each bracketed
section with your own content. The full task is in the
[F13 lab brief](../../docs/lessons/f13-reproducibility/lab.md).

## Scenario summary

I audited the claim that "the GPU is 20x faster" for small models by timing matrix
multiplications on the hardware I actually have, repeating a seeded training run,
and writing a measurement and reproducibility card. Where a GPU was unavailable,
I used the CPU-only substitution and labeled the GPU row as not executed.

## My decision

- Question: [for which sizes does a GPU help on this class of model?]
- Hardware used: [CPU model; GPU model and VRAM, or "no GPU available"].
- Largest measured speedup and at which size: [x.x at size N, or "not applicable"].
- Repeated seed-7 result: [identical / differs, with the value].
- Mean validation accuracy: [0.000] +/- [0.000] over seeds [7, 17, 27].
- Recommendation in one sentence: [when to use a GPU for this model size].

## Constraints I worked within

- CPU-only completion path if no GPU was available.
- No rented, borrowed, or misrepresented hardware.
- Python 3.12 and PyTorch from [requirements/cpu.txt](../../requirements/cpu.txt),
  or the optional [requirements/gpu.txt](../../requirements/gpu.txt) stack.
- Total benchmark runtime under [10] minutes.

## Required artifacts

| Artifact | Present | Notes |
| --- | --- | --- |
| `bench.py` or `bench.ipynb` | [ ] | Runs end to end |
| `inventory.json` | [ ] | No blank or guessed fields |
| `timings.csv` | [ ] | size, device, threads, dtype, median, min |
| `runs.jsonl` | [ ] | Seed 7 twice, seeds 17 and 27 once |
| `environment_report.json` | [ ] | Versions, device, seeds, mean, std |
| `card.md` | [ ] | Follows the headings below |
| `reflection.md` | [ ] | 200-300 words |

## Commands, seeds, and hardware

```text
Python:            [3.12.x]
torch:             [2.4.x, +cpu or CUDA tag]
OS:                [Windows 11 / other]
CPU:               [model, core count]
RAM:               [GB]
GPU:               [model and VRAM, or "not available"]
CUDA available:    [True / False]
Threads:           [1 / 2 / default]
Matrix sizes:      [128, 256, 512, 1024]
Warm-up / reps:    [3 / 10]
Training seeds:    [7 (twice), 17, 27]
Reproduce with:    [exact command]
Runtime:           [measured minutes]
```

## Report headings

```markdown
# F13 hardware and reproducibility card
## 1. Question
## 2. Machine
## 3. Benchmark protocol
## 4. Results
## 5. GPU status
## 6. Reproducibility
## 7. Recommendation
## 8. Reproduction
## 9. Honesty and privacy
```

## Validation checks

- [ ] Every inventory field is measured or marked `not available` with a reason.
- [ ] Median time increases with matrix size.
- [ ] The two seed-7 runs match to four decimal places.
- [ ] `runs.jsonl` contains exactly four training records.
- [ ] Recomputing mean and standard deviation matches `environment_report.json`.

## Rubric reminder

| Dimension | Weight |
| --- | --- |
| Technical correctness | 30 |
| Evaluation and diagnosis | 25 |
| Reproducibility | 15 |
| Data and ethics | 15 |
| Communication | 15 |
| **Total** | **100** |

## Self-check

- [ ] My GPU row is measured or explicitly `not executed`, never invented.
- [ ] Timings include warm-up and, on GPU, synchronization.
- [ ] Speedups are stated with matrix size and device.
- [ ] I reported mean and spread, not the best seed.
- [ ] I named the standard deviation formula I used.
- [ ] My recommendation is limited to the sizes I tested.
- [ ] No usernames, hostnames, or absolute paths remain.
- [ ] I did not claim a Colab or GPU run I did not perform.

Next: score the work with the
[F13 assessment](../../docs/lessons/f13-reproducibility/assessment.md).
