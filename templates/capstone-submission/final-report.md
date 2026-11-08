# Final technical report

**Project:** [replace]  
**Author:** [replace]  
**Date:** [replace]  
**Repository:** [replace]  
**One-command run:** `[replace]`  
**Data:** [replace: generated / downloaded / collected], licence: [replace]

Write 10-12 pages for a reader who has the repository but has not run it. Every
number must trace to a file your code wrote; name the file in the text or an
appendix. Delete a section only if it genuinely does not apply, and say so in
Section 3. The course's report template (`docs/course/projects/report-template.md`)
carries the same page budget.

## 1. Summary (five sentences)

[replace: the problem, the approach, the headline measured result with n and
uncertainty, the main limitation, and whether you would use it.]

## 2. Problem and users

[replace: the decision, who makes it now, the current process and its cost, and
why a simple rule is or is not sufficient.]

## 3. Scope and non-goals

**In scope:** [replace]  
**Out of scope:** [replace: include one thing a reader might assume it does]  
**Safety constraint:** [replace: the one thing the system must never do]

## 4. Data

[replace: origin, licence, size, labels, split construction, counts per class per
split, preprocessing, leakage checks, privacy, and known gaps. Reference the
dataset card rather than duplicating every row.]

## 5. Method

[replace: baseline, proposed approach, one rejected alternative and why. Include
the exact configuration and seed needed to rebuild the candidate.]

## 6. Evaluation design

[replace: metrics, frozen test construction, slices, thresholds, success
criteria, and what you did before opening the test set.]

## 7. Results

[replace: tables with counts and uncertainty. Separate validation from test and
teacher-forced from free-running. Do not summarise a table into a claim it does
not support.]

| Experiment | Configuration | Metric | n | 95% interval |
| --- | --- | ---: | ---: | --- |
| [replace] | | | | |

## 8. Error analysis

[replace: taxonomy with counts, at least two quoted examples, the worst slice,
and the condition that triggers the failure. Anecdotes illustrate; counts are the
evidence.]

## 9. Limitations and risks

[replace: what it cannot do, who could be harmed, the residual risk after
controls, and the measurement that would change your conclusion.]

## 10. Responsible-use controls

[replace: prohibited uses, privacy, access, approval boundaries, monitoring, and
rollback. For a system that acts, state the blast radius of its most dangerous
permitted action.]

## 11. Reproducibility

[replace: environment, dependencies, seeds, data command, manifest check,
training command, evaluation command, runtime, and artifact reload. Point to
`reproducibility.md`.]

## 12. Reflection

[replace: what you expected, what happened, what you would change, and how AI
assistance was used and checked.]

## References

- [replace: dataset citation and licence URL]
- [replace: base model or library citation]
- [replace: method paper, if any]
- [replace: course lesson or brief used]

## Appendix A - Full metric tables

[replace: the complete per-class, per-slice, and robustness tables, plus the
command that wrote them.]

## Appendix B - Experiment log

[replace: a readable summary of `experiments.csv`, including rejected runs and why
they were rejected.]

## Appendix C - Failure examples

[replace: full inputs and outputs for the failures discussed in Section 8. Do not
edit the model's output.]

## Appendix D - Audit or manifest excerpts

[replace: for P12, an audit excerpt and a tamper-test failure. For other projects,
the dataset manifest check and the artifact checksum.]
