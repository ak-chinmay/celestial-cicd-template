#!/usr/bin/env python3
"""Build the deterministic managed-file manifest for the CI/CD template."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".celestial" / "cicd-template-manifest.json"
TEMPLATE_VERSION = "1.0.0"
MANAGED_FILES = (
    (".github/pull_request_template.md", "0644", ()),
    (".github/workflows/celestial-ci.yml", "0644", ()),
    (
        ".github/workflows/celestial-delivery.yml",
        "0644",
        ("default_branch",),
    ),
    (".github/workflows/celestial-monitor.yml", "0644", ()),
    ("AGENTS.md", "0644", ()),
    ("CLAUDE.md", "0644", ()),
    ("ci/notify.py", "0755", ()),
    ("ci/run", "0755", ()),
    ("docs/ci-cd.md", "0644", ()),
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest() -> dict[str, object]:
    files = []
    for relative, mode, renders in MANAGED_FILES:
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            raise SystemExit(f"Managed template file missing or unsafe: {relative}")
        entry: dict[str, object] = {
            "path": relative,
            "sha256": digest(path),
            "mode": mode,
        }
        if renders:
            entry["render"] = list(renders)
        files.append(entry)
    return {
        "schema_version": 1,
        "template": "celestial-cicd-template",
        "template_version": TEMPLATE_VERSION,
        "files": files,
    }


def main() -> int:
    MANIFEST.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    MANIFEST.write_text(
        json.dumps(build_manifest(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
