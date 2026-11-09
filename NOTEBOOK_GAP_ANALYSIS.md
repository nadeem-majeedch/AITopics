# Notebook Gap Analysis

**Repository:** https://github.com/nadeem-majeedch/AITopics
**Live site:** https://nadeem-majeedch.github.io/AITopics/
**Audited commit:** `faf14e9` · **Date:** 2026-11-09

## Purpose

This analysis separates two different things that a raw notebook count conflates:

1. **Content gaps** — a module whose teaching or practice is missing.
2. **Format choices** — a module that is complete but deliberately does not use a
   notebook.

Only the first is a defect. The second is a design decision that has to be justified
on its own terms, which is what the first table does.

## Verdict

**COMPLETE WITH DOCUMENTED GAPS.** No module has missing teaching content. Two
modules have no dedicated notebook, both deliberately, and both are supported by
material that is published and reachable. Two publication-hygiene gaps affect how
learners obtain the notebook files rather than whether the material exists.

## Modules without a dedicated notebook

| Module | Lessons | Practice offered instead | Is a notebook required? | Justification |
| --- | --- | --- | --- | --- |
| M00 — Course orientation (3 h) | 0 lesson pages | Roadmap, learning paths, study guide, M00 syllabus plan, hardware guidance | **No** | Orientation has no executable content. A notebook would either repeat the environment check that F02/M01 already owns (`m01_environment_check.ipynb` covers versions, environments, and reproducibility) or become a reading assignment in the wrong medium. |
| M17 — Integrated capstone (40 h) | 3 lessons, 1 lab, 1 assessment | Reuse of the M04-M16 notebooks as components, plus a three-checkpoint lab and a weighted assessment on measured evidence | **No** | The capstone's deliverable is a defended package with frozen-test evidence, not a guided exercise. `cp02` states that the evidence, not the notebook's last cell, is what is assessed. A dedicated notebook would duplicate exercises learners have already executed and would risk becoming a template that weakens independent work. |

### What supports M00 on the live site

| Page | Status |
| --- | --- |
| `/course/roadmap/` | 200 |
| `/course/learning-paths/` | 200 |
| `/course/how-to-study/` | 200 |
| `/syllabus/level-0-start/` (M00 section) | 200 |

### What supports M17 on the live site

| Page | Status |
| --- | --- |
| `/lessons/capstone/` (index) | 200 |
| `/lessons/capstone/cp01-scoping-and-data/` | 200 |
| `/lessons/capstone/cp02-build-and-evidence/` | 200 |
| `/lessons/capstone/cp03-evaluation-and-packaging/` | 200 |
| Capstone lab and assessment | 200 |

## Modules with one notebook covering several modules

These are not gaps, but they are the places where a "one module = one notebook"
expectation would mislead a reader.

| Notebook | Modules served | Why one file | Risk |
| --- | --- | --- | --- |
| `m09_chatbots.ipynb` | M09 | Single module, descriptive reference build | None |
| `m10_rag.ipynb` | M10 | Single module; retrieval builds on M09 but stands alone | None |
| `m11_image_classification.ipynb` | M11 | Single module | None |
| `m12_object_detection.ipynb` | M12 | Single module | None |
| `m13_speech_audio.ipynb` | M13 (14 lessons) | One notebook serves the whole vertical slice; audio features, EER, and CTC are demonstrated in sequence | 22 cells for 14 lessons (1.6 cells per lesson, second-lowest in the course). Each lesson states what to run and the module carries eight lab briefs, so practice does not depend on the notebook alone |
| `m14_video_ai.ipynb` | M14 (15 lessons) | Same vertical-slice pattern | 19 cells for 15 lessons (1.3 cells per lesson, the lowest ratio in the course). The practice load sits in the eight lab briefs |
| `m15_agents.ipynb` | M15 (5 lessons) | Single module | None |
| `m16_production.ipynb` | M16 (5 lessons) | Single module | None |

**Observation worth recording, not fixing:** cells per lesson ranges from 1.3 (M14)
and 1.6 (M13) up to 7.0 (M07), because M06-M08 spread 4-3 lessons over 21-23 cell
notebooks while M13 and M14 spread 14-15 lessons over 19-22 cells. Both vertical
slices compensate with eight lab briefs each. If student feedback later shows that
the speech and video modules feel under-practised, the correct response is
additional lab briefs, not a numerical push toward more notebooks.

## Foundation sequence mapping

The 13 foundation units deliver M01-M03 plus the pre-M01 bridge, one notebook each:

| Units | Module delivered | Notebooks |
| --- | --- | --- |
| F01 | pre-M01 bridge | 1 |
| F02 | M01 | 1 |
| F03-F10 | M02 | 8 |
| F11-F13 | M03 | 3 |

Every unit's `notebook.md` points at the unit's own notebook, and every pointer
resolved. No unit shares or borrows another unit's notebook.

## Publication gaps (the actionable part)

### G1 — no link to the raw `.ipynb` from any live page (medium) — **closed in the repository 2026-11-09**

- **Observed:** all 26 raw files return `200` and are byte-identical to the committed
  blobs, but no page contains an `href` ending in `.ipynb`. MkDocs rewrites the
  Markdown links in the Notebook Library and lesson pages to the rendered notebook
  page, and `mkdocs-jupyter` with `include_source: true` adds no download control.
- **Impact:** a learner who wants to run a notebook locally must construct the URL
  pattern `/notebooks/<area>/<stem>/<stem>.ipynb`. That is discoverable for a
  confident user and a dead end for a beginner, and it contradicts the existing
  technical documentation that promises a downloadable copy on each page.
- **Action taken:** a MkDocs hook (`scripts/mkdocs_notebook_downloads.py`) now adds
  a visible **Download notebook (.ipynb)** button to each notebook page, and the
  technical documentation was updated to match. See the remediation summary below.

### G2 — hash verification fails on a Windows working-tree copy (low) — **documentation corrected 2026-11-09**

- **Observed:** the published file is byte-identical to `git show HEAD:<path>`, but the
  Windows checkout has CRLF endings. Hashing the working-tree file against the
  download reports a false mismatch; the parsed JSON is identical (`json_equal True`,
  first differing byte is byte 1).
- **Impact:** anyone following the documented "hash the download against the repo
  copy" step on Windows will think the file is corrupt.
- **Action taken:** `docs/technical/GITHUB-PAGES.md` and
  `docs/technical/final-audit.md` now verify with
  `git show HEAD:notebooks/... | sha256sum` and state the CRLF caveat.

### G3 — `labs/` directory is not published (informational)

`/AITopics/labs/` returns `404`. The nine `labs/**/README.md` files live outside
`docs/`, are absent from navigation, and are not linked from any page. They are
repository authoring guidance. No action; recorded so the 404 is not later mistaken
for a broken course link.

## Non-findings (checked and clear)

| Check | Result |
| --- | --- |
| Duplicate notebooks | 0 (26 unique stems, 0 duplicate SHA-256) |
| Notebook with no module and no page | 0 |
| Module pointing at a nonexistent notebook | 0 |
| Notebook page returning non-200 | 0 of 26 |
| Notebook download returning non-200 | 0 of 26 |
| Download that is not valid JSON | 0 of 26 |
| Download that differs from the committed blob | 0 of 26 |
| Broken notebook link on the site | 0 |
| Notebook with stored execution errors | 0 (all cells executed, per committed reports) |

## Recommended remediation order

1. **G1 — done.** A MkDocs hook (`scripts/mkdocs_notebook_downloads.py`, declared
   under `hooks:` in `mkdocs.yml`) adds a **Download notebook (.ipynb)** button to
   every rendered notebook page, pointing at the existing `include_source` copy.
   Verified on a local strict build: 26/26 pages, one link each, 26/26 links resolve,
   26/26 files parse and match the source notebook, no duplicate files, rendering
   unchanged. The published site shows the button after the next deployment.
2. **G2 — done.** `docs/technical/GITHUB-PAGES.md` and
   `docs/technical/final-audit.md` now verify downloads against
   `git show HEAD:<path>`, with the CRLF caveat stated.
3. No content work: do not create notebooks for M00 or M17, and do not subdivide the
   M13/M14 notebooks without evidence from student use.

## Notebook count reconciliation

The 26 notebooks are F01 (1), F02/M01 (1), F03-F10 (8), F11-F13 (3), and M04-M16
(13). A grouping that omits F02 accounts for 25; the M01 environment-check notebook
is the missing entry.

## Verdict restated

**COMPLETE WITH DOCUMENTED GAPS** at the time of the audit — 18/18 modules published,
26/26 notebooks live and valid, 2 modules intentionally notebook-free with published
alternatives. The two publication-hygiene gaps (G1 download link, G2 hash
instructions) are now closed in the repository and take effect on the next
deployment; G3 is informational. No teaching content was removed or blocked at any
point.
