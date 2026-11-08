# Notebook library

Every guided notebook in the course is listed here. Each page renders the notebook
with its saved outputs, so you can read it without installing anything. To run a
notebook, download the `.ipynb` file from the page or open it from a clone of the
repository.

All 26 notebooks were executed top-to-bottom on Windows 11, Python 3.12.10, CPU
only, on 2026-11-08. GPU and Google Colab execution are still pending unless a
notebook says otherwise. Saved outputs are evidence of that CPU run, not a
benchmark.

## Foundations (F01-F13, M01-M03)

| Unit | Notebook | Hardware | What it teaches |
| --- | --- | --- | --- |
| F01 | [Python essentials for AI](notebooks/foundations/f01_python_ai.ipynb) | CPU-only | Functions, collections, files, error handling, a first metric |
| F02 (M01) | [Environment check](notebooks/foundations/m01_environment_check.ipynb) | CPU-only | Virtual environments, package versions, Jupyter, reproducibility |
| F03 | [NumPy and pandas](notebooks/foundations/f03_numpy_pandas.ipynb) | CPU-only | Arrays, tables, selection, grouping, joins |
| F04 | [Data cleaning](notebooks/foundations/f04_data_cleaning.ipynb) | CPU-only | Missing values, categories, normalization, pipelines |
| F05 | [Train, validation, and test splits](notebooks/foundations/f05_splits.ipynb) | CPU-only | Grouped splits, leakage, baselines |
| F06 | [Exploratory data analysis](notebooks/foundations/f06_eda.ipynb) | CPU-only | Distributions, correlation, outliers, plots |
| F07 | [Supervised and unsupervised learning](notebooks/foundations/f07_supervised_unsupervised.ipynb) | CPU-only | Clustering, PCA, labels, comparison |
| F08 | [Regression and classification](notebooks/foundations/f08_regression_classification.ipynb) | CPU-only | Linear and logistic models, metrics, baselines |
| F09 | [Tree ensembles](notebooks/foundations/f09_tree_ensembles.ipynb) | CPU-only | Trees, forests, boosting, cross-validation |
| F10 | [Metrics and validation](notebooks/foundations/f10_metrics_validation.ipynb) | CPU-only | Imbalance, thresholds, overfitting, leakage |
| F11 | [Neural networks](notebooks/foundations/f11_neural_networks.ipynb) | CPU or GPU | Perceptrons, hidden layers, activations, MLPs |
| F12 | [Backpropagation](notebooks/foundations/f12_backpropagation.ipynb) | CPU or GPU | Tensors, autograd, losses, optimizers |
| F13 | [Reproducibility](notebooks/foundations/f13_reproducibility.ipynb) | CPU-only | Seeds, determinism, timing, run records |

## Model training (M04-M05)

| Module | Notebook | Hardware | What it teaches |
| --- | --- | --- | --- |
| M04 | [Training from scratch](notebooks/model-training/m04_training_from_scratch.ipynb) | CPU (GPU optional) | Training loop, augmentation, checkpoints, error analysis |
| M05 | [Data engineering](notebooks/model-training/m05_data_engineering.ipynb) | CPU-only | Cleaning, label audit, leakage, near-duplicates, dataset cards |

## LLMs and fine-tuning (M06-M08)

| Module | Notebook | Hardware | What it teaches |
| --- | --- | --- | --- |
| M06 | [Transformers](notebooks/llm-fine-tuning/m06_transformers.ipynb) | CPU or GPU | Tokens, attention, causal masking, a tiny language model |
| M07 | [SFT for small language models](notebooks/llm-fine-tuning/m07_sft_small_lm.ipynb) | CPU; GPU recommended | Prompt masks, supervised fine-tuning, evaluation |
| M08 | [LoRA and QLoRA](notebooks/llm-fine-tuning/m08_lora_qlora.ipynb) | CPU demonstration; GPU for real models | Adapters, rank, merging, quantization trade-offs |

## Chatbots and RAG (M09-M10)

| Module | Notebook | Hardware | What it teaches |
| --- | --- | --- | --- |
| M09 | [Chatbots](notebooks/chatbots-rag/m09_chatbots.ipynb) | CPU-only | Cited retrieval, hybrid search, history budgets, guardrails |
| M10 | [Retrieval-augmented generation](notebooks/chatbots-rag/m10_rag.ipynb) | CPU-only | Grounded generation, citation validation, abstention, evaluation |

## Computer vision (M11-M12)

| Module | Notebook | Hardware | What it teaches |
| --- | --- | --- | --- |
| M11 | [Image classification](notebooks/computer-vision/m11_image_classification.ipynb) | CPU-only | Pixels, grouped splits, CNN training, per-class errors |
| M12 | [Object detection](notebooks/computer-vision/m12_object_detection.ipynb) | CPU-only | Boxes, IoU, heatmaps, NMS, mAP, threshold trade-offs |

## Speech and audio (M13)

| Module | Notebook | Hardware | What it teaches |
| --- | --- | --- | --- |
| M13 | [Speech and audio AI](notebooks/speech-audio/m13_speech_audio.ipynb) | CPU-only | Waveforms, log-Mel features, speaker splits, robustness, EER, CTC |

## Video AI (M14)

| Module | Notebook | Hardware | What it teaches |
| --- | --- | --- | --- |
| M14 | [Video AI and traffic analytics](notebooks/video-ai/m14_video_ai.ipynb) | CPU-only | Frames, background subtraction, tracking, tripwire counting, MOTA |

## Agents and production (M15-M16)

| Module | Notebook | Hardware | What it teaches |
| --- | --- | --- | --- |
| M15 | [Tool-using agents](notebooks/ai-agents/m15_agents.ipynb) | CPU-only core | Tool schemas, the agent loop, budgets, approvals, traces |
| M16 | [Evaluation and serving](notebooks/production/m16_production.ipynb) | CPU-only | Metrics, calibration, drift, guardrails, artifacts |

## How to run a notebook

From the repository root, with the course environment installed:

```bash
python -m jupyter lab notebooks/chatbots-rag/m09_chatbots.ipynb
```

Each notebook starts by adding its section package to `sys.path`; run it from its
own directory or let Jupyter set the working directory. The first markdown cell
states the prerequisites, hardware, and dataset licence. If a step needs a
download or a GPU, the notebook says so and provides the CPU path where one exists.

## What the saved outputs do not prove

- They do not prove the notebook runs on your machine or on Google Colab.
- They do not prove a model generalises beyond the synthetic teaching data.
- They do not replace the independent lab or the assessment.
- They are not a benchmark against published models.

If a notebook fails, use the troubleshooting table at the end of that notebook and
the [technical troubleshooting page](technical/troubleshooting.md). Report the
module code, the exact cell, and the full error message.
