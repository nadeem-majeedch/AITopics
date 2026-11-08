# Assessments

Assessment in this course is designed to produce evidence of capability, not a
single exam score. Every module ends with a small artifact; the capstone combines
them into a defensible system.

!!! info "Question banks and solutions"
    Ready-to-use quizzes, code-reading exercises, debugging challenges, scenarios,
    lab assessments, and revision questions are in the
    [assessment bank](assessments/index.md). Answer keys live in a separate
    [solutions folder](assessments/solutions/index.md). None of it is graded or
    verified; the rubrics exist for self-assessment.

!!! note "Self-study and formal credit"
    This public course is built for self-study. Completing it does **not**
    automatically grant university credit or a certificate. Enrolled students
    follow their instructor's formal rules. Self-learners can use the rubrics to
    assess their own work and build a portfolio.

## Assessment philosophy

- **Applied over memorized.** You are assessed on systems you build and explain.
- **Evidence over claims.** Metrics, error analysis, and reproducible runs beat
  confident assertions.
- **Honest limitations.** A well-documented failure is better than a hidden one.
- **Process counts.** Data audits, experiment logs, and reflections are graded.
- **Ethics is engineering.** Licensing, privacy, bias, and security are part of
  correctness, not bonus points.

## Module assessment components

Each module is worth 100 points, distributed as follows.

| Component | Weight | What is assessed |
| --- | --- | --- |
| Knowledge check | 20% | Core concepts, definitions, and trade-offs |
| Guided notebook | 30% | Completion, correct execution, and interpretation |
| Independent lab | 40% | Application to a new problem against the lab brief |
| Reflection | 10% | Decisions, failures, limitations, and next steps |

### Knowledge check

A short set of questions or predict-the-output tasks. Some checks are
auto-gradable; others are self-scored with a published answer key. You should be
able to answer without notes before moving on.

### Guided notebook

The guided notebook is a worked example. Full credit requires:

- Running from a clean kernel without errors.
- Reproducing the stated result within a reasonable tolerance.
- Explaining at least two outputs in your own words.
- Recording environment, hardware, and seeds.

### Independent lab

The lab is the main assessment. It uses a different dataset, task, or constraint
from the guided notebook. The brief states the required deliverable, allowed
resources, and time budget.

### Reflection

A 200-400 word note covering:

- What you built and why.
- What you expected versus what happened.
- The most important failure you found.
- What you would change with more time or compute.
- Any AI assistance you used and how you verified it.

## Lab rubric

Use the same rubric for self-assessment and instructor review.

| Criterion | Weight | Excellent (4) | Meets (3) | Approaching (2) | Not yet (1) |
| --- | --- | --- | --- | --- | --- |
| Technical correctness | 30% | Works on unseen inputs, handles edge cases, code is clear | Works on the provided data and main cases | Partially works; errors in important cases | Does not run or does not address the task |
| Evaluation and evidence | 25% | Appropriate metrics, baselines, slices, uncertainty, error analysis | Correct metrics and a baseline | Metrics present but incomplete or misleading | No meaningful evaluation |
| Reproducibility | 15% | Clean environment, seeds, pinned versions, one-command or clear rerun | Reproducible with minor manual steps | Missing key settings or data steps | Cannot be reproduced |
| Data and ethics | 15% | License verified, privacy handled, bias/limitations documented | License and basic limitations documented | Weak documentation of data or risks | Ignores licensing, privacy, or obvious harms |
| Communication | 15% | Clear report, labeled figures, honest limitations, useful next steps | Understandable report with minor gaps | Hard to follow or missing key explanations | No usable explanation |

**Score interpretation**

| Points | Level | Meaning |
| --- | --- | --- |
| 90-100 | Excellent | Portfolio-ready; could be shown to an employer or supervisor |
| 80-89 | Proficient | Meets the module outcome; minor improvements possible |
| 70-79 | Passing | Core outcome achieved; revise weak evidence |
| Below 70 | Revise | Repeat the guided notebook and resubmit the lab |

## Capstone rubric

The capstone is assessed holistically. Each criterion is scored 1-4 and weighted.

| Criterion | Weight | What reviewers look for |
| --- | --- | --- |
| Problem framing and scope | 10% | A real, bounded problem; clear users; explicit non-goals |
| Data quality, licensing, and ethics | 15% | Legal data, documented provenance, privacy review, bias analysis |
| Technical implementation | 25% | Sound method, sensible baselines, clean code, appropriate model size |
| Evaluation and error analysis | 20% | Pre-registered metrics, held-out data, slices, failure taxonomy, uncertainty |
| Reproducibility and documentation | 15% | Environment, seeds, data scripts, model/dataset cards, runnable repo |
| Demo and communication | 10% | Working demo, clear report, honest limitations, effective presentation |
| Reflection and next steps | 5% | What was learned, what would change, realistic future work |

A capstone that makes an unsupported safety or performance claim cannot score
above "Approaching" on evaluation, regardless of the model's demo quality.

## Grading scale for instructor-led use

If this course is used in a formal setting, the following mapping is suggested:

| Percentage | Letter | Descriptor |
| --- | --- | --- |
| 90-100 | A | Excellent |
| 80-89 | B | Proficient |
| 70-79 | C | Satisfactory |
| 60-69 | D | Needs revision |
| Below 60 | F | Does not meet outcomes |

Instructors may adapt weights, but should publish changes before the module
begins.

## Resubmission and feedback

- Self-learners may revise a lab as many times as needed.
- Instructor-led cohorts should allow at least one resubmission for labs scoring
  below 70, with a documented improvement.
- Feedback should identify the weakest rubric criterion and one concrete next
  action.
- Regrade requests should point to the rubric, not to effort.

## Academic integrity

| Action | Status |
| --- | --- |
| Discussing concepts with classmates | Allowed |
| Sharing debugging tips | Allowed |
| Using AI to explain an error or review code | Allowed with disclosure |
| Copying another learner's notebook or report | Not allowed |
| Submitting AI-generated work as your own without disclosure | Not allowed |
| Fabricating metrics, citations, or dataset licenses | Not allowed |
| Using private or personal data without consent | Not allowed |

When in doubt, disclose. The reflection is the place to state what help you
received and how you verified it.

## Assessment evidence checklist

Before submitting any lab, confirm:

- [ ] The notebook runs from a clean kernel.
- [ ] Environment and hardware are recorded.
- [ ] Data source and license are stated.
- [ ] A baseline is included.
- [ ] Metrics match the task and are computed on held-out data.
- [ ] At least two failure cases are analyzed.
- [ ] Limitations and ethical risks are stated.
- [ ] No secrets, personal data, or unlicensed media are included.
- [ ] The reflection is written in your own words.

## Related pages

- [Capstone projects](projects.md)
- [How to study](how-to-study.md)
- [Quality standards](../planning/quality-standards.md)
