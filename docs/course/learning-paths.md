# Learning paths

The full program is broad. Most students do not need all of it. Choose a path
based on the system you want to build, then use the [roadmap](roadmap.md) for
scheduling. Each path lists prerequisites, modules, hours, and the artifact you
should be able to show at the end.

!!! tip "Start with foundations if you are unsure"
    Path 1 (AI foundations) is the base for every specialization. It is not
    wasted time: the labs in M02-M05 are the evidence most employers and
    supervisors ask for first.

## Path 1: AI foundations

**For:** students new to machine learning, or anyone who wants a rigorous base
before specializing.

**Prerequisites:** basic Python and high-school algebra.

| Order | Module | Hours |
| --- | --- | --- |
| 1 | M00 Course orientation | 3 |
| 2 | M01 Python and AI environment | 12 |
| 3 | M02 Machine learning foundations | 16 |
| 4 | M03 Deep learning foundations | 16 |
| 5 | M04 Training models from scratch | 18 |
| 6 | M05 Dataset preparation and labeling | 14 |
| | **Total** | **79** |

**You will be able to:** train and evaluate classical and deep models, diagnose
overfitting and data leakage, prepare a documented dataset, and explain your
results with appropriate metrics.

**Exit artifact:** a reproducible notebook and report for a tabular model and an
image model, each with a dataset card and error analysis.

**Next:** choose Path 2, 3, 4, or 5.

## Path 2: Language AI engineer

**For:** students who want to fine-tune small language models, build chatbots,
and implement RAG systems.

**Prerequisites:** Python, basic ML/DL, and comfort with probability. M04 is
recommended but not mandatory if you understand training loops.

| Order | Module | Hours |
| --- | --- | --- |
| 1 | M00-M01 Orientation and environment | 15 |
| 2 | M02-M03 ML and DL foundations | 32 |
| 3 | M05 Dataset preparation | 14 |
| 4 | M06 Transformers and language models | 18 |
| 5 | M07 Small language models and SFT | 24 |
| 6 | M08 LoRA, QLoRA, quantization | 18 |
| 7 | M09 Chatbots and conversational applications | 16 |
| 8 | M10 Embeddings, vector search, RAG | 18 |
| 9 | M16 Evaluation, security, deployment | 20 |
| 10 | M17 Capstone (language option) | 40 |
| | **Total** | **215** |

**You will be able to:** prepare instruction data, fine-tune a small model with
SFT and QLoRA, merge and quantize adapters, build a cited RAG chatbot, evaluate
retrieval and generation, and deploy it within a cost budget.

**Exit artifact:** a domain chatbot with a fine-tuned or adapted model, a
retrieval index, guardrail tests, an evaluation table, a model card, and a demo.

**Hardware note:** M07-M08 require a GPU. Use free Colab or Kaggle if needed.
M09-M10 and M16 can run on CPU with small models.

## Path 3: Vision and video engineer

**For:** students interested in image classification, detection, tracking, and
video analytics for legitimate applications such as inspection, retail,
robotics, agriculture, and traffic analysis.

**Prerequisites:** Python, ML/DL foundations, and data preparation.

| Order | Module | Hours |
| --- | --- | --- |
| 1 | M00-M05 Foundations | 79 |
| 2 | M11 Image classification | 18 |
| 3 | M12 Object detection and tracking | 20 |
| 4 | M14 Video understanding and analytics | 22 |
| 5 | M16 Evaluation, security, deployment | 20 |
| 6 | M17 Capstone (vision/video option) | 40 |
| | **Total** | **199** |

**You will be able to:** fine-tune image classifiers, train and evaluate
detectors, build tracking pipelines, process video streams efficiently, and
document privacy and licensing constraints.

**Exit artifact:** a detection and tracking prototype with an evaluation report,
a privacy review, and a demo on a public or consented clip.

**Hardware note:** training M11-M12 and M14 needs a GPU. Inference can be
demonstrated on CPU with small models and short clips.

**Ethics boundary:** this path does **not** cover face recognition, identity
inference, or covert surveillance. See [Capstone projects](projects.md) for
acceptable and unacceptable use.

## Path 4: Speech and audio engineer

**For:** students who want speech recognition, audio classification, or speech
generation systems.

**Prerequisites:** Python, deep-learning foundations, and data preparation.

| Order | Module | Hours |
| --- | --- | --- |
| 1 | M00-M05 Foundations | 79 |
| 2 | M13 Speech and audio AI | 22 |
| 3 | M16 Evaluation, security, deployment | 20 |
| 4 | M17 Capstone (speech option) | 40 |
| | **Total** | **161** |

**You will be able to:** preprocess audio, fine-tune or adapt an ASR model,
classify environmental or domain audio, generate speech with an open model,
and evaluate with WER/CER and listening tests.

**Exit artifact:** an ASR or audio assistant with a WER report, a failure
analysis by accent/noise condition, and a demo.

**Hardware note:** fine-tuning is GPU recommended. Inference and evaluation can
be done on CPU with small models and short clips.

## Path 5: AI agent engineer

**For:** students who want to build tool-using agents, workflows, and
retrieval-backed assistants with controlled autonomy.

**Prerequisites:** Python, basic ML/DL, transformers, chatbots, and RAG.

| Order | Module | Hours |
| --- | --- | --- |
| 1 | M00-M03 Orientation, environment, ML/DL | 47 |
| 2 | M05 Dataset preparation | 14 |
| 3 | M06 Transformers and language models | 18 |
| 4 | M09 Chatbots and conversational applications | 16 |
| 5 | M10 Embeddings, vector search, RAG | 18 |
| 6 | M15 AI agents, tools, memory, workflows | 24 |
| 7 | M16 Evaluation, security, deployment | 20 |
| 8 | M17 Capstone (agent option) | 40 |
| | **Total** | **197** |

**You will be able to:** design tool schemas, implement a bounded agent loop,
add short- and long-term memory, handle failures, evaluate task success and
trajectories, and defend against prompt injection and tool abuse.

**Exit artifact:** an agent with at least three tools, a memory strategy, a
permission model, a failure-injection test suite, and an evaluation report.

**Hardware note:** CPU is sufficient with hosted APIs or small local models.
Local large models require a GPU.

## Path 6: Full program

**For:** students who want the full breadth, a strong portfolio, and a serious
capstone.

| Level | Modules | Hours |
| --- | --- | --- |
| 0-5 | M00-M17 | 339 |

**You will be able to:** work across language, vision, speech, video, and agents,
and make defensible engineering decisions about evaluation, cost, security, and
deployment.

**Exit artifact:** a capstone plus at least six module labs that demonstrate
breadth and depth.

**Time:** 13 weeks full-time, 26 weeks standard, or 42 weeks relaxed. See the
[study schedules](roadmap.md#study-schedules).

## Choosing between language, vision, and agents

| Question | Suggested path |
| --- | --- |
| Do you want to build assistants, chatbots, or document QA? | Language AI |
| Do you want to work with images, cameras, inspection, or video? | Vision and video |
| Do you want to work with voice interfaces or audio data? | Speech and audio |
| Do you want to build multi-step tools and automation? | AI agents |
| Do you want to teach or do research across modalities? | Full program |

You can combine paths. The most common combinations are:

- **Language + agents:** fine-tuned model, RAG, then tool use.
- **Vision + video:** the natural sequence for camera-based systems.
- **Speech + language:** voice assistant with ASR, dialog, and TTS.
- **Vision + agents:** an agent that can inspect images with a vision model.

## Placement guidance

You may skip a module only if you can produce its exit artifact without help.

| Skip | Only if you can |
| --- | --- |
| M01 | Reproduce an environment from a lockfile and diagnose CUDA/CPU issues |
| M02 | Explain leakage, cross-validation, calibration, and imbalanced metrics |
| M03 | Write a PyTorch training loop and debug shapes and gradients |
| M04 | Train a CNN and justify regularization and augmentation choices |
| M05 | Write a labeling guide and dataset card with license and bias analysis |
| M06 | Explain tokenization, attention, and decoding, and train a tiny LM |
| M07 | Fine-tune an instruct model and build a held-out evaluation set |
| M08 | Quantize and merge adapters and measure quality and memory trade-offs |
| M09-M10 | Build a RAG chatbot with citations and retrieval/generation metrics |

When in doubt, take the module and use the lab as evidence. Skipping content is
cheaper than a capstone that cannot be defended.
