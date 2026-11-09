# Repository content audit

Audit date: **2026-11-09**. Branch: `release/v0.1.0-rc.1`. Audited commit:
`c6410ac` (one commit ahead of `origin/release/v0.1.0-rc.1` at `5fdf5de`).
This audit checks files on disk and their links, not claims in the README, the
curriculum map, or earlier audit reports.

## Verdict

**READY WITH DOCUMENTED LIMITATIONS at the repository-content level.** Every
advertised module has a lesson path, practical work, and an assessment; every
advertised notebook exists, is valid, has been executed, and is reachable. The
limitations are evidentiary, not missing-content claims: the public GitHub Pages
site is still 404, no validation or deployment workflow has run on GitHub, no GPU
or Colab execution exists, no human student pilot exists, and 20 notebooks do not
follow the newer named 14-section template.

## Verified inventory

Counts below are unique file paths, not rows in a table. Some computer-vision
lessons are shared by M11 and M12, and some lab briefs are shared by more than one
module, so the gate's row counts are larger than the unique counts.

| Artifact | Expected | Existing | Structurally complete | Partial | Missing |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lesson files | 105 | 105 | 105 | 0 | 0 |
| Notebooks | 26 | 26 | 26 valid and executed | 0 | 0 |
| Labs and project briefs | 52 | 52 | 52 | 0 | 0 |
| Assessments | 21 | 21 | 21 | 0 | 0 |
| Modules | 18 | 18 | 18 | 0 | 0 |

The notebook "complete" count means valid JSON, executable code, complete
execution counts, no stored errors, and a substantive Markdown/code mix. It does
not mean that all 26 meet the exact named 14-section template; only **6** do.

| Item | Verified count | Evidence |
| --- | ---: | --- |
| Modules inspected | 18 (M00-M17) | `scripts/check_course_inventory.py` |
| Unique module lesson files | 105 | 108 module rows after shared lessons are de-duplicated |
| Complete / partial / missing modules | 18 / 0 / 0 | Structural definition below |
| Executable notebooks | 26 | 13 foundation + 13 section notebooks |
| Valid and executed notebooks | 26 | JSON, stored outputs, and fresh CPU run |
| Notebooks meeting the exact 14-section named standard | 6 | M09-M14 only |
| Unique lab and project briefs | 52 | 76 module rows after shared briefs are de-duplicated |
| Unique assessments | 21 | 26 module rows after shared assessments are de-duplicated |
| Capstone project specifications | 12 | `scripts/check_course_projects.py` |
| Assessment banks with solutions | 8 | `scripts/check_course_projects.py` |
| Source Markdown pages | 296 | `scripts/check_docs_links.py` |
| Built site pages | 323 | `scripts/check_docs_links.py --site site` |

**Expected versus available:** lessons **105 / 105**, notebooks **26 / 26**,
labs and project briefs **52 / 52**, assessments **21 / 21**; missing **0** in
each category. The complete/partial/missing split is **18 / 0 / 0** modules under
the structural definition below.

The machine-readable companion is
[`repository-inventory.json`](repository-inventory.json). It records every
module, lesson, notebook, lab, assessment, word count, heading count, link state,
and notebook execution field. Regenerate it with:

```bash
python scripts/check_course_inventory.py --json docs/technical/repository-inventory.json
```

### What "complete" means here

A module is **complete** when every advertised file exists, every lesson has at
least 500 words and 3 level-2 headings, every lab and assessment has at least 300
words and 4 level-2 headings, every advertised resource is linked from at least
one Markdown page, and every notebook passes the notebook gate. **Partial** means
a file exists but fails one of those floors. **Missing** means an advertised path
does not exist.

This is a structural gate, not a claim that every lesson has been reviewed by a
teacher or tested with a student. All 18 modules pass the structural gate. That
does not erase the content limitations listed below.

## Notebook findings

All 26 notebooks are valid `nbformat` JSON, contain Markdown and executable code,
have complete execution counts, and store no error outputs. The fresh execution
after the Markdown repair completed **26 notebooks, 223 code cells, 152.6 s**.

Seven section notebooks had a real rendering defect: every Markdown paragraph had
been prefixed with `# `, so prose rendered as a first-level heading. The affected
files were:

- `notebooks/model-training/m04_training_from_scratch.ipynb`
- `notebooks/model-training/m05_data_engineering.ipynb`
- `notebooks/llm-fine-tuning/m06_transformers.ipynb`
- `notebooks/llm-fine-tuning/m07_sft_small_lm.ipynb`
- `notebooks/llm-fine-tuning/m08_lora_qlora.ipynb`
- `notebooks/ai-agents/m15_agents.ipynb`
- `notebooks/production/m16_production.ipynb`

Only Markdown source was changed. Code cells, outputs, and execution counts were
verified unchanged. M09-M14 already used the full named-section structure. The
other seven section notebooks and the 13 foundation notebooks remain substantive
but do not use all fourteen named sections; this is recorded in the
[Notebook coverage audit](notebook-coverage-audit.md).

## Directory findings

- **No notebook directory is empty.** All 26 `.ipynb` files are in place under
  `notebooks/`.
- **The top-level `labs/` directories no longer pretend to contain starter
  files.** Each applied area now has a `README.md` pointing to its real lab brief
  under `docs/lessons/` and its runnable code under `projects/`. The obsolete
  `.gitkeep` files were removed.
- **Generated data is not committed.** `data/` and `projects/*/data/` are
  regenerable and git-ignored. The committed foundation and training fixtures have
  manifests and CC0-1.0 provenance.
- **The video data command was wrong.** The generator is
  `projects/video-ai/scripts/make_video_data.py`, but seven lesson references told
  students to run `scripts/make_video_data.py` from the repository root. The
  references now use the real path; `projects/video-ai/lab_support.py` and
  `requirements/video.txt` were corrected too.

## Navigation and content repairs in this pass

- Linked the module names in `docs/course/roadmap.md`,
  `docs/course/learning-paths.md`, and `docs/syllabus/index.md` to the published
  module entry points.
- Added "Published material" links under every Mxx section in the six syllabus
  level pages.
- Turned the notebook paths and lesson names in
  `docs/planning/curriculum-coverage.md` into working relative links.
- Linked the course areas in the assessment coverage map and added a student-facing
  [Datasets and Resources](../resources/index.md) page to the site navigation.
- Added `labs/README.md` and eight area READMEs so a student who opens a top-level
  lab directory is sent to the actual brief instead of a dead end.
- Added a resource-reachability check and structural floors to
  `scripts/check_course_inventory.py`; it now also emits the machine-readable
  inventory.
- Corrected stale counts: 26 notebooks, 296 Markdown pages, 323 built pages, and
  572 release files.

## Gates run

All commands were run from the repository root in the existing virtual
environment on Windows 11, Python 3.12.10, CPU only.

| Gate | Command | Result |
| --- | --- | --- |
| Course inventory | `python scripts/check_course_inventory.py` | **PASS**: 18 modules, 105 unique lesson files, 26 notebooks, 52 unique labs/project briefs, 21 unique assessments |
| Notebook JSON and stored outputs | `python scripts/check_notebooks.py --validate` | **PASS**: 26 valid, executed, no stored errors |
| Notebook execution | `python scripts/check_notebooks.py --execute --timeout 300` | **PASS**: 26 notebooks, 223 cells, 152.6 s |
| Unit suite | `python -m unittest discover -s tests -v` | **PASS**: 269 tests, OK |
| Project specifications | `python scripts/check_course_projects.py` | **PASS**: 12 projects, 12 complete specifications, 8 assessment banks |
| Source links and anchors | `python scripts/check_docs_links.py` | **PASS**: 296 Markdown files, 0 broken |
| Strict site build | `python -m mkdocs build --strict -d site` | **PASS**: 0 warnings, 323 built pages |
| Built-site prefix and links | `python scripts/check_docs_links.py --site site` | **PASS**: 323 pages, absolute URLs use `/AITopics` |
| Licensing | `python scripts/check_licensing.py` | **PASS**: 8 checks, 572 release files classified |
| Whitespace | `git diff --check` | **PASS** |

## Remaining limitations

- **Public delivery is unverified.** The GitHub Pages API and public URL both
  return HTTP 404. The local build is not a deployment.
- **No GitHub Actions validation or deployment has run.** The two observed runs
  are Dependabot updates.
- **Twenty notebooks are below the newer named-section standard.** They are
  substantive and executed, but the exact 14-section template is enforced only
  for M09-M14.
- **No GPU or Colab execution.** The executable and stored evidence is local CPU.
- **No human student pilot.** Static journey checks are not a classroom study.
- **Synthetic data limits the claims.** High scores on generated fixtures show a
  pipeline works; they do not establish real-world accuracy.
- **No commit or push was made during this audit.** The public tree remains at
  `5fdf5de` until the release owner pushes the local work.

For page-level evidence, see the
[Navigation and link audit](navigation-and-link-audit.md),
[GitHub Pages deployment audit](github-pages-deployment-audit.md), and
[Student usability audit](student-usability-audit.md). The overall release status
is recorded in the [Final audit](final-audit.md).
