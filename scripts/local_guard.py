#!/usr/bin/env python3
"""
local_guard.py - System 1 本機高速決策門禁與 Ponytail 階梯審查器 (Decoupled & Pluggable)
相容 TypeSafe Jev / Ollaya /v1/systemone 開放規範
整合 gate.yaml 物理阻斷、正則憑證掃描、Ponytail 7 階梯與插拔式決策引擎
"""

import sys
import os
import re
import json
import time
import fnmatch
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# 確保 Windows / POSIX 終端統一支援 UTF-8 與 Emoji
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent

# 插拔式設定：可隨時透過環境變數無痛替換模型與服務端點
DECISION_API_URL = os.environ.get(
    "DECISION_API_URL",
    os.environ.get("OLLAYA_URL", "http://127.0.0.1:11435/v1/systemone")
)
DECISION_MODEL = os.environ.get("DECISION_MODEL", "laya:multilingual")
TIMEOUT_SEC = float(os.environ.get("DECISION_TIMEOUT", os.environ.get("OLLAYA_TIMEOUT", "10.0")))

# ANSI 顏色
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# 常見硬編碼金鑰的正則特徵 (Level 0 物理阻斷)
SECRET_PATTERNS = [
    (r"(?:api[_-]?key|secret|token|password|passwd|auth)[\s:=]+['\"][A-Za-z0-9_\-\.]{16,}['\"]", "疑似硬編碼 API 金鑰/密鑰"),
    (r"sk-[a-zA-Z0-9_\-]{20,}", "OpenAI / 服務金鑰 (sk-...)"),
    (r"ghp_[a-zA-Z0-9]{36,}", "GitHub Personal Access Token"),
    (r"AIza[0-9A-Za-z-_]{35}", "Google API Key"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
]


def normalize_path(path_str: str) -> str:
    """正規化路徑為 POSIX 正斜線並清理開頭 segment"""
    cleaned = path_str.replace("\\", "/").strip()
    if cleaned.startswith("./"):
        cleaned = cleaned[2:]
    cleaned = re.sub(r"/+", "/", cleaned)
    return cleaned


def match_glob(pattern: str, file_path: str) -> bool:
    """
    高強健度 Glob 匹配，支援 '**' 遞迴萬用字元與任意前綴路徑
    """
    norm_pat = normalize_path(pattern)
    norm_path = normalize_path(file_path)

    # 1. 直接相等
    if norm_pat == norm_path:
        return True

    # 2. 若規則以 **/ 開頭，去除前綴比對主檔名或任意子路徑
    if norm_pat.startswith("**/"):
        sub_pat = norm_pat[3:]
        # 比對全路徑或子路徑
        if fnmatch.fnmatch(norm_path, norm_pat) or fnmatch.fnmatch(norm_path, sub_pat):
            return True
        # 比對純檔名 (basename)
        base_name = norm_path.split("/")[-1]
        if fnmatch.fnmatch(base_name, sub_pat):
            return True
        # 若 sub_pat 同時以 /** 結尾 (如 **/secrets/** -> secrets/**)
        if sub_pat.endswith("/**"):
            sub_prefix = sub_pat[:-3]
            if norm_path.startswith(sub_prefix + "/") or norm_path == sub_prefix:
                return True

    # 3. 標準 fnmatch 匹配
    if fnmatch.fnmatch(norm_path, norm_pat):
        return True

    # 4. 若規則以 /** 結尾，匹配該目錄及其所有子檔案
    if norm_pat.endswith("/**"):
        prefix = norm_pat[:-3]
        if norm_path.startswith(prefix + "/") or norm_path == prefix:
            return True

    return False


def find_gate_file(custom_root: Optional[Path] = None) -> Optional[Path]:
    """多層級回退解析 gate.yaml 物理門禁配置"""
    root = custom_root or REPO_ROOT
    candidates = [
        root / "gate.yaml",
        Path.cwd() / "gate.yaml",
        root / "templates" / "loop-engineering" / "gate.yaml",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def parse_gate_yaml_simple(gate_file: Path) -> Tuple[List[str], int]:
    """輕量純標準庫 YAML 解析器，支援行內註解過濾"""
    denylist = []
    max_files = 8
    try:
        lines = gate_file.read_text(encoding="utf-8", errors="replace").splitlines()
        in_denylist = False
        for raw_line in lines:
            line = raw_line.split("#")[0].strip()
            if not line:
                continue

            if line.startswith("denylist:"):
                in_denylist = True
                continue
            elif in_denylist:
                if line.startswith("-"):
                    val = line.lstrip("- ").strip().strip('"').strip("'")
                    if val:
                        denylist.append(val)
                elif not line.startswith("-"):
                    in_denylist = False

            if line.startswith("maxFiles:"):
                try:
                    max_files = int(line.split(":")[1].strip())
                except ValueError:
                    pass
    except Exception:
        pass
    return denylist, max_files


def check_regex_secrets(text: str) -> List[str]:
    """使用正則快速掃描常見硬編碼敏感憑證 (純靜態，無模型依賴)"""
    found = []
    for pattern, desc in SECRET_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            found.append(desc)
    return found


def check_gate_yaml(changed_files: List[str], repo_root: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """依據 gate.yaml 審查變更檔案是否觸犯 denylist 或超過 maxFiles"""
    gate_file = find_gate_file(repo_root)
    if not gate_file:
        return False, []

    denylist, max_files = parse_gate_yaml_simple(gate_file)
    violations = []

    # 1. 檢查檔案總數上限
    if len(changed_files) > max_files:
        violations.append(f"變更檔案數 ({len(changed_files)}) 超過 gate.yaml 上限 ({max_files} 檔案)")

    # 2. 檢查 denylist 敏感路徑 (Globstar 遞迴比對)
    for f in changed_files:
        norm_f = normalize_path(f)
        for pattern in denylist:
            if match_glob(pattern, norm_f):
                violations.append(f"禁止自動修改敏感路徑: {norm_f} (符合規則: {pattern})")
                break

    return (len(violations) > 0), violations


def query_system_one(state_text: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    向 System 1 決策端點 (相容 TypeSafe Jev / Ollaya 等開放 /v1/systemone 協議) 發送結構化裁決請求
    依據環境變數動態適配 Provider:
      - 本地端點: Ollaya / vLLM (預設參考模型: laya:latest)
      - 雲端端點: Jev Cloud / TypeSafe API (可配置 API Key)
      - 降級引擎: 靜態啟發式規則引擎 (Static Fallback)
    """
    # 截取前 500 字元以安全適配中英文多語系在 System 1 模型 512 Token 上下文窗口
    truncated_state = state_text[:500] if len(state_text) > 500 else state_text

    payload = {
        "model": DECISION_MODEL,
        "state": truncated_state,
        "questions": {
            "has_test_seam": {
                "type": "noul",
                "instructions": "Does this code introduce test-only mock helpers, test stubs, or artificial testing backdoors?"
            },
            "ponytail_ladder": {
                "type": "choice",
                "instructions": "Which Ponytail ladder level does this code belong to?",
                "criteria": {
                    "1_yagni": "Speculative code that should not exist at all",
                    "2_existing": "Can reuse an existing function or helper in the codebase",
                    "3_stdlib": "Can be implemented using language standard library (Date, Regex, Math, Array)",
                    "4_native": "Can use native platform, browser, CSS, or DB constraint",
                    "5_deps": "Uses existing installed dependencies without new custom code",
                    "6_oneliner": "Can be written in a single concise line",
                    "7_mvp": "Requires minimum viable custom business logic"
                }
            },
            "overengineering_score": {
                "type": "score",
                "instructions": "Rate over-engineering level from 1 (minimal) to 5 (bloated/over-abstracted)",
                "criteria": [
                    "Minimal and clean, no unnecessary abstractions",
                    "Minor helpers, standard idiomatic code",
                    "Moderate complexity, some extra wrappers",
                    "High complexity, multiple layers of indirection",
                    "Severely over-engineered, excessive factories and wrappers"
                ]
            }
        }
    }

    headers = {"Content-Type": "application/json; charset=utf-8"}
    api_key = os.environ.get("TYPESAFE_API_KEY", os.environ.get("JEV_API_KEY", os.environ.get("DECISION_API_KEY")))
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            DECISION_API_URL,
            data=data,
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
            if resp.status == 200:
                res_body = json.loads(resp.read().decode("utf-8"))
                provider_tag = "System 1"
                if "11435" in DECISION_API_URL or "ollaya" in DECISION_API_URL.lower():
                    provider_tag = "Ollaya"
                elif "jev" in DECISION_API_URL.lower() or api_key:
                    provider_tag = "Jev Cloud"
                return res_body.get("answers", {}), f"{provider_tag} ({DECISION_MODEL})"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"{YELLOW}⚠️  決策端點回傳 HTTP {e.code}: {err_body}{RESET}", file=sys.stderr)
    except urllib.error.URLError:
        pass  # 離線時靜默由 Fallback 接管
    except Exception as e:
        print(f"{YELLOW}⚠️  決策端點呼叫異常: {e}{RESET}", file=sys.stderr)

    return None, "Static Rule Engine (Fallback)"


def run_guard(code_content: str, label: str = "Diff/Snippet", changed_files: Optional[List[str]] = None) -> int:
    """執行完整審查並以簡潔表格輸出結果，回傳退出碼 (0: 通過, 1: 攔截)"""
    if not code_content.strip() and not changed_files:
        print(f"{CYAN}ℹ️  [System 1 Guard] 內容為空，無變更需審查。{RESET}")
        return 0

    print(f"\n{BOLD}🛡️  [System 1 Guard] 啟動高速決策門禁審查 ({label})...{RESET}")
    
    is_blocked = False
    block_reasons = []

    # 1. 物理阻斷：gate.yaml 檢查 (Denylist & MaxFiles)
    gate_blocked = False
    if changed_files:
        gate_blocked, gate_violations = check_gate_yaml(changed_files)
        if gate_blocked:
            is_blocked = True
            block_reasons.extend(gate_violations)

    # 2. 物理阻斷：正則敏感金鑰檢查
    regex_secrets = check_regex_secrets(code_content)
    if regex_secrets:
        is_blocked = True
        for s in regex_secrets:
            block_reasons.append(f"物理阻斷：偵測到硬編碼憑證 ({s})")

    # 3. 呼叫 System 1 決策引擎 (可插拔式後端)
    t0 = time.perf_counter()
    answers, engine_name = query_system_one(code_content) if code_content.strip() else (None, "Bypassed")
    elapsed_ms = (time.perf_counter() - t0) * 1000

    seam_prob = 0.0
    ladder_choice = "N/A"
    ladder_conf = 0.0
    bloat_score = 1.0

    if answers:
        seam_prob = answers.get("has_test_seam", {}).get("noul", 0.0)
        ladder_obj = answers.get("ponytail_ladder", {})
        ladder_choice = ladder_obj.get("choice", "7_mvp")
        ladder_conf = ladder_obj.get("confidence", 0.0)
        score_obj = answers.get("overengineering_score", {})
        bloat_score = float(score_obj.get("score", 1.0))

        # 判定生產接縫 (Zero Production Seams)
        # 短程式碼 (< 80 字元) 且完全未出現測試相關關鍵字時，防止小模型無語境誤殺
        TEST_SEAM_KEYWORDS = ["mock", "stub", "fake", "spy", "fixture", "backdoor", "dummy", "test_", "__test"]
        has_seam_hint = any(kw in code_content.lower() for kw in TEST_SEAM_KEYWORDS)

        if seam_prob > 0.65:
            if len(code_content.strip()) < 80 and not has_seam_hint:
                # 視為微弱統計雜訊，不執行硬攔截
                pass
            else:
                is_blocked = True
                block_reasons.append(f"違反零生產接縫原則：偵測到測試專用 Mock/後門 (信心 {seam_prob*100:.1f}%)")

        # 判定嚴重肥大/過度工程 (修復: 設定 is_blocked = True)
        if bloat_score >= 4.0:
            is_blocked = True
            block_reasons.append(f"過度工程指數過高 ({bloat_score:.1f}/5)，違反 Ponytail 精簡原則")
    else:
        # Fallback 提示
        ladder_choice = "Static-Rules"

    status_header = f"{RED}🛑 BLOCK - 變更遭駁回{RESET}" if is_blocked else f"{GREEN}✅ PASS - 審查通過{RESET}"
    
    print("┌─────────────────────────────────────────────────────────────┐")
    print(f"│ 審查狀態: {status_header:<49} │")
    print(f"│ 決策引擎: {CYAN}{engine_name:<25}{RESET} 耗時: {elapsed_ms:6.1f} ms    │")
    print("├─────────────────────────────────────────────────────────────┤")
    print(f"│  • 生產接縫機率 (Zero Seams)   : {format_prob(seam_prob) if answers else '⚠️  離線降級放行'}                  │")
    print(f"│  • 硬編碼金鑰風險 (Regex Guard): {format_secret(len(regex_secrets))}                  │")
    print(f"│  • Ponytail 階梯定位           : {CYAN}{ladder_choice:<15}{RESET} (信心: {ladder_conf*100:4.1f}%) │")
    print(f"│  • 過度工程評分 (1~5)          : {format_score(bloat_score) if answers else 'N/A         '}                       │")
    print(f"│  • gate.yaml 門禁規範          : {format_gate_status(not gate_blocked)}                       │")
    print("└─────────────────────────────────────────────────────────────┘")

    if is_blocked:
        print(f"\n{RED}{BOLD}🚨 攔截原因：{RESET}")
        for r in block_reasons:
            print(f"  {RED}✖ {r}{RESET}")
        print(f"\n{YELLOW}💡 建議：請依照 Ponytail 7 階梯重構或拔除生產測試接縫後重試。{RESET}\n")
        return 1
    else:
        print(f"{GREEN}✨ 代碼符合邊界規範與 Ponytail 階梯，允許提交/合併。{RESET}\n")
        return 0


def format_prob(p: float) -> str:
    color = RED if p > 0.6 else (YELLOW if p > 0.3 else GREEN)
    return f"{color}{p*100:5.1f}%{RESET}"


def format_secret(count: int) -> str:
    if count > 0:
        return f"{RED}🚨 發現 {count} 處{RESET}"
    return f"{GREEN}✅ 乾淨   {RESET}"


def format_score(score: float) -> str:
    color = RED if score >= 4.0 else (YELLOW if score >= 3.0 else GREEN)
    return f"{color}{score:4.1f} / 5{RESET}"


def format_gate_status(is_clean: bool) -> str:
    if is_clean:
        return f"{GREEN}✅ 合規通過{RESET}"
    return f"{RED}🛑 違規攔截{RESET}"


def get_git_info() -> Tuple[str, List[str]]:
    """獲取當前工作區未提交的 git diff 與變更檔案清單 (包含已暫存、未暫存與未追蹤檔案)"""
    try:
        # 1. 抓取已追蹤變更檔案名稱 (diff against HEAD)
        name_bytes = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], stderr=subprocess.DEVNULL)
        changed_files = [f.strip() for f in name_bytes.decode("utf-8", errors="replace").splitlines() if f.strip()]

        # 2. 抓取未追蹤檔案清單 (Untracked files)
        untracked_bytes = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            stderr=subprocess.DEVNULL
        )
        untracked_files = [f.strip() for f in untracked_bytes.decode("utf-8", errors="replace").splitlines() if f.strip()]
        for uf in untracked_files:
            if uf not in changed_files:
                changed_files.append(uf)

        # 3. 抓取 diff 內容 (先 cached 後 HEAD)
        diff = subprocess.check_output(["git", "diff", "--cached"], text=True, errors="replace", stderr=subprocess.DEVNULL)
        if not diff.strip():
            diff = subprocess.check_output(["git", "diff", "HEAD"], text=True, errors="replace", stderr=subprocess.DEVNULL)

        # 4. 若有未追蹤檔案但 diff 為空，讀取未追蹤檔案內容納入審查字串
        if untracked_files and not diff.strip():
            extra_snippets = []
            for uf in untracked_files[:5]:
                p = Path(uf)
                if p.is_file():
                    try:
                        extra_snippets.append(f"--- untracked: {uf} ---\n" + p.read_text(encoding="utf-8", errors="replace")[:1000])
                    except Exception:
                        pass
            diff = "\n".join(extra_snippets)

        return diff, changed_files
    except Exception:
        return "", []


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="System 1 Local Guard - 解耦與插拔式高速決策門禁")
    parser.add_argument("--git", action="store_true", help="自動審查當前 git diff 與檔案變更")
    parser.add_argument("--code", type=str, help="直接傳入要審查的代碼字串")
    parser.add_argument("--file", type=str, help="指定要審查的檔案路徑")
    parser.add_argument("--stdin", action="store_true", help="從標準輸入 (stdin) 讀取內容")

    args = parser.parse_args()

    content = ""
    label = "Direct Input"
    changed_files = []

    if args.file:
        p = Path(args.file)
        if p.exists():
            content = p.read_text(encoding="utf-8", errors="replace")
            label = f"File: {p.name}"
            changed_files = [str(p)]
        else:
            print(f"{RED}❌ 找不到指定檔案: {args.file}{RESET}")
            sys.exit(1)
    elif args.code:
        content = args.code
        label = "Code Snippet"
    elif args.stdin:
        content = sys.stdin.read()
        label = "Stdin Stream"
    else:
        content, changed_files = get_git_info()
        label = f"Git Diff (Auto, {len(changed_files)} files)"

    sys.exit(run_guard(content, label, changed_files))
