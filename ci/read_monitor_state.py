#!/usr/bin/env python3
"""Read one bounded Celestial monitor-state value from an artifact archive."""

from __future__ import annotations

from pathlib import Path
import stat
import sys
import zipfile


MAX_ARCHIVE_BYTES = 1024 * 1024
MAX_STATE_BYTES = 16
VALID_STATES = {"success", "failure"}


def read_state(path: Path) -> str:
    metadata = path.lstat()
    if (
        not stat.S_ISREG(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or metadata.st_size > MAX_ARCHIVE_BYTES
    ):
        raise ValueError("invalid archive")
    with zipfile.ZipFile(path) as archive:
        entries = [
            entry
            for entry in archive.infolist()
            if entry.filename == "state" and not entry.is_dir()
        ]
        if len(entries) != 1 or entries[0].file_size > MAX_STATE_BYTES:
            raise ValueError("invalid state entry")
        value = archive.read(entries[0]).decode("ascii").strip()
    if value not in VALID_STATES:
        raise ValueError("invalid state value")
    return value


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    try:
        value = read_state(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile):
        return 1
    print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
