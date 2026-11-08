# Completion checklist

```markdown
**Projects:** [Index](index.md) · **Completion checklist** · [Report template](report-template.md)
```

Three checklists: one for a single capstone, one for the whole course, and one for
the portfolio you keep afterwards. Tick only what you can show in the repository;
an unticked box is information, not failure.

Before section A, assemble the ten files from the
[capstone submission package](submission-package.md). The sections below map
onto them: A1 to `project-scope.md`, A2 to `dataset-card.md`, A3 to
`experiments.csv` and `model-card.md`, A4 to `evaluation-report.md`, A5 to
`release-notes.md` and the final report, and A6 to `reproducibility.md` and
`README.md`.

## A. Before you call a capstone finished

### A1. Framing and scope

- [ ] The decision the system supports is stated in one sentence.
- [ ] The users are named, and the current process is described.
- [ ] Non-goals are listed, including one thing people might assume it does.
- [ ] The project fits the brief's scope; deviations are explained in the report.

### A2. Data and permissions

- [ ] The exact licence string and URL are recorded for every dataset.
- [ ] Every pretrained model's licence is recorded.
- [ ] Split construction is documented, with counts per class per split.
- [ ] Leakage checks were run, and the output is saved.
- [ ] No personal data, credentials, or unlicensed media are committed.
- [ ] The data can be regenerated or downloaded with a documented command.

### A3. Baseline and method

- [ ] At least one credible baseline appears in the results table.
- [ ] The baseline is a fair comparison (same split, same preprocessing rules).
- [ ] Hyperparameters were chosen on validation, and the report says so.
- [ ] One rejected alternative is described with the reason.

### A4. Evaluation

- [ ] The primary metric matches the task and the decision.
- [ ] Every metric is reported with n, and with an interval or a small-n caveat.
- [ ] The test set was opened once for the final numbers.
- [ ] At least three slices are analysed, with counts.
- [ ] A calibration, threshold, or abstention analysis exists where confidence is
      shown to a user.
- [ ] Error analysis has categories with counts, not only anecdotes.

### A5. Honesty

- [ ] Every number in the report traces to a file in `outputs/`.
- [ ] No borrowed benchmark number is presented as this project's result.
- [ ] Limitations name the condition that triggers the failure.
- [ ] Residual risk is stated for safety, privacy, or misuse where relevant.
- [ ] The reflection discloses AI assistance and how it was verified.

### A6. Engineering

- [ ] A stranger can run it from the README in a fresh environment.
- [ ] Dependencies are pinned, and the environment is described.
- [ ] Seeds are fixed, or residual nondeterminism is documented.
- [ ] Unit tests run without a GPU and pass.
- [ ] Model or system card exists and lists prohibited uses.
- [ ] Runtime and model size are reported.

## B. Course completion checklist

Use this to decide whether the course is finished for you. The course has no
enforced order; this is a defensible minimum.

### B1. Foundations

- [ ] F01-F05 completed: Python, environment, pandas, cleaning, splits.
- [ ] F06-F10 completed: EDA, supervised/unsupervised, regression and
      classification, trees and ensembles, metrics and validation.
- [ ] F11-F13 completed: neural networks, backpropagation, reproducibility.
- [ ] You can compute a metric by hand and explain why accuracy misleads on
      imbalanced data.

### B2. One domain section, in depth

Choose at least one and finish its modules, labs, and assessment:

- [ ] [Conversational AI](../../lessons/chatbots-rag/index.md) - 16 modules, 8 projects.
- [ ] [Computer Vision](../../lessons/computer-vision/index.md) - 14 modules, 8 labs.
- [ ] [Speech and Audio](../../lessons/speech-audio/index.md) - 14 modules, 8 labs.
- [ ] [Video AI](../../lessons/video-ai/index.md) - 15 modules, 8 labs.

### B3. Evaluation, safety, and operations

- [ ] You have measured a model on held-out data and reported uncertainty.
- [ ] You have audited a dataset for leakage and shown the effect.
- [ ] You have written a model or system card with prohibited uses.
- [ ] You have tested a system with adversarial or malformed input.
- [ ] You have a rollback or fallback story for at least one system.
- [ ] You can explain the difference between validation, test, and production
      monitoring without notes.

### B4. Assessment bank

- [ ] Chapter quizzes attempted; score recorded in `progress.md`.
- [ ] Conceptual questions answered in writing, checked against the solutions.
- [ ] At least six code-reading exercises completed.
- [ ] At least four debugging challenges solved.
- [ ] At least four scenario questions answered with a written decision.
- [ ] At least three evaluation exercises completed with numbers.
- [ ] End-of-course revision questions attempted closed-book.

### B5. Capstone

- [ ] One project from the [index](index.md) completed to the "Meets" level on
      every rubric criterion, or better.
- [ ] Report follows the [template](report-template.md).
- [ ] Demo runs from a clean checkout.
- [ ] Self-review checklist for that project is fully ticked.

### B6. Portfolio

- [ ] Repository is public or shareable, with no secrets and no unlicensed data.
- [ ] README states what the system does, what it does not do, and how to run it.
- [ ] One page per project: problem, result, limitation, link.
- [ ] You can talk for eight minutes about one project without slides.

## C. Progress record

Copy this table into `progress.md` at the repository root and fill it as you go.
It is for you; nothing reads it.

| Item | Date started | Date finished | Evidence (file or commit) | Self-score | Notes |
| --- | --- | --- | --- | --- | --- |
| F01 | | | | | |
| F02 | | | | | |
| ... | | | | | |
| Domain section | | | | | |
| Quiz bank | | | | | |
| Capstone proposal | | | | | |
| Capstone evaluation | | | | | |
| Capstone report | | | | | |
| Demo recorded | | | | | |

**Self-score bands** (from the [course assessment page](../assessments.md)):
90-100 portfolio-ready, 80-89 solid, 70-79 core met with weak evidence, below 70
revisit the weakest rubric criterion before moving on.

## D. If you are stuck

| Situation | What to do |
| --- | --- |
| Data licence unclear | Stop. Pick another dataset. A portfolio piece you cannot share is not worth the weeks. |
| Baseline beats your model | Report it. Then either improve the model with a stated hypothesis, or keep the baseline and explain why. |
| Metrics look too good | Audit the split and the features before celebrating. |
| No GPU | Every brief has a CPU path. Use the synthetic or small dataset and say so. |
| Annotation is taking days | Reduce classes or annotate every nth frame, and state the protocol. |
| You cannot finish in the estimated hours | Cut scope in the report, not evidence. A smaller system with a complete evaluation scores better. |
| You used AI to write code | Allowed with disclosure. You must be able to explain and debug every line you keep. |

---

**Related:** [Project index](index.md) · [Assessment bank](../assessments/index.md) · [How to study](../how-to-study.md)
