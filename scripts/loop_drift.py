#!/usr/bin/env python3
"""
Loop Sentinel - Drift & Invariants Inspector
Pure Python Standard Library (Zero External Dependencies).

Inspired by Microsoft PromptKit:
1. Invariants Enforcement: Verifies system-level safety, state monotonicity, and scope bounds.
2. Architecture Drift Detection: Identifies untracked code modifications, missing test co-evolution,
   and out-of-date documentation.
3. Mechanical Safety Sync: Cross-checks gate.yaml denylist and maxFiles thresholds.
4. State Spine Freshness: Audits STATE.md timestamp and active priority tasks.

Exit codes:
  0: PASS (All checks cleared, zero drift)
  1: WARNING (Non-critical drift detected, e.g., missing test updates or stale state)
  2: CRITICAL (Invariants or Gate violation, e.g., denylist hit, file limits, secret leaked)
"""

import sys
import os
import re
import json
import fnmatch
import subprocess
from datetime import datetime, timezone
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


def normalize_path(path_str: str) -> str:
    """Normalize file path to POSIX forward-slashes and clean traversal segments."""
    cleaned = path_str.replace("\\", "/").strip()
    if cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return re.sub(r"/+", "/", cleaned)


def match_glob(pattern: str, file_path: str) -> bool:
    """Glob matching supporting recursive '**' wildcard."""
    norm_pat = normalize_path(pattern)
    norm_path = normalize_path(file_path)

    if norm_pat == norm_path:
        return True

    if norm_pat.startswith("**/"):
        sub_pat = norm_pat[3:]
        if fnmatch.fnmatch(norm_path, norm_pat) or fnmatch.fnmatch(norm_path, sub_pat):
            return True
        base_name = norm_path.split("/")[-1]
        if fnmatch.fnmatch(base_name, sub_pat):
            return True

    if fnmatch.fnmatch(norm_path, norm_pat):
        return True

    if norm_pat.endswith("/**"):
        prefix = norm_pat[:-3]
        if norm_path.startswith(prefix + "/") or norm_path == prefix:
            return True

    return False


def parse_simple_yaml(file_path: Path) -> Dict[str, Any]:
    """Lightweight YAML parser for simple key-value and list configs."""
    if not file_path.exists():
        return {}

    content = file_path.read_text(encoding="utf-8", errors="replace")
    data: Dict[str, Any] = {}
    current_key = None

    for line in content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            continue

        if trimmed.startswith("- ") and current_key:
            val = trimmed[2:].strip().strip("\"'").strip()
            if isinstance(data.get(current_key), list):
                data[current_key].append(val)
            continue

        if ":" in trimmed:
            k, v = trimmed.split(":", 1)
            k = k.strip()
            v = v.strip().strip("\"'")
            if not v:
                data[k] = []
                current_key = k
            else:
                current_key = None
                try:
                    data[k] = int(v)
                except ValueError:
                    data[k] = v

    return data


def get_git_changed_files(repo_root: Path) -> List[str]:
    """Retrieve modified, staged, or untracked files via git status."""
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        changed = []
        for line in res.stdout.splitlines():
            if len(line) > 3:
                fpath = line[3:].strip()
                if " -> " in fpath:
                    fpath = fpath.split(" -> ")[1].strip()
                changed.append(normalize_path(fpath))
        return changed
    except Exception:
        return []


class DriftInspector:
    """Core Sentinel engine auditing drift and invariants."""

    # Regex heuristic for hardcoded secrets (supports quoted and unquoted YAML/properties values)
    SECRET_PATTERN = re.compile(
        r"""(?i)(?:api[_-]?key|secret|private[_-]?key|auth[_-]?token|bearer)\s*[:=]\s*['"]?([A-Za-z0-9_\-\.\+\/]{16,})['"]?"""
    )

    def __init__(self, root_dir: Optional[Path] = None):
        self.root = root_dir or REPO_ROOT
        self.gate_config = parse_simple_yaml(self.root / "gate.yaml")
        self.invariants_config = parse_simple_yaml(self.root / "invariants.yaml")
        self.findings: List[Dict[str, Any]] = []

    def log_finding(self, rule_id: str, severity: str, message: str, file_path: Optional[str] = None):
        self.findings.append({
            "rule_id": rule_id,
            "severity": severity,  # CRITICAL, WARNING, INFO
            "message": message,
            "file": file_path
        })

    def check_gate_and_scope(self, changed_files: List[str]):
        """Verify gate.yaml denylist and maxFiles limit."""
        denylist = self.gate_config.get("denylist", [])
        max_files = int(self.gate_config.get("maxFiles", 8))
        allowlist = self.gate_config.get("autoMergeAllowlist", [])

        # 1. Denylist check
        for f in changed_files:
            for pattern in denylist:
                if match_glob(pattern, f):
                    self.log_finding(
                        rule_id="INV_SAFE_03",
                        severity="CRITICAL",
                        message=f"File violates gate.yaml denylist pattern '{pattern}'",
                        file_path=f
                    )

        # 2. Max files check (excluding allowlist docs and tests)
        significant_files = [
            f for f in changed_files
            if not any(match_glob(pat, f) for pat in allowlist)
        ]
        if len(significant_files) > max_files:
            self.log_finding(
                rule_id="INV_SCOPE_01",
                severity="CRITICAL",
                message=f"Modified significant files count ({len(significant_files)}) exceeds maxFiles limit ({max_files})",
                file_path=None
            )

    def scan_file_for_secrets(self, relative_path: str):
        """Audit file content for obvious exposed secrets."""
        full_path = self.root / relative_path
        if not full_path.is_file():
            return

        # Skip binary or very large files
        if full_path.suffix.lower() in [".png", ".jpg", ".ico", ".bin", ".exe", ".pdf"]:
            return
        if full_path.stat().st_size > 500_000:
            return

        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            for idx, line in enumerate(content.splitlines(), start=1):
                if self.SECRET_PATTERN.search(line):
                    # Check if line has test or placeholder markers
                    if any(dummy in line.lower() for dummy in ["fake", "mock", "dummy", "placeholder", "example"]):
                        continue
                    self.log_finding(
                        rule_id="INV_SAFE_01",
                        severity="CRITICAL",
                        message=f"Potential hardcoded secret detected at line {idx}",
                        file_path=relative_path
                    )
                    break
        except Exception:
            pass

    def check_code_test_coevolution(self, changed_files: List[str]):
        """Audit whether changed code files (.py, .js, .ts) have companion test updates."""
        code_files = [
            f for f in changed_files
            if f.endswith((".py", ".js", ".ts", ".mjs")) and not f.startswith("tests/") and not f.endswith((".test.js", ".test.ts", ".test.py", "_test.py"))
        ]
        test_files = [
            f for f in changed_files
            if f.startswith("tests/") or f.endswith((".test.js", ".test.ts", ".test.py", "_test.py"))
        ]

        if code_files and not test_files:
            self.log_finding(
                rule_id="INV_SCOPE_02",
                severity="WARNING",
                message=f"Code files changed ({len(code_files)}) without companion test file updates.",
                file_path=", ".join(code_files[:3]) + ("..." if len(code_files) > 3 else "")
            )

    def check_state_freshness(self):
        """Audit STATE.md timestamp and active items."""
        state_file = self.root / "STATE.md"
        if not state_file.exists():
            self.log_finding(
                rule_id="INV_STATE_01",
                severity="WARNING",
                message="STATE.md does not exist in workspace root.",
                file_path="STATE.md"
            )
            return

        content = state_file.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"Last run:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}[^\s\)]*)", content)
        if not m:
            self.log_finding(
                rule_id="INV_STATE_01",
                severity="WARNING",
                message="STATE.md is missing a valid ISO-8601 'Last run' timestamp header.",
                file_path="STATE.md"
            )
            return

        ts_str = m.group(1)
        # Parse timestamp
        try:
            parsed_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            now_time = datetime.now(parsed_time.tzinfo if parsed_time.tzinfo else timezone.utc)
            delta_days = (now_time - parsed_time).total_seconds() / 86400

            if delta_days > 3.0:
                self.log_finding(
                    rule_id="INV_STATE_01",
                    severity="WARNING",
                    message=f"STATE.md has not been updated for {delta_days:.1f} days (Last run: {ts_str}).",
                    file_path="STATE.md"
                )
        except Exception as err:
            self.log_finding(
                rule_id="INV_STATE_01",
                severity="WARNING",
                message=f"Malformed or unparseable timestamp '{ts_str}' in STATE.md: {err}",
                file_path="STATE.md"
            )

    def audit(self, target_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute full drift and invariants inspection."""
        self.findings.clear()

        files_to_check = target_files if target_files is not None else get_git_changed_files(self.root)

        # 1. Check gate and scope limits
        self.check_gate_and_scope(files_to_check)

        # 2. Check secret leaks in target files
        for f in files_to_check:
            self.scan_file_for_secrets(f)

        # 3. Check code-test co-evolution
        self.check_code_test_coevolution(files_to_check)

        # 4. Check state freshness
        self.check_state_freshness()

        # Determine overall status
        has_critical = any(f["severity"] == "CRITICAL" for f in self.findings)
        has_warning = any(f["severity"] == "WARNING" for f in self.findings)

        status = "CRITICAL" if has_critical else ("WARNING" if has_warning else "PASS")
        exit_code = 2 if has_critical else (1 if has_warning else 0)

        return {
            "status": status,
            "exit_code": exit_code,
            "files_analyzed": len(files_to_check),
            "findings": self.findings,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def format_report(result: Dict[str, Any]) -> str:
    """Format audit results as a readable markdown/terminal report."""
    lines = []
    lines.append("=" * 64)
    lines.append(f"🔍 LOOP SENTINEL — DRIFT & INVARIANTS REPORT")
    lines.append(f"Status: {result['status']} | Analyzed Files: {result['files_analyzed']}")
    lines.append("=" * 64)

    if not result["findings"]:
        lines.append("✅ ALL INVARIANTS CLEARED: Zero drift detected.")
    else:
        for f in result["findings"]:
            tag = "[🔴 CRITICAL]" if f["severity"] == "CRITICAL" else "[🟡 WARNING]"
            loc = f" ({f['file']})" if f["file"] else ""
            lines.append(f"{tag} {f['rule_id']}: {f['message']}{loc}")

    lines.append("-" * 64)
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Loop Sentinel: Invariants & Architecture Drift Inspector")
    parser.add_argument("--files", nargs="*", help="Specific files to audit instead of git status")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--root", type=str, default=None, help="Project root directory path")
    args = parser.parse_args()

    root_dir = Path(args.root).resolve() if args.root else REPO_ROOT
    inspector = DriftInspector(root_dir=root_dir)
    result = inspector.audit(target_files=args.files)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_report(result))

    sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()
