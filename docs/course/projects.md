# Capstone projects

The capstone (M17) is where the course becomes a portfolio piece. You will
define a bounded problem, build a working system, evaluate it honestly, document
its risks, and present it.

A capstone is not "a model that runs once." It is a reproducible system with
evidence.

!!! info "Twelve detailed specifications"
    This page states the M17 requirements and the acceptance rules. The full
    briefs - scope, data, milestones, rubric, report outline, demo checklist - are
    in the [project index](projects/index.md), with a
    [report template](projects/report-template.md) and a
    [completion checklist](projects/completion-checklist.md). Start there if you
    are choosing a project.

## Eligibility

You should have completed, or be able to demonstrate the outcomes of:

- M01-M03 (environment, ML, deep learning).
- M05 (data preparation).
- The modules in your chosen path.
- M16 (evaluation, security, deployment) before final submission.

You may start the proposal after M05, but do not collect final data until your
proposal is reviewed.

## Cross-cutting requirements

Every capstone must include:

1. **Problem statement** with users, use case, scope, and explicit non-goals.
2. **Data audit**: provenance, license, consent, collection method, known bias,
   and a datasheet or dataset card.
3. **Baseline**: a simple, credible comparison (majority class, keyword search,
   pretrained off-the-shelf model, or human estimate).
4. **Evaluation plan written before the final build**: metrics, held-out data,
   slices, and failure criteria.
5. **Working demo** that a reviewer can run.
6. **Model or system card**: intended use, limitations, metrics, and risks.
7. **Security and privacy review**: threats, mitigations, and residual risk.
8. **Reproducible repository**: environment file, data download or preparation
   script, seeds, and clear run instructions.
9. **Final report** of 8-12 pages and an 8-10 minute presentation.
10. **Reflection** on decisions, failures, and next steps.

The five shapes below are the M17 acceptance categories. The
[project index](projects/index.md) expands them into twelve briefs (P01-P12); any
brief maps onto one of these shapes, and the requirements on this page still apply.

## Option A: Domain small-language-model assistant with RAG {#project-a}

**Problem:** build an assistant for a bounded, low-risk domain, such as campus
course policies, a public agricultural advisory corpus, a product manual, or an
open-source project's documentation.

**Core build:**

- Curate 50-300 public or owned documents and a 500-2,000 example instruction
  dataset.
- Fine-tune a small instruct model (for example 0.5B-1.5B parameters) with LoRA
  or QLoRA, or justify why RAG alone is sufficient.
- Build a retrieval pipeline with chunking, embeddings, vector search, and
  citations.
- Add refusal behavior for out-of-scope questions and prompt-injection tests.

**Evaluation:** retrieval recall@k, answer correctness on a held-out question
set, citation faithfulness, refusal appropriateness, latency, and cost.

**Risks:** hallucination, stale documents, copyright, prompt injection through
retrieved text.

**Compute:** one free GPU session for fine-tuning; CPU for retrieval and
evaluation.

## Option B: Visual inspection or classification system {#project-b}

**Problem:** classify or detect a visual condition for a legitimate task, such
as manufacturing defects, plant disease, waste sorting, retail shelf compliance,
or wildlife identification.

**Core build:**

- Collect or use 300-1,000 licensed images with a documented labeling guide.
- Train a transfer-learning classifier or a small detector.
- Build a simple demo with confidence display and abstention.
- Analyze errors by class, lighting, background, and camera source.

**Evaluation:** macro F1, per-class precision/recall, confusion matrix,
calibration, mAP for detection, and slice-based error analysis.

**Risks:** dataset bias, label noise, overfitting to backgrounds, deployment
domain shift, unsafe claims of accuracy.

**Compute:** free GPU for training; CPU inference is acceptable.

## Option C: Privacy-preserving video analytics {#project-c}

**Problem:** build an analytics prototype on public or consented footage for a
specific, legitimate purpose. Acceptable examples:

- Count vehicles by type and direction in a public traffic clip.
- Measure queue length or occupancy in a consented retail or service setting.
- Recognize clothing attributes for retail cataloging or robotics, using
  licensed catalog images or consented footage.

**Core build:**

- Detection plus multi-object tracking.
- Zone or line-crossing logic for counts.
- Attribute classifier for vehicle type or clothing attributes.
- Face and license-plate blurring before storage.
- A documented retention policy and access model.

**Evaluation:** counting error (MAE), tracking quality (for example MOTA/IDF1
where ground truth exists), attribute macro F1, processing FPS, and failure
analysis at occlusion and low light.

**Hard constraints:**

- No face recognition, identity inference, or re-identification of people.
- No covert surveillance, stalking, or inference of sensitive attributes.
- Use public, licensed, or explicitly consented footage only.
- Document purpose limitation, retention, and who can access outputs.

**Compute:** GPU for detection/tracking experiments; short clips keep costs low.

## Option D: Speech and audio assistant {#project-d}

**Problem:** build a voice interface or audio analysis system for a bounded
domain, such as lecture transcription with search, voice commands for a robot
simulator, or environmental sound alerts.

**Core build:**

- Preprocess audio and establish a baseline ASR or audio classifier.
- Fine-tune or adapt a small model on licensed or consented data.
- Add a downstream task: retrieval over transcripts, command execution, or
  alerting.
- Evaluate under noise, accent, microphone, and domain shift.

**Evaluation:** WER/CER by condition, audio classification macro F1, latency,
and a small listening test for generated speech if TTS is used.

**Risks:** consent for voice data, speaker privacy, accent and language bias,
background noise, TTS misuse.

**Compute:** GPU recommended for fine-tuning; CPU inference with small models.

## Option E: Tool-using AI agent {#project-e}

**Problem:** build an agent that completes a bounded multi-step task with tools.
Examples: a course assistant that searches materials and queries a schedule
database, a data-analysis agent that runs safe SQL and produces charts, or an
operations agent that triages simulated tickets.

**Core build:**

- At least three tools with typed schemas and strict validation.
- A planning loop with step limits, timeouts, and retries.
- Short-term conversation memory and a documented long-term memory strategy.
- Permission boundaries and a sandbox for code or database tools.
- A failure-injection suite and prompt-injection tests.

**Evaluation:** task success on 30 or more held-out tasks, tool-call accuracy,
trajectory efficiency, refusal appropriateness, latency, and cost per task.

**Risks:** prompt injection, tool abuse, data exfiltration, runaway loops,
over-trust in model output.

**Compute:** CPU with hosted APIs, or a small local model with a GPU.

## Suggested milestones

| Stage | Timing | Deliverable | Review focus |
| --- | --- | --- | --- |
| Proposal | After M05 | 1-page problem, users, data plan, risks | Scope is bounded; data is legal |
| Data audit | Before modeling | Dataset card, license, sample review | Provenance and bias |
| Baseline | Early build | Simple baseline and evaluation harness | Metrics are meaningful |
| Midpoint | Halfway | Working prototype, first metrics | Honest progress, not polish |
| Evaluation | Before final | Held-out results, slices, failure taxonomy | Claims match evidence |
| Security and ethics | Before final | Threat model and privacy review | Residual risk is acceptable |
| Final | End | Repo, report, cards, demo, talk | Reproducible, honest, useful |

## Submission structure

```text
projects/<your-name>/capstone/
  README.md
  requirements.txt
  configs/
  data/
    ...                    # download or generation script; no raw data committed
  notebooks/
    01-data-audit.ipynb
    02-baseline.ipynb
    03-model.ipynb
    04-evaluation.ipynb
  src/
  tests/
  outputs/
  artifacts/
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
  demo/
    app.py
```

Every capstone submits the same ten files in `submission/`. Copy them from the
[capstone submission package](projects/submission-package.md), which also
maps each file to the three checkpoint gates and provides the final checklist.

Do not commit datasets, model weights, API keys, or personal data. Provide
download scripts and checksums instead.

## Acceptable and unacceptable projects

| Acceptable | Not acceptable |
| --- | --- |
| Defect detection on licensed images | Face recognition or identity inference |
| Vehicle counting on public traffic video | Covert tracking of individuals |
| Clothing attribute classification on catalog data | Inferring sensitive traits about people |
| Assistive speech interface with consent | Voice cloning without consent |
| Document QA with citations | High-stakes medical or legal advice without supervision |
| Agent with sandboxed tools | Autonomous actions with real money or credentials |

If your idea is borderline, write to the instructor through GitHub Issues before
collecting data. A rejected idea is cheaper than an unusable project.

## Evaluation questions reviewers will ask

1. Who is the user, and what decision does this system support?
2. What is the baseline, and why is your model better or more appropriate?
3. What data was excluded, and why?
4. Which slices fail, and who is harmed by those failures?
5. What happens when the model is wrong or uncertain?
6. How would you detect drift or abuse after deployment?
7. What would you need to change before real-world use?

Prepare answers with evidence, not adjectives.

## Related pages

- [Assessments and rubrics](assessments.md)
- [Learning paths](learning-paths.md)
- [Evaluation, security, and deployment](../syllabus/level-5-production.md)
