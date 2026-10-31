# AITopics - Applied AI Engineering

**A self-paced, hands-on course on training, fine-tuning, evaluating, and deploying
language, vision, speech, video, and agentic AI systems.**

Created and taught by **Engr. Dr. Muhammad Nadeem Majeed**, Professor,
Department of Data Science (PUCIT), University of the Punjab, Lahore, Pakistan.

[Start with F01](docs/lessons/f01-python-ai/index.md) ·
[Foundation sequence](docs/lessons/index.md#foundation-sequence) ·
[Course site](docs/index.md) ·
[Learning paths](docs/course/learning-paths.md) ·
[Capstone projects](docs/course/projects.md)

> **Course status: foundation sequence F01-F13 published.**
> Thirteen units now have a complete lesson, executable notebook, lab brief, and
> assessment. F01-F13 deliver the approved M01-M03 material at a more granular
> pace. All foundation notebooks were executed top-to-bottom on Windows 11 with
> Python 3.12.10 on CPU; Google Colab and GPU verification are still pending.
> M04-M17 publish their plans only. See [Lessons](docs/lessons/index.md) and
> [Implementation phases](docs/planning/implementation-phases.md).

---

## What this course teaches, and why

Most AI tutorials stop at a toy demo or an API call. This course teaches the full
lifecycle: frame a problem, prepare and document data, train or adapt a model,
measure whether it works, reduce cost, secure the system, and deploy it with a
rollback plan.

The course is:

- **Practical first.** Every module ends with an independent lab and a published
  rubric, not just a finished notebook to read.
- **Progressive.** You start with Python and classical machine learning, then
  build up to fine-tuned small language models, retrieval-augmented chatbots,
  object detection, speech systems, video analytics, and tool-using agents.
- **Hardware honest.** Every exercise is labeled **CPU-only**, **GPU
  recommended**, or **GPU required**. Free Google Colab and Kaggle GPU tiers are
  supported where possible.
- **Open and local-first.** The core path uses free, open-source tools that run
  on Windows 11, Linux, or Google Colab. Paid APIs are optional, never mandatory.
- **Responsible by default.** Dataset licensing, privacy, bias, security, and
  evaluation are treated as engineering requirements, not footnotes.

## Who this course is for

- Undergraduate and postgraduate students in computer science, data science,
  software engineering, and related fields.
- Developers and analysts moving from classical software or statistics into AI.
- Researchers who need practical model-training and deployment skills.
- Instructors who want a modular, reusable applied-AI curriculum.

**Prior knowledge:** basic Python (variables, loops, functions, lists,
dictionaries, files), comfort with a terminal, and high-school algebra. You do
**not** need prior deep-learning experience. The mathematics you need is
introduced where it is used.

If your Python is rusty, start with
[F01 - Python essentials for AI](docs/lessons/f01-python-ai/index.md). See
[Prerequisites and readiness](docs/course/roadmap.md#prerequisites-and-readiness)
for the expected level and concrete readiness actions.

## What you will be able to do

By the end of the full program, you will be able to:

1. Build reproducible Python environments for CPU and GPU AI work on Windows 11
   and Google Colab.
2. Train, evaluate, and diagnose classical machine-learning and deep-learning
   models instead of only calling pretrained APIs.
3. Design datasets, write labeling guidelines, audit licenses, and document data
   with dataset cards.
4. Fine-tune small language models with supervised fine-tuning, LoRA, and
   QLoRA, and explain the memory, quality, and cost trade-offs.
5. Build domain chatbots and retrieval-augmented generation (RAG) systems with
   citations, guardrails, and measurable evaluation.
6. Train and adapt image classifiers, object detectors, and tracking pipelines.
7. Adapt speech-recognition, audio-classification, and speech-generation models.
8. Build privacy-preserving video analytics prototypes for legitimate tasks such
   as vehicle counting and clothing-attribute recognition.
9. Build AI agents with tool calling, memory, workflows, permissions, and
   failure handling.
10. Evaluate, red-team, package, and deploy an AI system with monitoring,
    documentation, and a rollback plan.

## Beginner-to-advanced path

| Level | Modules | Focus | Hours |
| --- | --- | --- | --- |
| 0 - Orientation | M00-M01 | Orientation, Python, environments, GPU/Colab setup | 15 |
| 1 - Foundations | M02-M05 | Machine learning, deep learning, training from scratch, data engineering | 64 |
| 2 - Language AI | M06-M10 | Transformers, small language models, LoRA/QLoRA, chatbots, RAG | 94 |
| 3 - Vision, speech, video | M11-M14 | Image classification, detection, tracking, speech/audio, video analytics | 82 |
| 4 - AI agents | M15 | Tool calling, memory, workflows, agent evaluation and safety | 24 |
| 5 - Production and capstone | M16-M17 | Evaluation, security, responsible AI, deployment, capstone | 60 |
| **Total** | **18 modules** | | **339** |

The detailed sequence, dependencies, and 13-, 16-, 26-, and 42-week schedules
are in the [course roadmap](docs/course/roadmap.md#study-schedules).

### Choose a learning path

| Path | Modules | Hours | Best for |
| --- | --- | --- | --- |
| [AI foundations](docs/course/learning-paths.md#path-1-ai-foundations) | M00-M05 | 79 | A solid ML/DL base before specializing |
| [Language AI engineer](docs/course/learning-paths.md#path-2-language-ai-engineer) | M00-M03, M05-M10, M16-M17 | 215 | Chatbots, small language models, RAG |
| [Vision and video engineer](docs/course/learning-paths.md#path-3-vision-and-video-engineer) | M00-M05, M11-M12, M14, M16-M17 | 199 | Detection, tracking, video analytics |
| [Speech and audio engineer](docs/course/learning-paths.md#path-4-speech-and-audio-engineer) | M00-M05, M13, M16-M17 | 161 | ASR, audio classification, speech generation |
| [AI agent engineer](docs/course/learning-paths.md#path-5-ai-agent-engineer) | M00-M03, M05-M06, M09-M10, M15-M17 | 197 | Tool-using agents and workflows |
| [Full program](docs/course/learning-paths.md#path-6-full-program) | M00-M17 | 339 | Portfolio-grade breadth and a capstone |

Each path assumes the listed foundations. Read
[learning paths](docs/course/learning-paths.md) for entry requirements,
sequencing, and what to skip safely.

## Foundation sequence

The foundation units are the recommended starting path. They map onto M01-M03,
so later prerequisites that name those module codes are satisfied by completing
the units.

| Unit | Title | Implements | Hours | Hardware | Status |
| --- | --- | --- | --- | --- | --- |
| F01 | Python essentials for AI | pre-M01 | 8 | CPU-only | [Published](docs/lessons/f01-python-ai/index.md) |
| F02 | Virtual environments, packages, Jupyter, Colab | M01 | 12 | CPU-only | [Published](docs/lessons/m01-environment/index.md) |
| F03 | NumPy and pandas for datasets | M02 | 8 | CPU-only | [Published](docs/lessons/f03-numpy-pandas/index.md) |
| F04 | Cleaning, missing values, categories, normalization | M02/M05 | 10 | CPU-only | [Published](docs/lessons/f04-data-cleaning/index.md) |
| F05 | Train, validation, and test splits | M02 | 8 | CPU-only | [Published](docs/lessons/f05-splits/index.md) |
| F06 | Exploratory data analysis and visualization | M02 | 8 | CPU-only | [Published](docs/lessons/f06-eda/index.md) |
| F07 | Supervised and unsupervised learning | M02 | 8 | CPU-only | [Published](docs/lessons/f07-supervised-unsupervised/index.md) |
| F08 | Regression and classification | M02 | 10 | CPU-only | [Published](docs/lessons/f08-regression-classification/index.md) |
| F09 | Decision trees, random forests, gradient boosting | M02 | 10 | CPU-only | [Published](docs/lessons/f09-tree-ensembles/index.md) |
| F10 | Metrics, overfitting, leakage, cross-validation | M02 | 10 | CPU-only | [Published](docs/lessons/f10-metrics-validation/index.md) |
| F11 | Neural network fundamentals | M03 | 10 | CPU or GPU | [Published](docs/lessons/f11-neural-networks/index.md) |
| F12 | Tensors, gradients, losses, optimizers, backpropagation | M03 | 12 | CPU or GPU | [Published](docs/lessons/f12-backpropagation/index.md) |
| F13 | CPU/GPU, seeds, reproducibility, tracking | M03 | 8 | CPU-only core | [Published](docs/lessons/f13-reproducibility/index.md) |

The units total more guided hours than the coarse M01-M03 plans because they add
explicit labs, assessments, and practice. The approved module codes and the
syllabus remain authoritative for credit and prerequisites.

## Module sequence

| Code | Module | Level | Hours | Hardware | Status |
| --- | --- | --- | --- | --- | --- |
| M00 | Course orientation and study plan | 0 | 3 | CPU-only | [Plan](docs/syllabus/level-0-start.md#m00) |
| M01 | Python and AI development environment | 0 | 12 | CPU-only | [Published as F02](docs/lessons/m01-environment/index.md) |
| M02 | Machine learning foundations | 1 | 16 | CPU-only | [Published as F03-F10](docs/lessons/f03-numpy-pandas/index.md) |
| M03 | Deep learning foundations | 1 | 16 | CPU or GPU | [Published as F11-F13](docs/lessons/f11-neural-networks/index.md) |
| M04 | Training models from scratch | 1 | 18 | GPU recommended | [Plan](docs/syllabus/level-1-foundations.md#m04) |
| M05 | Dataset preparation, labeling, cleaning, augmentation | 1 | 14 | CPU-only | [Plan](docs/syllabus/level-1-foundations.md#m05) |
| M06 | Transformers and language models | 2 | 18 | CPU or GPU | [Plan](docs/syllabus/level-2-language.md#m06) |
| M07 | Small language models and supervised fine-tuning | 2 | 24 | GPU required | [Plan](docs/syllabus/level-2-language.md#m07) |
| M08 | LoRA, QLoRA, quantization, efficient training | 2 | 18 | GPU required | [Plan](docs/syllabus/level-2-language.md#m08) |
| M09 | Chatbots and conversational applications | 2 | 16 | CPU or GPU | [Plan](docs/syllabus/level-2-language.md#m09) |
| M10 | Embeddings, vector search, and RAG | 2 | 18 | CPU-only | [Plan](docs/syllabus/level-2-language.md#m10) |
| M11 | Image classification and computer vision | 3 | 18 | GPU recommended | [Plan](docs/syllabus/level-3-vision-video.md#m11) |
| M12 | Object detection, tracking, transfer learning | 3 | 20 | GPU required | [Plan](docs/syllabus/level-3-vision-video.md#m12) |
| M13 | Speech recognition, audio classification, speech generation | 3 | 22 | GPU recommended | [Plan](docs/syllabus/level-3-vision-video.md#m13) |
| M14 | Video understanding and video analytics | 3 | 22 | GPU recommended | [Plan](docs/syllabus/level-3-vision-video.md#m14) |
| M15 | AI agents, tool calling, memory, workflows | 4 | 24 | CPU or API | [Plan](docs/syllabus/level-4-agents.md#m15) |
| M16 | Evaluation, security, responsible AI, deployment | 5 | 20 | CPU-only | [Plan](docs/syllabus/level-5-production.md#m16) |
| M17 | Integrated capstone | 5 | 40 | Depends | [Plan](docs/syllabus/level-5-production.md#m17) |

A **plan** defines objectives, practical work, rubric, and deliverables; it is not
a finished lesson. The [lessons index](docs/lessons/index.md) shows what is
published.

## Study independently

Every module follows the same loop:

1. **Lesson** - the minimum theory needed to reason about the practical.
2. **Guided notebook** - a runnable, annotated demonstration on a small, legal
   dataset.
3. **Independent lab** - apply the technique to a new problem under constraints.
4. **Assessment** - knowledge check, rubric, reflection, and portfolio evidence.

Useful starting points:

- [How to study](docs/course/how-to-study.md): weekly routine, notebook workflow,
  GPU budgeting, debugging, and AI-assistance rules.
- [Course conventions](docs/course/course-conventions.md): how the four page
  types fit together, file naming, and evidence standards.
- [Assessments](docs/course/assessments.md): weights, lab rubric, integrity, and
  the evidence checklist.
- [FAQ](docs/course/faq.md): time, cost, hardware, datasets, certificates, and
  common questions.

There is no proctored exam. Completing the public materials does **not** confer a
certificate, university credit, or professional certification. Enrolled students
follow their institution's rules.

## Run the notebooks

### Local Windows 11

F01 uses only the Python standard library and runs with any Python 3.10+
environment. F02-F10 need `requirements/notebooks.txt`. F11-F13 need
`requirements/cpu.txt`, which adds CPU-only PyTorch. All foundation notebooks run
on CPU; the GPU branches are optional and were not executed in the authoring
environment.

For the complete foundation sequence from PowerShell:

```powershell
git clone https://github.com/nadeem-majeedch/AITopics.git
cd AITopics
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements/cpu.txt
python -m jupyter lab notebooks/foundations/
```

The notebooks are numbered in course order. F02 is
`notebooks/foundations/m01_environment_check.ipynb`, because it implements the
approved M01 module.

M01 is CPU-only and uses the small digits dataset bundled with scikit-learn, so
it needs no dataset download:

```powershell
git clone https://github.com/nadeem-majeedch/AITopics.git
cd AITopics
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements/notebooks.txt
python -m jupyter lab notebooks/foundations/m01_environment_check.ipynb
```

If `Activate.ps1` is blocked, use a per-process policy change:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Do not change machine-wide security settings for one lab. If your cohort uses a
private or renamed repository, use the clone URL provided by your instructor.

### Linux or macOS

```bash
git clone https://github.com/nadeem-majeedch/AITopics.git
cd AITopics
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/notebooks.txt
python -m jupyter lab notebooks/foundations/m01_environment_check.ipynb
```

### Google Colab

1. Open [Google Colab](https://colab.research.google.com/).
2. Choose **File > Upload notebook** and select the `.ipynb` file from your clone.
3. Choose **Runtime > Change runtime type > CPU** for M01. A GPU is optional.
4. Choose **Runtime > Run all**.
5. Download the artifacts from the `outputs/` folder before the session ends.

Colab's `/content` directory is temporary. Save the executed notebook and report
to Drive or Git before disconnecting. Package versions on Colab will differ from
your local machine; the M01 lab uses that difference as evidence.

The [M01 notebook guide](docs/lessons/m01-environment/notebook.md) explains each
section, healthy output, and troubleshooting. The full M01 path is:

[Lesson](docs/lessons/m01-environment/index.md) →
[Guided notebook](docs/lessons/m01-environment/notebook.md) →
[Lab](docs/lessons/m01-environment/lab.md) →
[Assessment](docs/lessons/m01-environment/assessment.md)

The complete foundation path is F01 through F13. Each unit has the same four-page
structure; start at the [foundation sequence](docs/lessons/index.md#foundation-sequence)
table or open [F01](docs/lessons/f01-python-ai/index.md) directly.

## Labs, assessments, and projects

Independent labs are the core of the course. Each lab produces a small, reviewable
artifact: a notebook, a short report, a model card, an evaluation table, or a
working demo. Labs are designed to be completed on free infrastructure.

Module assessment uses four components:

| Component | Weight | Evidence |
| --- | --- | --- |
| Knowledge check | 20% | Short answers or auto-checkable questions |
| Guided notebook | 30% | A clean run with interpretation |
| Independent lab | 40% | Artifact scored against a published rubric |
| Reflection | 10% | What you learned and what you would change |

The lab rubric evaluates technical correctness, evaluation quality,
reproducibility, data ethics, and communication. The capstone has its own rubric.
See [Assessments](docs/course/assessments.md) and the
[M01 assessment](docs/lessons/m01-environment/assessment.md).

## Hardware and cloud expectations

| Setup | What you can do | What to expect |
| --- | --- | --- |
| **Laptop CPU, 8-16 GB RAM** | Levels 0-1, data engineering, RAG, small-model inference, agent orchestration, evaluation, deployment | The core path works without a GPU |
| **Free Colab or Kaggle GPU** | Fine-tuning, detection, speech, and video labs | Session or quota limits; save artifacts early |
| **Local NVIDIA GPU, 8 GB+ VRAM** | The full training path with fewer interruptions | Driver and PyTorch wheel compatibility matter |

- **CPU-only:** orientation, Python, classical ML, data engineering, RAG with small
  embedding models, agent orchestration, evaluation, and packaging.
- **GPU recommended:** deep-learning foundations, image classification, speech
  inference.
- **GPU required:** training from scratch at useful speed, LoRA/QLoRA
  fine-tuning, object-detection training, video-model training, and Whisper
  fine-tuning.
- **Free GPU options:** Google Colab free tier and Kaggle notebooks, subject to
  their quotas and session limits.
- **Disk:** keep at least 30 GB free for environments, datasets, and model
  caches.

The course never requires a paid API. If you cannot install a local GPU stack, use
Colab for GPU labs and keep a local CPU environment for development. See
[Troubleshooting](docs/technical/troubleshooting.md) for Windows, CUDA, Colab,
and storage issues.

## Datasets and pretrained models

- **M01 uses no external dataset.** It loads the digits data bundled with
  scikit-learn.
- **F01-F13 use four synthetic tables.** They are generated locally under
  CC0-1.0 by `scripts/make_foundation_data.py`, contain no real people, and are
  documented in [Foundation data and dependencies](docs/technical/foundation-assets.md).
- **Later modules use dataset cards and download scripts.** Raw datasets are not
  committed. Each card records the source, license, size, checksum, and intended
  use.
- **Public sources** include UCI, OpenML, Hugging Face Datasets, Kaggle, and
  project-specific archives. Check the license before training or publishing.
- **Pretrained models** come from libraries such as torchvision, Hugging Face
  Transformers, OpenAI Whisper, and Ultralytics YOLO. Weights are downloaded or
  cached locally, never committed.
- **Tokens and credentials** belong in environment variables or an ignored local
  secrets file. Never commit them, and never paste them into shared notebooks.

The full data and model policy is in the
[repository architecture](docs/planning/repository-architecture.md#data-and-model-policy).
The [FAQ](docs/course/faq.md#where-do-the-datasets-come-from) explains where data
comes from.

## Responsible AI, privacy, and safe experimentation

- Use data you have the right to use. Record consent and license terms.
- Remove personal identifiers from reports, screenshots, logs, and demos.
- Do not build face recognition, identity inference, covert surveillance, or
  non-consensual voice cloning.
- Do not scrape private data, bypass access controls, or disable TLS checks.
- Disclose substantive AI assistance in reflections.
- Report limitations and failure modes instead of hiding them.
- Keep experiments reproducible: seed, pin, record hardware, and state what
  changed.

The [capstone rules](docs/course/projects.md#acceptable-and-unacceptable-projects)
list acceptable and prohibited work. The
[academic integrity policy](docs/course/assessments.md#academic-integrity)
explains what you must do yourself.

## Capstone options

The final capstone is a complete, evaluated system with a reproducible repository,
a technical report, a model or dataset card, a demo, and a presentation.
Suggested options:

- [Option A](docs/course/projects.md#project-a): a domain small-language-model
  assistant with RAG and citations.
- [Option B](docs/course/projects.md#project-b): a visual inspection or
  classification system.
- [Option C](docs/course/projects.md#project-c): a privacy-preserving vehicle
  counting and clothing-attribute analytics prototype using public or consented
  footage.
- [Option D](docs/course/projects.md#project-d): a speech and audio assistant for
  a low-resource domain or language.
- [Option E](docs/course/projects.md#project-e): a tool-using agent with an
  evaluation suite and permission boundaries.

See [Capstone projects](docs/course/projects.md) for eligibility, milestones,
submission structure, and reviewer questions. Students may adapt the
[project specification template](docs/technical/templates/project.md) for a
proposal.

## Repository map

| Path | Contents | Status |
| --- | --- | --- |
| `README.md` | Student entry point | Available |
| `docs/` | Published course site: lessons, roadmap, syllabus, study guides, planning, technical docs | Available |
| `docs/lessons/` | Published lessons, notebook guides, labs, assessments | F01-F13 available |
| `docs/course/` | Roadmap, paths, study guide, conventions, assessments, projects, FAQ | Available |
| `docs/syllabus/` | Detailed plans for all 18 modules | Available |
| `notebooks/` | Executable guided notebooks by learning area | F01-F13 available |
| `labs/` | Lab starters and submission templates | Foundation starters available |
| `projects/` | Capstone templates and submission structure | Planned |
| `datasets/` | Dataset cards and download scripts; raw data is never committed | Foundation card and generator available |
| `scripts/` | Setup, download, evaluation, and maintenance automation | Foundation data generator available |
| `tests/` | Tests for shared utilities and notebook smoke checks | Planned |
| `requirements/` | Split dependency sets (docs, base, notebooks, CPU, GPU, LLM, agents, dev) | Partially available |
| `.github/workflows/` | CI and documentation deployment | Planned |

The full target tree, content ownership rules, and data policy are in the
[repository architecture](docs/planning/repository-architecture.md).

## Course status

| Item | Status |
| --- | --- |
| F01-F13 lessons, notebooks, labs, assessments | Published; all 13 notebooks executed top-to-bottom on Windows 11 CPU |
| Foundation Google Colab verification | Pending |
| Foundation GPU execution | Not executed; optional GPU paths documented |
| F02 (M01) lesson, notebook, lab, assessment | Published; notebook verified on Windows 11 |
| M04-M17 plans | Published |
| M04-M17 lessons and notebooks | In development |
| Documentation build | Verified locally with `mkdocs build --strict` on 2026-10-30 |
| Documentation site deployment | Not yet enabled |
| License files | Pending instructor approval |

Do not treat a published plan as a finished lesson. The
[lessons index](docs/lessons/index.md) and
[syllabus status key](docs/syllabus/index.md#status) use the same status language.

## Instructor

**Engr. Dr. Muhammad Nadeem Majeed**  
Professor, Department of Data Science (PUCIT)  
University of the Punjab, Lahore, Pakistan

Read [about the instructor](docs/about/instructor.md), including the course
rationale and teaching approach. Course questions, corrections, and contributions
are handled through the repository's GitHub Issues. Include the module code and
the exact page or notebook in your report.

## Contributing

Corrections, dataset suggestions, and new lab ideas are welcome. Read
[Contributing](docs/technical/contributing.md) and the
[quality standards](docs/planning/quality-standards.md) before opening a pull
request. New lessons start from the
[templates](docs/technical/templates/index.md). All contributions must respect
dataset licenses, privacy, and the course's responsible-AI rules.

## License and attribution

Course materials are intended for open educational use. A formal license has
**not yet been approved and committed**. The recommended split is:

- **Code and notebooks:** MIT License.
- **Prose, diagrams, and course text:** Creative Commons Attribution 4.0
  (CC BY 4.0), with attribution to the instructor.

Until the license files are added, copyright remains with the author and reuse
requires written permission. This is tracked as a release blocker in the
[content inventory](docs/planning/content-inventory.md).

## Technical documentation

Build commands, dependency management, CI/CD, GitHub Pages, maintainer
troubleshooting, and content standards are intentionally kept out of this
student-facing README:

- [Build and deploy](docs/technical/build-and-deploy.md)
- [Maintainer guide](docs/technical/maintainer-guide.md)
- [Contributing](docs/technical/contributing.md)
- [Troubleshooting](docs/technical/troubleshooting.md)
- [Quality standards](docs/planning/quality-standards.md)
- [Repository architecture](docs/planning/repository-architecture.md)
