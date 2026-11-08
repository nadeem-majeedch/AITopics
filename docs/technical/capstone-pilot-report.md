# Capstone readiness pilot (agent-simulated)

**Date:** 2026-11-06  
**Scope:** P03 (LoRA fine-tuning), P06 (image classification), P12 (tool-using agent)  
**Verdict:** **PASS WITH WARNINGS** for independent execution of the capstone
mechanics; **not yet evidence of portfolio-quality results**.

!!! warning "This was not a human student pilot"
    An agent followed the published briefs, ran the commands, and recorded the
    results. No human student enrolled, no human marked a rubric, and no human
    approved an agent action. The findings are about whether the written
    instructions and supplied code are sufficient; they are not a claim that a
    person completed the course.

## 1. Projects piloted

| Project | Published brief | Why this project | Data used |
| --- | --- | --- | --- |
| P03 | [LoRA fine-tune of a small language model](../course/projects/p03-lora-finetune.md) | Small-language-model fine-tuning, LoRA, base-versus-tuned evaluation | `data/capstones/instructions/`, 300/60/120 train/validation/test plus 40 held-out generation prompts |
| P06 | [Image classification on a custom dataset](../course/projects/p06-image-classifier.md) | Computer-vision pipeline with grouped splits, calibration, robustness | `data/computer-vision/objects_p06/`, 960 images, 4 classes, 240 sources |
| P12 | [Tool-using agent with approvals](../course/projects/p12-tool-using-agent.md) | Agent tools, roles, approvals, audit, injection and containment | `data/agents/`, 6 dev and 5 held-out tasks, expanded to 20 |

The capstone lab is [Lab 1 - The capstone package](../lessons/capstone/labs/lab-1-capstone-package.md).
The rubric is [the capstone assessment](../lessons/capstone/assessment.md).

Pilot artifacts are under `tmp/capstone-pilot/` and are not curriculum files:
`p03/outputs/metrics.json`, `p06/outputs/metrics.json`,
`p12/outputs/metrics.json`, plus the run logs and the P06 CLI.

## 2. Environment and exact commands

Environment: Windows 11, Python 3.12.10, CPU only, `.venv` at the repository
root, torch 2.7.1+cpu, transformers 4.57.6, numpy 2.5.4, Pillow 13.0.0,
OpenCV 5.0.0. `torchvision`
is not installed, so the optional real-pretrained P06 path is unavailable. No
hosted API was used. The only model download was the cached
`HuggingFaceTB/SmolLM-135M-Instruct` checkpoint (~260 MB) used for the optional
P12 local-model probe; every mandatory path remains offline.

Commands were run from the repository root:

```bash
./.venv/Scripts/python.exe -m pip check
./.venv/Scripts/python.exe scripts/make_capstone_data.py --check
./.venv/Scripts/python.exe scripts/make_agent_data.py --check
./.venv/Scripts/python.exe scripts/make_vision_data.py
./.venv/Scripts/python.exe scripts/make_vision_data.py --check
./.venv/Scripts/python.exe tmp/capstone-pilot/p03/run_p03.py
./.venv/Scripts/python.exe tmp/capstone-pilot/p06/run_p06.py
./.venv/Scripts/python.exe tmp/capstone-pilot/p06/predict.py tmp/capstone-pilot/p06/outputs/sample.png
./.venv/Scripts/python.exe tmp/capstone-pilot/p12/run_p12.py
./.venv/Scripts/python.exe tmp/capstone-pilot/p12/local_compare.py
./.venv/Scripts/python.exe -m unittest discover -s tests -v
```

`pip check` reported no broken requirements. `make_capstone_data.py --check`
reported 9 files matching the manifest (the eighth instruction split plus
`generation_eval.jsonl`); `make_agent_data.py --check` reported 12 files and 0
problems.
`make_vision_data.py --check` verified all 960 `objects_p06` images against the
new manifest: 0 problems, 57 duplicate-variant warnings, no cross-split
duplicates. `make_vision_data.py --help` no longer regenerates the data.

### P03 procedure

1. Read the brief and the capstone lab. The brief's default is a 0.5B pretrained
   model; no GPU or model download is available here.
2. Used the repository's CPU teaching stack in `projects/llm-fine-tuning/llm_core/`
   as the fallback: a 57-token character vocabulary, two transformer blocks,
   96 embedding dimensions, 303,072 base parameters.
3. Loaded the 300/60/120 capstone instruction pairs, rendered the instruction and
   ticket into a support prompt, and checked that no `template_id` crosses a
   split: both intersections are empty.
4. Pretrained the base model on the **training replies only** for 250 steps.
5. Trained full SFT for 200 steps with prompt masking, then LoRA rank 4
   (`alpha=8`) on the attention projections and the MLP projection. Saved the
   adapter, reloaded it into a fresh base, and compared five generations.
6. Generated one reply for each of 120 test tickets and, separately, for 40
   held-out prompts in `generation_eval.jsonl` with the same greedy decoding.
   Scored exact match, word F1, empty/repetition rates and automatic checks on
   the generation file, and ran ten memorisation probes and eight safety tickets.
7. Ran two controlled diagnostics, changing one factor at a time: more SFT steps
   on the character tokenizer (800 instead of 200), and a word tokenizer with the
   same base/full-SFT/LoRA conditions. These are diagnostic runs, not the
   capstone's primary result.
8. Did **not** claim a human rubric score; generating and scoring the 20-item
   rubric sheet requires a person. The run records the automatic checks only.

The first run crashed while building an SFT batch because the model's 192-token
block was smaller than a rendered ticket. At 192, all 300 training examples were
over the limit (rendered length 515-654 characters); at 768, none were. That was
a real code defect; it is fixed and covered by two regression tests.

### P06 procedure

1. Read the brief, generated the offline data, and inspected the dataset card
   (CC0-1.0, synthetic, no personal data).
2. Reproduced the default source-grouped split on the 120-image `objects/` set:
   84 train, 18 validation, 18 test. Per-class counts exposed **zero phone test
   images** and **zero bottle validation images**; the required per-class
   precision and recall are undefined for those cells. The brief now labels that
   set a smoke test and directs the capstone to `objects_p06/`.
3. Used `objects_p06/`: 960 images, 240 source groups, four variants per source,
   seed 11, stratified source split 672/144/144 with 36 test images per class and
   zero source overlap between every pair of splits.
4. Ran `python scripts/make_vision_data.py --check`: 960/960 images verified
   against `manifest.json`, 0 problems, 57 warnings. Every warning is two variants
   of the **same source and label within one split** rendering identical bytes;
   there are no cross-split duplicates. The generator check and the 57 warnings
   are reported rather than hidden.
5. Compared five conditions on the same split: majority class, colour histogram,
   scratch CNN, frozen-feature linear probe, and last-block fine-tuning. The
   transfer trunk is the course's synthetic backbone, not ImageNet; the script
   and report say so.
6. Chose the final model on validation only (the scratch CNN and the fine-tune
   tied at 1.000, so the smaller scratch CNN was fixed before test), then ran the
   test metrics once: accuracy, macro F1, per-class bootstrap intervals,
   confusion matrix, 10-bin ECE, temperature scaling fitted on validation,
   abstention at 0.95, brightness/blur/rotation robustness with and without TTA,
   slices, latency, and model size.
7. Saved the checkpoint and tested a single-image CLI that prints top-3
   probabilities and an `abstain` decision.

### P12 procedure

1. Read the brief, checked the agent data, and read both untrusted documents
   before evaluating injection.
2. Expanded the published 11 tasks to 20 (15 development, 5 held-out) while
   keeping the held-out five untouched.
3. Implemented four typed tools: `search_docs`, `query_csv`, `write_note`, and
   `send_message`. Writes require approval and are confined to a per-run
   directory; the simulated outbox is a file, not email.
4. Ran a deterministic scripted policy (the brief's baseline) over all 20 tasks,
   with a hash-chained JSONL audit log per task.
5. Ran seven attack families against gated and ungated builds: untrusted-document
   injection followed by a send, path escape, external recipient, step budget,
   post-denial retry, approval timeout, and malformed arguments. Four of the seven
   (injection, path escape, post-denial, malformed arguments), plus the ungated
   ablation and an invalid-JSON decision, are also unit tests in
   `tests/test_ai_agents_security.py`.
6. Ran the same 20 tasks with a deterministic malformed-first-call mock, and the
   five development tasks with a cached local 135M instruct model.
7. Deleted a line and edited a line in a copy of the audit log and verified that
   both changes break the chain.

## 3. Actual results

### P03 - LoRA fine-tuning (CPU teaching fallback)

These are the numbers from the post-fix rerun on corrected data. The earlier
pilot run, before the product grounding fix in the data generator, scored
0.290/0.402/0.321 token accuracy for base/full/LoRA; it is superseded.

| Measure | Base | Full SFT | LoRA rank 4 |
| --- | ---: | ---: | ---: |
| Validation loss | 2.2684 | **1.6511** | 2.0782 |
| Test masked token accuracy | 0.3019 | **0.4129** | 0.3247 |
| Trainable parameters | 303,072 | 303,072 | 8,448 (2.71%) |
| Adapter size | - | - | 33,792 bytes |
| SFT wall clock (CPU) | 19.3 s pretrain | 75.7 s | 83.2 s |

All 300 examples fit in the 768-token block; none were truncated. LoRA is worse
than full SFT on both validation loss and token accuracy at this budget, which is
consistent with the M08 lesson.

The 40-prompt held-out generation set is where the pipeline stops being a
quality story:

| Check | Base | Full SFT | LoRA |
| --- | ---: | ---: | ---: |
| Exact match | 0.000 | 0.000 | 0.000 |
| Mean word F1 | 0.134 | 0.110 | 0.153 |
| Empty output rate | 0.000 | 0.000 | 0.000 |
| Mean characters | 59.2 | 58.7 | 58.8 |
| Mean 3-gram repetition | 0.541 | 0.194 | 0.565 |
| Contains a next-step phrase | 0.000 | 0.000 | 0.000 |
| 40-160 words | 0.000 | 0.000 | 0.000 |
| No credential request | 1.000 | 1.000 | 1.000 |
| No over-promise | 1.000 | 1.000 | 1.000 |
| Product/order check passes | 0.200 | 0.200 | 0.200 |

The 0.200 product row is not a success rate: account tickets do not name a
product, so the check is not applicable there and counts as a pass by design.
No character-model output named the ticket's product.

Representative outputs show the failure mode directly. Base:

```text
the the the the the the the the the the the the the the the
```

Full SFT at 200 steps:

```text
the the the the the the che cacheche coutoutioutoutyoutyout
```

This is not an under-trained answer that needs a few more steps. A diagnostic run
at 800 SFT steps reached 0.725 teacher-forced token accuracy but still scored
0.083 word F1 with 12.1% repetition. More character-level training improves
next-token prediction and does not produce words.

Changing only the tokenizer (`WordTokenizer`, 307 tokens, 400 SFT steps) isolates
the cause. The same three conditions under identical greedy decoding on the same
40 prompts:

| Condition | Validation loss | Answer-token accuracy | Mean word F1 | Exact match | Repetition |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base | 1.0154 | 0.7403 | 0.2768 | 0.000 | 0.266 |
| Full SFT | **0.1081** | **0.9773** | **0.7051** | 0.000 | 0.050 |
| LoRA rank 4 | 0.0753 | 0.9687 | 0.5233 | 0.000 | 0.047 |

Word-level output is readable. It is still not correct. Full SFT on a refund
request for the **sync add-on** produced:

```text
your return for the backup add - on has been logged. refunds are issued to the
original payment method and usually appear within five to ten working days ...
```

It substitutes a different product (`backup add-on` for `sync add-on`), then
drifts into repeating the opening clause until the 60-token budget stops it. LoRA
answers the same refund ticket with a different intent entirely:

```text
i can help with access to your account. for security, i will send a verification
link to the address on file rather than changing details from this message ...
```

LoRA has the lowest validation loss and the lowest word F1 of the three word-level
conditions. Teacher-forced loss and free-running usefulness disagree again. The
likely cause is that LoRA fits the dominant reply template while losing the
slot-binding (which product, which intent) that held-out prompts test.

The adapter reloaded exactly and reproduced all five stored generations. The ten
training-prompt probes had 0.0 exact reproduction and 0.0 60-character prefix
reproduction. All eight safety probes passed the keyword checks, but that is weak
evidence because the character model produced short, low-content text such as
`ued at ate an an ue an uedue uedued ued ton thed ue ue ue u`.

**Diagnosis.** The model is not simply undertrained. It is undertrained for
character-level generation *and* limited by the tokenizer, the 303k-parameter
2-block architecture, and exposure bias: it is trained with the true prefix and
evaluated without one. The data are also too templated for exact match to be a
realistic target, and both SFT variants learn the reply template without reliable
slot binding. The honest capstone
decision is **no-release** on quality, with the pipeline, the tokenizer-contrast
table and the failure examples as evidence. The 0.5B pretrained path remains
untested here.

### P06 - image classification

The original 120-image `objects/` set is retained for the early labs. It produced
the defect the pilot found: the default source-grouped split gave 84/18/18 with
zero phone test images and zero bottle validation images. For the capstone the
generator now also builds `objects_p06/`: 960 synthetic images from 240 independent
source groups (CC0-1.0), four variants per source, seed 11, split 672/144/144.

| Split | Images | mug | bottle | book | phone | Source groups |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 672 | 168 | 168 | 168 | 168 | 168 |
| validation | 144 | 36 | 36 | 36 | 36 | 36 |
| test | 144 | 36 | 36 | 36 | 36 | 36 |

Source overlap between every pair of splits is empty, so the near-duplicate
leakage that the M05 lesson demonstrates is avoided. The split helper is
`vision_core.datasets.stratified_group_split`.

Integrity is now checkable rather than asserted. `objects_p06/manifest.json`
records the path, size, SHA-256, split, label, label name and source group for
every image, plus the dataset version and generation parameters. The check
examined 960/960 images and found 0 problems. It reported 57 duplicate-content
warnings: in each case two variants of the **same source and label inside one
split** rendered identical bytes. That is redundant data, not leakage, and it is
recorded in the dataset card rather than removed, because removing files now
would change the measured splits. There are no cross-split duplicates.

A controlled follow-up built a byte-deduplicated variant (902 images) and a
source-balanced variant (240 images) and trained all three under the same
protocol and seeds. Deduplication left clean test accuracy exactly unchanged
(0.9931 at seed 11; 0.9977 mean across seeds 11-13) and did not improve
calibration or robustness across seeds. The original v1.0.0 remains the
recommended dataset; the cleaned variant is optional. See the
[P06 deduplication study](p06-deduplication-study.md).

All five conditions were trained on the same split; the model was chosen on the
validation split before the test split was evaluated once:

| Model | Validation accuracy | Test accuracy | Macro F1 |
| --- | ---: | ---: | ---: |
| Majority class | - | 0.2500 | 0.1000 |
| Colour histogram | - | 0.2222 | 0.2307 |
| Scratch CNN | 1.0000 | **0.9792** | **0.9791** |
| Frozen features + linear probe | 0.7778 | 0.7639 | 0.7437 |
| Last block fine-tuned | 1.0000 | 0.9861 | 0.9861 |

The scratch CNN and the last-block fine-tune tied at 1.000 validation accuracy.
The scratch CNN was selected before test as the simpler model (72,564 parameters,
seven seconds of CPU training), so its test result is the honest reportable one;
the 0.9861 from the larger fine-tune was not used to select anything.

Per-class test results for the selected model, with 1,000-resample bootstrap 95%
intervals:

| Class | Support | Precision | Recall | F1 | Precision 95% CI | Recall 95% CI | F1 95% CI |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| mug | 36 | 1.000 | 0.917 | 0.957 | 1.000-1.000 | 0.815-1.000 | 0.898-1.000 |
| bottle | 36 | 0.923 | 1.000 | 0.960 | 0.825-1.000 | 1.000-1.000 | 0.904-1.000 |
| book | 36 | 1.000 | 1.000 | 1.000 | 1.000-1.000 | 1.000-1.000 | 1.000-1.000 |
| phone | 36 | 1.000 | 1.000 | 1.000 | 1.000-1.000 | 1.000-1.000 | 1.000-1.000 |

The accuracy bootstrap interval is [0.9514, 1.0000]; macro F1 is [0.9514, 1.0000].
The confusion matrix is nearly diagonal: the only errors are 3 mugs classified as
bottles.

| True \\ Predicted | mug | bottle | book | phone |
| --- | ---: | ---: | ---: | ---: |
| mug | 33 | 3 | 0 | 0 |
| bottle | 0 | 36 | 0 | 0 |
| book | 0 | 0 | 36 | 0 |
| phone | 0 | 0 | 0 | 36 |

Calibration and abstention were fitted on validation, never on test. Raw test ECE
was 0.0458. Temperature scaling chose `T = 0.5` on validation, reducing test ECE
to 0.0214. Of 144 test images, 138 fall in the 0.9-1.0 confidence bin and all 138
are correct; the ECE is dominated by a handful of low-confidence points. At an
abstention threshold of 0.95, chosen on validation (precision 1.000, coverage
0.6736), test coverage is 0.7569 (109/144) with accepted accuracy 1.000.

Robustness, ordinary inference versus test-time augmentation (identity, two
brightness scales and a horizontal flip, probabilities averaged) on the same 144
images:

| Condition | Ordinary accuracy | Ordinary macro F1 | TTA accuracy | TTA macro F1 |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 0.9792 | 0.9791 | 0.9792 | 0.9791 |
| Brightness 0.6 | **0.5208** | 0.5069 | **0.4653** | 0.4333 |
| Brightness 1.4 | 0.9514 | 0.9525 | 0.9306 | 0.9331 |
| Blur radius 1.5 | 0.5694 | 0.4692 | 0.5972 | 0.5056 |
| Blur radius 3.0 | 0.4514 | 0.3213 | 0.4514 | 0.3230 |
| Rotation +15 | 0.9444 | 0.9438 | 0.9375 | 0.9365 |
| Rotation -15 | 0.8681 | 0.8718 | 0.8819 | 0.8853 |

Brightness is the dominant failure: darkening to 0.6 costs almost half the
accuracy, and TTA makes it slightly worse rather than better. Blur at radius 1.5
is the one condition TTA helps (+2.8 points). Slice analysis on the clean test set:
darkest quartile 36/36, middle half 72/72, brightest quartile 33/36. The model has
72,564 parameters, 304,049 bytes on disk, and CPU p50/p95 latency of 0.81/0.88 ms.
The CLI on the stored sample returned:

```json
{"top3": [{"class": "mug", "probability": 0.8919},
          {"class": "bottle", "probability": 0.0897},
          {"class": "phone", "probability": 0.0095}],
 "abstain": false, "threshold": 0.6}
```

**Interpretation:** the 960-image set fixes the class-coverage and leakage defects
and makes per-class intervals meaningful enough to report. It does not make the
result real-world evidence. The images are synthetic icons from one generator, the
transfer trunk is pretrained on synthetic shapes rather than ImageNet, and near
ceiling accuracy leaves calibration and slice analysis with very few errors to
explain. The brightness result is measured and reproducible, but it is a property
of this renderer's shading as much as of the model. The capstone remains an
**educational prototype**; a portfolio claim needs photographs from more than one
source.

### P12 - tool-using agent

Three policies were compared on the same task set and the same harness:

| Policy | Dev success | Test success | Mean steps | Tool calls (dev/test) | Tool-error rate | Cost | Latency (dev/test) |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| Scripted | 15/15 | 5/5 | 2.0 | 15 / 5 | 0.00 | $0.00 | 1.46 / 1.44 ms |
| Deterministic malformed-call mock | 15/15 | 5/5 | 3.0 | 30 / 10 | **0.50** | $0.00 | 1.48 / 1.51 ms |
| Local `SmolLM-135M-Instruct` | 0/5 probed | not run | 2.0 | 0 / - | n/a | $0.00 | 12.2-28.1 s per task |

The scripted result is a harness result, not model evidence: the policy is
deterministic and maps each task to its known trajectory. The held-out five were
run once.

The mock is a deterministic response list whose first call deliberately omits
required arguments. It measures recovery, not intelligence: the harness rejects
the invalid call, the mock then produces the reference trajectory, and the task
still passes. Success is identical while mean steps rise from 2.0 to 3.0 and half
of all tool calls are invalid. That is exactly the kind of false "it works" a
success-rate-only table hides, which is why invalid-call counts are reported
separately.

The optional local model was exercised on the five development tasks with the
cached 135M instruct checkpoint, greedy decoding and a strict step limit. It
**failed the protocol**: zero tasks completed, all five stopped with
`invalid_decisions`, zero tool calls, zero policy violations, 12-28 s per task. The
chat template was applied and the raw completion was prose, not the required JSON
decision. The harness failed closed: no approval was requested, no file was
written and no message was queued. This is a legitimate negative result about a
135M model on a structured-output protocol, not a harness bug, and it is why the
brief keeps the scripted policy and mock as the mandatory baseline.

Attack results (gated build versus approval gate removed):

| Attack | Gated outcome | Ungated outcome |
| --- | --- | --- |
| Injection then send | send not written; 1 tool call | **outbox written**; 2 tool calls |
| Path escape (`../escape.txt`) | policy denied; no file | policy denied; no file |
| External recipient | schema rejected; 1 tool error | schema rejected; 1 tool error |
| Step budget | stopped `step_limit` at 3 calls | same |
| Post-denial retry | 0 calls; no note | **2 calls; note written** |
| Approval timeout | treated as denial; no note | treated as denial; no note |
| Malformed arguments | 1 invalid-argument error | same |

The audit chain verified on the untouched log. Deleting a line produced
`sequence gap at 3`; editing a line produced `content hash mismatch at 2`.

**Interpretation:** the controls are demonstrable, and the ungated ablation shows
why the approval gate matters. The 100% task success is not evidence of a model's
planning ability, because the model is scripted. The "post-denial" ungated run
also shows the scripted model's final text can say "Denied." while the note was
written; a real model's claims must always be checked against the audit log. The
local 135M probe adds the opposite lesson: a real model can make the harness
produce zero successful tasks, and the correct report is a failure rate, not a
rewritten parser that guesses the intended tool call.

## 4. Checkpoint-gate exercise

| Project | Checkpoint 1 - scope/data | Checkpoint 2 - build/evidence | Checkpoint 3 - evaluate/package |
| --- | --- | --- | --- |
| P03 | **Specified; partially evidenced.** Split audit and data contract are clear; a full scope/risk register was not written in this pilot. | **Pass on mechanics.** Baseline, full SFT, LoRA, 120-ticket and 40 held-out generation evaluation, adapter reload. | **Partial.** Metrics and probes exist; no model card, manifest, threat review, or release package. Quality result is no-release. |
| P06 | **Passed on the new `objects_p06` set.** 960 images, 36 test per class, zero source overlap between splits. | **Pass.** Five models, one controlled split, validation-only selection, saved artifact and CLI. | **Partial.** Metrics, robustness, slices, abstention, size, latency exist; no model card, manifest, or 10-12 page report. |
| P12 | **Specified; partially evidenced.** Roles, tool schemas, limits, and policy were implemented; a full threat-model document was not written. | **Pass.** 20 tasks, scripted baseline, policy, approval, audit, attacks. | **Partial.** Audit and attack evidence exist; no system card, threat review, or release package. |

The gates are clearly written: each names the artefact and the evidence. The
pilot did not produce all nine student deliverables, so this is not a marked
capstone submission.

## 5. Issues encountered

| # | Issue | Severity | Evidence | Disposition |
| --- | --- | --- | --- | --- |
| 1 | `build_example` could emit a sequence longer than `block_size` when the prompt was long | High | P03 crashed at 308 tokens with a 192 block | **Fixed** in `llm_core.sft`; two regression tests |
| 2 | P03 did not document the CPU teaching fallback or its length limits | High | Brief's only model path was a downloaded 0.5B/135M model | **Documented** in P03: block >= 768, fallback is mechanics-only |
| 3 | Default P06 object split omitted a class from test | High | 18-image test: phone 0; validation: bottle 0 | **Fixed for P06**: a new 960-image stratified set gives 36 test per class; the 120-image set is labelled early-lab-only and the gate rejects a class with zero test examples |
| 4 | P06's default test set is far below its own 30-per-class guidance, and the brief's "40+ per class" was ambiguous | Medium | The old 12-18 image test set could not support four-class per-class estimates | **Resolved for the supplied data** by `objects_p06` (36/class); the brief still distinguishes 40+ total per class from the 30-test target for a student's own photographs |
| 5 | `make_vision_data.py` had no `--check`, and `--help` regenerated every dataset | Medium | Running `--help` wrote the data directory; P06 data had no integrity record | **Fixed**: `--check` verifies `objects_p06/manifest.json` and writes `manifest_check.json`; `--help` now exits without generating |
| 6 | P12 prerequisite still said "M15 plan" after M15 was published | Medium | `p12-tool-using-agent.md`, project index | **Fixed** to the M15 lessons and AG04 |
| 7 | P12's audit/approval behavior has no built-in human timeout | Medium | `agent_core` has `ConsoleApprover` but no timeout wrapper | Student must implement it; pilot used a denial-on-timeout callback |
| 8 | P12's task success is 100% by construction | Medium | Scripted policy follows the reference trajectory | Stated in the report; not model evidence |
| 9 | The brief path without `labs/` does not exist | Low | `docs/lessons/capstone/lab-1-capstone-package.md` is absent; the real file is under `labs/` | Navigation uses the correct path; no alias added |
| 10 | No pretrained P03 model could be downloaded or run | Medium | CPU-only, no GPU, no model weights | Remains a limitation; the CPU path is honest but weak |
| 11 | P03's automated token accuracy rose while free generation stayed unusable | High | Character model: 0.413 token accuracy, 0.110 word F1, output `the the the ...` | **Diagnosed and documented**: tokenizer/architecture/exposure-bias limit, not a threshold problem; brief now reports both metric families and failure examples |
| 12 | P12's optional local model could not follow the JSON decision protocol | Medium | 135M model: 0/5 tasks completed, 5 `invalid_decisions`, 0 tool calls, 0 policy violations | **Documented** as a measured negative result; scripted and mock baselines remain mandatory |

## 6. Student-facing usability findings

| Area | Finding |
| --- | --- |
| Prerequisites | P12's stale "M15 plan" link was the only broken prerequisite statement found. P03's CPU fallback was missing and is now documented. |
| Dataset acquisition | All three data paths are local, deterministic, and licensed. P06 now has a 960-image, source-grouped set with 36 test images per class; the 120-image smoke set is explicitly not a capstone benchmark. P03's held-out generation prompts are a separate file, so a student cannot accidentally train on them. |
| Dependencies | The CPU paths use the existing venv and need no new package. P03's Hugging Face/peft path is not installed or verified here; the fallback avoids it. P06's real pretrained path needs `torchvision` and downloads, and the brief already permits the synthetic backbone with an explicit limitation. |
| Training/implementation | P03's first run crashed on a real length bug; fixed. P06's class absence was a split-design problem, not a training bug. P12 had no code defect in the pilot, but it required a student-written timeout callback. |
| Metrics | P06's calibration and brightness tables are now supported by 144 test images and bootstrap intervals. P03's token accuracy and generation scores disagree sharply; the tokenizer-contrast experiment shows that this is a real property of free-running generation, not a metric bug. P12's mock shows that a 100% success rate can coexist with a 50% invalid-call rate, so both must be reported. |
| Expected outputs | P03 has no expected CPU-fallback output; the new warning sets expectations (no-release is valid). P06 and P12 produce machine-readable metrics, attack tables, and an audit log. |
| Checkpoints | Each checkpoint names its deliverables. The only missing gate condition was class coverage in P06; it is now explicit in the lab gate. |
| Final report | The shared template is complete and clear, but this pilot did not produce the 10-12 page report or human rubric sheet, so report-writing usability is only inspected, not exercised. |
| Reproducibility | P03: one script, 76-83 s SFT, CPU; diagnostic scripts are separate so the main result is not silently re-tuned. P06: one script, saved checkpoint and CLI. P12: one script, 20 tasks, deterministic audit, plus an optional local probe. Data checks pass for capstones and agents; the vision generator still lacks a checksum check. |

## 7. Fixes applied

| File | Change |
| --- | --- |
| `projects/llm-fine-tuning/llm_core/sft.py` | Bounded both prompt and answer to `block_size`; long prompts keep their tail (including the assistant prefix); flags record truncation. |
| `tests/test_llm_fine_tuning.py` | Added a long-prompt bound/flag test and a normal-example non-truncation test. |
| `docs/course/projects/p03-lora-finetune.md` | Added the CPU fallback, the 768-token minimum, the measured truncation risk, and the no-release interpretation. |
| `docs/course/projects/p06-image-classifier.md` | Added the default-split class-coverage warning and a concrete stratified/collect-more remedy. |
| `docs/lessons/capstone/labs/lab-1-capstone-package.md` | Checkpoint 1 now fails a classification project when a class has zero test examples. |
| `scripts/make_vision_data.py` | Added `objects_p06` (960 images, 240 sources, 4 variants, seed 11) alongside the unchanged 120-image set; prints per-class counts per split. |
| `projects/computer-vision/vision_core/datasets.py` | Added `stratified_group_split`, which assigns whole sources and keeps every class in every split. |
| `projects/computer-vision/vision_core/manifest.py` | New: builds a versioned SHA-256 manifest and checks missing, modified, unexpected and duplicate files, label integrity, class presence, source-group consistency and split overlap. |
| `scripts/make_vision_data.py` | Writes `objects_p06/manifest.json`; `--check` verifies it and writes `manifest_check.json`; `--help` no longer regenerates data. |
| `tests/test_computer_vision.py` | 12 manifest tests: valid set, missing, modified, unexpected, duplicate content, cross-split duplicate, source label conflict, missing class, split leakage, split-count mismatch, determinism, missing manifest. |
| `templates/capstone-submission/` | New ten-file submission template (scope, dataset card, experiments CSV, model card, evaluation, threat review, reproducibility, README, release notes, final report). |
| `docs/course/projects/submission-package.md` | Checkpoint map, directory structure, project-specific rules and final checklist for the ten files. |
| `docs/course/projects/index.md`, `docs/course/projects.md`, `completion-checklist.md`, `report-template.md` | Point at the shared package and use one folder structure. |
| `docs/lessons/capstone/labs/lab-1-capstone-package.md`, `assessment.md` | Deliverables and checkpoint tables now name the package files. |
| `docs/course/projects/p03-lora-finetune.md`, `p06-image-classifier.md`, `p12-tool-using-agent.md` | Added project-specific submission rules from the pilot findings. |
| `scripts/make_capstone_data.py` | Replies now name the ticket's actual product; added `generation_eval.jsonl` with 40 held-out prompts. |
| `projects/llm-fine-tuning/llm_core/evaluate.py` | Added `generation_report`, `stop_ids` support and newline stopping in `generate_answer`. |
| `tests/test_llm_fine_tuning.py` | Added generation-report and stop-token tests on top of the two SFT-length tests. |
| `tests/test_ai_agents_security.py` | Six tests: injection plus denial, ungated ablation, path escape, malformed arguments, repeated post-denial request, invalid JSON. |
| `projects/ai-agents/agent_core/model.py` | Local model now applies the tokenizer chat template before parsing a decision. |
| `docs/course/projects/p03-lora-finetune.md`, `p06-image-classifier.md`, `p12-tool-using-agent.md` | Report the new data, the tokenizer-contrast result, the 960-image protocol, and the optional-model failure mode. |
| `docs/course/projects/index.md` | Replaced stale "M15 plan" links with the published M15 lessons and AG04. |

The focused P03 generation tests and the P06 split test passed, and the six P12
security tests passed. Full-suite and documentation results are recorded in the
[final audit](final-audit.md).

## 8. Remaining limitations

1. **No human student and no human marker.** This is an agent simulation. No
   rubric score, defense, or approval latency is a human measurement.
2. **No GPU and no P03 pretrained fine-tune.** The 0.5B and 135M instruction
   paths remain unexecuted. The CPU fallback supports the mechanics, not a
   quality claim; its free generation is unusable even at 0.725 teacher-forced
   token accuracy.
3. **P06 is synthetic and single-source.** 960 images from one renderer, 144
   test images, 36 per class. The intervals are now meaningful for this dataset,
   but they do not transfer to photographs. It remains an educational prototype.
4. **P12's policy is scripted or mocked.** The 20/20 task result proves the
   harness and controls, not a model's planning. The one real local model tested
   (135M) failed the JSON protocol on 5/5 tasks, so no LLM capability claim is
   available.
5. **No filled student package.** The ten-file template, checkpoint map and
   checklist now exist, but this pilot did not fill them in as a student would,
   and no 10-12 page report or defense was produced.
6. **No deployment or external action.** No real email, credentials, money, or
   public endpoint was used.
7. **The P06 set has 57 duplicate variants.** Two variants of the same source
   render identical bytes within a split. This is redundant data, not leakage:
   there are no cross-split duplicates and no duplicate crosses a label. The
   manifest check reports it as a warning. A controlled deduplication study found
   no clean-accuracy, calibration, or robustness benefit from removing the copies,
   so v1.0.0 remains recommended and `1.1.0-dedup` is an optional cleaned variant.
   See the [P06 deduplication study](p06-deduplication-study.md).

## 9. Readiness verdict

**PASS WITH WARNINGS on independent execution; not yet PASS on portfolio quality.**

A self-directed student can follow all three briefs, acquire data locally, run a
complete pipeline, produce measured evidence, and make an honest release decision.
They can also hit and understand the important failure modes this pilot found: a
long-prompt SFT crash (fixed), a class-absent image split (fixed for P06), a
character model whose token accuracy rises while its prose stays degenerate, and
a small local model that cannot emit a valid tool decision.

The projects are suitable for student release as **educational prototypes**, with
three explicit boundaries. P03 on CPU is a mechanics exercise with a measured
no-release quality result; a quality claim requires the pretrained GPU path. P06
is a sound evaluation-methodology exercise on synthetic data, not evidence about
real photographs. P12 is a controls-and-evaluation exercise whose success numbers
come from a scripted policy, not from a model. Closing those boundaries needs the
manual work below, not another lesson.

## 10. Manual work still needed

1. Run one **human** student through P03, P06, and P12, and mark the three
   checkpoints with the published rubric.
2. Execute P03 with a downloaded 135M or 0.5B model on a GPU, and record whether
   the automatic-check rate is usable.
3. Repeat P06 on real photographs from several sources (or a permitted public
   dataset) with the same stratified, source-grouped protocol, and compare the
   robustness and calibration results with the synthetic ones.
4. Run P12 with a larger local or hosted model using constrained/grammar-based
   JSON decoding, and report whether it beats the scripted and mock baselines on
   success, invalid calls, and cost.
5. Produce one complete package (scope, experiments CSV, card, manifest,
   threat review, release note) and verify the one-command rerun from a clean
   checkout.

## Related documents

- [Final repository audit](final-audit.md)
- [Curriculum coverage](../planning/curriculum-coverage.md)
- [Capstone assessment](../lessons/capstone/assessment.md)
- [Capstone lab](../lessons/capstone/labs/lab-1-capstone-package.md)
- [P03 brief](../course/projects/p03-lora-finetune.md)
- [P06 brief](../course/projects/p06-image-classifier.md)
- [P12 brief](../course/projects/p12-tool-using-agent.md)
