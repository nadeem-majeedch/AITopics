# Templates

These templates keep lessons, notebooks, labs, and project specifications
consistent. They are written for contributors, but students can reuse the project
specification template for a capstone proposal.

| Template | Use it for | Copy to |
| --- | --- | --- |
| [Chapter template](chapter.md) | The lesson page of a module | `docs/lessons/<module>/index.md` |
| [Notebook guide template](notebook.md) | Run instructions and expected output for a notebook | `docs/lessons/<module>/notebook.md` |
| [Lab template](lab.md) | An independent lab brief and rubric | `docs/lessons/<module>/lab.md` |
| [Assessment template](assessment.md) | Knowledge check, scoring, reflection, and completion checklist | `docs/lessons/<module>/assessment.md` |
| [Project specification template](project.md) | A capstone proposal or project brief | `projects/<project-name>.md` |

## How to use a template

1. Copy the template to the destination path. Do not edit the template itself
   for a single module.
2. Replace every prompt in square brackets. Delete sections that do not apply.
3. Keep the module header, hardware label, and navigation strip.
4. Use relative links to real files. Do not link to a page that does not exist.
5. Add the page to `mkdocs.yml` under the correct section.
6. Execute the notebook from a clean kernel and record the environment.
7. Run `mkdocs build --strict` and fix every warning.
8. Update the module status in the syllabus, lessons index, and planning docs.

The full publishing rules are in
[Course conventions](../../course/course-conventions.md) and
[Quality standards](../../planning/quality-standards.md).

## Definition of done for a new lesson

- [ ] Lesson, notebook guide, lab, and assessment pages exist.
- [ ] Every link and anchor resolves.
- [ ] The notebook runs top-to-bottom on at least one supported environment.
- [ ] Expected output and troubleshooting are based on a real run.
- [ ] The lab has constraints, deliverables, a rubric, and a privacy check.
- [ ] Hardware labels are accurate.
- [ ] No placeholder text remains.
- [ ] The site builds with `mkdocs build --strict`.
- [ ] The syllabus and status pages reflect the new state.

## Writing style

- Address the student directly as "you".
- Explain a term the first time you use it.
- Prefer a concrete command or example over an abstract description.
- State the hardware and time cost before the work.
- Separate what is required from what is optional.
- Do not claim a result, test, or build passed unless it was actually run.
- Do not promise certification, academic credit, or employment outcomes.
