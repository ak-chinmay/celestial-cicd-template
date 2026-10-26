#!/usr/bin/env python3
"""Fail closed unless pip requirement files use exact package pins."""

from __future__ import annotations

import re
from pathlib import Path
import sys


PIN_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*(?:\[[A-Za-z0-9_,.-]+\])?==[^=;*\s]+(?:\s*;\s*.+)?$"
)
INCLUDE_RE = re.compile(r"^(?:-r|--requirement|-c|--constraint)(?:\s+|=)(\S+)$")
MAX_FILES = 20
MAX_BYTES = 1024 * 1024


class RequirementError(RuntimeError):
    pass


def _logical_lines(path: Path) -> list[str]:
    if path.is_symlink() or not path.is_file():
        raise RequirementError("requirements-file-invalid")
    if path.stat().st_size > MAX_BYTES:
        raise RequirementError("requirements-file-too-large")
    logical: list[str] = []
    pending = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        pending += stripped
        if pending.endswith("\\"):
            pending = pending[:-1].rstrip() + " "
            continue
        logical.append(pending)
        pending = ""
    if pending:
        raise RequirementError("requirements-continuation-incomplete")
    return logical


def validate(root: Path, initial: Path) -> None:
    root = root.resolve(strict=True)
    pending = [initial]
    visited: set[Path] = set()
    pins = 0
    while pending:
        relative = pending.pop()
        lexical = root / relative
        if lexical.is_symlink():
            raise RequirementError("requirements-file-invalid")
        candidate = lexical.resolve(strict=False)
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise RequirementError("requirements-include-escapes-project") from error
        if candidate in visited:
            continue
        visited.add(candidate)
        if len(visited) > MAX_FILES:
            raise RequirementError("requirements-include-limit-exceeded")
        for line in _logical_lines(candidate):
            include = INCLUDE_RE.fullmatch(line)
            if include:
                pending.append(candidate.parent.relative_to(root) / include.group(1))
                continue
            without_hashes = re.sub(r"\s+--hash=sha256:[0-9a-fA-F]{64}", "", line)
            if not PIN_RE.fullmatch(without_hashes.strip()):
                raise RequirementError("requirements-must-use-exact-pins")
            pins += 1
    if pins == 0:
        raise RequirementError("requirements-have-no-package-pins")


def main() -> int:
    if len(sys.argv) != 2:
        print("requirements-validator-usage-error")
        return 2
    try:
        validate(Path.cwd(), Path(sys.argv[1]))
    except (OSError, UnicodeError, RequirementError) as error:
        print(str(error))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
