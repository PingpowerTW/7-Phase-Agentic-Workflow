#!/usr/bin/env python3
"""
7-Phase Agentic Workflow - Unified Test & Verification Runner (Tool Call Batching)
Pure Python Standard Library (Zero External Dependencies).

Executes all core project verification suites in a single batch process:
1. PromptScript DSL Validation (.promptscript/)
2. Prompt Frontmatter Schema Validation (16/16 Prompts)
3. Trust Governor & SHARS Thermodynamics Suite (8/8 Tests)
4. UI-Designer BM25 Engine & Windows UTF-8 Console Safety Check
5. 8-Facet Capsule Integrity Suite
6. UI/UX Anti-Slop Auditor Suite
7. GEPA Reflexion Engine Suite
8. System 1 Decision Gate (Noul / Choice / Score)
9. Loop Engineering Physical Safety Gate (Backslash & MaxFiles Protection)

Outputs a compact, token-optimized summary (<12 lines) unless --verbose is passed.
"""

import sys
import time
import subprocess
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_suite(name: str, cmd: list[str], cwd: Path) -> tuple[bool, str, float]:
    start = time.perf_counter()
    res = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")
    elapsed = time.perf_counter() - start
    is_ok = res.returncode == 0
    output = res.stdout if is_ok else (res.stdout + "\n" + res.stderr)
    return is_ok, output.strip(), elapsed


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    start_total = time.perf_counter()

    suites = [
        ("PromptScript DSL", [sys.executable, "scripts/sync_promptscript.py", "--check"], REPO_ROOT),
        ("Prompt Schema (16/16)", [sys.executable, "scripts/validate_prompts.py"], REPO_ROOT),
        ("Trust Governor & SHARS", [sys.executable, "skills/trust-governor/scripts/governor.py", "--test"], REPO_ROOT),
        ("UI-Designer & UTF-8 Safety", [sys.executable, "skills/ui-designer/scripts/search.py", "dark mode"], REPO_ROOT),
        ("8-Facet Capsule Integrity", [sys.executable, "scripts/capsule.py", "test"], REPO_ROOT),
        ("UI/UX Anti-Slop Auditor", [sys.executable, "scripts/ui_audit.py", "--test"], REPO_ROOT),
        ("GEPA Reflexion Engine", [sys.executable, "scripts/reflexion.py", "test"], REPO_ROOT),
        ("System 1 Decision Gate", [sys.executable, "scripts/system_one.py", "--test"], REPO_ROOT),
        ("Loop Engineering Gate", [sys.executable, "scripts/loop_gate.py", "--test"], REPO_ROOT),
        ("Loop Sentinel Drift (11 Tests)", [sys.executable, "-m", "unittest", "tests/test_loop_drift.py"], REPO_ROOT),
        ("Loop Graph Engine (6 Tests)", [sys.executable, "-m", "unittest", "tests/test_loop_graph.py"], REPO_ROOT),
    ]

    results = []
    all_ok = True

    for name, cmd, cwd in suites:
        is_ok, out, elapsed = run_suite(name, cmd, cwd)
        results.append((name, is_ok, out, elapsed))
        if not is_ok:
            all_ok = False

    total_time = time.perf_counter() - start_total

    # Render ultra-compact, token-optimized report
    print(f"[*] 7-Phase Agentic Workflow - Unified Verification Matrix ({len(suites)} Suites)")
    for name, is_ok, out, elapsed in results:
        status_tag = "PASS" if is_ok else "FAIL"
        symbol = "✓" if is_ok else "✗"
        print(f"  [{status_tag}] {symbol} {name:<26} ({elapsed:.2f}s)")
        if not is_ok or verbose:
            indented = "\n".join(f"      | {line}" for line in out.splitlines())
            print(f"{indented}")

    print("-" * 52)
    if all_ok:
        print(f"✨ ALL {len(suites)} SUITES PASSED ({total_time:.2f}s) - 100% Green & Ready!")
        sys.exit(0)
    else:
        print(f"❌ VERIFICATION FAILED ({total_time:.2f}s) - Please review errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
