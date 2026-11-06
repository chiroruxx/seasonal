import base64
import datetime as dt
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("distribution", Path(__file__).resolve().parents[1] / "scripts/distribution.py")
distribution = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(distribution)


class DistributionTest(unittest.TestCase):
    def test_version_code_increases_for_later_reruns(self):
        first = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
        self.assertLess(distribution.version_code(first), distribution.version_code(first + dt.timedelta(seconds=1)))
        with self.assertRaises(ValueError):
            distribution.version_code(distribution.EPOCH)

    def test_inputs_cannot_escape_or_inject_output(self):
        for story in ("../iteration0", "iteration0\ncommit=bad", "$(whoami)"):
            with self.assertRaises(ValueError):
                distribution.validate_story(story)
        for commit in ("HEAD", "a" * 39, "a" * 40 + "\n"):
            with self.assertRaises(ValueError):
                distribution.validate_commit(commit)
        self.assertEqual(distribution.validate_story("iteration0"), "iteration0")

    def test_restore_does_not_replace_a_key_and_restricts_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "debug.jks"
            with patch.dict(os.environ, {"SEASONAL_DEBUG_KEYSTORE_BASE64": base64.b64encode(b"keystore").decode()}):
                distribution.restore_key(target)
                self.assertEqual(target.read_bytes(), b"keystore")
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)
                with self.assertRaises(ValueError):
                    distribution.restore_key(target)
            with patch.dict(os.environ, {"SEASONAL_DEBUG_KEYSTORE_BASE64": "not:base64"}):
                with self.assertRaises(ValueError):
                    distribution.restore_key(Path(tmp) / "bad.jks")

    def test_missing_secrets_and_repository_key_path_are_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "missing"):
                distribution.required_env("SEASONAL_DEBUG_STORE_PASSWORD")
        with self.assertRaisesRegex(ValueError, "outside"):
            distribution.create_key(distribution.ROOT / "debug.jks")

    def test_pending_annotation_check_ignores_declarations_and_comments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "app/src/androidTest/Test.kt"
            source.parent.mkdir(parents=True)
            source.write_text("annotation class PendingAcceptance\n// @PendingAcceptance\n/* @PendingAcceptance */")
            with patch.object(distribution, "ROOT", root):
                distribution.check_pending()
                source.write_text("@PendingAcceptance\nclass Test")
                with self.assertRaisesRegex(ValueError, "remain"):
                    distribution.check_pending()


if __name__ == "__main__":
    unittest.main()
