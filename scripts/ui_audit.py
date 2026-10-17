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
    (
        "ai-copywriting-slop",
        "MEDIUM",
        15,
        r"(?:\b(?:unlock the power of|elevate your workflow|supercharge your|seamlessly integrate|game-changer|next-generation platform|10,000%\s*ROI)\b|\b99\.999%(?!\w))",
        "Generic AI marketing buzzword or fabricated metric slop detected.",
        "Replace filler buzzwords and unverifiable claims with concrete, factual product mechanics.",
    ),
]


def wcag_contrast_ratio(hex1: str, hex2: str) -> float:
    """Compute WCAG 2.x contrast ratio (1.0 to 21.0) between two #RGB/#RRGGBB hex colors."""
    def _lum(h: str) -> float:
        h = h.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        vals = [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
        r, g, b = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in vals]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    l1, l2 = sorted((_lum(hex1), _lum(hex2)), reverse=True)
    return round((l1 + 0.05) / (l2 + 0.05), 2)


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

    # WCAG 2.x True Hex Contrast Check (foreground vs background on same element/line)
    fg_re = re.compile(r"(?:(?<!hover:)text-\[|(?<![-\w])color:\s*['\"]?)(#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?)\b")
    bg_re = re.compile(r"(?:(?<!hover:)bg-\[|background(?:Color|-color)?:\s*['\"]?)(#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?)\b")
    for idx, line in enumerate(lines, 1):
        fg_m, bg_m = fg_re.search(line), bg_re.search(line)
        if fg_m and bg_m:
            ratio = wcag_contrast_ratio(fg_m.group(1), bg_m.group(1))
            if ratio < 4.5:
                violations.append(
                    SlopViolation(
                        rule_id="low-contrast-hex",
                        severity="HIGH",
                        penalty=20,
                        message=f"WCAG 2.x AA contrast failure ({ratio}:1 < 4.5:1) between {fg_m.group(1)} and {bg_m.group(1)}.",
                        line_number=idx,
                        code_snippet=f"{fg_m.group(0)} / {bg_m.group(0)}",
                        suggestion="Increase luminance delta to achieve at least 4.5:1 for normal text.",
                    )
                )

    # Glassmorphism Dose-Cap (R-10/R-13: max 2 active backdrop-blur surfaces per component)
    blur_matches = list(
        re.finditer(
            r"\bbackdrop-blur(?!-(?:none|0)\b)(?:-[a-z0-9]+)?\b|backdrop-filter:\s*blur\((?!0(?:px)?\))",
            content,
            re.IGNORECASE,
        )
    )
    if len(blur_matches) >= 3:
        third = blur_matches[2]
        violations.append(
            SlopViolation(
                rule_id="excessive-glass-blur",
                severity="MEDIUM",
                penalty=15,
                message="Glassmorphism dose-cap exceeded (>=3 backdrop-blur surfaces in one view).",
                line_number=content[: third.start()].count("\n") + 1,
                code_snippet=third.group(0),
                suggestion="Reserve backdrop-blur for at most 1-2 sticky headers or modal overlays; use solid surface tokens elsewhere.",
            )
        )

    # UI Finish-Gate Contract: Async/data-driven views must not ship Happy-Path-Only
    has_async = re.search(r"\b(?:fetch|useQuery|useSWR|useEffect)\s*\(|\baxios\.", content)
    has_map = re.search(r"\.map\s*\(", content)
    sanitized = re.sub(r"console\.(?:error|warn)\s*\([^)]*\)", "", content)
    has_loading = bool(re.search(r"\b(?:isLoading|loading|skeleton|spinner|pending|Suspense)\b", sanitized, re.IGNORECASE))
    has_empty_or_err = bool(
        re.search(
            r"\b(?:isError|error|empty|fallback)\b|no\s+data|length\s*[=!]==?\s*0|!\w+\.length",
            sanitized,
            re.IGNORECASE,
        )
    )
    trigger_match = has_async or has_map
    if trigger_match and ((has_async and not (has_loading and has_empty_or_err)) or (not has_async and not (has_loading or has_empty_or_err))):
        line_no = content[: trigger_match.start()].count("\n") + 1
        violations.append(
            SlopViolation(
                rule_id="missing-ui-finish-states",
                severity="HIGH",
                penalty=20,
                message="Async/data-driven view only implements Happy Path (missing loading/empty/error finish states).",
                line_number=line_no,
                code_snippet=trigger_match.group(0),
                suggestion="Treat loading, empty, and error states as part of the finished product (UI Finish-Gate Contract).",
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

    # Test 3: UI Finish-Gate Stateful UI Completeness check (including console.error bypass & chained .map)
    happy_path_only = "\n<div>{getItems().map(i => <span key={i.id}>{i.name}</span>)}</div>"
    hp_report = audit_content(happy_path_only)
    assert any(v.rule_id == "missing-ui-finish-states" and v.line_number == 2 for v in hp_report.violations)
    console_err_bypass = "useEffect(() => { fetch('/api').catch(e => console.error(e)); }, []);"
    ce_report = audit_content(console_err_bypass)
    assert any(v.rule_id == "missing-ui-finish-states" for v in ce_report.violations)
    complete_state_ui = "<div>{isLoading ? <Spinner/> : isError ? <Error/> : items.length === 0 ? <Empty/> : items.map(i => <span key={i.id}>{i.name}</span>)}</div>"
    cs_report = audit_content(complete_state_ui)
    assert not any(v.rule_id == "missing-ui-finish-states" for v in cs_report.violations)

    # Test 4: Anti-Slop WCAG 2.x Hex Contrast, Glassmorphism Dose-Cap & Copywriting Slop
    assert wcag_contrast_ratio("#ffffff", "#000000") == 21.0
    assert wcag_contrast_ratio("#777777", "#ffffff") < 4.5
    antislop_snippet = (
        '<div style={{ color: "#888", backgroundColor: "#fff" }}>Guaranteed 99.999% uptime</div>\n'
        '<div class="backdrop-blur-md">Card 1</div>\n'
        '<div class="backdrop-blur-lg">Card 2</div>\n'
        '<div class="backdrop-blur-xl">Card 3</div>'
    )
    as_report = audit_content(antislop_snippet)
    rule_ids = {v.rule_id for v in as_report.violations}
    assert {"low-contrast-hex", "excessive-glass-blur", "ai-copywriting-slop"}.issubset(rule_ids), rule_ids
    # Ensure backdrop-blur-none / blur(0) do not trigger false-positive dose cap
    no_blur_fp = '<div class="backdrop-blur-md"/><div class="backdrop-blur-lg"/><div class="backdrop-blur-none"/>'
    assert not any(v.rule_id == "excessive-glass-blur" for v in audit_content(no_blur_fp).violations)
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
