#!/usr/bin/env python3
"""
Unit tests for loop_drift.py (Loop Sentinel Drift & Invariants Inspector)
Pure Python unittest standard library.
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add scripts directory to sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from loop_drift import (
    normalize_path,
    match_glob,
    parse_simple_yaml,
    DriftInspector
)


class TestLoopDrift(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="drift_test_"))
        # Create minimal gate.yaml
        gate_yaml = self.test_dir / "gate.yaml"
        gate_yaml.write_text(
            """version: 1
maxFiles: 3
denylist:
  - "**/.env*"
  - "**/secrets/**"
  - "**/credentials/**"
autoMergeAllowlist:
  - "docs/**"
  - "**/*.md"
  - "**/*.test.py"
""",
            encoding="utf-8"
        )

        # Create minimal STATE.md
        state_md = self.test_dir / "STATE.md"
        state_md.write_text(
            """# Loop State
Last run: 2026-09-20T11:00:00+08:00
## High Priority
- [x] Initialized
""",
            encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_normalize_path(self):
        self.assertEqual(normalize_path("src\\utils\\helper.py"), "src/utils/helper.py")
        self.assertEqual(normalize_path("./scripts/test.py"), "scripts/test.py")
        self.assertEqual(normalize_path("a//b///c.txt"), "a/b/c.txt")

    def test_match_glob(self):
        self.assertTrue(match_glob("**/.env*", ".env"))
        self.assertTrue(match_glob("**/.env*", "config/.env.local"))
        self.assertTrue(match_glob("**/secrets/**", "backend/secrets/db_pass.txt"))
        self.assertFalse(match_glob("**/secrets/**", "src/public/index.html"))

    def test_denylist_violation(self):
        inspector = DriftInspector(root_dir=self.test_dir)
        res = inspector.audit(target_files=["src/app.py", "backend/secrets/jwt.key"])
        self.assertEqual(res["status"], "CRITICAL")
        self.assertEqual(res["exit_code"], 2)
        rules = [f["rule_id"] for f in res["findings"]]
        self.assertIn("INV_SAFE_03", rules)

    def test_max_files_exceeded(self):
        inspector = DriftInspector(root_dir=self.test_dir)
        # 4 significant files when maxFiles is 3
        res = inspector.audit(target_files=["f1.py", "f2.py", "f3.py", "f4.py"])
        self.assertEqual(res["status"], "CRITICAL")
        rules = [f["rule_id"] for f in res["findings"]]
        self.assertIn("INV_SCOPE_01", rules)

    def test_secret_detection(self):
        secret_file = self.test_dir / "config.py"
        # Split string literal so scanner doesn't flag this test file itself
        secret_file.write_text('API_KEY = "' + 'sk-live-1234567890abcdef1234567890' + '"', encoding="utf-8")

        inspector = DriftInspector(root_dir=self.test_dir)
        res = inspector.audit(target_files=["config.py"])
        self.assertEqual(res["status"], "CRITICAL")
        rules = [f["rule_id"] for f in res["findings"]]
        self.assertIn("INV_SAFE_01", rules)

    def test_secret_detection_ignores_mock(self):
        mock_file = self.test_dir / "mock_config.py"
        mock_file.write_text('API_KEY = "mock-live-1234567890abcdef1234567890"', encoding="utf-8")

        inspector = DriftInspector(root_dir=self.test_dir)
        res = inspector.audit(target_files=["mock_config.py"])
        # Should not flag mock as critical secret
        secret_findings = [f for f in res["findings"] if f["rule_id"] == "INV_SAFE_01"]
        self.assertEqual(len(secret_findings), 0)

    def test_code_without_tests_warning(self):
        code_file = self.test_dir / "service.py"
        code_file.write_text("def serve(): pass", encoding="utf-8")

        inspector = DriftInspector(root_dir=self.test_dir)
        res = inspector.audit(target_files=["service.py"])
        # Status should be WARNING due to lack of companion tests
        self.assertEqual(res["status"], "WARNING")
        rules = [f["rule_id"] for f in res["findings"]]
        self.assertIn("INV_SCOPE_02", rules)

    def test_code_with_tests_passes(self):
        code_file = self.test_dir / "service.py"
        code_file.write_text("def serve(): pass", encoding="utf-8")
        test_file = self.test_dir / "tests" / "service.test.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("def test_serve(): pass", encoding="utf-8")

        inspector = DriftInspector(root_dir=self.test_dir)
        res = inspector.audit(target_files=["service.py", "tests/service.test.py"])
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["exit_code"], 0)

    def test_unquoted_yaml_secret_detection(self):
        yaml_file = self.test_dir / "config.yaml"
        # Unquoted secret in YAML
        yaml_file.write_text("auth_token: " + "ghp_1234567890abcdef1234567890\n", encoding="utf-8")

        inspector = DriftInspector(root_dir=self.test_dir)
        res = inspector.audit(target_files=["config.yaml"])
        self.assertEqual(res["status"], "CRITICAL")
        rules = [f["rule_id"] for f in res["findings"]]
        self.assertIn("INV_SAFE_01", rules)

    def test_malformed_timestamp_warning(self):
        state_file = self.test_dir / "STATE.md"
        state_file.write_text("# Loop State\nLast run: INVALID_DATE_FORMAT_HERE\n", encoding="utf-8")

        inspector = DriftInspector(root_dir=self.test_dir)
        res = inspector.audit(target_files=[])
        # Should flag missing or malformed ISO timestamp
        rules = [f["rule_id"] for f in res["findings"]]
        self.assertIn("INV_STATE_01", rules)


if __name__ == "__main__":
    unittest.main()
