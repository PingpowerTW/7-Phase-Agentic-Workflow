#!/usr/bin/env python3
"""
Unit tests for local_guard.py (System 1 Local Guard & Ponytail Gate Enforcer)
Pure Python unittest standard library.
"""

import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add scripts directory to sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from local_guard import (
    normalize_path,
    match_glob,
    parse_gate_yaml_simple,
    check_gate_yaml,
    check_regex_secrets,
    run_guard
)


class TestLocalGuard(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="local_guard_test_"))
        self.gate_yaml = self.test_dir / "gate.yaml"
        self.gate_yaml.write_text(
            """version: 1
maxFiles: 3 # limit to 3 files
denylist:
  - "**/.env" # sensitive env
  - "**/.env.*"
  - "**/secrets/**"
  - "**/credentials/**"
  - "**/auth/**"
  - "**/*_key*"
""",
            encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_normalize_path(self):
        self.assertEqual(normalize_path("a\\b\\c.py"), "a/b/c.py")
        self.assertEqual(normalize_path("./src/app//index.ts"), "src/app/index.ts")
        self.assertEqual(normalize_path("  test/path.js  "), "test/path.js")

    def test_match_glob_globstar_and_root(self):
        # 1. Root and nested .env
        self.assertTrue(match_glob("**/.env", ".env"))
        self.assertTrue(match_glob("**/.env", "sub/.env"))
        self.assertTrue(match_glob("**/.env.*", ".env.local"))

        # 2. Directory prefix and nested
        self.assertTrue(match_glob("**/secrets/**", "secrets/key.txt"))
        self.assertTrue(match_glob("**/secrets/**", "app/secrets/deep/key.txt"))

        # 3. Auth directory vs file
        self.assertTrue(match_glob("**/auth/**", "auth/login.py"))
        self.assertTrue(match_glob("**/auth/**", "src/auth/service.py"))
        self.assertFalse(match_glob("**/auth/**", "author.py"))

        # 4. Pattern matching with wildcard
        self.assertTrue(match_glob("**/*_key*", "config/api_key.json"))
        self.assertTrue(match_glob("**/*_key*", "my_key_file.ts"))
        self.assertFalse(match_glob("**/*_key*", "keyboard.ts"))

    def test_check_gate_yaml_denylist(self):
        # Sensitive root-level and nested files MUST be blocked
        is_blocked, reasons = check_gate_yaml([".env"], repo_root=self.test_dir)
        self.assertTrue(is_blocked)
        self.assertTrue(any(".env" in r for r in reasons))

        is_blocked, reasons = check_gate_yaml(["auth/user.py"], repo_root=self.test_dir)
        self.assertTrue(is_blocked)
        self.assertTrue(any("auth" in r for r in reasons))

        # Safe files must pass
        is_blocked, reasons = check_gate_yaml(["src/components/Button.tsx", "docs/README.md"], repo_root=self.test_dir)
        self.assertFalse(is_blocked)
        self.assertEqual(len(reasons), 0)

    def test_check_gate_yaml_max_files(self):
        # 3 files allowed, 4 files provided -> blocked
        files = ["a.py", "b.py", "c.py", "d.py"]
        is_blocked, reasons = check_gate_yaml(files, repo_root=self.test_dir)
        self.assertTrue(is_blocked)
        self.assertTrue(any("超過 gate.yaml 上限" in r for r in reasons))

    def test_check_gate_yaml_inline_comments(self):
        denylist, max_files = parse_gate_yaml_simple(self.gate_yaml)
        self.assertEqual(max_files, 3)
        self.assertIn("**/.env", denylist)
        self.assertIn("**/secrets/**", denylist)

    def test_check_regex_secrets(self):
        # Detect OpenAI key
        code_with_key = 'const key = "sk-abcdefghijklmnopqrstuvwxyz1234567890";'
        found = check_regex_secrets(code_with_key)
        self.assertTrue(len(found) > 0)

        # Detect generic API key
        code_generic = 'api_key: "abcdef1234567890abcdef"'
        found = check_regex_secrets(code_generic)
        self.assertTrue(len(found) > 0)

        # Clean code passes
        clean_code = 'function calculateTotal(price, qty) { return price * qty; }'
        found = check_regex_secrets(clean_code)
        self.assertEqual(len(found), 0)

    def test_run_guard_clean_code(self):
        # A simple mathematical function should pass without false positive
        code = "def multiply(x, y):\n    return x * y\n"
        exit_code = run_guard(code, label="Test Clean Code")
        self.assertEqual(exit_code, 0)

    def test_run_guard_secret_block(self):
        code = 'AWS_SECRET = "AKIA1234567890123456";\n'
        exit_code = run_guard(code, label="Test Secret")
        self.assertEqual(exit_code, 1)

    def test_run_guard_overengineering_block(self):
        from unittest.mock import patch
        with patch("local_guard.query_system_one") as mock_q:
            mock_q.return_value = (
                {
                    "has_test_seam": {"noul": 0.05},
                    "ponytail_ladder": {"choice": "7_mvp", "confidence": 0.95},
                    "overengineering_score": {"score": 4.6}
                },
                "MockModel"
            )
            code = "class AbstractProxyFactoryBean:\n    pass\n"
            exit_code = run_guard(code, label="Test Overengineering")
            self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()

