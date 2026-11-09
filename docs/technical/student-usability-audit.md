# Student usability audit

Audit date: **2026-11-09**. Scope: whether a student can start at the course
home, choose a learning path, open a lesson, reach the matching notebook, complete
the lab, and find the assessment or capstone instructions without guessing a URL.

## Verdict

**PASS for the local built site; UNVERIFIED for public use.** All eight recorded
journeys resolve in the built output. GitHub Pages is 404, no human student pilot
was completed, and no browser interaction, mobile layout, or search-relevance
study was performed.

## Journeys exercised

These are static journey checks against the generated HTML: the page exists, the
expected link is in the page, and the target file exists. The table reports what
was actually checked.

| # | Student journey | Result |
| ---: | --- | --- |
| 1 | Beginner: home → F01 → notebook guide → lab → assessment | **PASS** |
| 2 | Beginner: open the corresponding F01 notebook page | **PASS**; `notebooks/foundations/f01_python_ai.ipynb` is rendered and downloadable |
| 3 | Complete a lab and find its assessment | **PASS** for F01 and the applied sections; 21 unique assessments exist |
| 4 | Basic-Python learner follows the ML path | **PASS**; F03 page → notebook → lab/assessment, with links to F04-F10 |
| 5 | LLM fine-tuning path | **PASS**; M06 page → notebook → Lab 1 → assessment |
| 6 | Computer-vision path | **PASS**; M11 page → notebook → Lab 1 → assessment |
| 7 | AI-agent path | **PASS**; M15 page → notebook → Lab 1 → assessment |
| 8 | Capstone specifications and submission | **PASS**; capstone index → lab, and project index → P01 / submission package |

Additional checks:

| Check | Result |
| --- | --- |
| Home → Datasets and Resources | **PASS** |
| Home → Course roadmap → study schedules anchor | **PASS** |
| Home → Notebook Library → all 26 notebooks | **PASS** |
| Applied lab brief reachable from its section index | **PASS** |
| `labs/` top-level README points to the real brief | **PASS** (repository view, not the MkDocs site) |
| Source links, anchors, and nav targets | **PASS: 296 files, 0 broken** |
| Built-site links and `/AITopics/` prefix | **PASS: 323 pages** |
| Strict MkDocs build | **PASS: 0 warnings** |

The static target check included these exact transitions:

- `site/index.html` → `site/lessons/f01-python-ai/index.html`
- F01 → `lessons/f01-python-ai/notebook/`, `lab/`, `assessment/`
- F03 → `notebook/`, `assessment/`
- M06 → `notebooks/llm-fine-tuning/m06_transformers/` and
  `lessons/llm-fine-tuning/labs/lab-1-tiny-lm/`
- M11 → `notebooks/computer-vision/m11_image_classification/` and its Lab 1
- M15 → `notebooks/ai-agents/m15_agents/` and its Lab 1
- Capstone index → `lessons/capstone/labs/lab-1-capstone-package/`
- Project index → `course/projects/p01-tabular-prediction/` and
  `course/projects/submission-package/`

## Student-facing improvements in this pass

- Every module name in the roadmap, learning paths, and syllabus overview is now a
  link, not plain text.
- Every Mxx section in the syllabus level pages has a **Published material** link.
- The assessment coverage map links its course areas.
- The new [Datasets and Resources](../resources/index.md) page answers the
  recurring questions: what data, where is it, what licence, what hardware, and
  what must I download?
- Empty top-level lab directories now contain README pointers to the actual brief
  and runnable code. A student is no longer left looking at an empty folder.
- The video-data command now names the real generator path.

## Usability limitations

- **No human pilot, think-aloud session, or classroom use.** The static journeys
  are not a substitute for watching a beginner struggle with the material.
- **No public-origin test.** The deployed URL is 404. The `/AITopics/` prefix has
  been exercised only in the local built output.
- **No search-quality or mobile evaluation.** MkDocs Material provides search and
  responsive layout, but relevance, keyboard navigation, and phone rendering were
  not measured.
- **No GPU or Colab run.** A student without a local CPU environment may need the
  Colab instructions, which remain unverified.
- **Twenty notebooks do not use the newer named-section structure.** Students can
  still use them, but the reading experience is less uniform.
- **Some lessons are long.** Time estimates and reading load have not been
  validated with students.
- **Synthetic exercises can score highly** without predicting real-world
  performance; the notebooks state this, but a student may still over-read a
  perfect fixture score.

## Release use

This audit supports a **READY WITH DOCUMENTED LIMITATIONS** release decision. It
does not support **READY FOR STUDENT USE**: the public site must be deployed and
the major paths checked on the public origin first, followed by a small human
pilot. See the [GitHub Pages deployment audit](github-pages-deployment-audit.md)
and the [Final audit](final-audit.md).
