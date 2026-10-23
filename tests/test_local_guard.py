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
        code_with_key = 'const key = "sk-' + 'abcdefghijklmnopqrstuvwxyz1234567890";'
        found = check_regex_secrets(code_with_key)
        self.assertTrue(len(found) > 0)

        # Detect generic API key
        code_generic = 'api_key: "' + 'abcdef1234567890abcdef"'
        found = check_regex_secrets(code_generic)
        self.assertTrue(len(found) > 0)

        # Clean code and words ending with 'sk-' (e.g. task-scheduler) pass without false positive
        clean_code = (
            "function calculateTotal(price, qty) { return price * qty; }\n"
            "// Anchor: #6-swc-ast-engine--llmcompiler-parallel-dag-task-scheduler-integration"
        )
        found = check_regex_secrets(clean_code)
        self.assertEqual(len(found), 0)

    def test_run_guard_clean_code(self):
        # A simple mathematical function should pass without false positive
        code = "def multiply(x, y):\n    return x * y\n"
        exit_code = run_guard(code, label="Test Clean Code")
        self.assertEqual(exit_code, 0)

    def test_run_guard_secret_block(self):
        code = 'AWS_SECRET = "AKIA' + '1234567890123456";\n'
        exit_code = run_guard(code, label="Test Secret")
        self.assertEqual(exit_code, 1)

    def test_run_guard_overengineering_and_handwired_relu(self):
        from unittest.mock import patch
        from local_guard import handwired_system_one, tune_handwired_weights

        # 1. Native Handwired ReLU blocks enterprise factory bloat & test seams with zero mocks
        bloated_code = (
            "class AbstractProxyFactoryBean:\n"
            "    pass\n"
            "class SingletonServiceManager:\n"
            "    pass\n"
        )
        self.assertEqual(run_guard(bloated_code, label="Handwired Overengineering"), 1)

        seam_code = "def set_mock_for_test(client):\n    return client\n"
        self.assertEqual(run_guard(seam_code, label="Handwired Seam"), 1)

        # 2. Concise one-liner maps to 6_oneliner on the Ponytail ladder
        ans = handwired_system_one("x = sum( items )\n")
        self.assertEqual(ans["ponytail_ladder"]["choice"], "6_oneliner")

        # 3. 'Learned Gallery' Differentiable Weight Unfreezing reduces loss toward human feedback & survives corrupt JSON
        with patch("pathlib.Path.cwd", return_value=self.test_dir):
            (self.test_dir / ".agent").mkdir(parents=True, exist_ok=True)
            (self.test_dir / ".agent" / "handwired_weights.json").write_text('{"w_seam": [1,2,3,4,5,6]}', encoding="utf-8")
            before = handwired_system_one(bloated_code)["overengineering_score"]["score"]
            tune_handwired_weights(bloated_code, target_seam=0.0, target_bloat=2.0, lr=0.15)
            after = handwired_system_one(bloated_code)["overengineering_score"]["score"]
            self.assertLess(after, before)

    def test_decision_regression_guard(self):
        import json
        from unittest.mock import patch
        agent_dir = self.test_dir / ".agent"
        agent_dir.mkdir(parents=True, exist_ok=True)
        snap = agent_dir / "SNAPSHOT.jsonl"
        snap.write_text(
            json.dumps({
                "type": "decision",
                "title": "Keep defaultRetryMax at 4",
                "decision": "Ten retries with backoff can block Do() for over an hour.",
                "touches": ["src/client.py#defaultRetryMax"],
                "ruled_out": ["defaultRetryMax = 10", "retries = 10"],
            }) + "\n",
            encoding="utf-8",
        )
        bad_diff = (
            "--- a/src/client.py\n"
            "+++ b/src/client.py\n"
            "@@ -10,1 +10,1 @@\n"
            "-defaultRetryMax = 4\n"
            "+defaultRetryMax = 10\n"
        )
        fix_diff = (
            "--- a/src/client.py\n"
            "+++ b/src/client.py\n"
            "@@ -10,1 +10,1 @@\n"
            "-defaultRetryMax = 10\n"
            "+defaultRetryMax = 4\n"
            "+defaultRetryMax = 100\n"
        )
        with patch("pathlib.Path.cwd", return_value=self.test_dir):
            # Re-introducing a ruled-out value on an anchored file blocks via run_guard
            self.assertEqual(run_guard(bad_diff, changed_files=["src/client.py"], label="Decision Regression"), 1)
            # Removing a ruled-out value (-defaultRetryMax = 10) or prefix-colliding token (100 vs 10) must NOT false-positive block
            self.assertEqual(run_guard(fix_diff, changed_files=["src/client.py"], label="Decision Fix"), 0)
            # Unrelated file does not trigger the file-scoped decision
            self.assertEqual(run_guard(bad_diff, changed_files=["src/other.py"], label="Other File"), 0)

            # Append-Only Revision (Latest-Wins per touches / category+subject):
            # Appending a revised decision for the same anchor supersedes the old ruled_out list,
            # while an orthogonal decision on the same file with a different subject coexists.
            with snap.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "type": "decision",
                    "category": "resilience",
                    "subject": "Retry cap",
                    "title": "Allow defaultRetryMax 10 with jitter, rule out 99",
                    "decision": "Jittered backoff makes 10 safe; 99 still blocks.",
                    "touches": ["src/client.py#defaultRetryMax"],
                    "ruled_out": ["defaultRetryMax = 99"],
                }) + "\n")
                f.write(json.dumps({
                    "type": "decision",
                    "category": "resilience",
                    "subject": "Timeout floor",
                    "title": "Never set timeout = 0",
                    "decision": "Zero timeout disables deadline protection.",
                    "touches": ["src/client.py"],
                    "ruled_out": ["timeout = 0"],
                }) + "\n")
            # Old ruled-out value (10) now passes
            self.assertEqual(run_guard(bad_diff, changed_files=["src/client.py"], label="Revised Decision Pass"), 0)
            # New ruled-out value (99) from 'Retry cap' blocks (was NOT overwritten by 'Timeout floor' on same file)
            diff_99 = "--- a/src/client.py\n+++ b/src/client.py\n@@ -10,1 +10,1 @@\n+defaultRetryMax = 99\n"
            self.assertEqual(run_guard(diff_99, changed_files=["src/client.py"], label="Revised Decision Block 99"), 1)
            # Orthogonal 'Timeout floor' decision on the same file also blocks
            diff_timeout = "--- a/src/client.py\n+++ b/src/client.py\n@@ -12,1 +12,1 @@\n+timeout = 0\n"
            self.assertEqual(run_guard(diff_timeout, changed_files=["src/client.py"], label="Coexisting Subject Block"), 1)

    def test_rollback_incident_to_eval_pipeline(self):
        import json
        import os
        import subprocess
        from local_guard import execute_rollback, evaluate_incidents

        # Initialize real git repo at test_dir boundary
        subprocess.run(["git", "init"], cwd=self.test_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.test_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Tester"], cwd=self.test_dir, check=True, capture_output=True)
        prod_file = self.test_dir / "service.py"
        prod_file.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
        subprocess.run(["git", "add", "service.py"], cwd=self.test_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "baseline"], cwd=self.test_dir, check=True, capture_output=True)

        orig_cwd = Path.cwd()
        try:
            os.chdir(self.test_dir)
            # Rollback #1: test seam backdoor
            prod_file.write_text("def add(a, b):\n    return a + b\ndef set_mock_for_test(x):\n    return x\n", encoding="utf-8")
            self.assertEqual(execute_rollback(), 0)
            self.assertNotIn("set_mock_for_test", prod_file.read_text(encoding="utf-8"))

            # Rollback #2: enterprise factory bloat (must preserve Rollback #1 in .agent/eval_incidents.jsonl!)
            prod_file.write_text("class AbstractProxyFactoryBean:\n    pass\nclass SingletonServiceManager:\n    pass\n", encoding="utf-8")
            reflexion_note = "[Reflexion] 錯誤假設: 需工廠封裝 | 根因定位: 違反YAGNI | 修正策略: 直接函式"
            self.assertEqual(execute_rollback(reflexion=reflexion_note), 0)

            inc_file = self.test_dir / ".agent" / "eval_incidents.jsonl"
            self.assertTrue(inc_file.is_file())
            lines = [ln for ln in inc_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
            self.assertEqual(len(lines), 2)
            self.assertGreater(json.loads(lines[0])["features"][0], 0.0)
            self.assertGreater(json.loads(lines[1])["features"][1], 0.0)
            self.assertEqual(json.loads(lines[1])["reflexion"], reflexion_note)

            # Verify SNAPSHOT.jsonl schema compatibility with auto-snapshot (requires 'ts' and 'project')
            snap_file = self.test_dir / ".agent" / "SNAPSHOT.jsonl"
            self.assertTrue(snap_file.is_file())
            snap_lines = [json.loads(ln) for ln in snap_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
            self.assertEqual(len(snap_lines), 2)
            self.assertIn("ts", snap_lines[1])
            self.assertNotIn("timestamp", snap_lines[1])
            self.assertEqual(snap_lines[1]["project"], self.test_dir.name)
            self.assertEqual(snap_lines[1]["type"], "failure_reflection")
            self.assertEqual(snap_lines[1]["reflexion"], reflexion_note)

            # Append corrupt JSON line to verify defensive parsing in evaluate_incidents()
            with inc_file.open("a", encoding="utf-8") as f:
                f.write("{corrupt_json_line\n")
            self.assertEqual(evaluate_incidents(), 0)
        finally:
            os.chdir(orig_cwd)

    def test_median_runtime_tracker(self):
        from local_guard import MedianRuntimeTracker
        tracker = MedianRuntimeTracker(window_size=9, min_samples=5)
        for v in [10.0, 12.0, 11.0, 9.0]:
            tracker.update(v)
            self.assertIsNone(tracker.get())
        tracker.update(500.0)  # extreme I/O spike outlier
        self.assertEqual(tracker.get(), 11.0)
        # Fill remaining window slots and verify circular eviction
        for v in [10.0, 10.0, 10.0, 10.0, 10.0]:
            tracker.update(v)
        self.assertEqual(tracker.get(), 10.0)
        self.assertEqual(tracker.adaptive_timeout_sec(10.0), 0.25)
        # Verify offline Handwired ReLU runs in run_guard do NOT pollute global _RUNTIME_TRACKER
        from local_guard import _RUNTIME_TRACKER
        _RUNTIME_TRACKER._samples.clear()
        for _ in range(6):
            run_guard("x = 1\n", label="Offline No-Pollute")
        self.assertIsNone(_RUNTIME_TRACKER.get())
        # Verify online HTTP 200 endpoint updates _RUNTIME_TRACKER while offline does not
        import http.server
        import threading
        import local_guard

        mock_payload = [b'```json\n{"has_test_seam":{"noul":0.01},"ponytail_ladder":{"choice":"7_mvp","confidence":0.9},"overengineering_score":{"score":1.2}}\n```']

        class _MockSystemOneHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                cl = int(self.headers.get("Content-Length", 0))
                if cl > 0:
                    self.rfile.read(cl)
                body = mock_payload[0]
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, format, *args):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), _MockSystemOneHandler)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        orig_url = local_guard.DECISION_API_URL
        try:
            local_guard.DECISION_API_URL = f"http://127.0.0.1:{port}/v1/systemone"
            _RUNTIME_TRACKER._samples.clear()
            for _ in range(5):
                res, mode = local_guard.query_system_one("x = 1\n")
                self.assertEqual(res.get("ponytail_ladder", {}).get("choice"), "7_mvp")
            self.assertEqual(len(_RUNTIME_TRACKER._samples), 5)
            self.assertIsNotNone(_RUNTIME_TRACKER.get())
            # Error JSON payload must Fail-Closed to Handwired ReLU and NOT pollute _RUNTIME_TRACKER
            mock_payload[0] = b'{"error": "rate limit exceeded"}'
            err_res, err_mode = local_guard.query_system_one("def set_mock_for_test(x): return x\n")
            self.assertEqual(err_mode, "Handwired ReLU (0-Token)")
            self.assertGreater(err_res["has_test_seam"]["noul"], 0.5)
            self.assertEqual(len(_RUNTIME_TRACKER._samples), 5)
        finally:
            local_guard.DECISION_API_URL = orig_url
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()



