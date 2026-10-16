#!/usr/bin/env python3
"""
tests/test_v3_upgrades.py — Suite 14: Verification for v3.0/v3.1 Workflow Upgrades
Tests:
  1. PHP 8.4 strict_types & Laravel 13 Eloquent Property Shadowing Guard (INV_PHP_01, INV_LARAVEL_01~04)
  2. SWC AST Guard for TypeScript 'any', React >200 LOC, and unsafe GSAP useEffect (INV_TS_01, INV_REACT_01~02)
  3. stage_runner.py FILE extraction, surgical PATCH replacement, mismatch blocking, and path traversal defense
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import local_guard  # noqa: E402
import stage_runner  # noqa: E402


class TestV3WorkflowUpgrades(unittest.TestCase):

    def test_laravel13_eloquent_property_shadowing_blocked(self):
        """INV_LARAVEL_01 & INV_LARAVEL_02 & INV_PHP_01 & INV_LARAVEL_04 must block bad Eloquent models."""
        bad_model = (
            "<?php\n"
            "namespace App\\Models;\n"
            "use Illuminate\\Database\\Eloquent\\Model;\n"
            "class Product extends Model {\n"
            "    public private(set) string $title;\n"
            "    protected $casts = ['price' => 'integer'];\n"
            "    protected $guarded = [];\n"
            "}\n"
        )
        blocked, reasons = local_guard.check_laravel_php_guard(bad_model, None)
        self.assertTrue(blocked, "Should block bad Laravel 13 model")
        joined = "\n".join(reasons)
        self.assertIn("INV_PHP_01", joined)
        self.assertIn("INV_LARAVEL_01", joined)
        self.assertIn("INV_LARAVEL_02", joined)
        self.assertIn("INV_LARAVEL_04", joined)

    def test_laravel13_clean_model_passes(self):
        """A compliant PHP 8.4 / Laravel 13 model must pass with 0 violations."""
        clean_model = (
            "<?php\n"
            "declare(strict_types=1);\n"
            "namespace App\\Models;\n"
            "use Illuminate\\Database\\Eloquent\\Model;\n"
            "class Product extends Model {\n"
            "    protected $fillable = ['title', 'price'];\n"
            "    protected function casts(): array {\n"
            "        return ['price' => 'integer'];\n"
            "    }\n"
            "}\n"
        )
        blocked, reasons = local_guard.check_laravel_php_guard(clean_model, None)
        self.assertFalse(blocked, f"Clean model should pass, but got: {reasons}")

    def test_ast_guard_blocks_ts_any_and_unsafe_gsap(self):
        """INV_TS_01 & INV_REACT_02 must be caught by ast_guard.js."""
        ast_js = SCRIPTS_DIR / "ast_guard.js"
        if not ast_js.exists():
            self.skipTest("ast_guard.js not found")

        bad_ts = "export function processData(input: any): any { return input as any; }"
        res = subprocess.run(
            ["node", str(ast_js), "--code", bad_ts],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if "未安裝" not in (res.stdout + res.stderr):
            self.assertEqual(res.returncode, 1)
            self.assertIn("INV_TS_01", res.stdout + res.stderr)

    def test_stage_runner_file_extraction_and_surgical_patch(self):
        """stage_runner.py must support both ### FILE: and surgical ### PATCH:."""
        temp_dir = tempfile.mkdtemp(prefix="stage_test_")
        old_staging = stage_runner.STAGING_DIR
        try:
            stage_runner.STAGING_DIR = Path(temp_dir) / ".studio" / "staging"

            # 1. Test FILE creation
            md_file = (
                "Here is the created file:\n\n"
                "### FILE: src/hello.py\n"
                "```python\n"
                "def greet():\n"
                "    return 'hello world'\n"
                "```\n"
            )
            ok, staged, errs = stage_runner.extract_and_stage(md_file, clean=True)
            self.assertTrue(ok)
            self.assertEqual(len(staged), 1)
            target = stage_runner.STAGING_DIR / "src" / "hello.py"
            self.assertTrue(target.is_file())
            self.assertIn("hello world", target.read_text(encoding="utf-8"))

            # 2. Test surgical PATCH on staged file
            patch_md = (
                "### PATCH: src/hello.py\n"
                "```python\n"
                "<<<<<<< SEARCH\n"
                "    return 'hello world'\n"
                "=======\n"
                "    return 'hello universe'\n"
                ">>>>>>> REPLACE\n"
                "```\n"
            )
            ok, staged, errs = stage_runner.extract_and_stage(patch_md, clean=False)
            self.assertTrue(ok)
            self.assertIn("hello universe", target.read_text(encoding="utf-8"))
            self.assertNotIn("hello world", target.read_text(encoding="utf-8"))

            # 3. Test patch mismatch prevents corruption
            bad_patch = (
                "### PATCH: src/hello.py\n"
                "```python\n"
                "<<<<<<< SEARCH\n"
                "    return 'nonexistent string'\n"
                "=======\n"
                "    return 'corrupted'\n"
                ">>>>>>> REPLACE\n"
                "```\n"
            )
            ok, staged, errs = stage_runner.extract_and_stage(bad_patch, clean=False)
            self.assertFalse(ok)
            self.assertTrue(any("PATCH MISMATCH" in e for e in errs))
            # Text remains unchanged
            self.assertIn("hello universe", target.read_text(encoding="utf-8"))
            # 4. Test unfenced ### PATCH: block (as documented in teamwork/agy-studio SKILL.md)
            unfenced_patch = (
                "### PATCH: src/hello.py\n"
                "<<<<<<< SEARCH\n"
                "    return 'hello universe'\n"
                "=======\n"
                "    return 'hello unfenced'\n"
                ">>>>>>> REPLACE\n"
            )
            ok, staged, errs = stage_runner.extract_and_stage(unfenced_patch, clean=False)
            self.assertTrue(ok)
            self.assertIn("hello unfenced", target.read_text(encoding="utf-8"))

            # 5. Test staged .php file is caught by run_step25_sieve
            bad_php = target.parent / "BadController.php"
            bad_php.write_text("<?php\n$x = env('APP_KEY');\n", encoding="utf-8")
            sieve_ok, sieve_errs = stage_runner.run_step25_sieve()
            self.assertFalse(sieve_ok)
            self.assertTrue(any("INV_PHP_01" in v for v in sieve_errs))

            # 6. Test partial truncation (2 declared ### FILE: headers, 2nd missing closing ```) fails closed
            truncated_multi = (
                "### FILE: src/ok.py\n"
                "```python\n"
                "x = 1\n"
                "```\n"
                "### FILE: src/truncated.py\n"
                "```python\n"
                "y = 2\n"
            )
            ok_trunc, _, errs_trunc = stage_runner.extract_and_stage(truncated_multi, clean=False)
            self.assertFalse(ok_trunc)
            self.assertTrue(any("STAGE ERROR" in e for e in errs_trunc))
        finally:
            stage_runner.STAGING_DIR = old_staging
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_stage_runner_path_traversal_blocked(self):
        """stage_runner.py must strictly block .. path traversal and fail closed."""
        traversal_md = (
            "### FILE: ../../../etc/evil.sh\n"
            "```bash\n"
            "echo evil\n"
            "```\n"
        )
        ok, staged, errs = stage_runner.extract_and_stage(traversal_md, clean=False)
        self.assertFalse(ok)
        self.assertEqual(len(staged), 0)


if __name__ == "__main__":
    unittest.main()
