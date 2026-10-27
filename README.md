# Celestial CI/CD template

Agent-neutral CI/CD files installed by Celestial into new or existing GitHub
repositories.

Projects expose one local verification contract:

```bash
./ci/run verify
```

The template provides reusable pull-request CI, exact-artifact Cloudflare Pages
delivery, post-deployment smoke tests, idempotent semantic GitHub Releases,
optional Telegram notifications, and transition-aware production monitoring.
Third-party Actions are pinned to full commit SHAs and jobs use least-privilege
permissions.

Normal installation is performed from the Celestial source repository:

```bash
./celestial setup-cicd /absolute/path/to/project
```

See [`docs/ci-cd.md`](docs/ci-cd.md) for the project adapter contract and
required GitHub variables, secrets, and environment configuration.

## Template development

Rebuild and validate the managed-file manifest before committing changes:

```bash
python3 scripts/build_manifest.py
python3 -m unittest discover -s tests -v
bash -n ci/run
```
