# Build and deploy

This page is for maintainers. Students do not need to build the site to use the
course.

## Current status

| Item | Status |
| --- | --- |
| Documentation framework | MkDocs with Material for MkDocs |
| Configuration | `mkdocs.yml` at repository root |
| Content root | `docs/` |
| Build output | `site/` (gitignored) |
| GitHub Pages | Configured for publication; **no deployment run yet** |
| `site_url` | `https://nadeem-majeedch.github.io/AITopics/` (project-site prefix) |
| Deployment workflow | `.github/workflows/deploy-pages.yml` (after successful validation on `main`, manual dispatch) |
| Validation workflow | `.github/workflows/validate-docs.yml` (pull requests, `main` pushes, and manual dispatch; docs, licensing validation, Python tests, notebooks, and manifests) |
| Publication guide | [GitHub Pages publication](GITHUB-PAGES.md) |
| Build verification | See [Verification log](#verification-log) |

The architecture phase intentionally did not enable deployment or modify remote
settings. The publication workflow and configuration have since been added; the
repository's Pages settings must still be switched to **GitHub Actions** by a
maintainer, and the first deployment has not been run. See
[GitHub Pages publication](GITHUB-PAGES.md) for the settings, the verification
steps, and the exact behaviour of both workflows.

## Requirements

- Python 3.11 or 3.12.
- Git.
- Internet access for the first dependency install.
- No Node.js, Ruby, or system-level package manager is required.

Documentation dependencies are deliberately small and live in
`requirements/docs.txt`:

```text
mkdocs>=1.6,<2
mkdocs-material>=9.6,<10
```

## Local setup on Windows 11

### PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements/docs.txt
python -m mkdocs serve
```

If PowerShell blocks activation, use the current-user policy for your account:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

This is a user-level setting. Do not change machine-wide policy without
administrator approval.

### Git Bash

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/docs.txt
python -m mkdocs serve
```

Open the URL printed by MkDocs, usually `http://127.0.0.1:8000/`.

## Build

```bash
python -m mkdocs build --strict
```

- `--strict` turns warnings into errors. Broken navigation, malformed pages, and
  many link problems fail the build.
- Output goes to `site/`.
- Use `python -m mkdocs build --clean` if stale files remain.
- Do not commit `site/`.

## Adding or changing pages

1. Create the Markdown file under the correct directory in `docs/`.
2. Add it to `nav` in `mkdocs.yml` in the pedagogical order.
3. Use relative links for internal pages, for example
   `[Roadmap](../course/roadmap.md)`.
4. Add alt text to images.
5. Run `mkdocs serve` and check the page on desktop and a narrow viewport.
6. Run `mkdocs build --strict`.
7. Update [Content inventory](../planning/content-inventory.md) if the page is a
   new course artifact.

Do not add empty pages to reserve navigation space. A page appears only when it
has real content.

## Link conventions

- Internal links: relative paths ending in `.md`; MkDocs converts them.
- External links: full `https://` URLs.
- Anchors: verify the heading exists; strict builds catch missing files but not
  every anchor typo.
- Do not link to a notebook path until the notebook exists.
- Colab links use this pattern:

```text
https://colab.research.google.com/github/nadeem-majeedch/AITopics/blob/main/notebooks/<area>/<notebook>.ipynb
```

This assumes the default branch is `main`. Confirm the branch before publishing.

## Branch assumptions

`mkdocs.yml` sets `edit_uri: edit/main/docs/`, and the Colab link pattern uses
`main`. If the repository's default branch is not `main`, update both before
publishing. The architecture phase could not verify the branch because the remote
repository was not accessible.

## GitHub Pages deployment

The repository now contains a deployment workflow and a validation workflow. The
live settings and the verification procedure are documented in
[GitHub Pages publication](GITHUB-PAGES.md); the summary below is for context.

Do not enable publication until the license is approved and the launch gate
passes.

### Prerequisites

1. Repository administrator access.
2. GitHub Pages enabled with **GitHub Actions** as the source.
3. `site_url` set in `mkdocs.yml` to the final URL.
4. A passing `mkdocs build --strict`.
5. A license file committed.

### Workflow files

Deployment is defined in the repository, not in this page:

| File | Purpose |
| --- | --- |
| `.github/workflows/deploy-pages.yml` | Strict build, link/anchor/prefix checks, upload the Pages artifact, deploy |
| `.github/workflows/validate-docs.yml` | Whole-repository gate: strict docs build plus CPU dependency install, `pip check`, licensing validation, 253 unit tests, manifest fixture tests, project and generated-data checks, and all 20 notebooks; no Pages permissions |
| `.github/dependabot.yml` | Monthly updates for `mkdocs`, `mkdocs-material`, and the Actions used |

`site_url` is already set to the project-site URL:

```yaml
site_url: https://nadeem-majeedch.github.io/AITopics/
```

The live URL remains unverified until a workflow run succeeds and the checks in
[Verify publication](GITHUB-PAGES.md#verify-publication) have been run.

### Alternative hosting

The site is static and can be hosted on Cloudflare Pages, Netlify, or an
institutional server. If you change hosts:

- Set `site_url` to the final URL.
- Do not add analytics without privacy review.
- Keep the same strict build command.
- Document the change in the [Maintainer guide](maintainer-guide.md).

## Notebooks and the docs build

Notebooks are not executed during the site build. This keeps builds fast and
avoids GPU or large-download requirements in CI.

Notebook execution is a separate quality gate:

- Run the notebook from a clean kernel.
- Record the environment and hardware.
- Save small outputs intentionally.
- Update the "last executed" metadata.
- Add the result to the module checklist.

The validation workflow now executes every notebook on a fresh CPU kernel with a
300-second per-cell timeout. It does not replace full execution on GPU or Colab,
which remain separately documented limitations. Run the same check locally with:

```bash
python scripts/check_notebooks.py --validate
python scripts/check_notebooks.py --execute --timeout 300
```

## Generated dataset manifests

Generated datasets are git-ignored, so a clean checkout has nothing to verify.
The CI command reports **SKIPPED** in that case; it never reports a skipped check
as a passed dataset. The checker itself is exercised by
`tests/test_vision_manifests.py` with a small synthetic fixture.

After generating the complete P06 and experimental sets, run the optional real
data gate:

```bash
python scripts/check_vision_manifests.py
python scripts/check_vision_manifests.py --require-datasets
```

The second command exits with status 2 if no `objects_p06*` dataset is present.

## Versioning and rollback

- Tag releases as `vYYYY.N` (for example `v2026.1`).
- Keep `CHANGELOG.md` (planned) with published modules and known gaps.
- If a deployment is broken, revert the offending commit on `main` and let the
  workflow redeploy. Do not force-push.
- Keep the previous release tag available for comparison.

## Security

- Deployment uses the minimum permissions: `contents: read`, `pages: write`,
  `id-token: write`.
- Do not store secrets in the docs build.
- Pin GitHub Actions versions. For higher assurance, pin third-party actions by
  commit SHA.
- Review dependency updates before merging.
- Do not publish notebooks with tokens, personal data, or private paths.

## Verification log

| Date | Environment | Command | Result |
| --- | --- | --- | --- |
| 2026-10-30 | Windows 11, Python 3.12.10, MkDocs 1.6.1, Material 9.8.0 | `python -m mkdocs build --strict` | Passed; 23 pages built in 0.67 s |
| 2026-10-30 | Same environment | Custom relative-link and anchor check | Passed; 101 relative links, 0 missing files, 0 missing anchors |
| 2026-10-30 | Same environment | `python -m mkdocs serve` and browser check | Home, roadmap (including Mermaid), and a module plan rendered correctly |
| 2026-10-30 | Windows 11, Python 3.12.10, CPU-only | Execute `notebooks/foundations/m01_environment_check.ipynb` from a clean kernel | Passed; 22 cells, accuracy 0.9778, reload and checksum assertions true, GPU section skipped safely. Colab execution still pending |
| 2026-10-30 | Windows 11, MkDocs 1.6.1, Material 9.8.0 | `python -m mkdocs build --strict` after M01 and template pages | Passed; 36 pages built in 0.81 s |
| 2026-10-30 | Same environment | Relative-link and anchor check across `docs/` and `README.md` | Passed; 321 relative links in 36 Markdown files, 0 missing files, 0 missing anchors |
| 2026-10-30 | Same environment | `mkdocs serve` and browser structural check | Landing page, hero links, 18 module cards, and the four M01 pages are present and linked. Full-page screenshot was unavailable in this browser surface, so visual rendering remains partly unverified |
| 2026-10-30 | Windows 11, Python 3.12.10, CPU-only | Execute the twelve new foundation notebooks top-to-bottom | Passed: all cells executed, 0 error outputs. F01-F10 on CPU; F11-F13 with PyTorch 2.4.1+cpu. No GPU or Colab run |
| 2026-10-30 | Windows 11, Python 3.12.10 | `nbformat.validate` on 13 foundation notebooks | Passed: 13 notebooks valid |
| 2026-10-30 | Windows 11, Python 3.12.10 | `python -m py_compile scripts/make_foundation_data.py` | Passed |
| 2026-10-30 | Windows 11, MkDocs 1.6.1, Material 9.8.0 | `mkdocs build --strict` after F01-F13 | Passed; 85 pages built in 2.09 s, 0 warnings |
| 2026-11-04 | Windows 11, Python 3.12.10, MkDocs 1.6.1, Material 9.8.0 | `python scripts/check_docs_links.py` | Passed; 224 Markdown files, every relative link, anchor, and nav entry resolves |
| 2026-11-04 | Same environment | `python -m mkdocs build --strict` with `site_url` set | Passed; 223 pages built in 5.20 s, 0 warnings |
| 2026-11-04 | Same environment | `python scripts/check_docs_links.py --site site` | Passed; 223 built pages, relative URLs resolve and every absolute URL uses the `/AITopics` prefix |
| 2026-11-04 | Same environment | Serve the build under `tmp/pages-sim/AITopics` and request pages, CSS, JavaScript, favicon, `sitemap.xml`, and search with HTTP | Passed; every asset and page returned 200 under the prefix, canonical URL and all 224 sitemap entries carry `https://nadeem-majeedch.github.io/AITopics/`, and search returned 9 matching documents with prefixed result links |
| 2026-11-04 | Same environment | `check-jsonschema` against the GitHub workflow schema and the Dependabot 2.0 schema | Passed for both workflows and `.github/dependabot.yml`; a deliberately malformed workflow was rejected, so the check is not a no-op |
| 2026-10-30 | Same environment | Relative-link and anchor check after F01-F13 | Passed; 903 links across 85 Markdown files in `docs/` and `README.md`, 0 missing files or anchors; 25 links in `labs/` and `datasets/` also pass |

Update this table only after actually running the command. Do not claim a build
passed without a recorded result.

## Toolchain lifecycle

The installed Material for MkDocs version (9.8.0) reports that the project
reaches end of life on **2027-05-05**, with critical fixes and security updates
until that date. The same team maintains **Zensical** as its successor and
documents compatibility with existing `mkdocs.yml` files.

Decision for this phase: keep MkDocs Material because it is supported through
2027 and the current site builds and renders correctly. Do not migrate in the
middle of content authoring. Evaluate Zensical before 2027, or earlier if a
security issue requires it, and record the migration in the
[Maintainer guide](maintainer-guide.md).

The build also prints the end-of-life notice on every run. It does not fail the
strict build. Do not silence it with `NO_MKDOCS_2_WARNING=1`; the warning is
useful maintenance information.

## Troubleshooting

See [Troubleshooting](troubleshooting.md) for common MkDocs, Python, and Windows
issues.

## Related documents

- [GitHub Pages publication](GITHUB-PAGES.md)
- [Site maintenance](site-maintenance.md)
- [Repository architecture](../planning/repository-architecture.md)
- [Quality standards](../planning/quality-standards.md)
- [Maintainer guide](maintainer-guide.md)
