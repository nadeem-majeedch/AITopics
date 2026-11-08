# Licensing decision package and implementation record

**Status: LICENSING IMPLEMENTED WITH WARNINGS.** The approved terms are
implemented and pass local validation; the warnings are the documented upstream
items in section 6, not missing licence files.

**Instructor approval:** recorded **2026-11-07**. The copyright holder's legal
name was confirmed by the instructor as **Muhammad Nadeem Majeed**. The approved
architecture is implemented in the working tree and validated locally. No commit
or push was performed. Instructor review of the final implementation report is
still required before publication.

This page records the decision and its implementation. It is not legal advice.
The evidence register is [Licensing and attribution register](licensing-and-attribution.md);
the student-facing map is
[`LICENSES/README.md`](https://github.com/nadeem-majeedch/AITopics/blob/main/LICENSES/README.md).

## 1. Instructor approval

The instructor approved the following terms:

| Material | Approved licence | Commercial reuse |
| --- | --- | --- |
| Original source code | MIT License | Allowed |
| Original educational content | Creative Commons Attribution 4.0 International (CC BY 4.0) | Allowed with attribution |
| Original synthetic datasets | CC0 1.0 Universal, after provenance verification | Allowed; no attribution required |
| Third-party code, data, media, and pretrained weights | Their original upstream terms | Only as the upstream terms allow |

The approval resolves the previous "no licence selected" gate. It does not
relicense third-party material and does not assert ownership of it.

## 2. Implementation date and files created

**Implementation date:** 2026-11-07.

| File | Purpose |
| --- | --- |
| `LICENSE` | Complete MIT text for original source code, with the recorded copyright holder and year |
| `LICENSES/CC-BY-4.0.txt` | Complete official CC BY 4.0 legal code |
| `LICENSES/CC0-1.0.txt` | Complete official CC0 1.0 legal code |
| `LICENSES/README.md` | Multi-licence map, attribution wording, third-party exclusions, and official-text hashes |
| `LICENSES/SYNTHETIC-DATA.md` | Provenance and CC0 dedication record, including the 960-image P06 set |
| `licensing-scope.json` | Machine-readable path scopes, exceptions, and unresolved items |
| `scripts/check_licensing.py` | Validator for texts, notices, scope, third-party exclusions, SSDLite status, and SPDX consistency |
| `tests/test_licensing.py` | Tests for missing files, missing exceptions, conflicting SPDX, unresolved weights, missing synthetic attribution, unclassified files, non-content placeholders, overlapping scopes, and the correct mixed configuration |
| `.github/workflows/validate-docs.yml` | Runs the licensing validator in CI |

Updated documentation: `README.md`, `docs/index.md`,
`docs/technical/licensing-and-attribution.md`, this page,
`docs/technical/release-readiness-audit.md`, `docs/technical/final-audit.md`,
`docs/technical/contributing.md`, `docs/planning/content-inventory.md`,
`docs/planning/implementation-phases.md`, and
`docs/lessons/video-ai/model-card.md`.

## 3. Scope of each licence

| Material | Licence | Scope |
| --- | --- | --- |
| Original Python source, tests, scripts, build configuration | MIT | `scripts/`, `tests/`, `projects/**/*.py`, `projects/**/configs/**`, `requirements/`, `.github/`, `mkdocs.yml`, `.gitignore`, `.env.example`; excludes generated outputs |
| Original lessons, documentation, labs, notebooks, templates, diagrams | CC BY 4.0 | `docs/`, `labs/`, `notebooks/`, `templates/`, `projects/**/*.md`, `README.md`, `licensing-scope.json`, and licensing documentation; notebooks are covered as whole files, including code cells and original outputs |
| Original synthetic datasets | CC0 1.0 | Deterministic outputs of the generators listed in `LICENSES/SYNTHETIC-DATA.md`, including P06; excludes third-party data and model checkpoints; generated directories are git-ignored |
| Official legal texts | Verbatim upstream texts | `LICENSE`, `LICENSES/CC-BY-4.0.txt`, and `LICENSES/CC0-1.0.txt` are not claimed as original AITopics content |
| Third-party material | Upstream terms | Never covered by the repository's MIT, CC BY 4.0, or CC0 1.0 grants |

The precise path globs and exclusions are in `licensing-scope.json`. A specific
file notice overrides the general map. No licence is inferred from a filename or
extension alone.

## 4. Copyright holder and official texts

| Field | Record |
| --- | --- |
| Copyright holder | **Muhammad Nadeem Majeed** |
| Evidence | Repository README, `docs/about/instructor.md`, and Git commit author metadata record the author as Engr. Dr. Muhammad Nadeem Majeed / Dr. Muhammad Nadeem Majeed. Honorifics are omitted from the licence line. |
| Year | **2026**, the year of the first repository commit and this implementation |
| Legal-name confirmation | **Instructor-confirmed.** The exact copyright holder is Muhammad Nadeem Majeed; the MIT notice uses that name without honorifics. |
| MIT source | <https://opensource.org/license/mit> |
| CC BY 4.0 source | <https://creativecommons.org/licenses/by/4.0/legalcode> |
| CC0 1.0 source | <https://creativecommons.org/publicdomain/zero/1.0/legalcode> |

The complete texts were downloaded from the official sources on 2026-11-07.
Line endings were normalised for hashing. The MIT body matches the official
162-word text; only the required copyright line differs. The CC texts match their
official SHA-256 values recorded in `LICENSES/README.md`.

## 5. Third-party exceptions

| Item | Bundled? | Exception / obligation |
| --- | --- | --- |
| NumPy, pandas, scikit-learn, SciPy, joblib, matplotlib, Pillow, PyTorch, torchvision, OpenCV, Jupyter, MkDocs, Material | No | Installed separately under their own licences; retain notices if redistributed |
| COCO, CIFAR-10, DeepFashion, TinyShakespeare, Fashion-MNIST, Speech Commands, and student datasets | No | Upstream terms; COCO annotations are CC BY 4.0 but images remain subject to Flickr terms |
| SmolLM2 and Qwen weights | No | Check the exact model card and revision; P03's "Apache-2.0 at the time of writing" is not a perpetual guarantee |
| Optional torchvision ImageNet backbones (ResNet-18 default) | No | Torchvision code is BSD-3-Clause; weight terms are model-specific and unresolved |
| Optional ASR/TTS models | No | No model is pinned; upstream model, weight, consent, and dataset terms apply |
| SSDLite320 COCO weights (`ssdlite320_mobilenet_v3_large_coco-a79551df.pth`) | No | Torchvision code is BSD-3-Clause; no separate weight licence is stated; weights may inherit COCO-derived terms and remain **unresolved**. The repository does not redistribute them. |
| Third-party images, audio, video, or quoted excerpts | No | None found bundled; future additions require source, licence, and attribution |
| GitHub Actions | No | External services; action pinning and provenance are reviewed separately |

No third-party code sample with an attribution requirement was identified. That
is a repository-search finding, not a legal code-similarity audit.

## 6. Remaining unresolved items

1. **SSDLite COCO weight terms.** Torchvision does not state a separate weight
   licence. The weights are not MIT, BSD-3-Clause, or CC BY 4.0 by repository
   declaration. Do not redistribute the weight file or a fine-tuned checkpoint
   without a separate review.
2. **Other pretrained model revisions.** Students must check the exact model card,
   revision, licence URL, and hash for SmolLM2, Qwen, and any other downloaded
   model.
3. **External datasets.** COCO image-level terms, DeepFashion restrictions, and
   student-selected datasets remain upstream matters.
4. **Fine-tuned checkpoints.** A checkpoint derived from third-party weights may
   inherit restrictions; the repository licence does not resolve that.
5. **Optional Streamlit/sentence-transformers stack.** Not installed in the audited
   environment; verify package and model terms before redistributing an
   environment that includes them.
6. **Code-similarity audit.** No similarity audit was performed. Any adapted
   external snippet must carry a source and licence note.
7. **Institutional or employer rights.** The repository record does not establish
   whether any institutional policy affects the author's licensing authority;
   that is an instructor/institutional review item.

These items are documented rather than guessed. The existence of the three
licence files does not mean the whole repository is legally cleared.

## 7. Validation evidence

Local validation on 2026-11-07:

| Check | Result |
| --- | --- |
| `python scripts/check_licensing.py` | **PASS**, 8 checks, 0 failures |
| Licensing unit tests | **11 tests, OK** |
| Full Python suite | **253 tests, OK** |
| Notebook JSON validation | **26 notebooks valid** |
| Course project specifications | **12 projects, 12 complete specs, 8 assessment banks** |
| Markdown links and anchors | **295 Markdown files, 0 failures** |
| Strict MkDocs build | **322 pages, 0 warnings** |
| Built-site prefix check | **322 pages, `/AITopics` prefix, 0 problems** |
| Workflow and Dependabot schemas | **Valid** — rechecked with `check-jsonschema` 0.39.0 |
| `pip check` | **Clean** |

The GitHub Actions workflow has **not executed on GitHub** because no commit or
push was performed. Local runs and schema validation are not a substitute for a
runner result.

## 8. Answers to the final audit questions

1. **Which original source-code files are covered by MIT?** Python source,
   tests, scripts, build configuration, and repository automation listed in the
   `original-source-code` scope of `licensing-scope.json`, excluding generated
   outputs and third-party dependencies.
2. **Which educational files are covered by CC BY 4.0?** Original Markdown
   lessons and documentation, labs, notebooks, templates, diagrams, and the
   licensing documentation, as listed in the `original-educational-content`
   scope.
3. **Which synthetic datasets are covered by CC0?** Deterministic outputs of the
   generators recorded in `LICENSES/SYNTHETIC-DATA.md`, including the P06 object
   set. The record confirms no third-party source material.
4. **Which third-party materials are excluded?** Dependencies, external datasets,
   external media, SmolLM2/Qwen weights, SSDLite COCO weights, and any fine-tuned
   checkpoints derived from them.
5. **Are any files of uncertain ownership still present?** No bundled third-party
   media or weights were found. External datasets and model weights remain
   upstream and are not redistributed. The code-similarity audit remains open.
6. **Are all three legal texts complete and verified?** Yes, locally: the MIT body
   matches the official text and both CC texts match their official SHA-256
   values. **GitHub Actions verification has not run.**
7. **Is the repository internally consistent about licensing?** The maintained
   notices now agree on the approved terms, and the instructor-confirmed
   copyright holder is recorded consistently; the validator checks for the
   previous contradictory statements. Historical audit pages retain their
   historical findings where clearly labelled.
8. **Which legal or attribution issues remain unresolved?** The items in section
   6, especially SSDLite weight terms, external model revisions, and institutional
   rights.

## 9. Review gate

The implementation is ready for instructor review. No commit or push has been
performed. Publication should wait until the instructor reviews this report and
the GitHub Actions workflow runs successfully.
