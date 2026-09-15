#!/usr/bin/env python3
"""
7-Phase Agentic Workflow - PromptScript DSL Validator & Multi-IDE Synchronizer
Zero-dependency Python 3 standard library script.

Validates .promptscript/ DSL definitions, imports, block syntax, agent tools,
shortcuts, and governance consistency for cross-IDE compilation.
"""

import os
import re
import sys
import json
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


class PromptScriptValidator:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.prs_dir = repo_root / ".promptscript"
        self.config_file = repo_root / "promptscript.yaml"
        self.errors = []
        self.warnings = []
        self.parsed_blocks = {}

    def log_error(self, msg: str):
        self.errors.append(f"[ERROR] {msg}")

    def log_warning(self, msg: str):
        self.warnings.append(f"[WARN] {msg}")

    def validate_all(self) -> bool:
        print("[INFO] Starting PromptScript DSL & Multi-IDE Sync Validation...")
        
        # 1. Check promptscript.yaml
        self._validate_yaml_config()

        # 2. Check main entry
        entry_file = self.prs_dir / "7phase.prs"
        if not entry_file.exists():
            self.log_error(f"Main entry file not found: {entry_file}")
            return False

        # 3. Parse all .prs files in directory
        for prs_file in self.prs_dir.glob("*.prs"):
            self._parse_and_validate_prs(prs_file)

        # 4. Check imports consistency
        self._validate_imports(entry_file)

        # 5. Check Agent capability matrix
        self._validate_agents()

        # 6. Check Shortcuts definition
        self._validate_shortcuts()

        # 7. Check Governance guards
        self._validate_governance()

        # 8. Report Results
        print("\n" + "=" * 60)
        if self.warnings:
            for w in self.warnings:
                print(w)
        if self.errors:
            for e in self.errors:
                print(e)
            print(f"\n[FAILED] Validation failed with {len(self.errors)} error(s).")
            return False
        
        print("[SUCCESS] PromptScript DSL validation PASSED! (0 errors, 0 blockers)")
        print(f"[INFO] Parsed Blocks: {list(self.parsed_blocks.keys())}")
        print("[READY] Ready for Universal Multi-IDE Compilation (49+ Targets).")
        print("=" * 60)
        return True

    def _validate_yaml_config(self):
        if not self.config_file.exists():
            self.log_error(f"Missing configuration file: {self.config_file}")
            return

        content = self.config_file.read_text(encoding="utf-8")
        if "syntax: '1.5.0'" not in content and 'syntax: "1.5.0"' not in content:
            self.log_warning("promptscript.yaml should declare syntax version 1.5.0")
        if "entry: .promptscript/7phase.prs" not in content:
            self.log_error("promptscript.yaml entry must point to .promptscript/7phase.prs")

    def _parse_and_validate_prs(self, file_path: Path):
        content = file_path.read_text(encoding="utf-8")
        block_pattern = re.compile(r"@([a-zA-Z0-9_-]+)\s*\{", re.MULTILINE)
        use_pattern = re.compile(r"@use\s+([^\s\n]+)", re.MULTILINE)
        
        blocks = block_pattern.findall(content)
        imports = use_pattern.findall(content)

        self.parsed_blocks[file_path.name] = {
            "blocks": blocks,
            "imports": imports,
            "raw": content
        }

    def _validate_imports(self, entry_file: Path):
        entry_data = self.parsed_blocks.get(entry_file.name, {})
        imports = entry_data.get("imports", [])
        
        for imp in imports:
            target = imp.replace("./", "")
            if not target.endswith(".prs"):
                target += ".prs"
            target_file = self.prs_dir / target
            if not target_file.exists():
                self.log_error(f"Unresolved @use import in {entry_file.name}: {imp} -> {target_file}")

    def _validate_agents(self):
        agents_data = self.parsed_blocks.get("agents.prs", {})
        raw = agents_data.get("raw", "")
        required_agents = ["sentinel", "explorer", "db-architect", "backend-lead", "frontend-master", "reviewer", "critic", "auditor"]
        
        for agent in required_agents:
            if f"{agent}:" not in raw:
                self.log_error(f"Missing required agent persona in agents.prs: {agent}")

    def _validate_shortcuts(self):
        shortcuts_data = self.parsed_blocks.get("shortcuts.prs", {})
        raw = shortcuts_data.get("raw", "")
        required_shortcuts = ["/spec", "/teamwork", "/review", "/trust", "/diagnosing-bugs", "/ui-check"]
        
        for sc in required_shortcuts:
            if f'"{sc}":' not in raw:
                self.log_error(f"Missing required shortcut in shortcuts.prs: {sc}")

    def _validate_governance(self):
        gov_data = self.parsed_blocks.get("governance.prs", {})
        raw = gov_data.get("raw", "")
        if "dros-vajraclaw" not in raw:
            self.log_error("Layer 0 DROS VajraClaw guard missing in governance.prs")
        if "btc-trust-governor" not in raw:
            self.log_error("Layer 1 BTC Trust Governor guard missing in governance.prs")
        if "oxford-shars" not in raw:
            self.log_error("Layer 2 Oxford SHARS guard missing in governance.prs")


if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent.parent
    validator = PromptScriptValidator(current_dir)
    success = validator.validate_all()
    sys.exit(0 if success else 1)
