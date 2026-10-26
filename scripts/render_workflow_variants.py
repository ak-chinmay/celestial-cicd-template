#!/usr/bin/env python3
"""Render adversarial default-branch variants for workflow linting."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys


TOKEN = "__CELESTIAL_DEFAULT_BRANCH__"
BRANCHES = ("main", "#prod", "!prod", "feature/release")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: render_workflow_variants.py OUTPUT_DIR")
    root = Path(__file__).resolve().parents[1]
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    source = root / ".github/workflows/celestial-delivery.yml"
    raw = source.read_text(encoding="utf-8")
    if raw.count(TOKEN) != 1:
        raise SystemExit("delivery workflow must contain one default-branch token")
    for index, branch in enumerate(BRANCHES):
        rendered = raw.replace(TOKEN, json.dumps(branch))
        (output / f"celestial-delivery-{index}.yml").write_text(rendered, encoding="utf-8")
    shutil.copy2(root / ".github/workflows/celestial-ci.yml", output / "celestial-ci.yml")
    shutil.copy2(root / ".github/workflows/celestial-monitor.yml", output / "celestial-monitor.yml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
