# Lessons

This section contains the student-facing lessons. A lesson is the working part of
a module: read the explanation, run the notebook, complete the lab, and check the
assessment. The [syllabus](../syllabus/index.md) remains the authoritative plan
for every module, including modules whose lessons are still being authored.

!!! info "What is available now"
    The **foundation sequence F01-F13 is published** as a complete vertical
    slice: lesson, executable notebook, lab brief, and assessment for every unit.
    F01-F13 deliver the approved M01-M03 material at a more granular pace, plus
    one pre-M01 Python unit. All foundation notebooks were executed top-to-bottom
    on Windows 11 with Python 3.12.10 on CPU. Google Colab verification is still
    pending, and no foundation notebook was executed on a GPU. All other modules
    (M04-M17) publish their plans only. M00 orientation is delivered through the
    [roadmap](../course/roadmap.md), [learning paths](../course/learning-paths.md),
    [study guide](../course/how-to-study.md), and the
    [M00 plan](../syllabus/level-0-start.md#m00).

## Foundation sequence

The foundation sequence is the recommended starting path. Its units map onto the
approved module codes, so later prerequisites such as "M02 completed" are
satisfied by finishing F03-F10.

| Unit | Title | Implements | Hours | Hardware | Lesson |
| --- | --- | --- | --- | --- | --- |
| F01 | Python essentials for AI | pre-M01 | 8 | CPU-only | [Published](f01-python-ai/index.md) |
| F02 | Virtual environments, packages, Jupyter, Colab | M01 | 12 | CPU-only | [Published](m01-environment/index.md) |
| F03 | NumPy and pandas for datasets | M02 | 8 | CPU-only | [Published](f03-numpy-pandas/index.md) |
| F04 | Cleaning, missing values, categories, normalization | M02/M05 | 10 | CPU-only | [Published](f04-data-cleaning/index.md) |
| F05 | Train, validation, and test splits | M02 | 8 | CPU-only | [Published](f05-splits/index.md) |
| F06 | Exploratory data analysis and visualization | M02 | 8 | CPU-only | [Published](f06-eda/index.md) |
| F07 | Supervised and unsupervised learning | M02 | 8 | CPU-only | [Published](f07-supervised-unsupervised/index.md) |
| F08 | Regression and classification | M02 | 10 | CPU-only | [Published](f08-regression-classification/index.md) |
| F09 | Decision trees, random forests, gradient boosting | M02 | 10 | CPU-only | [Published](f09-tree-ensembles/index.md) |
| F10 | Metrics, overfitting, leakage, cross-validation | M02 | 10 | CPU-only | [Published](f10-metrics-validation/index.md) |
| F11 | Neural network fundamentals | M03 | 10 | CPU or GPU | [Published](f11-neural-networks/index.md) |
| F12 | Tensors, gradients, losses, optimizers, backpropagation | M03 | 12 | CPU or GPU | [Published](f12-backpropagation/index.md) |
| F13 | CPU/GPU, seeds, reproducibility, tracking | M03 | 8 | CPU-only core | [Published](f13-reproducibility/index.md) |

F01-F13 total 122 guided hours, which is more than the 44 hours assigned to
M01-M03 in the syllabus. The difference is deliberate: the foundation units add
guided practice, independent labs, and assessment time that the module plans
budget at a coarser level. Treat the unit hours as planning estimates, not as a
second allocation of credit.

The foundation dataset card and dependency sets are documented in
[Foundation data and dependencies](../technical/foundation-assets.md).

## How a lesson is organized

Every lesson follows the same four-page pattern. The strip at the top and bottom
of each page lets you move without returning to this index.

| Page | What it is for | When to use it |
| --- | --- | --- |
| **Lesson** | Concepts, worked explanations, common failures, checkpoint | Before and during the notebook |
| **Guided notebook** | How to run the notebook, expected output, troubleshooting | While completing the guided practical |
| **Lab brief** | An independent task, constraints, deliverables, rubric | After the notebook runs cleanly |
| **Assessment** | Knowledge check, scoring, reflection, completion checklist | At the end of the module |

The reusable structure is documented in
[Course conventions](../course/course-conventions.md). Contributors should start
from the [templates](../technical/templates/index.md).

## Full module map

| Code | Module | Level | Hours | Hardware | Lesson |
| --- | --- | --- | --- | --- | --- |
| M00 | Course orientation and study plan | 0 | 3 | CPU-only | [Plan](../syllabus/level-0-start.md#m00) |
| M01 | Python and AI development environment | 0 | 12 | CPU-only | [Published as F02](m01-environment/index.md) |
| M02 | Machine learning foundations | 1 | 16 | CPU-only | [Published as F03-F10](f03-numpy-pandas/index.md) |
| M03 | Deep learning foundations | 1 | 16 | CPU or GPU | [Published as F11-F13](f11-neural-networks/index.md) |
| M04 | Training models from scratch | 1 | 18 | GPU recommended | [Plan](../syllabus/level-1-foundations.md#m04) |
| M05 | Dataset preparation, labeling, cleaning, augmentation | 1 | 14 | CPU-only | [Plan](../syllabus/level-1-foundations.md#m05) |
| M06 | Transformers and language models | 2 | 18 | CPU or GPU | [Plan](../syllabus/level-2-language.md#m06) |
| M07 | Small language models and supervised fine-tuning | 2 | 24 | GPU required | [Plan](../syllabus/level-2-language.md#m07) |
| M08 | LoRA, QLoRA, quantization, efficient training | 2 | 18 | GPU required | [Plan](../syllabus/level-2-language.md#m08) |
| M09 | Chatbots and conversational applications | 2 | 16 | CPU or GPU | [Plan](../syllabus/level-2-language.md#m09) |
| M10 | Embeddings, vector search, and RAG | 2 | 18 | CPU-only | [Plan](../syllabus/level-2-language.md#m10) |
| M11 | Image classification and computer vision | 3 | 18 | GPU recommended | [Plan](../syllabus/level-3-vision-video.md#m11) |
| M12 | Object detection, tracking, transfer learning | 3 | 20 | GPU required | [Plan](../syllabus/level-3-vision-video.md#m12) |
| M13 | Speech recognition, audio classification, speech generation | 3 | 22 | GPU recommended | [Plan](../syllabus/level-3-vision-video.md#m13) |
| M14 | Video understanding and video analytics | 3 | 22 | GPU recommended | [Plan](../syllabus/level-3-vision-video.md#m14) |
| M15 | AI agents, tool calling, memory, workflows | 4 | 24 | CPU or API | [Plan](../syllabus/level-4-agents.md#m15) |
| M16 | Evaluation, security, responsible AI, deployment | 5 | 20 | CPU-only | [Plan](../syllabus/level-5-production.md#m16) |
| M17 | Integrated capstone | 5 | 40 | Depends | [Plan](../syllabus/level-5-production.md#m17) |

"Plan" means the module's objectives, practical work, rubric, and deliverables
are specified, but the lesson and notebook are not yet published. Do not treat a
plan as a finished lesson. The [syllabus status key](../syllabus/index.md#status)
defines each stage.

## Start with F01

Start with [F01 - Python essentials for AI](f01-python-ai/index.md) if your
Python is shaky, then continue to
[F02 - Python and AI development environment](m01-environment/index.md). F02 is
CPU-only, uses a bundled dataset, and produces the environment evidence that every
later module assumes. If your Python is already solid, you may begin at F02 and
return to F01 only for the specific toolkit skills you are missing.

If you are unsure about your starting point, read
[Prerequisites and readiness](../course/roadmap.md#prerequisites-and-readiness)
or use the [placement guidance](../course/learning-paths.md#placement-guidance).
