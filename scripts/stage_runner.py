#!/usr/bin/env python3

"""

stage_runner.py — Zero-Token Sandbox Stager, Step 2.5 Deterministic Sieve & Atomic Committer

Pure Python 3 Standard Library. Eliminates Double Output-Token Tax in /teamwork & /agy-studio.

Usage:

  1. Parse Worker markdown output into .studio/staging/:

     python scripts/stage_runner.py stage --input worker_output.md

  2. Run Step 2.5 0-Token Pre-Review Sieve (local_guard + ast_guard + ui_audit):

     python scripts/stage_runner.py sieve

  3. Atomically promote verified files from .studio/staging/ to project workspace:

     python scripts/stage_runner.py commit

"""

import argparse

import re

import shutil

import subprocess

import sys

from pathlib import Path

from typing import List, Tuple

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent

STAGING_DIR = REPO_ROOT / ".studio" / "staging"

# Matches: ### FILE: path/to/file.ext followed by a fenced code block

FILE_BLOCK_RE = re.compile(

    r"###\s+FILE:\s+([^\r\n]+)\r?\n+```[^\r\n]*\r?\n(.*?)\r?\n```",

    re.DOTALL

)

def extract_and_stage(markdown_text: str, clean: bool = False) -> List[Path]:

    """Extract ### FILE: blocks from worker output and write to .studio/staging/."""

    if clean and STAGING_DIR.exists():

        shutil.rmtree(STAGING_DIR)

    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    staged_files: List[Path] = []

    for match in FILE_BLOCK_RE.finditer(markdown_text):

        rel_path_str = match.group(1).strip().strip("`'\"")

        code_body = match.group(2)

        # Prevent path traversal outside staging

        norm_rel = Path(rel_path_str.replace("\\", "/").lstrip("/"))

        if ".." in norm_rel.parts:

            print(f"[BLOCK] 拒絕非法路徑穿越: {rel_path_str}", file=sys.stderr)

            continue

        dest = STAGING_DIR / norm_rel

        dest.parent.mkdir(parents=True, exist_ok=True)

        dest.write_text(code_body + "\n", encoding="utf-8")

        staged_files.append(norm_rel)

    print(f"[STAGE] 已將 {len(staged_files)} 個檔案落地至沙盒 .studio/staging/: {[str(p) for p in staged_files]}")

    return staged_files

def run_step25_sieve() -> Tuple[bool, List[str]]:

    """Run 0-Token deterministic guards (local_guard, ast_guard, ui_audit) on staged files."""

    if not STAGING_DIR.exists():

        print("[SIEVE] 沙盒目錄為空，無需檢驗。")

        return True, []

    staged_files = [p for p in STAGING_DIR.rglob("*") if p.is_file()]

    if not staged_files:

        return True, []

    rel_paths = [str(p.relative_to(STAGING_DIR)).replace("\\", "/") for p in staged_files]

    abs_paths = [str(p) for p in staged_files]

    errors: List[str] = []

    # 1. Check gate.yaml denylist & maxFiles against target relative paths

    sys.path.insert(0, str(REPO_ROOT / "scripts"))

    try:

        import local_guard

        gate_blocked, gate_violations = local_guard.check_gate_yaml(rel_paths, REPO_ROOT)

        if gate_blocked:

            errors.extend(gate_violations)

        # Check secrets & System 1 guard per file

        combined_code = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in staged_files)

        secrets = local_guard.check_regex_secrets(combined_code)

        for s in secrets:

            errors.append(f"硬編碼憑證攔截: {s}")

    except Exception as ex:

        errors.append(f"local_guard 載入異常: {ex}")

    # 2. Run Level 0.5 SWC AST Guard on staged JS/TS files

    js_files = [p for p in abs_paths if p.lower().endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"))]

    ast_script = REPO_ROOT / "scripts" / "ast_guard.js"

    if js_files and ast_script.exists():

        res = subprocess.run(

            ["node", str(ast_script)] + js_files,

            capture_output=True, text=True, encoding="utf-8", errors="replace"

        )

        if res.returncode == 1:

            errors.append(f"AST Guard 違規:\n{(res.stdout + res.stderr).strip()}")

    # 3. Run UI Anti-Slop Audit on staged Frontend UI components (.tsx, .jsx, .vue, .html)

    ui_files = [p for p in abs_paths if p.lower().endswith((".tsx", ".jsx", ".vue", ".html")) and ".test." not in p.lower() and ".spec." not in p.lower()]

    ui_script = REPO_ROOT / "scripts" / "ui_audit.py"

    if ui_files and ui_script.exists():

        for uf in ui_files:

            res = subprocess.run(

                [sys.executable, str(ui_script), uf, "--check", "--threshold", "80"],

                capture_output=True, text=True, encoding="utf-8", errors="replace"

            )

            if res.returncode != 0:

                errors.append(f"UI Anti-Slop 未達標 (<80) [{Path(uf).name}]:\n{res.stdout.strip()}")

    if errors:

        print("🛑 [STEP 2.5 SIEVE: BLOCK] 0-Token 確定性門禁攔截，直接退回 Worker（不消耗 AI 審查官 Token）：")

        for e in errors:

            print(f"  ✖ {e}")

        return False, errors

    print(f"✅ [STEP 2.5 SIEVE: PASS] {len(staged_files)} 個沙盒檔案全數通過 0-Token 門禁！准許進入 Step 3 對抗審查。")

    return True, []

def commit_sandbox() -> int:

    """Atomically move verified files from .studio/staging/ into the real workspace."""

    if not STAGING_DIR.exists():

        print("[COMMIT] 無沙盒檔案可提交。")

        return 0

    ok, _ = run_step25_sieve()

    if not ok:

        print("[COMMIT ABORTED] 沙盒檔案未通過 Step 2.5 門禁，禁止合流至正式工作區！", file=sys.stderr)

        return 1

    moved = 0

    for src_file in STAGING_DIR.rglob("*"):

        if not src_file.is_file():

            continue

        rel = src_file.relative_to(STAGING_DIR)

        dst_file = REPO_ROOT / rel

        dst_file.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(src_file, dst_file)

        moved += 1

    shutil.rmtree(STAGING_DIR)

    print(f"🚀 [COMMIT SUCCESS] 已將 {moved} 個驗證通過的檔案零 Token 原子合流至正式工作區！")

    return 0

def main():

    parser = argparse.ArgumentParser(description="Zero-Token Sandbox Stager & Step 2.5 Sieve")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_stage = sub.add_parser("stage", help="從 Markdown 檔案或 stdin 擷取 ### FILE: 寫入 .studio/staging/")

    p_stage.add_argument("--input", "-i", type=str, help="Markdown 輸入檔案路徑 (未指定則讀 stdin)")

    p_stage.add_argument("--clean", action="store_true", help="寫入前清空舊沙盒")

    sub.add_parser("sieve", help="對 .studio/staging/ 執行 Step 2.5 0-Token 確定性快篩")

    sub.add_parser("commit", help="將驗證通過的沙盒檔案原子移動至正式目錄")

    args = parser.parse_args()

    if args.cmd == "stage":

        text = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()

        extract_and_stage(text, clean=args.clean)

    elif args.cmd == "sieve":

        ok, _ = run_step25_sieve()

        sys.exit(0 if ok else 1)

    elif args.cmd == "commit":

        sys.exit(commit_sandbox())

if __name__ == "__main__":

    main()
