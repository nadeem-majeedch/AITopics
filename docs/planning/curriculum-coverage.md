# Curriculum coverage: M04-M16

This page maps the modules from M04 to M16 to their published lessons, notebooks,
labs, and assessments. It is maintainer documentation: it records what exists, what
was executed, and what remains limited. Student navigation belongs in the
[lessons index](../lessons/index.md) and the [notebook library](../notebook-library.md).

Status as of **2026-11-08**. Every notebook below was executed top-to-bottom in the
project virtual environment on Windows 11, Python 3.12.10, CPU only, unless a
limitation says otherwise.

## Summary

| Module | Lessons | Notebook | Labs | Assessment | Status |
| --- | --- | --- | --- | --- | --- |
| M04 | 5 | `notebooks/model-training/m04_training_from_scratch.ipynb` | 2 | 1 | Published, executed |
| M05 | 5 | `notebooks/model-training/m05_data_engineering.ipynb` | 2 | 1 | Published, executed |
| M06 | 4 | `notebooks/llm-fine-tuning/m06_transformers.ipynb` | 3 (shared) | 1 | Published, executed |
| M07 | 3 | `notebooks/llm-fine-tuning/m07_sft_small_lm.ipynb` | 3 (shared) | 1 | Published, executed |
| M08 | 3 | `notebooks/llm-fine-tuning/m08_lora_qlora.ipynb` | 3 (shared) | 1 | Published, executed |
| M09 | 16 | [M09 notebook](../notebooks/chatbots-rag/m09_chatbots.ipynb) | 8 projects (shared) | 1 | Published, executed |
| M10 | 16 (shared) | [M10 notebook](../notebooks/chatbots-rag/m10_rag.ipynb) | 8 projects (shared) | 1 | Published, executed |
| M11 | 14 | [M11 notebook](../notebooks/computer-vision/m11_image_classification.ipynb) | 8 (shared) | 1 | Published, executed |
| M12 | 14 (shared) | [M12 notebook](../notebooks/computer-vision/m12_object_detection.ipynb) | 8 (shared) | 1 | Published, executed |
| M13 | 14 | [M13 notebook](../notebooks/speech-audio/m13_speech_audio.ipynb) | 8 | 1 | Published, executed |
| M14 | 15 | [M14 notebook](../notebooks/video-ai/m14_video_ai.ipynb) | 8 | 1 | Published, executed |
| M15 | 5 | `notebooks/ai-agents/m15_agents.ipynb` | 1 | 1 | Published, executed |
| M16 | 5 | `notebooks/production/m16_production.ipynb` | 1 | 1 | Published, executed |
| M17 | 3 | reuses M04-M16 notebooks | 1 | 1 | Published; capstone is project work, not a new notebook |

Total for M04-M08 and M15-M17: **33 lessons, 7 executed notebooks, 8 lab briefs,
and 5 assessments**. The four applied slices add **M09-M14 with six executed
notebooks** and their existing lesson, lab, and assessment corpus. The whole course
now ships **26 executed notebooks**, all linked from the
[notebook library](../notebook-library.md).

## M04 - Training models from scratch

Section: [`docs/lessons/model-training/`](../lessons/model-training/index.md)

| Lesson | Topic |
| --- | --- |
| `mt01-training-loop.md` | the training loop, batches, epochs, and logging |
| `mt02-loss-and-optimizer.md` | loss functions, gradients, SGD/Adam, learning rate |
| `mt03-augmentation-and-regularization.md` | augmentation, weight decay, dropout, early stopping |
| `mt04-evaluation-and-error-analysis.md` | metrics, confusion, slices, error inspection |
| `mt05-checkpoints-and-compute.md` | checkpoints, resumption, mixed precision, cost |

Notebook evidence: 300 synthetic images split 210/45/45. Random split leaks 91
near-duplicate images; the grouped split leaks 0. Random-split accuracy 0.867 versus
grouped 0.622 (premium slice 0.244), which is the leakage lesson. Plain 0.956 versus
augmented 1.000. bf16 3.50 ms/step versus fp32 1.73 ms/step on this CPU, reported as
a measured negative result. Checkpoint restore is exact. Error analysis finds 2
errors on the plain model, both circle-to-triangle.

Labs: `labs/lab-1-training-ablation.md` (controlled ablation),
`labs/lab-2-dataset-audit.md` (audit and leakage probe).

## M05 - Dataset preparation, labelling, cleaning, augmentation

Section: [`docs/lessons/model-training/`](../lessons/model-training/index.md)

| Lesson | Topic |
| --- | --- |
| `mt06-dataset-audit.md` | inventory, missingness, duplicates, class balance |
| `mt07-cleaning-and-labels.md` | normalisation, label taxonomy, adjudication |
| `mt08-leakage-and-splits.md` | grouped, temporal, and near-duplicate leakage |
| `mt09-label-noise.md` | noise models, agreement, kappa, cleaning limits |
| `mt10-dataset-cards.md` | provenance, licence, intended use, limitations |

Notebook evidence: 650 messy rows cleaned to 600; 10 blank labels and 49 duplicate
rows removed. Vocabulary 533. Random split 0.983 versus grouped 0.984 with
near-duplicate overlap 16 versus 0; 24,976 near-duplicate pairs measured. Noise
curve 1.000/0.868/0.794/0.382. Cohen's kappa 0.866/0.723/0.509. A dataset card is
written by the notebook.

Note: `scikit-learn` is blocked by Windows Application Control in this environment
(`DLL load failed while importing _weight_vector`), so the notebook implements
Naive Bayes and kappa inline. No lesson depends on the blocked DLL.

## M06 - Transformers and language models

Section: [`docs/lessons/llm-fine-tuning/`](../lessons/llm-fine-tuning/index.md)

| Lesson | Topic |
| --- | --- |
| `lf01-tokens-and-embeddings.md` | tokenisation, vocabulary, embeddings |
| `lf02-attention.md` | queries, keys, values, causal masking |
| `lf03-transformer-block.md` | residual stream, layer norm, MLP, stacking |
| `lf04-tiny-lm-training.md` | training a character-level transformer |

Notebook evidence: 23 cells, 239,040 parameters, 400 steps in 22.8 s on CPU (24.8 s in an earlier run). Loss
3.454 to 0.433; validation perplexity 1.54. The model is deliberately tiny; the
lesson is the mechanism and the measurement, not the benchmark.

## M07 - Small language models and supervised fine-tuning

| Lesson | Topic |
| --- | --- |
| `lf05-sft-data-and-templates.md` | instruction format, chat templates, split by template |
| `lf06-sft-loss-and-masking.md` | label shifting, prompt masking, padded batches |
| `lf07-evaluating-assistants.md` | exact match, token F1, forgetting, held-out templates |

Notebook evidence: answer loss 1.039 to 0.315. Exact match 0.688 to 0.905; first-12
tokens 0.411 to 0.818; word F1 0.087 to 0.258. Forgetting check 0.885 to 1.072,
reported rather than hidden. FAQ splits are disjoint by question template, not by
topic; this is documented because it makes the evaluation harder, not easier.

## M08 - LoRA, QLoRA, quantization, efficient training

| Lesson | Topic |
| --- | --- |
| `lf08-lora.md` | low-rank adapters, rank, alpha, merge |
| `lf09-quantization-and-qlora.md` | int8/int4, error, QLoRA trade-offs |
| `lf10-merging-and-serving.md` | merge, export, serving contracts |

Notebook evidence: LoRA 8,448 parameters (3.34% of the model), loss 0.601 versus
0.315 full fine-tuning, accuracy 0.816 versus 0.905. Merge delta 6.7e-6. int8
259.8 KiB (3.758x smaller), int4 139.1 KiB (7.022x); accuracy 0.905/0.900;
agreement 0.992/0.895. The lesson is that compression is a measured trade-off, not
a free win.

Shared code: `projects/llm-fine-tuning/llm_core/` (`data`, `tokenizer`, `model`,
`train`, `sft`, `lora`, `quantize`, `evaluate`). Reused by all three notebooks and
covered by `tests/test_llm_fine_tuning.py` (33 tests).

## M09-M14 - Applied vertical slices

These six notebooks close the gap between the ten existing applied lessons and a
runnable guided practical. Each uses the section's tested `*_core` package and its
CC0-1.0 synthetic data. No notebook downloads a model or a dataset.

| Module | Notebook | Evidence from the executed run |
| --- | --- | --- |
| M09 | [m09_chatbots.ipynb](../notebooks/chatbots-rag/m09_chatbots.ipynb) | Six cited FAQ chunks; BM25, dense, and hybrid rankings; bounded history retains 2 of 10 messages; injection flagged with two matches; email and student id redacted |
| M10 | [m10_rag.ipynb](../notebooks/chatbots-rag/m10_rag.ipynb) | Registration answer cites `registration.md`; fabricated `[99]` rejected; strict configuration abstains on an off-corpus question |
| M11 | [m11_image_classification.ipynb](../notebooks/computer-vision/m11_image_classification.ipynb) | 210/45/45 grouped images; 0.867 test accuracy against 0.40 majority baseline; per-class confusion and confident errors |
| M12 | [m12_object_detection.ipynb](../notebooks/computer-vision/m12_object_detection.ipynb) | 40 images, 59 boxes; mAP@0.5 0.169; per-class AP; predicted boxes inspected against truth |
| M13 | [m13_speech_audio.ipynb](../notebooks/speech-audio/m13_speech_audio.ipynb) | 135/30/27 clips split by source with zero source overlap; synthetic four-class test accuracy 1.0; worst robustness condition narrowband 4 kHz; speaker EER 0.331; CTC toy decode `stra` |
| M14 | [m14_video_ai.ipynb](../notebooks/video-ai/m14_video_ai.ipynb) | 60 frames, 8 vehicles; oracle count 8/8; noisy tracker MOTA 0.9812 with 0 ID switches and 9 false negatives; tracked count 8/8; measured tracker RTF 0.002 |

These results are evidence that the notebooks execute and that their measurement
paths work. They are not evidence of real-world accuracy: M11-M14 use small
synthetic corpora, and M13's perfect classifier score reflects separable synthetic
classes. The notebooks state that limitation next to the numbers.

## M15 - AI agents

Section: [`docs/lessons/ai-agents/`](../lessons/ai-agents/index.md)

| Lesson | Topic |
| --- | --- |
| `ag01-agent-loop.md` | observe, decide, act; the decision protocol |
| `ag02-tool-schemas.md` | strict schemas, side effects, least privilege |
| `ag03-memory-and-state.md` | bounded window, provenance, trust, purge |
| `ag04-budgets-and-approvals.md` | stop reasons and human gates |
| `ag05-injection-and-evaluation.md` | indirect injection and task scoring |

Notebook evidence: a two-tool task stops `final` after 3 steps and 2 calls; a
repeating model stops with `repeated_action`; a denied write returns
`approval_denied`; a path escape returns `policy_denied` even when approved; the
untrusted-tool-output envelope is shown; the evaluation suite scores 2/3 because a
deliberate negative control fails.

Defect fixed during authoring: `agent_core.memory` compared trust with the wrong
inequality, so a `tool`-trusted entry could pass a `user` bar. Both `recall` and
`search` now reject entries below the requested trust. Regression tests:
`tests/test_ai_agents_memory.py` (4 tests).

## M16 - Evaluation, security, responsible AI, deployment

Section: [`docs/lessons/production/`](../lessons/production/index.md)

| Lesson | Topic |
| --- | --- |
| `pr01-metrics-and-intervals.md` | Wilson intervals, bootstrap, paired comparisons |
| `pr02-calibration.md` | ECE, Brier, temperature scaling |
| `pr03-drift.md` | PSI, feature versus concept drift, decisions |
| `pr04-guardrails-and-cards.md` | adversarial recall/FPR, model cards, claims audit |
| `pr05-artifacts-and-serving.md` | manifests, digests, p50/p95 latency |

Notebook evidence: AUC 0.778; accuracy 0.790 (293/371), Wilson [0.745, 0.828]; MAE
0.329 [0.308, 0.350]; ECE 0.067 raw and 0.075 after temperature 1.10, a measured
regression; drift week 1 hold, week 2 investigate (usage PSI 1.171, tickets 1.212,
region 0.492); guard recall 0.75 with false-positive rate 0.0 and four documented
misses; card audit passes; tampering is detected; 40/40 HTTP 200, p50 15.53 ms, p95
16.72 ms in the recorded run (p95 16.31 ms in an earlier run; loopback jitters).

Reused code: `projects/production/eval_core/`.

## M17 - Integrated capstone

Section: [`docs/lessons/capstone/`](../lessons/capstone/index.md)

| Lesson | Topic |
| --- | --- |
| `cp01-scoping-and-data.md` | decision, metric, data contract, risk register |
| `cp02-build-and-evidence.md` | end-to-end path, controlled comparisons, experiment log |
| `cp03-evaluation-and-packaging.md` | frozen test, threat review, packaging, release |

The capstone does not add a notebook. It requires reusing the notebooks and
packages from M04-M16 in one project, with the twelve specifications in
`docs/course/projects/` and the rubric in
[`docs/course/projects.md`](../course/projects.md). The lab is
`labs/lab-1-capstone-package.md`, with three gated checkpoints. Every project
submits the same ten files from `templates/capstone-submission/`, mapped to the
checkpoints by the [submission package guide](../course/projects/submission-package.md).

## Reuse and duplication review

| Shared asset | Reused by | New duplicate created? |
| --- | --- | --- |
| `projects/computer-vision/vision_core/` | M04, M05 (image data, metrics) | No |
| `projects/ai-agents/agent_core/` | M15 | No |
| `projects/production/eval_core/` | M16 | No |
| `projects/llm-fine-tuning/llm_core/` | M06, M07, M08 | One new package, because no existing package covered tokenisation, SFT, LoRA, or quantization |
| `scripts/make_training_data.py` | M04, M05 datasets | No; bug fixed and reused |

No notebook duplicates a lab. Each notebook teaches a mechanism with expected
outputs; each lab asks for an independent result with a rubric.

## Known limitations

| Limitation | Scope | Handling |
| --- | --- | --- |
| No GPU execution | All seven notebooks ran on CPU | Optional GPU notes are labelled; no GPU figure is claimed |
| No Hugging Face download | M07/M08 real-model path | CPU-sized local implementation; the pretrained path is documented as optional and not executed here |
| `scikit-learn` DLL blocked | M05 inline implementations | Documented in the notebook and above; no result depends on it |
| FAQ splits are template-disjoint | M07 evaluation | Documented; the split is harder than a random split |
| Temperature scaling regressed | M16 | Reported with a paired interval, not hidden |
| Capstone is agent-simulated, not human | M17 | P03, P06, and P12 were run by an agent through their pipelines and gates; no human student or human marker has completed the rubric. See the [capstone pilot report](../technical/capstone-pilot-report.md) |
| Capstone evidence is prototype-grade | M17 | P03's CPU model is no-release on generation quality; P06's 960 images are synthetic from one renderer; P12's success figures come from a scripted policy, and the one local model tested failed the tool-decision protocol. The pilot report states each boundary |

## Verification

Commands and results are recorded in the
[final audit](../technical/final-audit.md). The checks cover unit tests, notebook
format and execution, lab selftests, strict documentation build, internal links and
anchors, and the GitHub Pages prefix.
