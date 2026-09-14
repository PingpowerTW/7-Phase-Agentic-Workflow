#!/usr/bin/env python3
"""
Prompt Frontmatter Validator (Pure Python Stdlib)
Validates all .prompt.md files in prompts/ against prompts/shared/prompt-schema.json.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Extract and parse YAML frontmatter from markdown content without external pyyaml dependency."""
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", content, re.DOTALL)
    if not match:
        raise ValueError("Missing or malformed YAML frontmatter delimiters (--- ... ---).")

    yaml_text = match.group(1)
    body = match.group(2)

    data: Dict[str, Any] = {}
    for line in yaml_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if ":" not in line:
            continue

        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()

        # Handle quoted strings
        if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
            val = val[1:-1]
        # Handle array format [a, b, c]
        elif val.startswith("[") and val.endswith("]"):
            items = [item.strip().strip("'").strip('"') for item in val[1:-1].split(",") if item.strip()]
            data[key] = items
            continue

        data[key] = val

    return data, body


def validate_prompt_data(data: Dict[str, Any], schema: Dict[str, Any], filepath: Path) -> List[str]:
    """Validate parsed frontmatter dictionary against schema definitions."""
    errors: List[str] = []
    required_fields = schema.get("required", [])

    # Check required fields
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            errors.append(f"Missing required field: '{field}'")

    # Validate mode enum
    valid_modes = schema["properties"]["mode"]["enum"]
    if "mode" in data and data["mode"] not in valid_modes:
        errors.append(f"Invalid mode '{data['mode']}'. Allowed: {valid_modes}")

    # Validate version semver pattern
    version_pattern = schema["properties"]["version"]["pattern"]
    if "version" in data and not re.match(version_pattern, str(data["version"])):
        errors.append(f"Invalid version format '{data['version']}'. Expected semver (e.g. 1.0.0)")

    # Validate stack enum
    valid_stacks = schema["properties"]["stack"]["enum"]
    if "stack" in data and data["stack"] not in valid_stacks:
        errors.append(f"Invalid stack '{data['stack']}'. Allowed: {valid_stacks}")

    # Validate patterns array
    valid_patterns = schema["properties"]["patterns"]["items"]["enum"]
    if "patterns" in data:
        if not isinstance(data["patterns"], list):
            errors.append(f"'patterns' must be an array, got {type(data['patterns']).__name__}")
        else:
            for p in data["patterns"]:
                if p not in valid_patterns:
                    errors.append(f"Invalid pattern '{p}'. Allowed: {valid_patterns}")

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    prompts_dir = repo_root / "prompts"
    schema_path = prompts_dir / "shared" / "prompt-schema.json"

    if not schema_path.exists():
        print(f"[ERROR] Schema file not found: {schema_path}", file=sys.stderr)
        return 1

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    prompt_files = list(prompts_dir.rglob("*.prompt.md"))
    if not prompt_files:
        print(f"[WARN] No .prompt.md files found in {prompts_dir}")
        return 0

    print(f"[*] Validating {len(prompt_files)} prompt files against {schema_path.name}...")

    total_errors = 0
    for file in sorted(prompt_files):
        rel_path = file.relative_to(repo_root)
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            frontmatter, _ = parse_frontmatter(content)
            errors = validate_prompt_data(frontmatter, schema, file)

            if errors:
                print(f"  [FAIL] {rel_path}:")
                for err in errors:
                    print(f"         - {err}")
                total_errors += len(errors)
            else:
                print(f"  [PASS] {rel_path} (mode: {frontmatter.get('mode')}, stack: {frontmatter.get('stack')})")

        except Exception as e:
            print(f"  [FAIL] {rel_path}: Syntax/Parser error - {e}")
            total_errors += 1

    print("-" * 60)
    if total_errors == 0:
        print(f"[+] All {len(prompt_files)} prompt files passed schema validation successfully!")
        return 0
    else:
        print(f"[-] Validation failed with {total_errors} errors across prompt files.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
