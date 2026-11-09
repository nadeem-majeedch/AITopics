# Assessment bank

```markdown
**Assessments:** **Overview** · [Quizzes](quiz-bank.md) · [Conceptual](conceptual.md) · [Code reading](code-reading.md) · [Debugging](debugging.md) · [Scenarios](scenarios.md) · [Lab assessments](lab-assessments.md) · [Evaluation exercises](evaluation-exercises.md) · [Revision](revision.md) · [Solutions](solutions/index.md)
```

Eight banks of questions and tasks that test whether you understand the material,
not whether you can retype a notebook. Answers are in a separate
[solutions](solutions/index.md) folder so you can attempt the work first.

!!! warning "No grading, no certificate"
    These are self-study instruments. Nothing in this section is marked, verified,
    moderated, or graded by the course author, and completing it confers no credit,
    certificate, or university qualification. If you study through an institution,
    your instructor's rules replace everything here.

## What each bank is for

| Bank | Format | Volume | Best used |
| --- | --- | --- | --- |
| [Chapter quizzes](quiz-bank.md) | Multiple choice and one-line answers | 6 chapters x 6 questions | At the end of each chapter, closed-book, 10 minutes |
| [Conceptual questions](conceptual.md) | Written explanations, 3-6 sentences | 20 questions | After a section, to check the mental model |
| [Code reading](code-reading.md) | Read a snippet, predict or critique | 7 exercises | Before writing similar code yourself |
| [Debugging](debugging.md) | Broken code plus a symptom | 7 challenges | When you have written enough code to recognise the failures |
| [Scenarios](scenarios.md) | Decisions with justification | 8 scenarios | After the evaluation and safety material |
| [Lab assessments](lab-assessments.md) | Timed practical tasks with evidence requirements | 6 assessments | As a substitute for a module lab, or a rehearsal |
| [Evaluation exercises](evaluation-exercises.md) | Numeric, hand-computable | 7 exercises | Before trusting any metric you compute |
| [Revision](revision.md) | Short answers across the course | 30 questions | In the last week, closed-book |

Each bank states its own marking guidance. They all use the same four-level scale
so your self-assessment is comparable across the course.

## How to use the banks honestly

1. **Attempt before reading solutions.** Write your answer, then open the solution
   file. Reading a solution and thinking "yes, I knew that" is not evidence.
2. **Score against the descriptors, not against effort.** A partial answer that
   names the mechanism but misses the consequence is "Approaching", not "Meets".
3. **Redo the misses later.** Wait at least two days. If you cannot redo it, you
   learned the answer, not the idea.
4. **Keep a log.** `progress.md` with date, bank, score, and the items you missed is
   more useful than a percentage.
5. **Do not treat a high quiz score as mastery.** Quizzes check recall. The labs,
   scenarios, and capstone check whether you can build and defend something.

## Self-assessment scale

| Level | Points | Descriptor |
| --- | --- | --- |
| Excellent | 4 | Correct, complete, and explains the consequence; names a failure mode unprompted |
| Meets | 3 | Correct with a complete mechanism; minor omissions |
| Approaching | 2 | Partly correct; right vocabulary, incomplete reasoning |
| Not yet | 1 | Wrong, or restates the question without a mechanism |

Convert to a percentage with `(points / (4 x items)) x 100`. The bands below are
for your own tracking only.

| Percentage | Reading |
| --- | --- |
| 90-100 | Ready to use this material in a project |
| 80-89 | Solid; revisit the specific misses |
| 70-79 | Core idea present, reasoning thin; reread the linked module |
| Below 70 | Reread the module and redo the bank before moving on |

## Coverage map

| Course area | Quiz chapter | Conceptual | Code reading | Debugging | Scenario | Lab assessment | Evaluation | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [F01-F05 data and splits](../../lessons/f01-python-ai/index.md) | 1 | 1-5 | 1, 3 | 1, 4 | 2 | 1 | 1 | 1-6 |
| [F06-F10 classical ML](../../lessons/f06-eda/index.md) | 2 | 6-10 | 4 | 2, 3 | 1 | 1 | 1, 2 | 7-12 |
| [F11-F13 neural networks](../../lessons/f11-neural-networks/index.md) | 3 | 11-13 | 2 | - | 3 | - | 4 | 13-17 |
| [Conversational AI and RAG](../../lessons/chatbots-rag/index.md) | 4 | 14-16 | 6 | 6 | 4 | 2 | 6 | 18-22 |
| [Vision, speech, video](../../lessons/computer-vision/index.md) | 5 | 17-18 | 5, 7 | 5, 7 | 5 | 3, 4, 5 | 2, 3 | 23-27 |
| [Evaluation, security, production](../../lessons/production/index.md) | 6 | 19-20 | - | - | 6-8 | 6 | 2, 4, 5, 7 | 28-30 |

## Advanced assignments

Some items are marked **advanced**. They ask you to justify, not just compute:

- model selection against a stated baseline and cost;
- data quality, including labelling, coverage, and licence;
- fine-tuning decisions versus prompting, retrieval, or a simpler model;
- evaluation methodology, including splits, slices, and uncertainty;
- limitations and who is harmed by them;
- responsible-use controls: access, approval, monitoring, and refusal.

An advanced answer that lists controls without saying what they prevent scores
"Approaching" at best. The solutions show the standard expected: a claim, the
evidence for it, and the condition under which it fails.

## Academic integrity and AI assistance

| Action | Status |
| --- | --- |
| Discussing a question with a peer | Allowed |
| Using documentation to check an API | Allowed |
| Using an AI assistant to explain an error | Allowed, disclose it |
| Asking an AI assistant for the answer, then writing it as yours | Not allowed |
| Copying a solution file into your submission | Not allowed; the solutions are for checking |
| Fabricating a metric or a citation | Not allowed |

The point of the banks is diagnostic. Cheating them cheats only your own map of what
you know.

## Related pages

- [Course assessments and rubrics](../assessments.md) - module weights and the capstone rubric
- [Capstone projects](../projects/index.md) - where the skills are actually used
- [How to study](../how-to-study.md) - spacing, retrieval practice, and logs
