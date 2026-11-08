# GitHub Pages deployment audit

Audit date: **2026-11-08**. Repository:
`https://github.com/nadeem-majeedch/AITopics`. Branch audited:
`release/v0.1.0-rc.1`.

## Verdict

**NOT DEPLOYED.** The project-site URL and the Pages API both returned HTTP 404
during this audit. No validation or deployment workflow has run on GitHub
Actions. The local build passes, but a local build is not evidence that Pages is
published.

## Read-only observations

| Check | Observed result |
| --- | --- |
| `GET https://api.github.com/repos/nadeem-majeedch/AITopics/pages` | **404 Not Found** |
| `GET https://nadeem-majeedch.github.io/AITopics/` | **404 Not Found** |
| Workflow runs API, latest five | **2 runs total** |
| Run 1 | `github_actions in /. - Update`, branch `release/v0.1.0-rc.1`, completed, success |
| Run 2 | `pip in /. - Update`, branch `release/v0.1.0-rc.1`, completed, success |
| Repository validation workflow | **No run found** |
| Pages deployment workflow | **No run found** |

The two runs are Dependabot update jobs, not the repository's validation or
deployment workflows. Their success does not validate the course content.

## Configured workflow behaviour

- `.github/workflows/validate-docs.yml` runs on pull requests targeting `main`,
  pushes to `main`, pushes to `release/**`, and manual dispatch. It validates
  licensing, installs the CI requirements, runs the 253-test suite, checks the
  project specifications, validates and executes the 26 notebooks, checks links,
  runs the strict MkDocs build, and checks the `/AITopics/` site prefix.
- `.github/workflows/deploy-pages.yml` deploys only from `main` after a
  successful validation run, or by explicit manual dispatch. It does not deploy
  automatically from a release branch.
- No commit, push, tag, release, Pages enablement, or deployment was performed
  during this audit.

## What this means

The course can be reviewed for deployment, but it is **not live for students**.
The remaining deployment steps are maintainer actions:

1. Review and merge the release work through the normal pull-request process.
2. Let the validation workflow run on GitHub Actions and inspect its result.
3. Enable GitHub Pages with the configured GitHub Actions source if it is still
   disabled.
4. Run the deployment workflow from `main`.
5. Verify the public `/AITopics/` URL, representative lesson and notebook pages,
   search, and the navigation paths on the deployed origin.

Do not describe the site as published until step 5 succeeds. The local evidence
for the site is recorded in the
[Navigation and link audit](navigation-and-link-audit.md).
