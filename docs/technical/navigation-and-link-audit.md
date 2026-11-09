# Navigation and link audit

Audit date: **2026-11-09**. Scope: MkDocs navigation, Markdown links and anchors,
built HTML links, `/AITopics/` URL handling, table navigation, and direct notebook
access. Branch: `release/v0.1.0-rc.1`, commit `c6410ac`.

## Verdict

**PASS in the local source and built site.** All 296 Markdown files, their internal
links, heading anchors, and navigation entries resolve. The strict build produces
323 pages with no warnings, and the built-site checker finds no broken relative
links and no absolute URLs that bypass `/AITopics/`.

The public origin is **not** verified: `https://nadeem-majeedch.github.io/AITopics/`
returns HTTP 404. This audit therefore proves local navigation, not public
delivery.

## Before and after

| Check | Before repair | After repair |
| --- | ---: | ---: |
| Source Markdown files | 295 | 296 |
| Broken Markdown links, anchors, or nav targets | 0 | 0 |
| Built HTML pages | 322 | 323 |
| Broken built-site links or assets | 0 | 0 |
| Root-absolute internal links outside `/AITopics/` | 0 | 0 |
| Notebooks in MkDocs navigation | 26 of 26 | 26 of 26 |
| Notebooks linked from Notebook Library | 26 of 26 | 26 of 26 |
| Student entry pages with module links repaired | Not linked | Roadmap, learning paths, syllabus overview, six level pages, assessment coverage map |

No dead hyperlink was found in the baseline. The real navigation defect was
different: many tables listed a topic, notebook, or lesson as plain text, so a
student reading the page had no clickable route to the resource. A second defect
was a stale command path for the video generator, not a hyperlink.

## Tables and paths repaired

- `docs/course/roadmap.md`: all 18 module names now link to a published entry
  point.
- `docs/course/learning-paths.md`: all six path tables link their module rows.
- `docs/syllabus/index.md`: the module table links every module; the notebook count
  is corrected to 26.
- `docs/syllabus/level-0-start.md` through `level-5-production.md`: every `## Mxx`
  section now has a **Published material** link to its lesson sequence.
- `docs/planning/curriculum-coverage.md`: notebook paths and lesson code names are
  working relative links.
- `docs/course/assessments/index.md`: the six "Course area" cells link to the
  relevant lesson sequences.
- `docs/index.md`: the level table links each syllabus level, and the datasets
  section links the new resources page.
- `docs/planning/content-inventory.md`: marked as a maintainer page, because some
  code-formatted paths are planned helpers rather than student links.

## New student entry points

- [Datasets and Resources](../resources/index.md) is in the top-level navigation.
  It lists every course dataset, generator, licence rule, hardware tier, and
  pretrained-model caveat.
- `labs/README.md` and the eight area READMEs replace empty `.gitkeep` directories
  with pointers to the actual lab brief and runnable project. A student who opens
  `labs/computer-vision/` now sees where the eight briefs live.
- The [Notebook Library](../notebook-library.md) remains the shortest route when a
  student knows the topic but not the module number.

## Verification commands and results

```bash
python scripts/check_docs_links.py
python -m mkdocs build --strict -d site
python scripts/check_docs_links.py --site site
```

| Check | Result |
| --- | --- |
| Source Markdown, links, anchors, and nav entries | **PASS: 296 Markdown files, 0 broken** |
| Strict MkDocs build | **PASS: 0 warnings, 323 built pages** |
| Built-site relative links and assets | **PASS** |
| Absolute URLs under `/AITopics/` | **PASS** |
| Notebooks listed in navigation | **26 of 26** |
| Notebooks linked from Notebook Library | **26 of 26** |
| Resource reachability (`check_course_inventory.py`) | **PASS: every advertised lesson, lab, assessment, and notebook is linked** |

The page-level journey checks are recorded in the
[Student usability audit](student-usability-audit.md). The built-site checker
resolves virtual `mkdocs-jupyter` notebook pages, so a notebook link is checked at
its rendered output location, not only as a source `.ipynb`.

## Remaining navigation limitations

- **The public site is absent.** The built site has not been served from the
  `/AITopics/` origin, because GitHub Pages returns 404.
- **No browser interaction test.** The checker verifies href targets and prefix
  handling; it does not test search relevance, keyboard behavior, or mobile
  layout.
- **Some maintainer pages are intentionally not student navigation.** They retain
  planned paths in code formatting rather than creating links to nonexistent
  files.
- **Previous/next navigation comes from the Material theme footer.** Section pages
  also carry a section-path line. There is no bespoke previous/next control on
  every foundation page, so a theme change could alter that affordance.

For publication status, see the
[GitHub Pages deployment audit](github-pages-deployment-audit.md). For the overall
decision, see the [Final audit](final-audit.md).
