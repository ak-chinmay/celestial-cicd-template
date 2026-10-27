from __future__ import annotations

import unittest

from ci import release_version


class ReleaseVersionTests(unittest.TestCase):
    def test_initial_release_and_default_patch(self) -> None:
        self.assertEqual(release_version.choose_version([], [], []), "v0.1.0")
        self.assertEqual(
            release_version.choose_version(["v0.1.0", "not-semver"], [], []),
            "v0.1.1",
        )

    def test_release_labels_select_semantic_bump(self) -> None:
        cases = {
            "release:major": "v3.0.0",
            "release:minor": "v2.5.0",
            "release:patch": "v2.4.8",
        }
        for label, expected in cases.items():
            with self.subTest(label=label):
                self.assertEqual(
                    release_version.choose_version(["v2.4.7"], [], [label]),
                    expected,
                )

    def test_existing_target_tag_is_reused(self) -> None:
        self.assertEqual(
            release_version.choose_version(
                ["v1.0.0", "v1.1.0"],
                ["v1.1.0"],
                ["release:major"],
            ),
            "v1.1.0",
        )

    def test_conflicting_release_labels_are_rejected(self) -> None:
        with self.assertRaisesRegex(release_version.VersionError, "at most one"):
            release_version.choose_version(
                ["v1.0.0"],
                [],
                ["release:major", "release:minor"],
            )

    def test_invalid_label_json_is_rejected(self) -> None:
        for value in ("not json", "{}", '["release:patch", 1]'):
            with self.subTest(value=value):
                with self.assertRaises(release_version.VersionError):
                    release_version.parse_labels(value)


if __name__ == "__main__":
    unittest.main()
