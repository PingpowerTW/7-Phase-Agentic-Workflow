#!/usr/bin/env python3
"""
stage_runner.py — v3.1 Zero-Token Sandbox Stager (Full File + Surgical Patch), Step 2.5 Sieve & Atomic Committer
Pure Python 3 Standard Library. Eliminates Double Output-Token Tax & Full-File Rewrite Waste.

Supports two extraction modes from Worker Markdown output:
  1. ### FILE: path/to/file.ext       (For new files or full rewrites)
  2. ### PATCH: path/to/existing.ext  (For surgical edits using SEARCH/REPLACE blocks, saving 85% output tokens)
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
STAGING_DIR = REPO_ROOT / ".studio" / "staging"

# Mode 1: Full file block (### FILE: path)
FILE_BLOCK_RE = re.compile(
    r"###\s+FILE:\s+([^\r\n]+)\r?\n+```[^\r\n]*\r?\n(.*?)\r?\n```",
    re.DOTALL
)

# Mode 2: Surgical patch block (### PATCH: path) — supports both fenced (```) and unfenced SEARCH/REPLACE blocks
PATCH_BLOCK_RE = re.compile(
    r"###\s+PATCH:\s+([^\r\n]+)\r?\n+(.*?)(?=\r?\n###\s+(?:FILE|PATCH):|\Z)",
    re.DOTALL
)

# Search / Replace hunk inside a PATCH block
HUNK_RE = re.compile(
    r"<{5,9}\s*SEARCH\r?\n(.*?)\r?\n={5,9}\r?\n(.*?)\r?\n>{5,9}\s*REPLACE",
    re.DOTALL
)


def _safe_rel_path(raw_path: str) -> Optional[Path]:
    norm_rel = Path(raw_path.strip().strip("`'\"").replace("\\", "/").lstrip("/"))
    if ".." in norm_rel.parts:
        print(f"[BLOCK] 拒絕非法路徑穿越: {raw_path}", file=sys.stderr)
        return None
    return norm_rel


def apply_surgical_patch(original_text: str, patch_body: str, file_label: str) -> Tuple[bool, str, List[str]]:
    """Apply SEARCH/REPLACE hunks to original_text with exact matching."""
    hunks = list(HUNK_RE.finditer(patch_body))
    if not hunks:
        return False, original_text, [f"[PATCH ERROR] {file_label}: 找不到有效的 <<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE 區塊"]

    modified = original_text.replace("\r\n", "\n")
    errors: List[str] = []

    for idx, h in enumerate(hunks, 1):
        search_str = h.group(1).replace("\r\n", "\n")
        replace_str = h.group(2).replace("\r\n", "\n")

        if search_str in modified:
            if modified.count(search_str) > 1:
                errors.append(
                    f"[PATCH AMBIGUOUS] {file_label} (Hunk #{idx}): SEARCH 區塊在檔案中出現 {modified.count(search_str)} 次！"
                    f"FIX: 請在 SEARCH 區塊多包含前後 2~3 行上下文以確保唯一性。"
                )
                continue
            modified = modified.replace(search_str, replace_str, 1)
        else:
            errors.append(
                f"[PATCH MISMATCH] {file_label} (Hunk #{idx}): 原檔中找不到完全匹配的 SEARCH 區塊（防止幻覺覆寫已攔截）。"
                f"FIX: 請先讀取目標檔案確認實際行內容與縮排後再發起 PATCH。"
            )

    return (len(errors) == 0), modified, errors


def extract_and_stage(markdown_text: str, clean: bool = False) -> Tuple[bool, List[Path], List[str]]:
    """Extract ### FILE: and ### PATCH: blocks from worker output into .studio/staging/."""
    if clean and STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    staged_files: List[Path] = []
    patch_errors: List[str] = []

    # 1. Process full FILE blocks
    file_matches = list(FILE_BLOCK_RE.finditer(markdown_text))
    declared_file_headers = re.findall(r"^\s*###\s+FILE:\s+([^\r\n]+)", markdown_text, re.MULTILINE)
    if len(file_matches) < len(declared_file_headers):
        patch_errors.append(
            f"[STAGE ERROR] 宣告了 {len(declared_file_headers)} 個 ### FILE: 標記，"
            f"但僅成功解析 {len(file_matches)} 個完整代碼區塊（可能有未閉合的 ``` 圍欄或輸出截斷）。"
        )

    for match in file_matches:
        norm_rel = _safe_rel_path(match.group(1))
        if not norm_rel:
            patch_errors.append(f"[STAGE BLOCK] 非法路徑穿越已攔截: {match.group(1).strip()}")
            continue
        dest = STAGING_DIR / norm_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(match.group(2) + "\n", encoding="utf-8")
        if norm_rel not in staged_files:
            staged_files.append(norm_rel)

    # 2. Process surgical PATCH blocks (fenced or unfenced)
    for match in PATCH_BLOCK_RE.finditer(markdown_text):
        norm_rel = _safe_rel_path(match.group(1))
        if not norm_rel:
            patch_errors.append(f"[STAGE BLOCK] 非法路徑穿越已攔截: {match.group(1).strip()}")
            continue

        staged_target = STAGING_DIR / norm_rel
        workspace_target = REPO_ROOT / norm_rel

        if staged_target.is_file():
            base_text = staged_target.read_text(encoding="utf-8", errors="replace")
        elif workspace_target.is_file():
            base_text = workspace_target.read_text(encoding="utf-8", errors="replace")
        else:
            patch_errors.append(f"[PATCH ERROR] {norm_rel}: 目標原始檔案不存在，新建檔案請改用 ### FILE: {norm_rel}")
            continue

        ok, new_text, errs = apply_surgical_patch(base_text, match.group(2), str(norm_rel))
        if not ok:
            patch_errors.extend(errs)
            continue

        staged_target.parent.mkdir(parents=True, exist_ok=True)
        staged_target.write_text(new_text if new_text.endswith("\n") else new_text + "\n", encoding="utf-8")
        if norm_rel not in staged_files:
            staged_files.append(norm_rel)

    # Fail-Closed: if input declared ### FILE: or ### PATCH: headers but 0 files were staged, report error
    if not patch_errors and not staged_files and re.search(r"###\s+(?:FILE|PATCH):", markdown_text):
        patch_errors.append("[STAGE ERROR] 偵測到 ### FILE:/PATCH: 標記，但未擷取到有效代碼區塊（請檢查 ``` 圍欄格式）。")

    if patch_errors:
        for pe in patch_errors:
            print(f"🛑 {pe}", file=sys.stderr)
        return False, staged_files, patch_errors

    print(f"[STAGE] 已將 {len(staged_files)} 個檔案落地至沙盒 .studio/staging/: {[str(p) for p in staged_files]}")
    return True, staged_files, []


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

        # Check PHP 8.4 / Laravel 13 guard on staged absolute paths
        php_blocked, php_violations = local_guard.check_laravel_php_guard(combined_code, abs_paths)
        if php_blocked:
            errors.extend(php_violations)
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

    # 3. Run UI Anti-Slop Audit on staged Frontend UI components
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
    parser = argparse.ArgumentParser(description="Zero-Token Sandbox Stager & Step 2.5 Sieve (v3.1)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_stage = sub.add_parser("stage", help="從 Markdown 檔案或 stdin 擷取 ### FILE: 與 ### PATCH: 寫入 .studio/staging/")
    p_stage.add_argument("--input", "-i", type=str, help="Markdown 輸入檔案路徑 (未指定則讀 stdin)")
    p_stage.add_argument("--clean", action="store_true", help="寫入前清空舊沙盒")

    sub.add_parser("sieve", help="對 .studio/staging/ 執行 Step 2.5 0-Token 確定性快篩")
    sub.add_parser("commit", help="將驗證通過的沙盒檔案原子移動至正式目錄")

    args = parser.parse_args()
    if args.cmd == "stage":
        text = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        ok, staged, errs = extract_and_stage(text, clean=args.clean)
        sys.exit(0 if ok else 1)
    elif args.cmd == "sieve":
        ok, _ = run_step25_sieve()
        sys.exit(0 if ok else 1)
    elif args.cmd == "commit":
        sys.exit(commit_sandbox())


if __name__ == "__main__":
    main()
