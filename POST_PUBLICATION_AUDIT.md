# Post-Publication Completeness Audit

**Repository:** https://github.com/nadeem-majeedch/AITopics
**Live site:** https://nadeem-majeedch.github.io/AITopics/
**Audited commit:** `faf14e9` (`Fix licensing checks for Linux temporary paths`), branch `release/v0.1.0-rc.1`
**Audit date:** 2026-11-09
**Scope:** module-to-notebook coverage and the published notebook experience

## Verdict

**COMPLETE WITH DOCUMENTED GAPS**

All 18 modules (M00-M17) are published. Every module that the syllabus designs around
executable practice has a dedicated notebook, and all 26 notebooks are linked from
the site, render as pages, and are served as valid JSON. Two modules (M00, M17)
have no dedicated notebook by design, and each is delivered through an explicitly
documented alternative format. Three gaps are recorded below; none removes
published teaching content, and none blocks study.

## What was checked, and how

| Objective | Method | Result |
| --- | --- | --- |
| 18 modules identified | `docs/lessons/index.md` "Full module map" plus per-section navigation in `mkdocs.yml` | 18 modules M00-M17 |
| Notebook inventory | `git ls-files 'notebooks/*.ipynb'`, JSON parse of each file | 26 notebooks, all `nbformat` 4 |
| Notebook-to-module mapping | Notebook headings, section index pages, and per-unit `notebook.md` references | 26 mapped, 0 ambiguous, 0 mis-mapped |
| Modules without notebooks | Mapping cross-check against the module map | 2 (M00, M17), both intentional |
| Live page status | HTTP GET for all 26 notebook pages on the published origin | 26/26 → `200` |
| Live download status | HTTP GET for all 26 `<stem>.ipynb` files | 26/26 → `200`, `application/x-ipynb+json` |
| Download validity | Each downloaded file parsed with `json.load` | 26/26 valid JSON, 469 cells, 223 code cells |
| Download fidelity | SHA-256 of each download vs `git show HEAD:<path>` | 26/26 identical to the committed blob |
| Broken links | HTTP status of every notebook page, download, section index, library, and lab/resources page | No broken notebook link |
| Duplicates | SHA-256 of all 26 files, stem uniqueness | 0 duplicate files, 26 unique stems |

Notebook totals: 469 cells, 223 code cells, 246 Markdown cells. Cell counts per notebook
range from 12 (F06) to 26 (M15).

## Findings

### F1 — M00 and M17 have no dedicated notebook (by design, not a gap in teaching)

**M00 (course orientation, 3 h)** is delivered through four pages that exist and
resolve on the live site: the roadmap, the learning paths, the study guide, and the
M00 section of the Level 0 syllabus. An orientation module has nothing to execute.

**M17 (integrated capstone, 40 h)** has three lessons, one lab brief, one assessment,
and an explicit statement on `docs/lessons/index.md` that it "reuses M04-M16"
notebooks. The capstone's own lessons (`cp01`-`cp03`) state that its evidence is an
independently measured result, not a notebook run. Adding a 27th notebook here would
duplicate exercises the learners have already completed.

**Assessment:** no action. Recorded so that the two "missing" modules are not
mistaken for unfinished work.

### F2 — the raw `.ipynb` files are served but no live page links to them

This is the one substantive finding.

- All 26 raw files return `200` at
  `/AITopics/notebooks/<area>/<stem>/<stem>.ipynb` and are byte-identical to the
  committed blobs.
- No page on the site links to those URLs. The Notebook Library table and every
  lesson page write Markdown links such as
  `[Chatbots](notebooks/chatbots-rag/m09_chatbots.ipynb)`, and MkDocs rewrites each
  one to the rendered page `../notebooks/chatbots-rag/m09_chatbots/`.
- `mkdocs-jupyter` is configured with `include_source: true`, which copies the file
  into the build, but it does not add a download button or link to the notebook page
  (verified: the rendered page contains no `href` ending in `.ipynb` and no
  download control).

So a learner can read every notebook but can only obtain the `.ipynb` by
constructing the URL. This contradicts documentation in `docs/technical/` that
describes a downloadable copy on each notebook page.

**Recommended action (not applied):** add one explicit "Download .ipynb" link per
notebook page — for example a short line at the top of each `notebooks/**` entry in
`mkdocs.yml`, or a link rendered through an HTML anchor that MkDocs will not rewrite.

### F3 — hash verification of a download fails on a Windows working-tree copy

The published `.ipynb` is byte-identical to the Git blob, but a Windows checkout has
CRLF line endings, so `sha256sum download vs notebooks/…` in the working tree
reports a mismatch even though the JSON is identical (verified: `json_equal True`,
diff at byte 1, 941 CRLF bytes in the working copy, 0 in the download).

**Recommended action (not applied):** document verification against
`git show HEAD:<path> | sha256sum`, or a Linux/WSL checkout, instead of the raw file.

### F4 — `labs/` is not published (expected)

`/AITopics/labs/` returns `404`. `labs/README.md` and the eight `labs/*/README.md`
files sit outside `docs/` and are not in the navigation; no documentation page links
to them. They are authoring guidance for the repository, not course pages. No action.

## Coverage summary

| Measure | Value |
| --- | --- |
| Modules | 18 (M00-M17) |
| Modules with a dedicated notebook | 16 (M01-M16) |
| Modules with a notebook sequence | M02 (F03-F10), M03 (F11-F13) |
| Modules delivered in another format | 2 (M00 orientation, M17 capstone reusing M04-M16) |
| Lesson units published | 105 (104 mapped to modules, plus F01 as a pre-M01 bridge) |
| Notebooks | 26 (all executed, all published) |
| Live notebook pages | 26/26 `200` |
| Live notebook downloads | 26/26 `200`, 26/26 valid JSON, 26/26 identical to the committed blob |
| Duplicate or mis-mapped notebooks | 0 |
| Broken notebook links | 0 |

## Notebook count reconciliation (26 vs 25)

A grouping that lists F01, F03-F10, F11-F13 and M04-M16 accounts for 25 notebooks.
The 26th is **F02**, the M01 environment-check notebook:

| Group | Notebooks | Module |
| --- | --- | --- |
| F01 (`f01_python_ai`) | 1 | pre-M01 bridge |
| **F02 (`m01_environment_check`)** | **1** | **M01** |
| F03-F10 | 8 | M02 |
| F11-F13 | 3 | M03 |
| M04-M16 | 13 | one per module |
| **Total** | **26** | |

F02 appears in the M01 row and row 2 of the detail table in
`MODULE_NOTEBOOK_MATRIX.md`, and in the F02 row of the foundation table in
`NOTEBOOK_GAP_ANALYSIS.md`, so no report undercounted. The grouping above is the one
that omitted it. The counts are unchanged; this reconciliation makes the 26 explicit.

## Remediation (applied 2026-11-09)

| Finding | Status | Change |
| --- | --- | --- |
| F1 — M00/M17 have no notebook | No action (by design) | Unchanged |
| **F2 — no link to the raw `.ipynb`** | **Closed in the repository** | New MkDocs hook `scripts/mkdocs_notebook_downloads.py`, declared under `hooks:` in `mkdocs.yml`, adds a **Download notebook (.ipynb)** button to every rendered notebook page |
| **F3 — hash check misleads on Windows** | **Corrected in the documentation** | `docs/technical/GITHUB-PAGES.md` and `docs/technical/final-audit.md` now verify against `git show HEAD:<path>` |
| F4 — `labs/` not published | Informational | Unchanged |

Remediation verification (local strict build, `tmp/site`):

| Check | Result |
| --- | --- |
| Pages with the download button | 26 of 26 notebook pages, exactly one link each |
| Button present on non-notebook pages | 0 |
| Download links resolve in the built site | 26/26 |
| Downloaded files parse as JSON | 26/26 (`nbformat` 4) |
| Downloaded files match the source notebook | 26/26 byte-identical to the working-tree file, 26/26 JSON-identical to the `HEAD` blob |
| Duplicate `.ipynb` files introduced | 0 (26 copies, 26 unique names — the `include_source` copies that already existed) |
| Notebook rendering | Unchanged: 323 pages built, notebook content and outputs intact |
| Strict build / links | `mkdocs build --strict` 0 warnings; source links 296 files OK; built-site links 323 pages OK |
| HTTP resolution | Built site served locally: all 26 download links return `200` |
| Licensing validator | `RESULT: PASS`, 567 release files classified, SPDX identifiers consistent |
| Unit tests | 71 of 84 discovered tests pass, including all 15 licensing tests. The 13 remaining tests in 5 modules cannot import: this machine has Python 3.14 and the pinned `torch<2.5` (and `opencv`) have no 3.14 wheels. The same suite passed 273/273 on the documented Python 3.12 environment before that interpreter was removed. |

Files changed for students and maintainers: `docs/notebook-library.md` (the button is
now the documented download route), `docs/course/how-to-study.md` (step 1 of the
notebook workflow), `mkdocs.yml` (the `hooks:` entry), and `licensing-scope.json` (the
three root-level audit reports are declared as CC BY 4.0 original educational
content, which keeps the scope-coverage check green).

The change is in the working tree only. The published site still shows the
pre-remediation pages until the next deployment.

## Limitations of this audit

- **No local build was run.** The project `.venv` is orphaned on this machine: its
  recorded base interpreter (`Python312`) was replaced by `Python314`/`Python315`, so
  `python scripts/…`, `mkdocs build`, and the unit-test suite cannot start
  (`No Python at …\Python312\python.exe`). The audit therefore used Python 3.14 with
  the standard library for JSON validation and checked the **live site** directly for
  rendering and availability, which is stronger evidence of publication than a local
  build would have been.
- **Notebook execution was not re-run.** Execution status (223 code cells, previously
  verified top-to-bottom on CPU) is taken from the committed reports; the audit
  verified structure, not re-execution.
- **Single-client HTTP only.** Rendered pages were fetched without a browser, so
  JavaScript-dependent behaviour (search) and mobile layout were not assessed; both
  were out of scope for notebook coverage.
- **Live checks reflect the site at audit time.** GitHub Pages serves the commit
  deployed on 2026-11-09; a later deployment would need re-verification.

## Files produced by this audit

- `POST_PUBLICATION_AUDIT.md` (this file)
- `MODULE_NOTEBOOK_MATRIX.md`
- `NOTEBOOK_GAP_ANALYSIS.md`

The audit itself modified nothing. The remediation it records changed two
student-facing documentation pages (`docs/notebook-library.md`,
`docs/course/how-to-study.md`), one site configuration file (`mkdocs.yml`), one
licensing scope entry, and two technical pages (`docs/technical/GITHUB-PAGES.md`,
`docs/technical/final-audit.md`); it added the hook script
`scripts/mkdocs_notebook_downloads.py`. No notebook, lesson, lab, dataset, test, or
Git state was touched. Scratch data was written under the ignored `tmp/audit/`
directory.
