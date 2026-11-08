# Capstone report template

```markdown
**Projects:** [Index](index.md) · [Completion checklist](completion-checklist.md) · **Report template**
```

A 10-12 page technical report, plus appendices. Write it for a reader who has your
repository but has not run it. Every number must come from a file your code wrote;
if you cannot point to the file, the number does not go in the report.

This structure is also provided as a fill-in file at
`templates/capstone-submission/final-report.md` in the course repository. Submit
that filled file; use this page for the page budget and prose guidance.

!!! note "Self-study use"
    There is no submission portal and no grader. This template exists so your own
    report has the sections a reviewer would look for. Keep it in `reports/report.md`
    next to the code.

## Structure and page budget

| Section | Pages | What it must contain |
| --- | --- | --- |
| 1. Title, summary, links | 0.5 | Project, your name, date, repository, demo command |
| 2. Problem and users | 1 | Decision supported, who uses it, why the current process fails |
| 3. Scope and non-goals | 0.5 | In scope, out of scope, one safety constraint |
| 4. Data | 1.5 | Source, licence, size, labelling, splits, known gaps |
| 5. Method | 1.5 | Baseline, proposed approach, one rejected alternative and why |
| 6. Evaluation design | 1 | Metrics, test construction, slices, thresholds, success criteria |
| 7. Results | 2 | Tables with counts and uncertainty; measured, not summarised |
| 8. Error analysis | 1.5 | Taxonomy with counts, examples, worst slice |
| 9. Limitations and risks | 1 | What it cannot do, who could be harmed, residual risk |
| 10. Responsible-use controls | 0.5 | Prohibited uses, privacy, access, monitoring |
| 11. Reproducibility | 0.5 | Environment, seeds, commands, runtime |
| 12. Reflection | 0.5 | Decisions, failures, what you would change |
| Appendices | as needed | Full metric tables, annotation guide, prompts, audit excerpts |

Delete sections that genuinely do not apply, and say so in section 3 rather than
leaving an empty heading.

## Skeleton

```markdown
# [Project title]

**Author:** [name]  
**Date:** [YYYY-MM-DD]  
**Repository:** [path or URL]  
**Run:** `[one command]`  
**Data:** [generated / downloaded / collected], licence: [string]

## 1. Summary

[Five sentences: the problem, the approach, the headline measured result with its
uncertainty, the main limitation, and whether you would use it.]

## 2. Problem and users

[The decision the system supports. Who makes that decision now, how, and what it
costs them. One paragraph on why a simple rule is insufficient - or why it might be
sufficient, if that is what you found.]

## 3. Scope and non-goals

**In scope:** [three to five capabilities]

**Out of scope:** [three to five exclusions, with the reason]

**Safety constraint:** [one constraint that protects users or data]

## 4. Data

| Item | Value |
| --- | --- |
| Source | [generator, URL, or collection method] |
| Licence | [exact string] + URL |
| Size | [rows / images / clips / hours] |
| Labels | [who labelled, guide, agreement] |
| Splits | [how, sizes, leakage checks] |
| Personal data | [none, or what and how it is protected] |
| Known gaps | [what the data does not represent] |

[One paragraph on what you would collect next and why.]

## 5. Method

[Baseline first, then the proposed approach. Include a table comparing the
alternatives you considered and the reason for the choice. State hyperparameters
that matter and where they came from (validation, not test).]

## 6. Evaluation design

| Item | Plan |
| --- | --- |
| Primary metric | [metric and why] |
| Secondary metrics | [metrics] |
| Test set | [size, construction, when it was opened] |
| Slices | [groups and minimum counts] |
| Thresholds | [how chosen, from what data] |
| Success criterion | [number set before the final run] |

[State any change to this plan after it was written, and why.]

## 7. Results

[One table per experiment. Include n, the point estimate, and an interval or a
clear statement that n is too small. Show the baseline in the same table as the
proposed method. Do not average over slices that behave differently.]

## 8. Error analysis

[Taxonomy table: category, count, share, one example. Then two or three quoted
failures. Then the worst slice and what it implies.]

## 9. Limitations and risks

[Numbered list. Each item: what fails, under what conditions, who is affected, and
how you would detect it. "Small dataset" is not a limitation unless you say what
it prevents you from claiming.]

## 10. Responsible-use controls

[Prohibited uses, data retention, access, human oversight, monitoring, and the
residual risk you accept.]

## 11. Reproducibility

[Python and library versions, hardware, seeds, data generation command, training
command, evaluation command, wall-clock time, and the checksum of the data
manifest.]

## 12. Reflection

[300-500 words: what you expected, what happened, the most important failure, what
you would change with more time, and what AI assistance you used and how you
verified it.]
```

## Writing rules

1. **Numbers have owners.** Every table has a caption naming the file it came from,
   for example `outputs/metrics.json` produced by `src/evaluate.py`.
2. **Say what a metric does not measure.** AUC does not measure calibration; WER
   does not measure meaning; mAP does not measure counting accuracy.
3. **Separate measured from expected.** If a number is a target, a paper's result,
   or an estimate, label it in the sentence, not in a footnote.
4. **No naked adjectives.** "Robust", "fast", and "accurate" need a number, a
   comparison, or deletion.
5. **Quote failures verbatim.** A paraphrase of a bad output is less convincing than
   the output.
6. **Counts with percentages.** "84% of 19 clips" beats "84%".
7. **One headline result.** If everything is a headline, nothing is.

## Evidence appendix

Include, in this order:

- [ ] Full metrics JSON, pretty-printed.
- [ ] Confusion matrix or per-class table with counts.
- [ ] The evaluation script's console output for the final run.
- [ ] Dataset manifest hash and the command that verifies it.
- [ ] The annotation guide, if you annotated anything.
- [ ] Audit-log excerpt for agent or action projects.
- [ ] Prompts and decoding configuration for generative projects.

## Common report failures

| Failure | Why it loses marks | Fix |
| --- | --- | --- |
| Results table without a baseline | No evidence the model is worth using | Add the baseline row |
| Test score reported after tuning on test | The number is optimistic and unusable | Report validation and one final test run |
| "Works well" with no metric | Unfalsifiable | Replace with a measured statement |
| Limitations copied from a template | Not specific to your system | Name the failure and its trigger |
| No licence for the data | The work cannot be shared | Record the licence or remove the data |
| Reflection describes the code | Reflection is about decisions | Focus on choices, surprises, and changes |
| 30 pages of screenshots | Length is not evidence | Move to an appendix, keep the argument tight |

---

**Related:** [Completion checklist](completion-checklist.md) · [Assessment bank](../assessments/index.md) · [Project index](index.md)
