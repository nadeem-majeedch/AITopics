# GitHub Pages publication

Maintainer documentation for publishing this course as a **GitHub Pages project
site**. Students do not need this page.

| Item | Value |
| --- | --- |
| Repository | `https://github.com/nadeem-majeedch/AITopics` |
| Framework | MkDocs 1.6 with Material for MkDocs 9.6+ |
| Configuration | `mkdocs.yml` (repository root) |
| Content root | `docs/` |
| Build output | `site/` (git-ignored, never committed) |
| Published URL | `https://nadeem-majeedch.github.io/AITopics/` |
| `site_url` | `https://nadeem-majeedch.github.io/AITopics/` |
| Deployment workflow | `.github/workflows/deploy-pages.yml` |
| PR validation workflow | `.github/workflows/validate-docs.yml` |
| Dependency updates | `.github/dependabot.yml` |

!!! warning "Publication status"
    The workflows and configuration on this page were added and validated
    locally on 2026-11-04. **No GitHub Actions run or Pages deployment has been
    performed from this machine**, so the public URL must be treated as
    unverified until the first successful workflow run is inspected. See
    [Verify publication](#verify-publication).

## Why the base path matters

This is a **project site**, not a user site, so every published URL lives under
the repository prefix:

```text
https://nadeem-majeedch.github.io/AITopics/
```

Two things must agree with that prefix:

1. **`site_url` in `mkdocs.yml`.** It sets canonical URLs, the sitemap, and the
   Open Graph metadata. Without it MkDocs emits URLs rooted at the domain and the
   sitemap points at the wrong location.
2. **Page and asset URLs inside the HTML.** MkDocs writes **relative** URLs
   (`../../assets/stylesheets/main.css`), which resolve correctly under any
   prefix. A hand-written root-absolute link such as `/course/roadmap.md` would
   break, because the browser would request `https://nadeem-majeedch.github.io/course/...`
   instead of `/AITopics/course/...`.

The source has no root-absolute internal links. `scripts/check_docs_links.py`
fails the build if one appears, either in Markdown or in the generated HTML. It
does accept absolute URLs that already carry the `/AITopics` prefix, because
MkDocs writes those into `404.html` deliberately: that page is served at
arbitrary depths and cannot use relative URLs.

Do not set `use_directory_urls: false` to work around a prefix problem. The
relative-URL scheme already handles the prefix; changing that setting alters
every published URL.

## Prerequisites

- Maintainer access to the repository (to merge to `main` and to change Pages
  settings once).
- The repository default branch is **`main`**. The workflow triggers and
  `edit_uri` both assume it.
- GitHub Actions enabled for the repository.
- GitHub Pages available for this repository. Pages is free for public
  repositories; for a private repository the account plan must include Pages.
  If **Settings → Pages** offers no source option, confirm visibility and plan
  before debugging the workflow.
- No secrets. The build installs two public packages and deploys a public static
  site; it needs no tokens, API keys, or environment variables.

Local prerequisites for reproducing the build:

- Python 3.12 (3.11 also works; CI uses 3.12).
- `requirements/docs.txt` (MkDocs and Material only, no ML dependencies).

## Build command

From the repository root, in a virtual environment:

```bash
python -m pip install -r requirements/docs.txt
python scripts/check_docs_links.py
python -m mkdocs build --strict
python scripts/check_docs_links.py --site site
```

- `--strict` turns MkDocs warnings into errors, so a missing nav file or a bad
  page fails the build locally exactly as it would in CI.
- The output is `site/`. It is git-ignored; do not commit it.
- The link checker also verifies heading anchors and every `nav` entry.

## Local preview

```bash
python -m mkdocs serve
```

Open `http://127.0.0.1:8000/`. The preview serves at the domain root, so it does
**not** exercise the `/AITopics/` prefix. To test the prefix, serve the built
output under a directory named `AITopics`:

```bash
python -m mkdocs build --strict
mkdir -p tmp/pages-sim/AITopics
cp -r site/. tmp/pages-sim/AITopics/
cd tmp/pages-sim && python -m http.server 8765
```

Then open `http://127.0.0.1:8765/AITopics/` and check a nested page such as
`http://127.0.0.1:8765/AITopics/course/projects/`. `tmp/` is git-ignored.

## Repository settings required

These are one-time, manual, administrator actions. They cannot be set from this
repository and must not be changed by automation.

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
   Do not choose "Deploy from a branch"; the workflow uploads an artifact rather
   than committing to `gh-pages`.
2. Confirm the default branch is `main`
   (**Settings → General → Default branch**).
3. Leave **Enforce HTTPS** enabled after the first deployment.
4. Do not add a custom domain unless the course owner decides to. If one is
   added, `site_url` must change and the CNAME file becomes part of the build.
5. Optional: under **Settings → Environments → github-pages**, restrict who may
   deploy. The environment is created by the first deployment; no secrets belong
   in it.

No repository secret is required, and none should be added for this workflow.

## Workflow behaviour

### `deploy-pages.yml` — Deploy documentation

| Property | Value |
| --- | --- |
| Triggers | successful **Validate repository** run on `main` (`workflow_run`); `workflow_dispatch` |
| Permissions (top level) | `contents: read` |
| Permissions (deploy job) | `pages: write`, `id-token: write` |
| Concurrency | group `pages`, `cancel-in-progress: false` |
| Build job | check out the validated run's `head_sha` → Python 3.12 with pip cache → install docs deps → link/anchor/nav check → `mkdocs build --strict` → built-site prefix check → `actions/configure-pages` → `actions/upload-pages-artifact` (`site`) |
| Deploy job | needs build → `actions/deploy-pages` in the `github-pages` environment |

The deploy job does not run on pull requests. The build job checks out the
validated commit and does not modify the repository; the artifact is the static
`site/` directory. A successful push validation is therefore the normal
deployment gate, while manual dispatch remains an explicit maintainer action.

Actions used: `actions/checkout@v4`, `actions/setup-python@v5`,
`actions/configure-pages@v5`, `actions/upload-pages-artifact@v3`,
`actions/deploy-pages@v4`. They are pinned to major versions, which is the
standard GitHub-maintained pattern; pin to a commit SHA instead if the owner
requires it.

### `validate-docs.yml` — Validate repository

The file name is historical; the workflow now covers the whole repository.

| Property | Value |
| --- | --- |
| Triggers | pull requests targeting `main`; pushes to `main`; `workflow_dispatch` |
| Permissions | `contents: read` only |
| Concurrency | per-ref, `cancel-in-progress: true` |
| Python job | install `requirements/ci.txt`, `pip check`, licensing validation, 253 unit tests, a synthetic manifest fixture, project checks, generated-data check, notebook JSON validation, and execution of all 20 notebooks |
| Documentation job | install docs dependencies, link/anchor/nav check, strict build, and prefix check |
| Pages actions | none; no artifact upload, no deployment job |

This is the gate that catches a broken link, failed test, invalid notebook, or
manifest problem **before** merge or deployment. A fork pull request cannot
publish anything because it has no Pages permission and no deployment job. A
direct push to `main` is validated too; Pages deployment waits for the successful
run instead of starting from the push itself.

### Dependency updates

`.github/dependabot.yml` opens monthly pull requests for `mkdocs`,
`mkdocs-material`, and the GitHub Actions used by these workflows. Each PR runs
`validate-docs.yml`. Dependabot does not update the ML dependency sets; update
them deliberately because notebook execution depends on the resolved CPU stack.

### Validating these files before committing

A YAML parse alone does not prove a workflow is valid. Validate against the
published schema instead, in a throwaway environment:

```bash
python -m venv tmp/valvenv
tmp/valvenv/Scripts/python -m pip install check-jsonschema
tmp/valvenv/Scripts/check-jsonschema --builtin-schema vendor.github-workflows \
  .github/workflows/deploy-pages.yml .github/workflows/validate-docs.yml
tmp/valvenv/Scripts/check-jsonschema \
  --schemafile https://json.schemastore.org/dependabot-2.0.json .github/dependabot.yml
```

All three files validate as of 2026-11-07. `tmp/` is git-ignored, so the virtual
environment and any incident artifacts stay out of the repository.

## Expected published URL

```text
https://nadeem-majeedch.github.io/AITopics/
```

Sitemap: `https://nadeem-majeedch.github.io/AITopics/sitemap.xml`

The first deployment can take a few minutes to become reachable; later
deployments usually replace content within a minute. If the URL returns 404 after
a successful run, check the Pages source setting and the environment URL reported
by the deploy job.

## Inspect build and deployment failures

1. **Actions tab → Deploy documentation → the run.** The failing step is marked
   in red; expand it for the log.
2. **Locally reproduce the failing step.** A strict-build failure names the file
   and the warning:

   ```bash
   python -m mkdocs build --strict
   ```

   A link failure names the page and the target:

   ```bash
   python scripts/check_docs_links.py
   ```

3. **Download the artifact** from the run summary to inspect exactly what was
   built (`github-pages` artifact).
4. **Deploy-job failures** are usually permissions, environment protection, or
   Pages settings. Read the `actions/deploy-pages` step log; it reports the HTTP
   status from the Pages API.
5. With the GitHub CLI:

   ```bash
   gh run list --workflow=deploy-pages.yml
   gh run view <run-id> --log-failed
   gh run watch <run-id>
   ```

### Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Aborted with a BuildError` / warnings as errors | Missing nav target, bad page, duplicate anchor | Run the strict build locally; fix the named file |
| Link check fails | Relative link typo, missing heading anchor, root-absolute link | Run `check_docs_links.py`; use a relative `.md` link |
| Deploy job fails with 403/404 from Pages | Pages source not set to GitHub Actions, or Pages disabled | Settings → Pages → Source: GitHub Actions |
| `Get Pages site failed` | Pages not enabled for the repository | Enable Pages, then re-run the workflow |
| Environment waiting for approval | Protection rule on `github-pages` | Approve the deployment, or relax the rule deliberately |
| Deployment does not run after a push | Validation did not finish successfully, wrong branch, or Actions/Pages disabled | Check the Validate repository run and the default branch |
| Site loads unstyled or 404s assets | A root-absolute asset URL was introduced | Run `check_docs_links.py --site site` |
| Old content after a successful run | CDN/propagation delay, or the run deployed from another branch | Wait, then compare the run's commit SHA with `main` |

## Verify publication

Run these **after** a real workflow run has succeeded. Do not report the site as
published based on the workflow file alone.

```bash
# 1. The deployment run succeeded and deployed the expected commit
gh run list --workflow=deploy-pages.yml --limit 3
gh run view <run-id> --json conclusion,headSha,url

# 2. The site answers with 200 at the project prefix
curl -sS -o /dev/null -w "%{http_code}\n" https://nadeem-majeedch.github.io/AITopics/

# 3. A nested page and an asset answer with 200 (not the GitHub 404 page)
curl -sS -o /dev/null -w "%{http_code}\n" https://nadeem-majeedch.github.io/AITopics/course/projects/
curl -sS -o /dev/null -w "%{http_code}\n" https://nadeem-majeedch.github.io/AITopics/sitemap.xml

# 4. The HTML points at the correct canonical URL
curl -sS https://nadeem-majeedch.github.io/AITopics/ | grep -o '<link rel="canonical"[^>]*>'

# 5. The stylesheet referenced by the page loads
curl -sS https://nadeem-majeedch.github.io/AITopics/ | grep -o 'href="[^"]*main[^"]*\.css"'
```

In a browser, confirm: the home page is styled, search returns results, the
sidebar and tabs work, a deep page such as **Capstone projects → Project index**
renders, and the 404 page is the site's own page rather than GitHub's generic one.

Record the verification in the log in
[Build and deploy](build-and-deploy.md#verification-log) only after running it.

## Related documents

- [Build and deploy](build-and-deploy.md) — framework, local setup, conventions
- [Site maintenance](site-maintenance.md) — dependency updates and local validation
- [Maintainer guide](maintainer-guide.md) — review and release process
- [Troubleshooting](troubleshooting.md) — MkDocs, Python, and Windows issues
