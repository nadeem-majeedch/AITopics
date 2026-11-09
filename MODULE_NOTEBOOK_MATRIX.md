# Module-to-Notebook Matrix

**Repository:** https://github.com/nadeem-majeedch/AITopics
**Live site:** https://nadeem-majeedch.github.io/AITopics/
**Audited commit:** `faf14e9` · **Date:** 2026-11-09

Notebook pages on the live site follow
`/AITopics/notebooks/<area>/<stem>/`; the raw file sits beside it at
`<stem>.ipynb`. The status column records what was actually observed over HTTP.

## Coverage matrix

| Module | Title | Lessons | Notebook(s) | Practical topics | Availability | Live status |
| --- | --- | --- | --- | --- | --- | --- |
| M00 | Course orientation and study plan | 0 lesson pages (4 orientation pages) | — | Study plan, hardware, placement, tool setup decisions | **No notebook, by design** — delivered as roadmap, learning paths, study guide, and the M00 syllabus plan | Orientation pages `200`; no notebook expected |
| M01 | Python and AI development environment | 1 (F02) | `foundations/m01_environment_check.ipynb` | Virtual environments, package versions, Jupyter, reproducibility | Dedicated | Page `200`, file `200` |
| M02 | Machine learning foundations | 8 (F03-F10) | `foundations/f03_numpy_pandas.ipynb`, `f04_data_cleaning`, `f05_splits`, `f06_eda`, `f07_supervised_unsupervised`, `f08_regression_classification`, `f09_tree_ensembles`, `f10_metrics_validation` | Arrays and tables, cleaning, splits and leakage, EDA, supervised vs unsupervised, regression and classification, trees and boosting, metrics and cross-validation | Dedicated sequence | 8/8 pages `200`, 8/8 files `200` |
| M03 | Deep learning foundations | 3 (F11-F13) | `foundations/f11_neural_networks.ipynb`, `f12_backpropagation`, `f13_reproducibility` | Perceptrons and MLPs, tensors and autograd, seeds and determinism | Dedicated sequence | 3/3 pages `200`, 3/3 files `200` |
| M04 | Training models from scratch | 5 (mt01-mt05) | `model-training/m04_training_from_scratch.ipynb` | Training loop, loss and optimizer, augmentation, error analysis, checkpoints | Dedicated | Page `200`, file `200` |
| M05 | Dataset preparation, labeling, cleaning, augmentation | 5 (mt06-mt10) | `model-training/m05_data_engineering.ipynb` | Dataset audit, label cleaning, leakage, label noise, dataset cards | Dedicated | Page `200`, file `200` |
| M06 | Transformers and language models | 4 (lf01-lf04) | `llm-fine-tuning/m06_transformers.ipynb` | Tokens, attention, transformer block, tiny LM training | Dedicated | Page `200`, file `200` |
| M07 | Small language models and supervised fine-tuning | 3 (lf05-lf07) | `llm-fine-tuning/m07_sft_small_lm.ipynb` | SFT data and templates, loss masking, assistant evaluation | Dedicated | Page `200`, file `200` |
| M08 | LoRA, QLoRA, quantization, efficient training | 3 (lf08-lf10) | `llm-fine-tuning/m08_lora_qlora.ipynb` | Adapters and rank, quantization, merging and serving | Dedicated | Page `200`, file `200` |
| M09 | Chatbots and conversational applications | 8 (ca01-ca08) | `chatbots-rag/m09_chatbots.ipynb` | Cited retrieval, hybrid search, history budgets, guardrails, Streamlit app, local models | Dedicated | Page `200`, file `200` |
| M10 | Embeddings, vector search, and RAG | 8 (ca09-ca16) | `chatbots-rag/m10_rag.ipynb` | Embeddings, chunking, vector search, grounded generation, citations, abstention, evaluation | Dedicated | Page `200`, file `200` |
| M11 | Image classification and computer vision | 7 (cv01-cv07) | `computer-vision/m11_image_classification.ipynb` | Pixels and channels, grouped splits, CNNs, transfer learning, fine-tuning | Dedicated | Page `200`, file `200` |
| M12 | Object detection, tracking, transfer learning | 7 (cv08-cv14) | `computer-vision/m12_object_detection.ipynb` | Boxes and IoU, heatmaps, NMS, mAP, thresholds, similarity, latency | Dedicated | Page `200`, file `200` |
| M13 | Speech recognition, audio classification, speech generation | 14 (sa01-sa14) | `speech-audio/m13_speech_audio.ipynb` | Waveforms, log-Mel features, speaker splits, robustness, EER, CTC | Dedicated | Page `200`, file `200` |
| M14 | Video understanding and video analytics | 15 (vd01-vd15) | `video-ai/m14_video_ai.ipynb` | Frames, background subtraction, tracking, tripwire counting, MOTA | Dedicated | Page `200`, file `200` |
| M15 | AI agents, tool calling, memory, workflows | 5 (ag01-ag05) | `ai-agents/m15_agents.ipynb` | Tool schemas, agent loop, memory, budgets and approvals, injection and evaluation | Dedicated | Page `200`, file `200` |
| M16 | Evaluation, security, responsible AI, deployment | 5 (pr01-pr05) | `production/m16_production.ipynb` | Metrics with intervals, calibration, drift, guardrails and model cards, artifacts and serving | Dedicated | Page `200`, file `200` |
| M17 | Integrated capstone | 3 (cp01-cp03) | — | Scoping and data, build and evidence, evaluation and packaging | **No notebook, by design** — reuses M04-M16 notebooks; the deliverable is measured evidence and a defended package | Lessons, lab, and assessment `200` |

Outside the module map, **F01** (`foundations/f01_python_ai.ipynb`, pre-M01 bridge)
adds the 26th notebook: functions, collections, files, error handling, a first metric.

## Notebook count reconciliation

The 26 notebooks break down as F01 (1), **F02/M01 (1)**, F03-F10 (8), F11-F13 (3),
and M04-M16 (13). A grouping that omits F02 accounts for 25; the M01
environment-check notebook is the 26th.

## Notebook detail

| # | Notebook | Area | Cells | Code cells | Live page | Live file |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `f01_python_ai.ipynb` | foundations | 19 | 9 | 200 | 200 |
| 2 | `m01_environment_check.ipynb` | foundations | 22 | 11 | 200 | 200 |
| 3 | `f03_numpy_pandas.ipynb` | foundations | 19 | 9 | 200 | 200 |
| 4 | `f04_data_cleaning.ipynb` | foundations | 13 | 6 | 200 | 200 |
| 5 | `f05_splits.ipynb` | foundations | 17 | 8 | 200 | 200 |
| 6 | `f06_eda.ipynb` | foundations | 12 | 6 | 200 | 200 |
| 7 | `f07_supervised_unsupervised.ipynb` | foundations | 15 | 7 | 200 | 200 |
| 8 | `f08_regression_classification.ipynb` | foundations | 13 | 6 | 200 | 200 |
| 9 | `f09_tree_ensembles.ipynb` | foundations | 15 | 7 | 200 | 200 |
| 10 | `f10_metrics_validation.ipynb` | foundations | 15 | 7 | 200 | 200 |
| 11 | `f11_neural_networks.ipynb` | foundations | 15 | 7 | 200 | 200 |
| 12 | `f12_backpropagation.ipynb` | foundations | 15 | 8 | 200 | 200 |
| 13 | `f13_reproducibility.ipynb` | foundations | 15 | 7 | 200 | 200 |
| 14 | `m04_training_from_scratch.ipynb` | model-training | 20 | 11 | 200 | 200 |
| 15 | `m05_data_engineering.ipynb` | model-training | 21 | 10 | 200 | 200 |
| 16 | `m06_transformers.ipynb` | llm-fine-tuning | 23 | 11 | 200 | 200 |
| 17 | `m07_sft_small_lm.ipynb` | llm-fine-tuning | 21 | 10 | 200 | 200 |
| 18 | `m08_lora_qlora.ipynb` | llm-fine-tuning | 17 | 8 | 200 | 200 |
| 19 | `m09_chatbots.ipynb` | chatbots-rag | 17 | 7 | 200 | 200 |
| 20 | `m10_rag.ipynb` | chatbots-rag | 17 | 7 | 200 | 200 |
| 21 | `m11_image_classification.ipynb` | computer-vision | 20 | 10 | 200 | 200 |
| 22 | `m12_object_detection.ipynb` | computer-vision | 17 | 9 | 200 | 200 |
| 23 | `m13_speech_audio.ipynb` | speech-audio | 22 | 11 | 200 | 200 |
| 24 | `m14_video_ai.ipynb` | video-ai | 19 | 10 | 200 | 200 |
| 25 | `m15_agents.ipynb` | ai-agents | 26 | 11 | 200 | 200 |
| 26 | `m16_production.ipynb` | production | 24 | 10 | 200 | 200 |
| | **Total** | | **469** | **223** | **26/26** | **26/26** |

## Section-to-notebook index on the site

Each section index links its notebooks and each link resolved to a `200` page:

| Section page | Modules | Notebook links |
| --- | --- | --- |
| `/lessons/model-training/` | M04-M05 | 2 |
| `/lessons/llm-fine-tuning/` | M06-M08 | 3 |
| `/lessons/ai-agents/` | M15 | 1 |
| `/lessons/production/` | M16 | 1 |
| `/lessons/capstone/` | M17 | 0 (documented reuse) |
| `/lessons/chatbots-rag/` | M09-M10 | 2 |
| `/lessons/computer-vision/` | M11-M12 | 2 |
| `/lessons/speech-audio/` | M13 | 1 |
| `/lessons/video-ai/` | M14 | 1 |
| `/notebook-library/` | all | 26 unique targets, all `200` |

## Remediation note (2026-11-09)

Every notebook page now carries a **Download notebook (.ipynb)** button provided by
`scripts/mkdocs_notebook_downloads.py` (declared under `hooks:` in `mkdocs.yml`).
The status column above reflects the site as audited; after the next deployment each
"file `200`" entry is reachable from the page itself instead of by URL construction.

## Mapping consistency checks

| Check | Result |
| --- | --- |
| Notebook filename code matches its module code (M04-M16) | 13/13 consistent |
| Foundation notebook referenced by the matching unit's `notebook.md` | 13/13 consistent |
| Notebook heading matches the module it is mapped to | 26/26 consistent |
| Notebooks mapped to more than one module | 0 |
| Modules claiming a notebook that does not exist | 0 |
| Notebooks present but not referenced anywhere | 0 |
| Duplicate notebook files (identical content) | 0 |
