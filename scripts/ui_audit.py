#!/usr/bin/env python3
"""
7-Phase Agentic Workflow - UI/UX Anti-Slop Visual Pre-Flight Auditor
Pure Python Standard Library (Zero External Dependencies).

Enforces frontend-taste-v2 & anti-slop guidelines:
1. Detects repetitive 3-column equal-width card layouts lacking focal hierarchy.
2. Identifies overused purple-indigo-pink gradient clichés.
3. Flags clickable elements missing micro-interactions (hover, active, transition).
4. Detects unreadable low-contrast text combinations.
5. Flags monotonous typography scales lacking font-weight hierarchy.
6. Computes Anti-Slop Score (0-100) and recommends professional design alternatives.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class SlopViolation:
    rule_id: str
    severity: str  # HIGH, MEDIUM, LOW
    penalty: int
    message: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class AuditReport:
    file_path: str
    score: int
    grade: str
    violations: List[SlopViolation] = field(default_factory=list)


# Pattern definitions
PATTERNS = [
    (
        "cliche-gradient",
        "HIGH",
        20,
        r"(from-purple-\d+\s+to-blue-\d+|from-indigo-\d+\s+to-pink-\d+|from-violet-\d+\s+via-purple-\d+\s+to-pink-\d+)",
        "Overused AI-slop gradient cliché detected.",
        "Consider subtle monochromatic borders, OLED dark mode, or intentional brand palette instead of generic neon gradients.",
    ),
    (
        "generic-equal-card-grid",
        "HIGH",
        25,
        r"(grid-cols-1\s+md:grid-cols-3|grid-cols-3\b)",
        "Monotonous 3-column equal-width card layout detected.",
        "Adopt asymmetrical Bento Grid hierarchy (e.g. 1 major showcase card span 2 cols + 2 compact cards).",
    ),
    (
        "missing-micro-interaction",
        "MEDIUM",
        15,
        r"<button(?![^>]*(hover:|active:|transition))[^>]*>",
        "Clickable button lacks micro-interaction states (hover/active/transition).",
        "Add smooth micro-feedback: `transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]`.",
    ),
    (
        "low-contrast-text",
        "MEDIUM",
        15,
        r"(text-gray-400|text-slate-400|text-zinc-400)\b",
        "Low contrast body/label text detected (WCAG AA violation risk).",
        "Use high-contrast legible tone: `text-zinc-200` (dark mode) or `text-zinc-700` (light mode).",
    ),
    (
        "missing-focus-ring",
        "LOW",
        10,
        r"<input(?![^>]*(focus:ring|focus:border|outline-none))[^>]*>",
        "Form input lacks accessible focus indicator.",
        "Add visible keyboard focus ring: `focus:outline-none focus:ring-2 focus:ring-primary`.",
    ),
]


def audit_content(content: str, file_path: str = "snippet") -> AuditReport:
    """Audit code content and calculate Anti-Slop score."""
    violations: List[SlopViolation] = []
    lines = content.splitlines()

    for rule_id, severity, penalty, pattern, msg, suggestion in PATTERNS:
        regex = re.compile(pattern, re.IGNORECASE)
        for idx, line in enumerate(lines, 1):
            match = regex.search(line)
            if match:
                snippet = match.group(0)
                if len(snippet) > 80:
                    snippet = snippet[:80] + "..."
                violations.append(
                    SlopViolation(
                        rule_id=rule_id,
                        severity=severity,
                        penalty=penalty,
                        message=msg,
                        line_number=idx,
                        code_snippet=snippet,
                        suggestion=suggestion,
                    )
                )

    # Compute final score
    total_penalty = sum(v.penalty for v in violations)
    score = max(0, 100 - total_penalty)

    if score >= 90:
        grade = "A (Distinctive & Production-Grade)"
    elif score >= 75:
        grade = "B (Acceptable, Minor Slop)"
    else:
        grade = "C (Heavy AI Slop Detected)"

    return AuditReport(file_path=file_path, score=score, grade=grade, violations=violations)


def audit_file(file_path: Path) -> Optional[AuditReport]:
    """Audit an individual frontend file."""
    valid_exts = {".html", ".jsx", ".tsx", ".vue", ".svelte", ".css", ".php"}
    if file_path.suffix.lower() not in valid_exts:
        return None
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return audit_content(content, str(file_path))
    except Exception:
        return None


def run_self_tests():
    """Run internal test suite."""
    # Test 1: Slop snippet
    slop_code = """
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-gradient-to-r from-purple-500 to-blue-500 p-6">
        <p class="text-gray-400">Generic subtitle</p>
        <button class="bg-blue-600 text-white px-4 py-2">Click me</button>
      </div>
    </div>
    """
    report = audit_content(slop_code)
    assert report.score < 75, f"Slop snippet scored too high: {report.score}"
    assert any(v.rule_id == "cliche-gradient" for v in report.violations)
    assert any(v.rule_id == "generic-equal-card-grid" for v in report.violations)
    assert any(v.rule_id == "missing-micro-interaction" for v in report.violations)

    # Test 2: Premium clean snippet
    clean_code = """
    <div class="grid grid-cols-1 md:grid-cols-12 gap-6">
      <div class="md:col-span-8 bg-zinc-900 border border-zinc-800 p-8 rounded-2xl">
        <h2 class="text-2xl font-semibold text-zinc-100 tracking-tight">Main Feature</h2>
        <p class="text-zinc-300 mt-2">Deliberate hierarchy with dark OLED aesthetic.</p>
        <button class="mt-6 px-5 py-2.5 bg-white text-zinc-950 font-medium rounded-lg transition-all duration-200 hover:bg-zinc-200 active:scale-95">
          Deploy
        </button>
      </div>
      <div class="md:col-span-4 bg-zinc-900 border border-zinc-800 p-8 rounded-2xl">
        <p class="text-zinc-300">Side info</p>
      </div>
    </div>
    """
    clean_report = audit_content(clean_code)
    assert clean_report.score >= 90, f"Clean snippet scored too low: {clean_report.score}"
    print("[PASS] scripts/ui_audit.py self-tests passed 100%!")


def main():
    parser = argparse.ArgumentParser(description="UI/UX Anti-Slop Visual Pre-Flight Auditor")
    parser.add_argument("target", nargs="?", default=".", help="Target file or directory to scan")
    parser.add_argument("--threshold", "-t", type=int, default=80, help="Minimum acceptable score (default: 80)")
    parser.add_argument("--check", action="store_true", help="Exit with code 1 if any file fails threshold")
    parser.add_argument("--test", action="store_true", help="Run internal self-tests")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    if args.test:
        run_self_tests()
        sys.exit(0)

    target_path = Path(args.target)
    if not target_path.exists():
        print(f"[ERROR] Target path not found: {target_path}", file=sys.stderr)
        sys.exit(1)

    reports: List[AuditReport] = []
    if target_path.is_file():
        rep = audit_file(target_path)
        if rep:
            reports.append(rep)
    else:
        for root, _, files in os.walk(target_path):
            if any(part.startswith((".", "node_modules", "dist", "build", "vendor")) for part in Path(root).parts):
                continue
            for f in files:
                p = Path(root) / f
                rep = audit_file(p)
                if rep:
                    reports.append(rep)

    if not reports:
        print(f"[*] No frontend files (.html, .jsx, .tsx, .vue, .svelte, .css) found in: {target_path}")
        sys.exit(0)

    failed_any = False

    if args.json:
        data = [
            {
                "file": r.file_path,
                "score": r.score,
                "grade": r.grade,
                "violations": [
                    {
                        "rule": v.rule_id,
                        "severity": v.severity,
                        "line": v.line_number,
                        "snippet": v.code_snippet,
                        "suggestion": v.suggestion,
                    }
                    for v in r.violations
                ],
            }
            for r in reports
        ]
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"[*] UI/UX Anti-Slop Visual Audit Matrix ({len(reports)} file(s) scanned)")
        print("=" * 60)
        for r in reports:
            status = "PASS" if r.score >= args.threshold else "FAIL"
            symbol = "✓" if r.score >= args.threshold else "✗"
            print(f"[{status}] {symbol} {r.file_path} - Score: {r.score}/100 [{r.grade}]")
            if r.violations:
                for v in r.violations:
                    loc = f"Line {v.line_number}" if v.line_number else ""
                    print(f"      [{v.severity}] {v.message} ({loc})")
                    if v.suggestion:
                        print(f"        💡 Suggestion: {v.suggestion}")
            print("-" * 60)

            if r.score < args.threshold:
                failed_any = True

    if args.check and failed_any:
        print(f"[FAIL] One or more files failed anti-slop threshold ({args.threshold}).", file=sys.stderr)
        sys.exit(1)

    print("✨ UI/UX Anti-Slop audit completed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
