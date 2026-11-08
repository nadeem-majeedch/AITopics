# Capstone submission package

```markdown
**Projects:** [Index](index.md) · [Report template](report-template.md) · [Completion checklist](completion-checklist.md) · **Submission package**
```

Every capstone submits the same ten files, whatever the project. Copy the
reusable scaffold from `templates/capstone-submission/` in the course repository
into your project as `submission/`, fill each file in, and keep it next to the
code that produced the numbers.

The package is deliberately plain Markdown and CSV so it diffs in Git and does
not depend on a notebook, a GPU, or a service. The mandatory path for every
project runs on CPU.

## Directory structure

```text
capstone-pXX/
  README.md
  requirements.txt
  configs/
  data/
  src/
  tests/
  outputs/                       # metrics, predictions, logs
  artifacts/                     # model or adapter (checksum, not usually committed)
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
```

`submission/README.md` is the package's entry point. The repository root
`README.md` may be the same file or a short pointer to it; do not maintain two
different descriptions of the project.

## What each file is for

| File | Contents | First needed at |
| --- | --- | --- |
| `project-scope.md` | decision, users, objectives, scope, metric, data contract, risk register | Checkpoint 1 |
| `dataset-card.md` | origin, licence, size, labels, preprocessing, privacy, limitations | Checkpoint 1 |
| `experiments.csv` | one row per run: id, code and data digest, config, seed, model, metrics, runtime, decision | Checkpoint 2 |
| `model-card.md` | intended use, architecture, training, evaluation, limitations, risks | Checkpoint 2 draft, checkpoint 3 final |
| `evaluation-report.md` | frozen-test metrics with n and intervals, slices, failure cases, interpretation | Checkpoint 3 |
| `threat-and-responsible-use-review.md` | privacy, safety, fairness, misuse, security controls, residual risk | Checkpoint 3 |
| `reproducibility.md` | environment, dependencies, seeds, commands, expected outputs, reload | Checkpoint 2, verified at 3 |
| `README.md` | install, run, expected outputs, overview, limitations | Checkpoint 2 |
| `release-notes.md` | version, evidence summary, known limitations, monitoring, rollback, decision | Checkpoint 3 |
| `final-report.md` | the 10-12 page technical report built from the files above | Checkpoint 3 |

Use the [report template](report-template.md) for the page budget and prose
guidance. `submission/final-report.md` is the same structure with prompts you
replace.

## Checkpoints

The authoritative gates are in the
[capstone lab](../../lessons/capstone/labs/lab-1-capstone-package.md) and the
[assessment](../../lessons/capstone/assessment.md). The package maps to them as
follows.

### Checkpoint 1 - scope and data (20%)

Submit `project-scope.md` and `dataset-card.md`.

- The decision is stated in one sentence, with a metric and a threshold.
- False positives and false negatives have a stated cost.
- The split unit matches deployment, and every class has test examples.
- The risk register has at least six rows with mitigations and owners.
- Licences and a data-generation or download command are recorded.

### Checkpoint 2 - build and evidence (35%)

Submit a working path, `experiments.csv`, `reproducibility.md`, and a draft
`model-card.md` and `README.md`.

- Data to one prediction runs from a clean checkout.
- Baseline and candidate use the same split and preprocessing.
- One controlled comparison is reported in full, including a rejected change.
- Every run in `experiments.csv` has a seed, config, data digest, and decision.
- The manifest or dataset check passes, and a tamper test fails.

### Checkpoint 3 - evaluation, security, packaging (45%)

Submit `evaluation-report.md`, the final `model-card.md`,
`threat-and-responsible-use-review.md`, `release-notes.md`, and
`final-report.md`.

- The test set and scoring rule were frozen before the final run.
- Every headline metric has n, and an interval or a small-n caveat.
- At least one slice and the inspected failures are reported.
- The threat review states residual risk and an owner.
- The release decision follows the evidence, with monitoring and a rollback trigger.
- A second person can reproduce the headline result within its interval.

## Final package checklist

- [ ] All ten files exist and none still contains a `[replace ...]` placeholder.
- [ ] Every number in the report traces to a file under `outputs/` or
      `artifacts/`, and that file is named.
- [ ] Dataset and model licences are exact strings with URLs.
- [ ] Seeds, environment, and the one-command rerun are recorded.
- [ ] Dataset manifest or generator check passes; the tamper test failed as expected.
- [ ] Test metrics include n and uncertainty; no test number is used for tuning.
- [ ] Per-class or per-slice results are shown where the brief requires them.
- [ ] Failure analysis has categories with counts and at least two quoted examples.
- [ ] Unsuccessful experiments are in `experiments.csv` with a reason, not deleted.
- [ ] Optional paths (GPU, hosted API, pretrained model) are labelled unverified
      if they were not run.
- [ ] Prohibited uses and residual risks are stated.
- [ ] `README.md` reproduces the headline run on CPU without a GPU.
- [ ] The reflection discloses AI assistance and how the output was checked.

## Reporting unsuccessful experiments

An honest negative result is a valid result. Report it in this shape:

1. **What you expected** and why, in one or two sentences.
2. **What you ran**: experiment id, config, seed, data digest, and command.
3. **What happened**: the metric or failure mode, with n and a run count.
4. **What you checked** before concluding it was the method and not a bug:
   data, labels, tokenizer or preprocessing, metric code, and a smoke test.
5. **What it means**: the scope of the claim, and the condition that would
   change it.
6. **What you did next**: the decision recorded in `experiments.csv`.

Do not tune a threshold until a failure disappears, hide a failed run, or
describe a synthetic, scripted, or mock result as real-world model capability.
An acceptable failure analysis names the failure, quantifies it, explains the
most likely cause with evidence, and states what would falsify that explanation.

## Project-specific requirements

Each brief adds rules for these files:

- [P03 - LoRA fine-tuning](p03-lora-finetune.md#submission-package-and-p03-requirements):
  separate mechanics from generation quality, compare base/full SFT/LoRA, quote
  failures, and mark the pretrained path optional and unverified.
- [P06 - image classifier](p06-image-classifier.md#submission-package-and-p06-requirements):
  state the synthetic single-renderer limitation, run the dataset check, and
  report per-class intervals, calibration, and robustness.
- [P12 - tool-using agent](p12-tool-using-agent.md#submission-package-and-p12-requirements):
  separate scripted policy tests from model tests, keep the malformed-call
  control, report gated and ungated attacks, and report fail-closed results.
