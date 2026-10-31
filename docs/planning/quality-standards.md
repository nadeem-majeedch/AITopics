# Quality standards

These standards define what "done" means for course content. They apply to
lessons, notebooks, labs, datasets, models, assessments, and the site.

The goal is not perfection. It is content that a student can run, understand,
and trust, and that a maintainer can update without reverse-engineering it.

## Definition of done for a module

A module is publishable only when all of the following are true.

- [ ] Syllabus plan is updated with final objectives, hours, and hardware.
- [ ] Lesson page follows the module template and is linked in navigation.
- [ ] Guided notebook runs top-to-bottom from a clean kernel.
- [ ] Notebook records environment, hardware, seeds, data source, and runtime.
- [ ] Notebook has been executed on the supported environments.
- [ ] Independent lab brief states task, constraints, deliverables, and rubric.
- [ ] Dataset card includes source, license, checksum, and limitations.
- [ ] Model card is included if a model is distributed or recommended.
- [ ] Knowledge check and answer key exist (or are scheduled before release).
- [ ] Technical review is complete.
- [ ] Pedagogical review is complete.
- [ ] License and ethics review is complete.
- [ ] Links, downloads, and commands are verified.
- [ ] `mkdocs build --strict` passes.
- [ ] Content inventory is updated.
- [ ] No secrets, personal data, unlicensed media, or large binaries are tracked.

## Module template

Lesson pages should use this structure unless there is a documented reason not
to.

```markdown
# MXX - Module title

One-paragraph purpose.

**Hardware:** CPU-only | **Time:** X hours | **Prerequisite:** MXX

## Learning objectives
## Why this matters
## Core concepts
## Worked example
## Guided notebook
## Common failure modes
## Independent lab
## Assessment rubric
## Deliverables
## Reflection questions
## Further reading
## Next step
```

The lesson explains; the notebook demonstrates; the lab assesses. Do not put the
entire lab solution in the lesson.

## Notebook standards

### Header

The first Markdown cell must contain:

- Module code and title.
- Hardware label and estimated runtime.
- Prerequisites.
- Dataset name and license.
- Last execution date.
- Environment summary (Python, key package versions).
- A one-sentence purpose.

### Structure

1. Setup and imports.
2. Configuration (paths, seeds, device).
3. Data loading with a documented source.
4. Core demonstration, split into small steps with Markdown explanations.
5. Exercises or "try this" prompts.
6. Evaluation and interpretation.
7. Cleanup (free GPU memory, close files).
8. Next step and links.

### Data and reproducibility

- Use a small dataset or a documented subset.
- Download only from official sources; verify a checksum when possible.
- Store raw data outside Git, under `data/` or the platform's temporary storage.
- Set seeds in one place and explain which libraries are covered.
- Record versions and hardware in the output.
- Avoid hidden state: restart and run all before submission.
- Pin dependencies in the notebook header or a linked requirements file.

### Outputs

- Keep outputs small and meaningful.
- Clear huge logs, full datasets, base64 images, and video dumps before commit.
- Prefer a few representative plots over dozens.
- Never include personal data, API keys, or private paths in outputs.
- Ensure outputs do not contradict the narrative.

### Hardware labels

Use exactly one of: **CPU-only**, **CPU or GPU**, **GPU recommended**, **GPU
required**. If a GPU is required, provide a free-tier path or state clearly that
the lab cannot be completed without one.

### Code

- Use `pathlib` for paths.
- Avoid hard-coded absolute paths and usernames.
- Keep cells short enough to read.
- Do not hide essential logic in a helper without explaining it.
- Use comments only where the reason is non-obvious.
- Do not print secrets or environment variables that may contain them.

### Colab compatibility

- Provide a setup cell that installs only what is missing.
- Avoid local-only paths; use a configuration cell.
- Do not assume Google Drive is mounted.
- Warn about session limits and checkpointing.
- Test at least once on Colab before marking the notebook published.

## Code standards

- Python 3.11 or 3.12.
- Format and lint with Ruff.
- Type hints for public functions in `src/aitopics_course/`.
- Prefer standard library and small dependencies.
- No wildcard imports.
- No global mutable configuration.
- Raise specific exceptions with actionable messages.
- Never swallow exceptions silently.
- Do not commit generated code without review.

## Testing standards

| Test type | Scope | Runs in CI |
| --- | --- | --- |
| Unit tests | Shared package functions, metrics, seeding, paths | Yes |
| Schema tests | Dataset and model card required fields | Yes |
| Docs build | `mkdocs build --strict` | Yes |
| Link checks | Internal links; external with allowlist | Yes or scheduled |
| Notebook smoke | Fast subset, tiny data, no GPU | Yes |
| Full notebook execution | All published notebooks, stated hardware | Scheduled, recorded |
| GPU tests | Training and inference labs | Manual or scheduled GPU runner |

- Default CI must not require a GPU, paid API, or large download.
- Network-dependent tests must be marked and skippable.
- A notebook is not "tested" because it was opened once. It must be executed
  from a clean kernel.
- Record the execution result, environment, and date.

## Dataset standards

Every dataset card must state:

| Field | Requirement |
| --- | --- |
| Name and version | Exact identifier and retrieval date |
| Source | Official URL or citation |
| License | Exact license and any restrictions |
| Size and format | Files, rows, classes, resolution, duration |
| Fields | Schema and label definitions |
| Splits | How train/validation/test are defined |
| Collection method | Who collected it, how, and when |
| Consent | Status for human-derived data |
| Personal data | Presence and handling |
| Known bias | Coverage gaps and label issues |
| Limitations | What the dataset cannot support |
| Checksum | Hash for the downloaded artifact |
| Redistribution | Whether raw data may be committed (usually no) |

Rules:

- Do not use "publicly available" as a license.
- Research-only and non-commercial datasets must be marked clearly.
- Do not infer sensitive attributes.
- Do not commit raw data unless the license explicitly permits it.
- Provide a download script rather than a mirror when possible.
- Remove or blur personal data in examples.

## Model standards

Every recommended or fine-tuned model needs a model card with:

- Base model, version, and license.
- Intended use and users.
- Out-of-scope uses.
- Training data summary and license.
- Method and hyperparameters.
- Evaluation data, metrics, and slices.
- Known failure modes.
- Ethical and safety risks.
- Hardware and runtime.
- Contact and attribution.

Do not claim a model is "safe", "accurate", or "production-ready" without
evidence and scope.

## Assessment standards

- Rubrics are published before the lab.
- Criteria map to learning objectives.
- Point weights sum correctly.
- Sample submissions or anchor examples exist for reviewer calibration.
- Labs state time and compute budgets.
- Labs are solvable with the taught material and allowed resources.
- Answer keys and reference solutions are maintainer-only by default.
- AI assistance rules are explicit.
- Accessibility accommodations do not change the learning outcome.

## Accessibility and inclusive language

- Use a logical heading hierarchy; do not skip levels.
- Add alt text to images and diagrams.
- Explain Mermaid diagrams in text.
- Do not rely on color alone to convey meaning.
- Provide captions or transcripts for audio and video.
- Use descriptive link text, not "click here".
- Keep tables narrow enough to read on mobile.
- Prefer short sentences and define jargon on first use.
- Use inclusive examples and avoid stereotypes.
- Avoid unnecessary personal data in examples.

## Security and responsible AI

- No real credentials, tokens, or personal data in notebooks or outputs.
- No instructions for malware, credential theft, evasion, or harmful surveillance.
- No face recognition, identity inference, or covert tracking.
- No non-consensual voice cloning or impersonation.
- Agent labs use sandboxed tools with no spending or destructive actions.
- Prompt-injection examples are contained and defensive.
- Video and audio labs include privacy impact assessments.
- Dependencies are pinned and reviewed.
- Generated content is labeled and licensed appropriately.

If a lesson could be misused, add a clear scope and mitigation note, and consult
the instructor before publishing.

## Style guide

- Use US English: `license`, `labeled`, `modeling`, `behavior`.
- Use title case for headings, sentence case for table cells.
- Use "you" for the learner and "we" for the course.
- Prefer active voice and short paragraphs.
- Define acronyms on first use (ASR, RAG, LoRA, mAP, WER).
- Use code formatting for paths, commands, and identifiers.
- Do not use emojis in course content.
- Do not use hype: "revolutionary", "magic", "guaranteed".
- Attribute quotations and third-party figures.
- Link to primary sources where possible.
- Keep line lengths readable; Markdown wraps visually.

## Review checklist

### Technical

- [ ] Code runs from a clean environment.
- [ ] Versions and hardware are recorded.
- [ ] Data source and checksum are correct.
- [ ] Metrics are computed on held-out data.
- [ ] Claims match the evidence.
- [ ] Failure modes are documented.
- [ ] No secrets or personal data.

### Pedagogical

- [ ] Objectives are measurable.
- [ ] Prerequisites are accurate.
- [ ] The notebook prepares the learner for the lab.
- [ ] The lab is achievable within the time budget.
- [ ] The rubric matches the objectives.
- [ ] Explanations define jargon.
- [ ] Exercises have a clear purpose.

### Ethics and licensing

- [ ] Dataset license is verified and compatible with use.
- [ ] Model license and acceptable-use policy are verified.
- [ ] Privacy and consent are documented.
- [ ] Harmful or surveillance uses are excluded.
- [ ] Third-party assets are attributed.
- [ ] No unlicensed media is embedded.

## Review workflow

1. **Author self-check** against this page.
2. **Technical review** by someone who can run the notebook.
3. **Execution record** on Windows 11 and Colab or the stated hardware.
4. **Pedagogical review** by the instructor or an experienced TA.
5. **Ethics and license review** for data, models, and applications.
6. **Publish** only after all checks pass; update navigation and inventory.

## Maintenance cadence

| Frequency | Task |
| --- | --- |
| Every change | Docs build, link check, targeted notebook execution |
| Monthly | Dependency review; issue triage |
| Quarterly | Full notebook execution audit; dataset link and license check |
| Annually | License review; roadmap revision; accessibility audit |
| Per release | Changelog, tag, known-limitations update |

Content that cannot be reproduced is marked "unverified" rather than silently
left online.
