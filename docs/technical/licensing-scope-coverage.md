# Licensing scope coverage

**Audit date:** 2026-11-07  
**Method:** `git ls-files --cached --others --exclude-standard`, excluding the
tool-managed `.freebuff/` directory, compared with `licensing-scope.json` and its
explicit non-content rules.

This report covers the release tree only. Ignored data, model caches, outputs,
virtual environments, and build output are not release files.

## 1. Final classification

| Scope | Licence | Files |
| --- | --- | ---: |
| Original source code | MIT | 192 |
| Original educational content | CC BY 4.0 | 338 |
| Official legal texts | Upstream legal text | 3 |
| Non-content `.gitkeep` placeholders | No licence asserted | 23 |
| **Total** | | **556** |

There are **0 unclassified files** and **0 overlapping scopes**. The synthetic
data scope classifies no files in the release tree because generated data is
git-ignored; it remains applicable to local generator output under the provenance
record.

## 2. Scope details

### Original source code (MIT)

Includes Python source, tests, scripts, project configuration JSON, repository
automation, `mkdocs.yml`, `.gitignore`, `.env.example`, and `requirements/`.
Third-party dependencies are not vendored and are not covered by this scope.

### Original educational content (CC BY 4.0)

Includes `README.md`, `docs/`, `labs/`, `notebooks/`, `templates/`, project
Markdown, dataset Markdown, licensing documentation, and `licensing-scope.json`.
Notebooks are covered as whole files, including their original code cells and
outputs.

### Original synthetic data (CC0 1.0)

The manifest lists the deterministic output paths for the nine generators in
`LICENSES/SYNTHETIC-DATA.md`, including the P06 object set. All such paths are
git-ignored. They are CC0 only when produced by the recorded generators from
fixed seeds and after the provenance review; downloaded or third-party data is
excluded.

### Official legal texts

`LICENSE` is the MIT text with the required copyright line.
`LICENSES/CC-BY-4.0.txt` and `LICENSES/CC0-1.0.txt` are verbatim official texts.
They are not claimed as original AITopics content.

### Non-content placeholders

All 23 `.gitkeep` files are zero-byte Git placeholders. They contain no
copyrightable expression and carry no licence assertion. They are listed
explicitly in `licensing-scope.json` rather than being silently classified as
educational or source content.

## 3. Unclassified files found and corrected

| Path | Previous state | Disposition |
| --- | --- | --- |
| `.env.example` | Unclassified | MIT configuration template; contains no secrets |
| `LICENSE` | Unclassified | Official legal-text scope |
| `licensing-scope.json` | Unclassified | CC BY 4.0 educational/metadata scope |
| `projects/ai-agents/configs/agent_policy.json` | Unclassified | MIT project configuration |
| `projects/chatbots-rag/README.md` | Unclassified | CC BY 4.0 project documentation |
| `projects/video-ai/configs/video_analytics.json` | Unclassified | MIT project configuration |
| `datasets/.gitkeep` | Unclassified | Non-content placeholder |
| `projects/.gitkeep` | Unclassified | Non-content placeholder |

The other 21 `.gitkeep` files were already within broad directory scopes; the
explicit non-content rule now prevents them from being treated as licensed
content.

## 4. Generated-data ignore gap

Before the audit, 11 files under `datasets/training/generated/` were untracked
but not ignored. They would have been included by `git add -A`. The directory is
now covered by an explicit `.gitignore` rule. This changed no dataset content and
no historical experiment result.

The local ignored artifacts include:

- `projects/video-ai/.cache/torch/hub/checkpoints/ssdlite320_mobilenet_v3_large_coco-a79551df.pth`
- `projects/video-ai/.cache/torch/hub/checkpoints/mobilenet_v3_large-8738ca79.pth`
- generated training, vision, audio, video, and capstone data
- `outputs/` checkpoints and figures

None is a release file. The SSDLite and MobileNetV3 weight files are third-party
downloads and are not redistributed.

## 5. Mixed-content directories

| Directory | Mixed content | Handling |
| --- | --- | --- |
| `projects/` | Python code (MIT), Markdown (CC BY 4.0), config JSON (MIT), `.gitkeep` (non-content) | Split by manifest patterns; no overlap |
| `datasets/` | README Markdown (CC BY 4.0), `.gitkeep`, ignored generated data (CC0 when generated) | Generated data excluded from the release tree; provenance record covers it |
| `LICENSES/` | Original licensing docs (CC BY 4.0) and official legal texts | Separate scopes; legal texts are not relicensed |
| `.github/` | Workflow/config files (MIT) and `.gitkeep` placeholders | MIT scope plus explicit non-content rule |
| `notebooks/` | Notebooks (CC BY 4.0), `.gitkeep` | Whole-file CC BY 4.0; placeholders are non-content |
| `labs/` | Lab Markdown (CC BY 4.0), `.gitkeep` | CC BY 4.0; placeholders are non-content |

## 6. Broad patterns reviewed

| Pattern | Assessment |
| --- | --- |
| `docs/**` | Intentionally broad educational scope; no third-party media found in the tracked tree |
| `notebooks/**` | Intentional whole-notebook CC BY 4.0; outputs are original, not third-party, and future media needs review |
| `labs/**` | Lab material written for the course; no copied external assets identified |
| `projects/**/*.py` | Original project code; third-party imports are dependencies, not vendored source |
| `projects/**/*.md` | Project documentation added to CC BY 4.0 after the gap was found |
| `projects/**/configs/**` | Small original configuration JSON; no secrets or third-party data |
| `datasets/**/*.md` | Dataset documentation only; generated data is separately scoped |
| `**/.gitkeep` | Explicit non-content rule; no licence assertion |

No broad pattern currently covers an identified third-party file. That is a
repository-search finding, not a legal title opinion.

## 7. Files requiring individual notices

- `LICENSE` carries the MIT copyright line: `Copyright (c) 2026 Muhammad Nadeem Majeed`, confirmed by the instructor.
- The CC BY 4.0 and CC0 1.0 legal texts are unmodified official documents.
- No tracked third-party file requires a separate notice because none is
  bundled.
- A future contributor media file, adapted code snippet, or downloaded artifact
  must carry its own source, licence, and attribution note and must update the
  manifest and third-party inventory.

## 8. Residual uncertainty

The scope map cannot prove ownership of every line. It classifies the release
tree, records the third-party exclusions, and makes future additions fail the
coverage check until they are reviewed. It is not a code-similarity audit and
does not resolve the external dataset or model-weight terms recorded in the
[Third-party inventory](third-party-inventory.md).
