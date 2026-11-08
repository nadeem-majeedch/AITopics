# Student usability audit

Audit date: **2026-11-08**. Scope: whether a student can find the course, choose
a path, open a lesson, run the matching notebook, and complete the practical
work and assessment without guessing a URL.

## Verdict

**The built course is navigable and usable for review. It is not yet verified as
a public student experience.** All required paths resolve in the local site, but
GitHub Pages is not live and no human student pilot was completed.

## Paths exercised

| Student task | Result |
| --- | --- |
| Start at the course home | Pass in the built site |
| Choose a beginner, intermediate, or advanced path | Pass: the syllabus paths are present and linked |
| Open a module lesson | Pass: all 18 modules have lesson files |
| Open the matching notebook | Pass: 26 of 26 notebooks are directly linked |
| Find a lab or project brief | Pass: 52 briefs are present |
| Find an assessment | Pass: 21 assessments are present |
| Move between notebooks | Pass: previous/next links resolve after the M15/M16 fix |
| Search the site | Available in the MkDocs Material theme |
| Open the notebook source | Pass: `include_source: true` copies the `.ipynb` beside the rendered page |

The canonical entry points are the repository README, the course home, the
[Notebook Library](../notebook-library.md), and the lessons index. The library is
the shortest route when a student knows the topic but not the module number.

## Recommended first session

1. Read the course home and choose a path.
2. Open F01 and follow its notebook guide.
3. Run `notebooks/foundations/f01_python_ai.ipynb` on a CPU.
4. Complete the F01 lab and knowledge check.
5. Continue through F03-F13 before starting an applied module.

For an applied learner, M09-M10 (chatbots/RAG), M11-M12 (vision), M13 (speech),
and M14 (video) each have a runnable notebook, a section index, labs, and an
assessment.

## Evidence that the paths work

- `python scripts/check_docs_links.py` reports 295 Markdown files with no broken
  links, anchors, or navigation entries.
- `python -m mkdocs build --strict -d site` completes with zero warnings and
  produces 322 pages.
- `python scripts/check_docs_links.py --site site` reports no broken built-site
  links and no absolute URLs outside `/AITopics/`.
- `python scripts/check_course_inventory.py` confirms 18 modules, 105 lesson
  files, 26 notebooks, 52 labs/project briefs, and 21 assessments.

## Usability limitations

- No human student pilot, think-aloud session, or classroom use was completed.
  The agent-simulated capstone is not a substitute for a student.
- The public Pages URL returns 404, so navigation has not been checked on the
  deployed origin or on a phone.
- Search relevance, reading level, time estimates, and mobile layout were not
  measured with students.
- GPU and Colab paths are documented but not executed. A student without a local
  CPU environment may need the Colab instructions, which are unverified.
- The 20 legacy notebooks have less uniform section structure than M09-M14.
- Synthetic exercises can produce high scores that do not predict real-world
  performance; the notebooks now state this explicitly.

## Release use

This audit supports deployment review, not a claim that the course is already
student-ready in public. After deployment, repeat the path checks on the live
`/AITopics/` origin and run a small human pilot before making that claim.
