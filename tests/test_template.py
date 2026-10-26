from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".celestial" / "cicd-template-manifest.json"
REMOTE_ACTION = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")


class TemplateTests(unittest.TestCase):
    def test_manifest_matches_managed_files(self) -> None:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["template"], "celestial-cicd-template")
        paths = []
        for entry in payload["files"]:
            relative = entry["path"]
            self.assertNotIn("..", Path(relative).parts)
            path = ROOT / relative
            self.assertTrue(path.is_file())
            self.assertFalse(path.is_symlink())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"])
            expected_mode = int(entry["mode"], 8)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), expected_mode)
            paths.append(relative)
        self.assertEqual(paths, sorted(set(paths)))

    def test_workflows_pin_remote_actions_and_avoid_target_trigger(self) -> None:
        for path in sorted((ROOT / ".github" / "workflows").glob("celestial-*.yml")):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("pull_request_target", text)
            for raw in text.splitlines():
                line = raw.strip()
                if not line.startswith("uses:"):
                    continue
                value = line.split("uses:", 1)[1].strip().split()[0]
                if value.startswith("./"):
                    continue
                self.assertRegex(value, REMOTE_ACTION)

    def test_delivery_reuses_exact_artifact_without_cancellation(self) -> None:
        text = (ROOT / ".github/workflows/celestial-delivery.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("cancel-in-progress: false", text)
        self.assertIn("celestial-production-${{ needs.resolve.outputs.target_sha }}", text)
        self.assertIn("git merge-base --is-ancestor", text)
        self.assertNotIn("pull_request_target", text)

    def test_static_site_adapter_builds_nonempty_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            (project / "site").mkdir()
            (project / "site" / "index.html").write_text("hello", encoding="utf-8")
            (project / "ci").mkdir()
            shutil.copy2(ROOT / "ci" / "run", project / "ci" / "run")
            os.chmod(project / "ci" / "run", 0o755)
            completed = subprocess.run(
                [str(project / "ci" / "run"), "verify"],
                cwd=project,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                (project / ".ci" / "artifact" / "index.html").read_text(
                    encoding="utf-8"
                ),
                "hello",
            )

    def test_smoke_rejects_non_https_without_echoing_value(self) -> None:
        completed = subprocess.run(
            [str(ROOT / "ci" / "run"), "smoke", "http://secret.invalid/path"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertNotIn("secret.invalid", completed.stderr)

    def test_notification_client_rejects_missing_credentials(self) -> None:
        environment = dict(os.environ)
        environment.pop("TELEGRAM_BOT_TOKEN", None)
        environment.pop("TELEGRAM_CHAT_ID", None)
        completed = subprocess.run(
            ["python3", str(ROOT / "ci" / "notify.py"), "--check"],
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout.strip(), "notification-credentials-invalid")


if __name__ == "__main__":
    unittest.main()
