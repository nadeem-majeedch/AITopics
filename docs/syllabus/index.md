# Syllabus overview

The course has **18 modules in 6 levels**. This page explains how the module
plans are structured and maps the course to the 16 learning areas it covers.

!!! warning "Plans and the published foundation sequence"
    Every module below has a complete plan: objectives, prerequisites, study
    time, theory, notebook, lab, rubric, deliverables, and next step. **F01-F13
    are published** with lessons, executable notebooks, lab briefs, and
    assessments, delivering M01-M03. M04-M17 still publish plans only. Lesson
    pages and notebooks are authored in the order defined in
    [Implementation phases](../planning/implementation-phases.md) and must pass
    the [quality standards](../planning/quality-standards.md) before release.

## Hardware legend

| Label | Meaning |
| --- | --- |
| **CPU-only** | Completes comfortably on a modern laptop CPU with 8-16 GB RAM |
| **CPU or GPU** | CPU works with reduced data/model size; GPU is faster |
| **GPU recommended** | CPU is possible but slow; free Colab/Kaggle GPU is advised |
| **GPU required** | The core lab needs a GPU with roughly 8-16 GB VRAM, free-tier or local |
| **Depends** | Determined by the capstone option |

## Modules at a glance

| Code | Module | Level | Hours | Hardware | Primary artifact |
| --- | --- | --- | --- | --- | --- |
| M00 | Course orientation and study plan | 0 | 3 | CPU-only | Personal study plan |
| M01 | Python and AI development environment | 0 | 12 | CPU-only | Environment report |
| M02 | Machine learning foundations | 1 | 16 | CPU-only | Tabular model and report |
| M03 | Deep learning foundations | 1 | 16 | CPU or GPU | Ablation study |
| M04 | Training models from scratch | 1 | 18 | GPU recommended | Trained CNN and experiment log |
| M05 | Dataset preparation, labeling, cleaning, augmentation | 1 | 14 | CPU-only | Dataset card and labeling guide |
| M06 | Transformers and language models | 2 | 18 | CPU or GPU | Tiny language model |
| M07 | Small language models and supervised fine-tuning | 2 | 24 | GPU required | Fine-tuned adapter and evaluation |
| M08 | LoRA, QLoRA, quantization, efficient training | 2 | 18 | GPU required | Efficiency trade-off report |
| M09 | Chatbots and conversational applications | 2 | 16 | CPU or GPU | Chatbot with guardrails |
| M10 | Embeddings, vector search, and RAG | 2 | 18 | CPU-only | Cited RAG system |
| M11 | Image classification and computer vision | 3 | 18 | GPU recommended | Domain image classifier |
| M12 | Object detection, tracking, transfer learning | 3 | 20 | GPU required | Detection and tracking demo |
| M13 | Speech recognition, audio classification, speech generation | 3 | 22 | GPU recommended | ASR/audio system with WER |
| M14 | Video understanding and video analytics | 3 | 22 | GPU recommended | Privacy-preserving analytics prototype |
| M15 | AI agents, tool calling, memory, workflows | 4 | 24 | CPU or API | Evaluated tool-using agent |
| M16 | Evaluation, security, responsible AI, deployment | 5 | 20 | CPU-only | Deployed, tested system |
| M17 | Integrated capstone | 5 | 40 | Depends | Full capstone package |
| | **Total** | | **339** | | |

## Coverage of the 16 learning areas

| # | Learning area | Modules |
| --- | --- | --- |
| 1 | Python and AI development environment | M00, M01 |
| 2 | Machine learning and deep learning foundations | M02, M03 |
| 3 | Training models from scratch | M04 |
| 4 | Dataset preparation, labeling, cleaning, augmentation | M05 |
| 5 | Transformers and language models | M06 |
| 6 | Small language models and fine-tuning | M07 |
| 7 | LoRA, QLoRA, quantization, efficient training | M08 |
| 8 | Chatbots and conversational applications | M09 |
| 9 | Embeddings, vector search, RAG | M10 |
| 10 | Image classification and computer vision | M11 |
| 11 | Object detection, tracking, transfer learning | M12 |
| 12 | Speech recognition, audio classification, speech generation | M13 |
| 13 | Video understanding, classification, tracking, analytics | M14 |
| 14 | AI agents, tool calling, memory, workflows | M15 |
| 15 | Evaluation, testing, security, responsible AI, deployment | M16 |
| 16 | Integrated capstone projects | M17 |

## What every module plan contains

Each module is specified with the same fields:

| Field | Purpose |
| --- | --- |
| **Learning objectives** | Measurable capabilities you should gain |
| **Prerequisites** | Modules and skills required before starting |
| **Study time** | Split into theory, guided notebook, lab, and assessment |
| **Required theory** | Concepts to read and be able to explain |
| **Guided notebook** | Planned notebook path, dataset, and tasks |
| **Independent lab** | A new task with constraints and expected evidence |
| **Assessment criteria** | Rubric weights specific to the module |
| **Deliverables** | What goes into your portfolio |
| **Next step** | The recommended follow-on module |
| **Risks and notes** | Hardware, licensing, privacy, and common failure modes |

Published lessons and lab briefs live in `docs/lessons/`, executable notebooks in
`notebooks/`, and starters or submission templates in `labs/`. Until a module's
files exist, pass review, and its notebook has been executed, the module is
**plan published**, not available.

## Levels

| Level | Theme | Modules | Hours |
| --- | --- | --- | --- |
| 0 | Orientation and environment | M00-M01 | 15 |
| 1 | Foundations | M02-M05 | 64 |
| 2 | Language AI | M06-M10 | 94 |
| 3 | Vision, speech, and video AI | M11-M14 | 82 |
| 4 | AI agents | M15 | 24 |
| 5 | Production and capstone | M16-M17 | 60 |

## Assessment model

Every module uses the same weights: knowledge check 20%, guided notebook 30%,
independent lab 40%, reflection 10%. The lab rubric evaluates technical
correctness, evaluation quality, reproducibility, data ethics, and
communication. The capstone has its own weighted rubric. See
[Assessments](../course/assessments.md).

## How to read the plans

- Start with the [roadmap](../course/roadmap.md) for sequencing and schedules.
- Read the level page for the modules in your path.
- Treat hour estimates as medians for a prepared learner, not guarantees.
- Follow the "next step" links; they encode the intended dependency order.
- Check hardware labels before starting a lab, and have a backup plan.

## Status

| Status | Meaning |
| --- | --- |
| Plan published | This page: objectives, labs, rubrics, and deliverables are defined |
| Content in authoring | Lesson page and notebook are being written |
| Content in review | Authored content is under technical and pedagogical review |
| Published | Lesson, notebook, lab, and assessment are available and the notebook has been executed on the supported environments |

At the time of this release, **F01-F13 are published** and deliver M01-M03;
M04-M17 are **plan published**. The foundation notebooks have been executed on
Windows 11 CPU. Google Colab verification is pending, and no foundation notebook
has been executed on a GPU. No module is marked fully verified until its notebook
has run on every supported environment.
