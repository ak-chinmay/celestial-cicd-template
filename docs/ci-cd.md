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
NOTIFICATIONS_ENABLED
MONITOR_ENABLED
SMOKE_MARKERS
```

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

## Template updates

Run the same Celestial installation command again. Files unchanged since their
last installation may update automatically. Locally modified files are retained
and listed in `.celestial/cicd-install-report.md` for manual resolution in the
installation pull request.
