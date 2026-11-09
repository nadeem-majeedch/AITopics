# GitHub Pages deployment audit

Audit date: **2026-11-09**. Repository:
`https://github.com/nadeem-majeedch/AITopics`. Branch audited:
`release/v0.1.0-rc.1`, commit `c6410ac` (ahead 1 of
`origin/release/v0.1.0-rc.1` at `5fdf5de`).

## Verdict

**NOT DEPLOYED.** The Pages API and the project URL both return HTTP 404. No
validation or deployment workflow has run on GitHub Actions. The local strict
build passes, but a local build is not evidence that the site is published.

## Read-only evidence

| Check | Observed result |
| --- | --- |
| `GET https://api.github.com/repos/nadeem-majeedch/AITopics` | **200**; public; `has_pages: true`; `default_branch: release/v0.1.0-rc.1` |
| `GET https://api.github.com/repos/nadeem-majeedch/AITopics/pages` | **404 Not Found** |
| `GET https://nadeem-majeedch.github.io/AITopics/` | **404 Not Found** |
| Workflow runs API | **2 runs total** |
| Run 1 | Dependabot `github_actions in /. - Update`; release branch; success |
| Run 2 | Dependabot `pip in /. - Update`; release branch; success |
| Validate repository workflow | **No run found** |
| Deploy documentation workflow | **No run found** |

`has_pages: true` in the repository metadata is not proof of a live site. The
Pages API 404 is the stronger signal: Pages has not been configured with a usable
deployment source. The two Dependabot successes do not validate course content or
the MkDocs build.

## Workflow configuration after repair

### `.github/workflows/validate-docs.yml`

- Pull requests targeting `main` or `release/**`.
- Pushes to `main` or `release/**`.
- Manual `workflow_dispatch`.
- `contents: read` only; no Pages permission, no artifact upload.
- Runs licensing, `pip check`, the 269-test suite, project checks, the generated
  manifest check, notebook validation, notebook execution, source links, strict
  MkDocs, and built-site prefix checks.

### `.github/workflows/deploy-pages.yml`

- Triggered by a **successful Validate repository run on `main` or
  `release/**`**, or by manual `workflow_dispatch`.
- Does **not** deploy pull-request runs.
- Builds and checks the site, configures Pages, uploads the artifact, and deploys
  in the `github-pages` environment.
- Top-level `contents: read`; deploy job `pages: write` and `id-token: write`.
- Concurrency group `pages`, with no cancellation of an in-progress deployment.

The previous trigger allowed only a successful validation run on `main`. The
repository has no `main` branch on the remote; its default branch is the release
branch. A push to the release branch would have validated but the deployment
workflow would never have been selected. The trigger now includes `release/**`.
This is a configuration repair, not a deployment: nothing was run or published.

`mkdocs.yml` now uses:

```yaml
site_url: https://nadeem-majeedch.github.io/AITopics/
edit_uri: edit/release/v0.1.0-rc.1/docs/
```

The edit URI points at the current default branch. The publication guide records
that it must be updated after a merge to `main`.

## Required repository settings

These are one-time administrator actions; this audit did not change them.

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.** Do not
   choose "Deploy from a branch".
2. Confirm the default branch is `release/v0.1.0-rc.1`, or update `mkdocs.yml`,
   the Colab URL example, and the workflow triggers if the branch changes.
3. Leave **Enforce HTTPS** enabled after the first successful deployment.
4. Do not add a custom domain unless the owner decides to; if added, change
   `site_url` and the CNAME.
5. No repository secret is required for this build.

The `pages` API 404 is consistent with Step 1 not yet having been completed, or
with Pages never having been initialized. A maintainer must inspect the settings
before diagnosing the workflow.

## What remains before students can use the site

1. Push the local release commit and let **Validate repository** run.
2. Inspect the validation logs; do not infer success from the presence of a YAML
   file.
3. Select **GitHub Actions** as the Pages source if it is still disabled.
4. Run **Deploy documentation** (or let the successful validation run trigger it)
   and inspect the deployment receipt and job logs.
5. Verify `https://nadeem-majeedch.github.io/AITopics/`, a nested lesson, a
   rendered notebook, the stylesheet, search, and the site's own 404 page on the
   public origin.

The exact commands and checks are in
[GitHub Pages publication](GITHUB-PAGES.md#verify-publication). Do not describe
the site as published until step 5 succeeds.

## What this audit did not do

- No commit, push, tag, release, Pages enablement, or deployment.
- No change to GitHub repository settings, branch protection, environments, or
  secrets.
- No claim that a successful local build implies a successful hosted build.

For local site evidence, see the
[Navigation and link audit](navigation-and-link-audit.md). For the release
decision, see the [Final audit](final-audit.md).
