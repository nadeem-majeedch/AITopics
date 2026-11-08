# Independent final licensing audit

**Audit date:** 2026-11-07  
**Status:** **LICENSING IMPLEMENTED WITH WARNINGS**  
**Release verdict:** **NOT RELEASE READY** until the external and human checks in
the [v1 release-candidate checklist](v1-release-candidate-checklist.md) are
complete.

This audit inspected the actual licence files, scope manifest, validator, tests,
and release tree. It did not rely only on the implementation report. It is not
legal advice.

## 1. Files inspected

- `LICENSE`
- `LICENSES/CC-BY-4.0.txt`
- `LICENSES/CC0-1.0.txt`
- `LICENSES/README.md`
- `LICENSES/SYNTHETIC-DATA.md`
- `licensing-scope.json`
- `scripts/check_licensing.py`
- `tests/test_licensing.py`
- `.gitignore`, `.github/workflows/validate-docs.yml`, and the documentation
  cross-references listed below

## 2. Exact legal texts

| Item | Independent result | Status |
| --- | --- | --- |
| MIT body | 162 words; normalized SHA-256 `fe2a9817987f862eaced948f0468c7f51d2fedfc48c5c505b246a49a3870e9a5`; matches the official Open Source Initiative text | **Verified** |
| CC BY 4.0 | 18,657 bytes; SHA-256 `9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411`; matches the official `legalcode.txt` after line-ending normalization | **Verified** |
| CC0 1.0 | 7,048 bytes; SHA-256 `a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499`; matches the official `legalcode.txt` after line-ending normalization | **Verified** |
| Copyright line | `Copyright (c) 2026 Muhammad Nadeem Majeed`; the year is consistent with the first commit and implementation date | **Verified as recorded** |
| Legal-name confirmation | The instructor confirmed the exact name **Muhammad Nadeem Majeed** on 2026-11-08; honorifics are omitted from the licence line | **Instructor-confirmed** |

The CC texts were fetched from the official Creative Commons `legalcode.txt`
URLs for this audit and compared with the local files. The MIT body was fetched
from `https://opensource.org/license/mit`, normalized, and hashed. The legal texts
are not relicensed as AITopics content.

## 3. SPDX identifiers

| Scope | Identifier | SPDX-valid | Status |
| --- | --- | --- | --- |
| Original source code | `MIT` | Yes | **Verified** |
| Original educational content | `CC-BY-4.0` | Yes | **Verified** |
| Original synthetic data | `CC0-1.0` | Yes | **Verified** |
| Legal texts | `upstream-text` (not an SPDX licence identifier) | Internal marker only | **Verified as a non-SPDX marker** |

The validator checks declared `SPDX-License-Identifier` values in source and
documentation files and rejects identifiers that conflict with the manifest.
There are no files with a conflicting identifier in the release tree.

## 4. Scope coverage

The release tree was enumerated with:

```bash
git ls-files --cached --others --exclude-standard
```

After excluding the tool-managed `.freebuff/` directory and the newly ignored
`datasets/training/generated/` outputs, **556 files** were classified:

| Scope | Files |
| --- | ---: |
| Original source code (MIT) | 192 |
| Original educational content (CC BY 4.0) | 338 |
| Original synthetic data (CC0 1.0) | 0 in the release tree; generators and ignored outputs are recorded separately |
| Official legal texts | 3 |
| Non-content placeholder (`.gitkeep`) | 23 |
| **Total** | **556** |

The release tree contains no tracked synthetic-data output because the generated
directories are ignored. The CC0 dedication still applies when those generators
produce data locally; the provenance record is not a claim that the files are
committed.

### Gaps found and corrected during the audit

1. **Eight unclassified release files:** `.env.example`, `LICENSE`,
   `licensing-scope.json`, `projects/ai-agents/configs/agent_policy.json`,
   `projects/chatbots-rag/README.md`,
   `projects/video-ai/configs/video_analytics.json`, and two `.gitkeep`
   placeholders.
   - Configuration files were added to the MIT source scope.
   - Project Markdown was added to the CC BY 4.0 educational scope.
   - `LICENSE` was added to the legal-text scope.
   - `licensing-scope.json` was added to the educational scope.
   - `.gitkeep` files were made explicit non-content placeholders rather than
     receiving a misleading licence.
2. **Generated training data was not ignored.** The 11 non-ignored files under
   `datasets/training/generated/` would have entered a `git add -A` commit. A
   `datasets/training/generated/` rule was added to `.gitignore`; this does not
   modify the data or historical results.
3. **The validator had no repository-wide coverage check.** A
   `check_scope_coverage` method now fails on unclassified files and overlapping
   scopes, and accepts only explicit non-content placeholders.
4. **Regression tests were missing.** Three tests now cover an unclassified file,
   a non-content placeholder, and overlapping scopes.

The detailed per-directory report is in
[Scope coverage](licensing-scope-coverage.md).

## 5. Third-party exclusions

- No third-party dataset, model weight, media file, or vendored dependency is in
  the release tree.
- The local ignored caches contain SSDLite COCO and MobileNetV3 weight files.
  They are not release files and are not redistributed.
- The SSDLite **code** is BSD-3-Clause. The SSDLite **COCO weights** have no
  separate licence stated by torchvision and remain **unresolved**.
- Fine-tuned checkpoints derived from those weights are also unbundled and
  require a separate review before distribution.
- Optional torchvision ImageNet backbones, SmolLM2, Qwen, and student-selected
  ASR/TTS models are not bundled; their exact revisions and terms remain
  upstream matters.

The structured list is in the [Third-party inventory](third-party-inventory.md).

## 6. CC0 provenance

`LICENSES/SYNTHETIC-DATA.md` records nine generators, fixed seeds, no network
access, and no third-party source material. The P06 object set is recorded as 960
synthetic images rendered from NumPy primitives, with 57 same-split duplicate
groups that are generated variants rather than third-party copies.

**Status: Verified for the listed generators and the P06 record.** This is a
provenance review, not a copyright audit of every possible output. Third-party
datasets, downloaded media, and model checkpoints are excluded.

## 7. Cross-document consistency

| Document | Finding | Status |
| --- | --- | --- |
| `README.md`, `docs/index.md` | State MIT, CC BY 4.0, CC0 1.0, and third-party exclusions consistently | **Consistent** |
| `LICENSES/README.md` | Licence map, attribution wording, exclusions, and hashes match the files | **Consistent** |
| `LICENSES/SYNTHETIC-DATA.md` | Nine generators and the P06 record match the scope manifest | **Consistent** |
| `licensing-scope.json` | Four scopes, five third-party exclusions, and explicit non-content rules | **Consistent after corrections** |
| `docs/technical/licensing-and-attribution.md` | Register now links the structured inventory and records optional model gaps | **Consistent after corrections** |
| `docs/technical/licensing-decision-package.md` | Status remains `LICENSING IMPLEMENTED WITH WARNINGS`; scope list includes the newly classified files | **Consistent after corrections** |
| `docs/lessons/computer-vision/model-card.md` | The example no longer implies that all model weights are covered by the course licence | **Corrected** |
| `docs/lessons/video-ai/model-card.md` | States SSDLite code BSD-3-Clause and weights unresolved, unbundled | **Consistent** |

The licensing status was **not** upgraded to release-ready. The remaining
warnings are external facts, not missing repository files.

## 8. Validator coverage and limitations

The validator now performs eight checks:

1. required files exist;
2. legal texts match the expected hashes and markers;
3. the scope manifest has valid scopes, exclusions, and unresolved items;
4. every release file is classified, with no overlapping scopes;
5. documentation contains the approved statements and register categories;
6. SSDLite code and weight terms are distinguished and the weights are marked
   unresolved;
7. the P06 CC0 record is explicit;
8. declared SPDX identifiers are known and consistent.

**Limitations:**

- It checks path classification, not ownership or originality of file contents.
- It does not perform a code-similarity or provenance scan for copied snippets.
- It does not verify external dataset or model licences; it checks that they are
  recorded as unresolved or upstream-controlled.
- It does not validate the legal effect of the licences or institutional rights.
- Its release-file enumeration depends on Git; without Git it falls back to a
  filesystem walk, which is less precise about ignored artifacts.
- It does not check whether a contributor has authority to license a new file.

These limitations are documented rather than hidden. Manual review is still
required for new third-party material.

## 9. Audit conclusion

The licence architecture is implemented and internally consistent. The exact
legal texts, copyright line, SPDX identifiers, file scopes, CC0 provenance, and
third-party exclusions were verified to the extent possible from the repository
and official texts.

**Final licensing status: `LICENSING IMPLEMENTED WITH WARNINGS`.**

The warnings are:

1. SSDLite COCO weight terms remain unresolved;
2. optional model and dataset revisions remain upstream matters;
3. fine-tuned checkpoints require separate review;
4. no code-similarity audit was performed.

The repository must **not** be labelled `RELEASE READY` until the remaining
external and human checks in the release-candidate checklist are complete.
