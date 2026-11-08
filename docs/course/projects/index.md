# Capstone projects

```markdown
**Start here:** [Choose a project](#choose-a-project) · [Prerequisite map](#prerequisite-map) · [Rules for every project](#rules-for-every-project) · [Report template](report-template.md) · [Completion checklist](completion-checklist.md)
```

Twelve project specifications, organised by difficulty. Each one is a complete
brief: problem, scope, data and licences, baseline, milestones, folder layout,
tasks, evaluation plan, metrics, deliverables, extensions, failure modes, rubric,
self-review list, report outline, and demo checklist.

Every project is designed to be completed by one self-directed learner with no
instructor: the data can be generated or downloaded from a stated source, the code
runs on a CPU unless the brief says otherwise, and the evaluation is defined before
you start building.

!!! note "Self-study, not accreditation"
    These briefs are assessment instruments for your own use. Nothing here is
    graded, verified, or certified by the course author. The rubrics exist so you
    can judge your own evidence against a stated standard.

## Choose a project

| ID | Project | Difficulty | Effort | Hardware | Best if you want to |
| --- | --- | --- | --- | --- | --- |
| [P01](p01-tabular-prediction.md) | Customer churn prediction | Foundation | 25-35 h | CPU | Learn the full ML system skeleton once, properly |
| [P02](p02-text-classifier.md) | Support-ticket text classifier | Foundation | 30-40 h | CPU | Work with text, leakage, and abstention |
| [P03](p03-lora-finetune.md) | LoRA fine-tune of a small language model | Intermediate | 35-45 h | 1 free GPU or CPU (135M) | Learn fine-tuning and defend it against prompting |
| [P04](p04-grounded-chatbot.md) | Document-grounded chatbot with citations | Intermediate | 40-50 h | CPU | Build retrieval that can be audited |
| [P05](p05-local-assistant-gui.md) | Local assistant with a desktop interface | Intermediate | 40-50 h | CPU | Ship something a non-technical person can use |
| [P06](p06-image-classifier.md) | Image classification on your own dataset | Intermediate | 40-50 h | CPU or GPU | Learn transfer learning and robustness testing |
| [P07](p07-object-detector.md) | Fine-tuned object detector | Advanced | 50-65 h | CPU (small set) or GPU | Work with boxes, IoU, and mAP in depth |
| [P08](p08-speech-transcription.md) | Speech recognition and transcription app | Intermediate | 40-50 h | CPU | Evaluate ASR honestly with WER |
| [P09](p09-video-vehicle-analytics.md) | Vehicle detection, counting, tracking | Advanced | 55-70 h | CPU or GPU | Build a video pipeline with privacy controls |
| [P10](p10-garment-attributes.md) | Garment category and colour recognition | Intermediate | 40-55 h | CPU or GPU | Handle two heads and a taxonomy problem |
| [P11](p11-action-recognition.md) | Video action-recognition prototype | Advanced | 50-65 h | CPU (synthetic) or GPU | Compare frame and temporal models |
| [P12](p12-tool-using-agent.md) | Tool-using agent with approvals | Advanced | 60-80 h | CPU | Build an agent with real access controls |

**Effort** is planning time for one learner, including writing. It is an estimate,
not a promise; data collection and annotation usually take longer than expected.

### Suggested sequences

| Your goal | Sequence |
| --- | --- |
| First complete system | P01 → P02 → P04 → P05 |
| Language AI portfolio | P02 → P03 → P04 → P12 |
| Vision portfolio | P06 → P07 → P10 → P11 |
| Media and video | P08 → P09 → P11 |
| Agentic systems | P04 → P12, with P05 for the interface |
| Maximum learning per hour | P01, then one of P04/P06, then P12 |

Do **one** project well rather than three badly. A capstone with a measured error
analysis, a working rerun, and an honest limitations section is worth more than a
folder of notebooks.

## Prerequisite map

Modules refer to the published lesson sections. If a section is still a plan, the
brief says so and the project can be completed with the published material plus the
linked code.

| Project | Required modules | Helpful modules | Existing code to read first |
| --- | --- | --- | --- |
| P01 | [F03](../../lessons/f03-numpy-pandas/index.md), [F04](../../lessons/f04-data-cleaning/index.md), [F05](../../lessons/f05-splits/index.md), [F08](../../lessons/f08-regression-classification/index.md), [F09](../../lessons/f09-tree-ensembles/index.md), [F10](../../lessons/f10-metrics-validation/index.md) | [F06](../../lessons/f06-eda/index.md), [F13](../../lessons/f13-reproducibility/index.md) | `projects/production/lab1_model_comparison.py` |
| P02 | [F04](../../lessons/f04-data-cleaning/index.md), [F05](../../lessons/f05-splits/index.md), [F08](../../lessons/f08-regression-classification/index.md), [F10](../../lessons/f10-metrics-validation/index.md), [CA09](../../lessons/chatbots-rag/ca09-embeddings.md), [CA14](../../lessons/chatbots-rag/ca14-evaluation.md) | [F11](../../lessons/f11-neural-networks/index.md) | `projects/production/lab2_data_leakage.py` |
| P03 | [F11](../../lessons/f11-neural-networks/index.md), [F12](../../lessons/f12-backpropagation/index.md), [F13](../../lessons/f13-reproducibility/index.md), [CA03](../../lessons/chatbots-rag/ca03-calling-a-model.md), [CA15](../../lessons/chatbots-rag/ca15-fine-tuned-models.md) | [CA05](../../lessons/chatbots-rag/ca05-prompts-and-structured-output.md) | `projects/chatbots-rag/project_d_local_model.py` |
| P04 | [CA09](../../lessons/chatbots-rag/ca09-embeddings.md), [CA10](../../lessons/chatbots-rag/ca10-chunking.md), [CA11](../../lessons/chatbots-rag/ca11-vector-search.md), [CA12](../../lessons/chatbots-rag/ca12-rag.md), [CA13](../../lessons/chatbots-rag/ca13-citations-and-abstention.md), [CA14](../../lessons/chatbots-rag/ca14-evaluation.md), [CA16](../../lessons/chatbots-rag/ca16-privacy-and-deployment.md) | [F10](../../lessons/f10-metrics-validation/index.md) | `projects/chatbots-rag/project_f_cited_assistant.py`, `project_g_evaluation.py` |
| P05 | [CA03](../../lessons/chatbots-rag/ca03-calling-a-model.md), [CA04](../../lessons/chatbots-rag/ca04-history-and-context.md), [CA06](../../lessons/chatbots-rag/ca06-streamlit-interface.md), [CA07](../../lessons/chatbots-rag/ca07-local-models.md), [CA16](../../lessons/chatbots-rag/ca16-privacy-and-deployment.md) | [P04](p04-grounded-chatbot.md) | `projects/chatbots-rag/app_streamlit.py` |
| P06 | [CV02](../../lessons/computer-vision/cv02-datasets-and-annotation-formats.md), [CV03](../../lessons/computer-vision/cv03-preprocessing-and-augmentation.md), [CV05](../../lessons/computer-vision/cv05-classification-from-scratch.md), [CV06](../../lessons/computer-vision/cv06-transfer-learning.md), [CV07](../../lessons/computer-vision/cv07-fine-tuning.md), [CV14](../../lessons/computer-vision/cv14-evaluation-robustness-deployment.md) | [CV12](../../lessons/computer-vision/cv12-embeddings-and-similarity.md) | `projects/computer-vision/lab3_scratch_vs_transfer.py` |
| P07 | [CV02](../../lessons/computer-vision/cv02-datasets-and-annotation-formats.md), [CV08](../../lessons/computer-vision/cv08-training-detectors.md), [CV09](../../lessons/computer-vision/cv09-boxes-iou-map.md), [CV14](../../lessons/computer-vision/cv14-evaluation-robustness-deployment.md) | [CV05](../../lessons/computer-vision/cv05-classification-from-scratch.md) | `projects/computer-vision/lab5_detector_training.py` |
| P08 | [SA02](../../lessons/speech-audio/sa02-loading-and-preprocessing.md), [SA03](../../lessons/speech-audio/sa03-waveform-spectrogram-mel.md), [SA07](../../lessons/speech-audio/sa07-asr-and-stt.md), [SA08](../../lessons/speech-audio/sa08-wer-and-transcription-evaluation.md), [SA09](../../lessons/speech-audio/sa09-adapting-pretrained-asr.md) | [SA14](../../lessons/speech-audio/sa14-optimization-and-deployment.md) | `projects/speech-audio/lab_c_transcribe_clip.py`, `lab_d_wer_evaluation.py` |
| P09 | [VD02](../../lessons/video-ai/vd02-reading-and-writing.md), [VD03](../../lessons/video-ai/vd03-frame-extraction-and-datasets.md), [VD06](../../lessons/video-ai/vd06-detection-on-frames.md), [VD07](../../lessons/video-ai/vd07-tracking-and-track-ids.md), [VD08](../../lessons/video-ai/vd08-counting-and-traffic-flow.md), [VD14](../../lessons/video-ai/vd14-evaluation-and-deployment.md), [VD15](../../lessons/video-ai/vd15-responsible-video-analytics.md) | [CV09](../../lessons/computer-vision/cv09-boxes-iou-map.md) | `projects/video-ai/lab3_tracking_and_counting.py` |
| P10 | [CV03](../../lessons/computer-vision/cv03-preprocessing-and-augmentation.md), [CV06](../../lessons/computer-vision/cv06-transfer-learning.md), [CV07](../../lessons/computer-vision/cv07-fine-tuning.md), [VD10](../../lessons/video-ai/vd10-clothing-and-appearance.md), [VD15](../../lessons/video-ai/vd15-responsible-video-analytics.md) | [CV12](../../lessons/computer-vision/cv12-embeddings-and-similarity.md) | `projects/video-ai/lab5_garment_attributes.py` |
| P11 | [VD05](../../lessons/video-ai/vd05-image-vs-temporal-models.md), [VD11](../../lessons/video-ai/vd11-action-recognition.md), [VD12](../../lessons/video-ai/vd12-video-classification-and-events.md), [VD13](../../lessons/video-ai/vd13-fine-tuning.md), [VD14](../../lessons/video-ai/vd14-evaluation-and-deployment.md) | [F11](../../lessons/f11-neural-networks/index.md) | `projects/video-ai/lab6_action_recognition.py` |
| P12 | [M15 agents](../../lessons/ai-agents/index.md), [AG04 approvals](../../lessons/ai-agents/ag04-budgets-and-approvals.md), [CA05](../../lessons/chatbots-rag/ca05-prompts-and-structured-output.md), [CA13](../../lessons/chatbots-rag/ca13-citations-and-abstention.md), [CA16](../../lessons/chatbots-rag/ca16-privacy-and-deployment.md) | [P04](p04-grounded-chatbot.md), [P05](p05-local-assistant-gui.md) | `projects/ai-agents/project_f_approved_file_assistant.py` |

!!! warning "Prerequisites are about skills, not checkboxes"
    If you cannot explain why a grouped split matters, or what mAP averages over,
    the project will expose it. Read the module before starting rather than during
    the final week.

## Rules for every project

These apply to all twelve briefs and are part of every rubric.

1. **Licence first.** Record the exact licence string and URL for every dataset and
   pretrained model. If the licence is unclear, do not use it.
2. **No personal data.** No names, faces, voices, addresses, or customer records
   without documented consent and a retention plan. Never commit raw data.
3. **Baseline before model.** A majority class, a keyword rule, a pretrained
   off-the-shelf model, or a human estimate. The comparison must be fair.
4. **Evaluation plan before the final build.** Write metrics, splits, slices, and
   failure criteria in the proposal. Changing them later is allowed if you say so.
5. **Measured, not assumed.** Every number in the report traces to a file your code
   wrote. No invented benchmark scores, no borrowed numbers from papers presented
   as your result.
6. **Uncertainty where it matters.** Intervals, counts per slice, or explicit "n is
   too small to interpret".
7. **Failure analysis with counts.** Anecdotes are illustration; the taxonomy is the
   evidence.
8. **One-command rerun.** Environment file, seeds, and a README that a stranger can
   follow.
9. **Responsible-use controls.** A model or system card with prohibited uses, and a
   security or privacy section where the project touches people or actions.
10. **Reflection.** What you expected, what happened, what you would change. This is
    where AI assistance is disclosed.

## What a completed project contains

```text
capstone-pXX/
  README.md               # what it is, how to run, what it does not do
  requirements.txt        # pinned
  data/                   # cards and manifests; no raw data in Git
  src/                    # importable code, CLI entry point
  tests/                  # unit tests that run without a GPU
  outputs/                # generated metrics and predictions
  artifacts/              # model or adapter, with a checksum
  submission/
    project-scope.md
    dataset-card.md
    experiments.csv
    model-card.md
    evaluation-report.md
    threat-and-responsible-use-review.md
    reproducibility.md
    README.md
    release-notes.md
    final-report.md
```

The per-project folder sections list the specific files. Deviating is fine; having
no structure is not. Copy the ten `submission/` files from the
[capstone submission package](submission-package.md); every project submits
the same set, and the package guide maps each file to a checkpoint.

## How the work is assessed

Each brief has a weighted rubric with four performance levels. The criteria differ
by project, but the shape is constant: problem framing, data and licensing,
implementation, evaluation, reproducibility, communication. A project that makes an
unsupported performance or safety claim cannot score above "Approaching" on
evaluation, whatever the demo looks like.

Use the [completion checklist](completion-checklist.md) before you call a project
finished, the [submission package](submission-package.md) for the files and
checkpoint gates, and the [report template](report-template.md) for the write-up.

## Related pages

- [Assessments and rubrics](../assessments.md) - course-wide weighting and integrity rules
- [Assessment bank](../assessments/index.md) - quizzes, code reading, debugging, scenarios
- [Learning paths](../learning-paths.md) - which sections feed which project
- [M17 capstone](../../lessons/capstone/index.md) - the module this section serves
