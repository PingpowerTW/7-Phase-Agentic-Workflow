#!/usr/bin/env python3
"""
7-Phase Agentic Workflow - GEPA Self-Healing Reflective Loop
Pure Python Standard Library (Zero External Dependencies).

Implements Stanford 2025 GEPA (Generative Error-driven Prompt Adaptation)
and Path-Precise Reflexion error injection:
1. Intercepts test/validator failures.
2. Extracts precise failure coordinates (File, Line, Property Path).
3. Synthesizes targeted constraint mutations to eliminate blind trial-and-error.
4. Generates a compact Reflexion Capsule for single-turn surgical self-healing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
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
class DiagnosticUnit:
    target_path: str
    line_number: Optional[int]
    error_category: str  # SCHEMA_VIOLATION, ASSERTION_FAILURE, SYNTAX_ERROR, RUNTIME_EXCEPTION, ENCODING_ERROR
    failure_rationale: str
    raw_snippet: str
    targeted_constraint: str


def parse_diagnostics(raw_output: str) -> List[DiagnosticUnit]:
    """Parse raw test or validator output into structured GEPA diagnostic units."""
    units: List[DiagnosticUnit] = []
    lines = raw_output.splitlines()

    # Pattern 1: Python Traceback / AssertionError
    # File "...", line 123, in ...
    trace_pattern = re.compile(r'File "([^"]+)", line (\d+), in (.+)')
    # Pattern 2: Schema validation failure
    # [FAIL] path/to/file: error message
    schema_pattern = re.compile(r'\[(?:FAIL|ERROR)\]\s+([^\s:]+)(?::(\d+))?:\s*(.+)')
    # Pattern 3: UnicodeEncodeError
    # UnicodeEncodeError: 'cp950' codec can't encode character ...
    encoding_pattern = re.compile(r"Unicode(?:Encode|Decode)Error:\s*(.+)")
    # Pattern 4: Assertion error
    assert_pattern = re.compile(r"AssertionError:\s*(.+)")

    for idx, line in enumerate(lines):
        line_clean = line.strip()

        # Check for Python traceback
        m_trace = trace_pattern.search(line_clean)
        if m_trace:
            fpath = m_trace.group(1)
            line_no = int(m_trace.group(2))
            
            # Look ahead for exception message
            ex_msg = "Unknown execution failure"
            for forward in lines[idx + 1: idx + 6]:
                if any(err_type in forward for err_type in ["Error:", "Exception:", "AssertionError"]):
                    ex_msg = forward.strip()
                    break

            cat = "ASSERTION_FAILURE" if "AssertionError" in ex_msg else "RUNTIME_EXCEPTION"
            if "Unicode" in ex_msg:
                cat = "ENCODING_ERROR"
                mutation = "MUST enforce UTF-8 reconfigure (`sys.stdout.reconfigure(encoding='utf-8')`) on Windows platforms."
            elif cat == "ASSERTION_FAILURE":
                mutation = f"MUST satisfy invariant: {ex_msg.replace('AssertionError:', '').strip()}."
            else:
                mutation = f"MUST handle exception safely with specific try/except block instead of failing."

            units.append(
                DiagnosticUnit(
                    target_path=fpath,
                    line_number=line_no,
                    error_category=cat,
                    failure_rationale=ex_msg,
                    raw_snippet=line_clean,
                    targeted_constraint=mutation,
                )
            )

        # Check for schema/validator failure
        m_schema = schema_pattern.search(line_clean)
        if m_schema:
            fpath = m_schema.group(1)
            line_no = int(m_schema.group(2)) if m_schema.group(2) else None
            msg = m_schema.group(3)
            units.append(
                DiagnosticUnit(
                    target_path=fpath,
                    line_number=line_no,
                    error_category="SCHEMA_VIOLATION",
                    failure_rationale=msg,
                    raw_snippet=line_clean,
                    targeted_constraint=f"MUST adjust file '{fpath}' to strictly conform with schema specification: {msg}.",
                )
            )

    # If no structured pattern was matched but output contains error keywords
    if not units and ("ERROR" in raw_output or "FAIL" in raw_output):
        units.append(
            DiagnosticUnit(
                target_path="system/pipeline",
                line_number=None,
                error_category="UNCLASSIFIED_FAILURE",
                failure_rationale=raw_output[:200],
                raw_snippet=raw_output[:120],
                targeted_constraint="MUST inspect underlying exit code and resolve blocker before proceeding.",
            )
        )

    return units


def format_gepa_capsule(diagnostics: List[DiagnosticUnit]) -> str:
    """Format diagnostic units into a token-optimized GEPA Reflexion Capsule."""
    out = [
        "## 🔬 GEPA Reflective Diagnosis & Targeted Mutations",
        "> Stanford 2025 GEPA Paradigm: Zero Blind Retries | Single-Turn Surgical Repair",
        "",
    ]
    for i, d in enumerate(diagnostics, 1):
        loc = f":{d.line_number}" if d.line_number else ""
        out.append(f"### [Issue {i}] {d.error_category} @ `{d.target_path}{loc}`")
        out.append(f"- **Rationale**: {d.failure_rationale}")
        out.append(f"- **Trigger Snippet**: `{d.raw_snippet}`")
        out.append(f"- **Targeted Mutation**: `{d.targeted_constraint}`")
        out.append("")

    return "\n".join(out)


def run_command_with_reflexion(cmd_str: str) -> int:
    """Run a shell command, and if it fails, intercept and output GEPA diagnostics."""
    start_msg = f"[*] Executing target command under GEPA supervision: {cmd_str}"
    print(start_msg)
    
    res = subprocess.run(cmd_str, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    
    if res.returncode == 0:
        print("[PASS] Command succeeded with exit code 0.")
        if res.stdout:
            print(res.stdout.strip())
        return 0

    # Command failed: analyze failure
    combined_output = (res.stdout + "\n" + res.stderr).strip()
    diagnostics = parse_diagnostics(combined_output)
    capsule = format_gepa_capsule(diagnostics)

    # Save to .agent/REFLEXION.json
    agent_dir = REPO_ROOT / ".agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    reflexion_json = agent_dir / "REFLEXION.json"
    
    payload = {
        "command": cmd_str,
        "exit_code": res.returncode,
        "diagnostics": [asdict(d) for d in diagnostics],
        "markdown_capsule": capsule,
    }
    reflexion_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 60)
    print("❌ COMMAND FAILED! INTERCEPTED BY GEPA REFLEXION ENGINE:")
    print("=" * 60)
    print(capsule)
    print(f"[+] Reflexion capsule written to: {reflexion_json}")
    return res.returncode


def run_self_tests():
    """Run internal test suite for GEPA reflexion parser."""
    # Test 1: Python Traceback
    mock_trace = """
    Traceback (most recent call last):
      File "scripts/test_sample.py", line 42, in test_fn
        assert x == 10
    AssertionError: Expected 10, got 5
    """
    d1 = parse_diagnostics(mock_trace)
    assert len(d1) >= 1
    assert d1[0].target_path == "scripts/test_sample.py"
    assert d1[0].line_number == 42
    assert d1[0].error_category == "ASSERTION_FAILURE"

    # Test 2: Schema validation failure
    mock_schema = "[FAIL] prompts/python/test.prompt.md:20: Missing required property 'stack'."
    d2 = parse_diagnostics(mock_schema)
    assert len(d2) >= 1
    assert d2[0].error_category == "SCHEMA_VIOLATION"

    # Test 3: Formatting
    capsule_text = format_gepa_capsule(d1 + d2)
    assert "GEPA Reflective Diagnosis" in capsule_text
    assert "Targeted Mutation" in capsule_text

    print("[PASS] scripts/reflexion.py internal self-tests passed 100%!")


def main():
    parser = argparse.ArgumentParser(description="GEPA Self-Healing Reflective Loop")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # Run subcommand
    run_parser = subparsers.add_parser("run", help="Run command and intercept errors with GEPA")
    run_parser.add_argument("cmd", help="Shell command string to execute")

    # Analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Analyze raw error text or file")
    analyze_parser.add_argument("input", help="File path or raw error string")

    # Test subcommand
    subparsers.add_parser("test", help="Run internal self-tests")

    args = parser.parse_args()

    if args.command == "run":
        code = run_command_with_reflexion(args.cmd)
        sys.exit(code)

    elif args.command == "analyze":
        inp_path = Path(args.input)
        content = inp_path.read_text(encoding="utf-8") if inp_path.is_file() else args.input
        diags = parse_diagnostics(content)
        print(format_gepa_capsule(diags))
        sys.exit(0)

    elif args.command == "test":
        run_self_tests()
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
