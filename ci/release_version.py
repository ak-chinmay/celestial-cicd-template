#!/usr/bin/env python3
"""Choose an idempotent semantic release tag for a target commit."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass


SEMVER_PATTERN = re.compile(
    r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)
RELEASE_LABELS = {
    "release:major": "major",
    "release:minor": "minor",
    "release:patch": "patch",
}


class VersionError(ValueError):
    """Raised when release version inputs are unsafe or ambiguous."""


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def from_tag(cls, tag: str) -> Version | None:
        match = SEMVER_PATTERN.fullmatch(tag)
        if match is None:
            return None
        return cls(*(int(component) for component in match.groups()))

    def tag(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"

    def bump(self, kind: str) -> Version:
        if kind == "major":
            return Version(self.major + 1, 0, 0)
        if kind == "minor":
            return Version(self.major, self.minor + 1, 0)
        if kind == "patch":
            return Version(self.major, self.minor, self.patch + 1)
        raise VersionError(f"Unsupported release bump: {kind}")


def select_bump(labels: Iterable[str]) -> str:
    selected = {RELEASE_LABELS[label] for label in labels if label in RELEASE_LABELS}
    if len(selected) > 1:
        raise VersionError(
            "Use at most one release:major, release:minor, or release:patch label"
        )
    return next(iter(selected), "patch")


def choose_version(
    all_tags: Iterable[str],
    target_tags: Iterable[str],
    labels: Iterable[str],
) -> str:
    target_versions = [
        version
        for tag in target_tags
        if (version := Version.from_tag(tag)) is not None
    ]
    if target_versions:
        return max(target_versions).tag()

    bump = select_bump(labels)
    versions = [
        version
        for tag in all_tags
        if (version := Version.from_tag(tag)) is not None
    ]
    if not versions:
        return "v0.1.0"
    return max(versions).bump(bump).tag()


def git_tags(*arguments: str) -> list[str]:
    result = subprocess.run(
        ["git", "tag", *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


def parse_labels(value: str) -> list[str]:
    try:
        labels = json.loads(value or "[]")
    except json.JSONDecodeError as error:
        raise VersionError("Release labels must be a JSON array") from error
    if not isinstance(labels, list) or not all(
        isinstance(label, str) for label in labels
    ):
        raise VersionError("Release labels must be a JSON array of strings")
    return labels


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-sha", required=True)
    parser.add_argument("--labels-json", default="[]")
    arguments = parser.parse_args()

    version = choose_version(
        git_tags("--list"),
        git_tags("--points-at", arguments.target_sha),
        parse_labels(arguments.labels_json),
    )
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
