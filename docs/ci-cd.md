# Project CI/CD contract

## Local commands

Every contributor and agent uses the same entry point:

```bash
./ci/run verify
./ci/run smoke "$PRODUCTION_URL"
```

The checked-in adapter is conservative. It supports a locked Node project with
a `test` and `build` script, or a Python project with pinned development
requirements, pytest, and a checked-in `site/` deployment directory. Customize
`ci/run` when the project has a different verified build contract.

`verify` recreates `.ci/artifact/`, installs locked dependencies, runs available
format/lint checks, runs mandatory tests, and creates the production artifact.
It fails when no supported production artifact can be identified.

`smoke` makes three bounded requests to `PRODUCTION_URL`. Set optional
`CELESTIAL_SMOKE_MARKERS` to comma-separated public strings that must occur in
the response. Response bodies and sensitive headers are never printed.

## Workflows

- `celestial-ci.yml` verifies pull requests and is reusable by delivery.
- `celestial-delivery.yml` reuses CI for the exact default-branch SHA, downloads
  that artifact, deploys it to Cloudflare Pages, and smoke-tests production.
- `celestial-monitor.yml` performs scheduled/manual smoke checks and notifies
  only on failure/recovery transitions.

Existing project workflows may remain alongside these namespaced files. Do not
copy logic between workflow files; keep project-specific behavior in `ci/run`.

## GitHub configuration

Repository variables:

```text
PRODUCTION_URL
CLOUDFLARE_PROJECT
CLOUDFLARE_PRODUCTION_BRANCH
NOTIFICATIONS_ENABLED
MONITOR_ENABLED
SMOKE_MARKERS
```

`CLOUDFLARE_PRODUCTION_BRANCH` must exactly match the production branch configured for the Cloudflare Pages project. Other branch names create preview deployments.

Repository secrets:

```text
CLOUDFLARE_API_TOKEN
CLOUDFLARE_ACCOUNT_ID
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

Create a protected GitHub environment named `production`. Add required human
reviewers when production delivery needs approval.

CI receives no secrets. Deployment receives only Cloudflare credentials.
Notification steps receive only Telegram credentials. With notifications
disabled, missing Telegram secrets do not block CI or delivery.

## Manual recovery

Use the delivery workflow's `workflow_dispatch` input with a full lowercase
commit SHA reachable from the default branch. The workflow refuses abbreviated,
foreign, or unverified commits and never rebuilds inside the deployment job.

## GitHub releases

After deployment and the production smoke test succeed, the delivery workflow
looks up the merged pull request whose merge commit is the exact delivery SHA.
When exactly one pull request targets the repository default branch, the
workflow creates an idempotent GitHub Release. The pull request title becomes
the release title, while GitHub-generated release notes provide the changelog.

Release versions use semantic tags. Add one optional pull request label to
choose the next increment:

```text
release:major
release:minor
release:patch
```

With no release label, the workflow increments the patch version. The first
release is `v0.1.0`. On a new target, conflicting release labels fail before
creating a tag.
Rerunning delivery for a SHA that already has a semantic tag reuses that tag;
an existing release is left unchanged, and a matching tag without a release is
published with that tag.

Direct pushes and manual recovery targets without exactly one matching merged
pull request still deploy successfully, but release creation is skipped and
the reason is written to the workflow summary. No additional secret or
repository variable is required; the release job uses the workflow's scoped
`GITHUB_TOKEN`. The context job receives `pull-requests: read`, while only the
publishing job receives `contents: write`.

Telegram delivery notifications include the merged pull request number and
title, the release version and URL (or an explicit skipped/not-published
status), and the production URL. Failure notifications also include the
workflow run URL. Commit SHAs are intentionally omitted from these messages.

## Template updates

Run the same Celestial installation command again. Files unchanged since their
last installation may update automatically. Locally modified files are retained
and listed in `.celestial/cicd-install-report.md` for manual resolution in the
installation pull request.
