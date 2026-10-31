# Course conventions

This page explains how course material is organized and how you are expected to
use it. The conventions exist so that every module feels familiar: you should
never have to guess where the notebook, lab, or rubric lives.

The published [M01 lesson](../lessons/m01-environment/index.md) is the reference
example for all four student page types.

## The four student pages

| Page | Purpose | What you do there | Where it lives |
| --- | --- | --- | --- |
| **Lesson** | Explains the concepts and the reasoning behind the practical | Read, take notes, check your understanding | `docs/lessons/<module>/index.md` |
| **Guided notebook** | Tells you how to run the notebook, what healthy output looks like, and how to fix common failures | Run the notebook from a clean kernel | `docs/lessons/<module>/notebook.md` |
| **Lab brief** | Defines an independent task, constraints, deliverables, and rubric | Produce and submit evidence | `docs/lessons/<module>/lab.md` |
| **Assessment** | Knowledge check, scoring, reflection, and completion checklist | Self-assess and decide whether to continue | `docs/lessons/<module>/assessment.md` |

A module is **published** only when all four pages exist and its notebook has been
executed on the supported environments. A module whose plan is published but whose
lesson is not is marked **plan** in the [module map](../lessons/index.md#full-module-map).

## Where files live

| Content | Location | Notes |
| --- | --- | --- |
| Published lesson pages | `docs/lessons/<module>/` | One directory per module, lowercase slug |
| Executable notebooks | `notebooks/<area>/` | Run top-to-bottom; never a substitute for the lesson |
| Lab briefs | `docs/lessons/<module>/lab.md` | Student-facing, linked in navigation |
| Lab starters and submission templates | `labs/<area>/` | Optional starting files; copy them to your portfolio |
| Capstone specifications | `projects/` | Student and reviewer templates |
| Dataset cards and download scripts | `datasets/` | Raw data is never committed |
| Module plans | `docs/syllabus/` | Objectives, hours, rubric, risks, next step |
| Contributor templates | `docs/technical/templates/` | Starting points for new material |

Areas use consistent names: `foundations`, `model-training`,
`llm-fine-tuning`, `chatbots-rag`, `computer-vision`, `speech-audio`,
`video-ai`, `ai-agents`, and `production`.

## Module navigation

Every lesson page starts and ends with the same navigation strip:

```text
Module path: Lesson · Guided notebook · Lab brief · Assessment
```

The current page is bold and the other three are links. The site also provides
breadcrumbs, the left navigation, and previous/next footer links. If you are ever
unsure where you are, the breadcrumb at the top of the page shows the module and
the page type.

## What every module header states

| Field | Example | Why you need it |
| --- | --- | --- |
| Module code and title | M01 - Python and AI development environment | Stable reference for questions and submissions |
| Study time | 12 hours | Planning, not a guarantee |
| Hardware label | CPU-only | Whether your machine can run the core work |
| Prerequisites | M00 and basic Python | What to finish first |
| Deliverable | Environment report | What goes into your portfolio |

Hardware labels follow the [syllabus legend](../syllabus/index.md#hardware-legend):

- **CPU-only:** completes on a modern laptop CPU.
- **CPU or GPU:** CPU works with reduced data or model size.
- **GPU recommended:** CPU is possible but slow; free Colab or Kaggle GPU is advised.
- **GPU required:** the core lab needs a GPU, free-tier or local.
- **Depends:** the capstone option determines the hardware.

## How to work through a module

1. **Read the lesson before running code.** You need the vocabulary to interpret
   the output.
2. **Run the guided notebook from a clean kernel.** Do not skip a required cell;
   fix the cause instead.
3. **Save the evidence.** Keep the executed notebook, report, and any logs.
4. **Do the lab without copying the guided notebook.** The lab is a new task under
   constraints, not a repeat.
5. **Score yourself with the assessment page.** Record which rubric dimension is
   weakest.
6. **Write the reflection.** Explain what you would do differently, not just what
   you did.
7. **Add the artifact to your portfolio.** Use one folder per module.

The full weekly routine is in [How to study](how-to-study.md). The evidence
standard is in [Assessments](assessments.md).

## File naming for your submissions

Use lowercase, hyphenated names with the module code first:

```text
m01-environment/
  m01_environment_check.ipynb
  environment_A.json
  environment_B.json
  requirements.lock
  environment_report.md
  reflection.md
```

Guidelines:

- Put the module code in the filename only when the file could be confused with
  another module's artifact.
- Use ISO dates (`2026-10-30`) if you keep multiple versions.
- Do not put your student ID, email address, or other personal data in filenames.
- Do not commit generated model weights, datasets, caches, or virtual
  environments.
- If a file contains personal paths or hostnames, redact them before sharing.

## Evidence and portfolio

A completed module produces evidence, not just a feeling of understanding. For
each module, keep:

- The executed notebook with outputs.
- The lab artifact named in the brief.
- The rubric self-score and a short note on the weakest dimension.
- The reflection.
- A one-line entry in your portfolio README linking to the artifact.

Do not rewrite history to make a failed attempt disappear. Keep the final version
and, if useful, a short note about what failed. Reviewers value an honest
diagnosis more than a perfect first run.

## AI assistance and integrity

You may use AI assistants to explain concepts, debug errors, and suggest tests.
You must run the work, verify the output, and disclose substantive assistance.
Do not submit generated evidence for a machine or experiment you did not run.

The rules are in [Academic integrity](assessments.md#academic-integrity) and
[How to study](how-to-study.md#academic-integrity-and-ai-assistants).

## For contributors

New material starts from a template, not a blank page:

- [Chapter template](../technical/templates/chapter.md)
- [Notebook guide template](../technical/templates/notebook.md)
- [Lab template](../technical/templates/lab.md)
- [Assessment template](../technical/templates/assessment.md)
- [Project specification template](../technical/templates/project.md)

Before publishing, a module must pass the
[quality standards](../planning/quality-standards.md), its notebook must run
top-to-bottom, every internal link must resolve, and the site must build with
`mkdocs build --strict`. The [Contributing guide](../technical/contributing.md)
explains the review process.

## Reporting a problem

When you report a broken link, unclear explanation, or failing cell, include:

- The module code and page title.
- The exact URL or repository path.
- Your operating system, Python version, and package versions.
- The command or cell that failed and the full error message.
- What you expected and what happened.

Use the repository's GitHub Issues. Do not include tokens, personal data, or
large logs with private paths.

## Status language

| Term | Meaning |
| --- | --- |
| **Plan** | Objectives, practical work, rubric, and deliverables are specified |
| **In authoring** | Lesson or notebook is being written |
| **In review** | Material is complete enough for technical and pedagogical review |
| **Published** | Lesson, notebook, lab, and assessment are available and verified |
| **Verified** | The notebook has been executed on the supported environments |

These terms are used consistently in the [syllabus status key](../syllabus/index.md#status)
and the [lessons index](../lessons/index.md).
