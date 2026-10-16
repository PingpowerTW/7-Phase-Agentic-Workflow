#!/usr/bin/env python3
"""
7-Phase Agentic Workflow - Loop Engineering Physical Safety Gate
Pure Python Standard Library (Zero External Dependencies).

Enforces machine-readable safety gates from gate.yaml:
1. Path Denylist: Blocks access to sensitive/secret paths (.env, credentials, auth, billing, migrations).
2. Max Files Limit: Halts and escalates if changes exceed the maximum file threshold (default 8).
3. Cross-Platform Path Normalization: Prevents Windows backslash (`\\`) bypass vulnerabilities.
4. Auto-Merge Allowlist: Confirms whether changed paths qualify for safe auto-merge.

Exit codes:
  0: PASS (All checks cleared)
  2: REJECT / ESCALATE (Denylist triggered or file count exceeded)
  1: ERROR (Config missing or invalid)
"""

import sys
import os
import re
import fnmatch
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GATE_PATH = REPO_ROOT / "gate.yaml" if (REPO_ROOT / "gate.yaml").exists() else (REPO_ROOT / "templates" / "loop-engineering" / "gate.yaml")


def normalize_path(path_str: str) -> str:
    """Normalize file path to POSIX forward-slashes and clean traversal segments."""
    cleaned = path_str.replace("\\", "/").strip()
    # Remove leading ./
    if cleaned.startswith("./"):
        cleaned = cleaned[2:]
    # Collapse duplicate slashes
    cleaned = re.sub(r"/+", "/", cleaned)
    return cleaned


def match_glob(pattern: str, file_path: str) -> bool:
    """
    Robust glob matching supporting '**' recursive wildcard.
    Handles exact, prefix, suffix, and directory patterns across platforms.
    """
    norm_pat = normalize_path(pattern)
    norm_path = normalize_path(file_path)

    # Direct equality
    if norm_pat == norm_path:
        return True

    # If pattern starts with **/, also test without the prefix
    if norm_pat.startswith("**/"):
        sub_pat = norm_pat[3:]
        # Match filename directly or any subpath
        if fnmatch.fnmatch(norm_path, norm_pat) or fnmatch.fnmatch(norm_path, sub_pat):
            return True
        # Check if basename matches
        base_name = norm_path.split("/")[-1]
        if fnmatch.fnmatch(base_name, sub_pat):
            return True
        if sub_pat.endswith("/**"):
            sub_prefix = sub_pat[:-3]
            if norm_path.startswith(sub_prefix + "/") or norm_path == sub_prefix:
                return True

    # Standard fnmatch
    if fnmatch.fnmatch(norm_path, norm_pat):
        return True

    # If pattern ends with /**, match any path that starts with directory prefix
    if norm_pat.endswith("/**"):
        prefix = norm_pat[:-3]
        if norm_path.startswith(prefix + "/") or norm_path == prefix:
            return True

    return False


def find_gate_file(custom_root: Optional[Path] = None) -> Optional[Path]:
    """Multi-level fallback resolution for gate.yaml configuration."""
    root = custom_root or REPO_ROOT
    candidates = [
        root / "gate.yaml",
        Path.cwd() / "gate.yaml",
        root / "templates" / "loop-engineering" / "gate.yaml",
        REPO_ROOT / "templates" / "loop-engineering" / "gate.yaml",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def parse_gate_yaml(gate_path: Path) -> Dict[str, Any]:
    """
    Lightweight, robust YAML parser for gate.yaml without PyYAML dependency.
    Safely parses version, maxFiles, denylist, and autoMergeAllowlist (stripping inline comments).
    """
    if not gate_path.exists():
        found = find_gate_file(gate_path.parent)
        if found:
            gate_path = found
        else:
            raise FileNotFoundError(f"gate.yaml not found at {gate_path}")

    content = gate_path.read_text(encoding="utf-8", errors="replace")

    config: Dict[str, Any] = {
        "version": 1,
        "maxFiles": 8,
        "denylist": [],
        "autoMergeAllowlist": []
    }

    current_section = None
    for raw_line in content.splitlines():
        trimmed = raw_line.split("#")[0].strip()
        if not trimmed:
            continue

        # Top-level keys
        if trimmed.startswith("version:"):
            current_section = None
            try:
                config["version"] = int(trimmed.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif trimmed.startswith("maxFiles:"):
            current_section = None
            try:
                config["maxFiles"] = int(trimmed.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif trimmed.startswith("denylist:"):
            current_section = "denylist"
        elif trimmed.startswith("autoMergeAllowlist:"):
            current_section = "autoMergeAllowlist"
        elif trimmed.startswith("-") and current_section in config:
            val = trimmed.lstrip("- ").strip().strip("\"'").strip()
            if val:
                config[current_section].append(val)
        elif not trimmed.startswith("-"):
            current_section = None

    return config


class LoopGateEnforcer:
    """Mechanical gatekeeper enforcing physical boundaries before file I/O."""

    def __init__(self, gate_config_path: Optional[Path] = None):
        self.config_path = gate_config_path or DEFAULT_GATE_PATH
        self.config = parse_gate_yaml(self.config_path)
        self.max_files = self.config.get("maxFiles", 8)
        self.denylist = self.config.get("denylist", [])
        self.allowlist = self.config.get("autoMergeAllowlist", [])

    def check_paths(self, changed_paths: List[str]) -> Tuple[bool, List[str], str]:
        """
        Verify list of changed files against physical constraints.
        Returns: (passed: bool, violations: List[str], reason: str)
        """
        violations = []

        # Check 1: Denylist matching with cross-platform normalization (applies to ALL files)
        for path in changed_paths:
            norm_p = normalize_path(path)
            for pat in self.denylist:
                if match_glob(pat, norm_p):
                    violations.append(f"Blocked by '{pat}': {path}")
                    break

        if violations:
            return False, violations, f"Path Denylist triggered: {len(violations)} restricted file(s) detected."

        # Check 2: Max files threshold (autoMergeAllowlist docs/markdown do not count toward code limit)
        code_files = [
            p for p in changed_paths
            if not any(match_glob(pat, normalize_path(p)) for pat in self.allowlist)
        ]
        if len(code_files) > self.max_files:
            return False, [], f"Exceeded maximum file threshold ({len(code_files)} > {self.max_files})"

        return True, [], "All physical gates cleared."

    def is_auto_merge_allowed(self, changed_paths: List[str]) -> bool:
        """Check if all files belong strictly to autoMergeAllowlist."""
        if not changed_paths:
            return False

        for path in changed_paths:
            norm_p = normalize_path(path)
            matched = any(match_glob(pat, norm_p) for pat in self.allowlist)
            if not matched:
                return False
        return True


def run_tests() -> bool:
    """Adversarial test suite verifying denylist, windows backslashes, and maxFiles."""
    enforcer = LoopGateEnforcer()

    # Adversarial Test 1: Standard denylist files
    ok1, v1, r1 = enforcer.check_paths([".env", "credentials/service.json"])
    assert not ok1 and len(v1) == 2, f"Failed to block standard denylist: {v1}"

    # Adversarial Test 2: Windows backslash bypass attempt
    ok2, v2, r2 = enforcer.check_paths(["auth\\login.py", "secrets\\keys.pem", "billing\\invoice.ts"])
    assert not ok2 and len(v2) == 3, f"Windows backslash bypass succeeded! Violations: {v2}"

    # Adversarial Test 3: Prefix variation (.env.production, .env.local)
    ok3, v3, r3 = enforcer.check_paths(["frontend/.env.production"])
    assert not ok3 and len(v3) == 1, f"Failed to block .env.production: {v3}"

    # Adversarial Test 4: Max files violation (> 8 files)
    fake_files = [f"src/module_{i}.py" for i in range(10)]
    ok4, v4, r4 = enforcer.check_paths(fake_files)
    assert not ok4 and "threshold" in r4, f"Failed to block file count overflow: {r4}"

    # Adversarial Test 4b: autoMergeAllowlist (.md / docs/**) excluded from maxFiles count
    mixed_files = [f"src/module_{i}.py" for i in range(6)] + [f"docs/doc_{i}.md" for i in range(5)]
    ok4b, v4b, r4b = enforcer.check_paths(mixed_files)
    assert ok4b and len(v4b) == 0, f"Allowlist .md files should not trigger maxFiles overflow: {r4b}"

    # Adversarial Test 5: Clean safe changes
    safe_files = ["src/app.py", "src/components/Button.tsx", "tests/test_app.py"]
    ok5, v5, r5 = enforcer.check_paths(safe_files)
    assert ok5 and len(v5) == 0, f"Safe files incorrectly blocked: {v5}"

    # Adversarial Test 6: Auto-merge allowlist verification
    allow_ok = enforcer.is_auto_merge_allowed(["docs/guide.md", "README.md"])
    assert allow_ok, "Auto-merge allowlist failed for markdown docs"

    allow_reject = enforcer.is_auto_merge_allowed(["docs/guide.md", "src/auth.py"])
    assert not allow_reject, "Auto-merge allowed non-allowlist file!"

    print("[PASS] LoopGateEnforcer: 6/6 adversarial assertions passed cleanly (Backslash Bypass, Glob, MaxFiles).")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        ok = run_tests()
        sys.exit(0 if ok else 1)

    # CLI check mode
    if len(sys.argv) > 1:
        paths = sys.argv[1:]
        enforcer = LoopGateEnforcer()
        passed, violations, reason = enforcer.check_paths(paths)
        if passed:
            print(f"✓ Gate Cleared: {reason}")
            sys.exit(0)
        else:
            print(f"🚨 GATE VIOLATION (Exit 2): {reason}")
            for v in violations:
                print(f"   - {v}")
            sys.exit(2)
    else:
        print("Usage: python loop_gate.py <file1> <file2> ... | --test")
        sys.exit(1)
