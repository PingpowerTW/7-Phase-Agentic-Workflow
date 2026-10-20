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
import socket
import subprocess
import urllib.request
import urllib.error
from urllib.parse import urlparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# 確保 Windows / POSIX 終端統一支援 UTF-8 與 Emoji
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from loop_gate import normalize_path, match_glob, find_gate_file, parse_gate_yaml  # noqa: E402

# 插拔式設定：可隨時透過環境變數無痛替換模型與服務端點
DECISION_API_URL = os.environ.get(
    "DECISION_API_URL",
    os.environ.get("OLLAYA_URL", "http://127.0.0.1:11435/v1/systemone")
)
DECISION_MODEL = os.environ.get("DECISION_MODEL", "laya:multilingual")
TIMEOUT_SEC = float(os.environ.get("DECISION_TIMEOUT", os.environ.get("OLLAYA_TIMEOUT", "10.0")))
_LOCAL_ENDPOINT_CACHE: Dict[str, bool] = {}

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
    (r"(?<![a-zA-Z0-9])sk-[a-zA-Z0-9_\-]{20,}", "OpenAI / 服務金鑰 (sk-...)"),
    (r"ghp_[a-zA-Z0-9]{36,}", "GitHub Personal Access Token"),
    (r"AIza[0-9A-Za-z-_]{35}", "Google API Key"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
]


class GateResult(tuple):
    denylist: List[str]
    max_files: int
    allowlist: List[str]

    def __new__(cls, denylist: List[str], max_files: int, allowlist: Optional[List[str]] = None):
        return super().__new__(cls, (denylist, max_files))

    def __init__(self, denylist: List[str], max_files: int, allowlist: Optional[List[str]] = None):
        self.denylist = denylist
        self.max_files = max_files
        self.allowlist = allowlist or []


def parse_gate_yaml_simple(gate_file: Path) -> GateResult:
    """複用 loop_gate.parse_gate_yaml 唯一真實來源並回傳向後相容之 GateResult"""
    try:
        cfg = parse_gate_yaml(gate_file)
        return GateResult(cfg.get("denylist", []), cfg.get("maxFiles", 8), cfg.get("autoMergeAllowlist", []))
    except Exception:
        return GateResult([], 8, [])


def check_regex_secrets(text: str) -> List[str]:
    """使用正則快速掃描常見硬編碼敏感憑證 (純靜態，無模型依賴)"""
    found = []
    for pattern, desc in SECRET_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            found.append(desc)
    return found


def check_ast_guard(code_content: str, changed_files: Optional[List[str]]) -> Tuple[bool, List[str]]:
    """調用 scripts/ast_guard.js 進行 Level 0.5 確定性 AST 語意審查 (零生產接縫 & 垃圾測試門禁)"""
    guard_js = Path(__file__).resolve().parent / "ast_guard.js"
    if not guard_js.exists():
        return False, []

    js_files = [f for f in (changed_files or []) if re.search(r"\.(js|jsx|ts|tsx|mjs|cjs)$", f, re.I)]
    if not js_files and not code_content.strip():
        return False, []

    cmd = ["node", str(guard_js)]
    if js_files:
        cmd.extend(js_files)
    elif code_content.strip():
        cmd.extend(["--code", code_content])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=15)
        if proc.returncode == 1:
            err_output = (proc.stderr or proc.stdout).strip().splitlines()
            violations = [line for line in err_output if "INV_VERIFY" in line or "BLOCK" in line or "嚴禁" in line]
            if not violations:
                violations = ["AST 門禁阻斷：違反零生產接縫 (INV_VERIFY_03) 或垃圾測試規範 (INV_VERIFY_02)"]
            return True, violations
    except Exception:
        pass  # Node 未安裝時自動安全放行，不中斷本地開發

    return False, []


def check_laravel_php_guard(code_content: str, changed_files: Optional[List[str]]) -> Tuple[bool, List[str]]:
    """
    Level 0.5 PHP 8.4+ / Laravel 13+ 確定性零技術債與防 Bug 門禁 (0 Token, <5ms)
    檢查項目：
    1. INV_PHP_01: 強制 declare(strict_types=1);
    2. INV_LARAVEL_01: Eloquent Model Property Shadowing 屬性遮蔽防護
    3. INV_LARAVEL_02: 強制使用 casts(): array 方法取代舊版 $casts 屬性
    4. INV_LARAVEL_03: Thin Controller, Fat Action (Controller 嚴禁 >120 行或含裸 DB 查詢)
    5. INV_LARAVEL_04: 嚴禁 $guarded = [] 批量賦值漏洞
    """
    violations: List[str] = []
    php_files = [f for f in (changed_files or []) if f.lower().endswith(".php") and not f.lower().endswith(".blade.php")]

    # 將要檢查的目標統一轉為 (檔名, 內容) 清單
    targets: List[Tuple[str, str]] = []
    if php_files:
        for pf in php_files:
            p = Path(pf) if Path(pf).is_absolute() else (REPO_ROOT / pf)
            if p.is_file():
                targets.append((normalize_path(pf), p.read_text(encoding="utf-8", errors="replace")))
    elif not changed_files and code_content.strip() and ("<?php" in code_content or "namespace App\\" in code_content):
        targets.append(("snippet.php", code_content))

    if not targets:
        return False, []

    # Model 內合法的 Eloquent 系統屬性白名單
    ELOQUENT_ALLOWED_PROPS = {
        "table", "primaryKey", "keyType", "incrementing", "with", "withCount",
        "preventsLazyLoading", "perPage", "exists", "wasRecentlyCreated",
        "connection", "timestamps", "dateFormat", "Casts", "touches",
        "observables", "relations", "hidden", "visible", "appends",
        "fillable", "guarded", "dates", "casts", "dispatchesEvents"
    }

    for norm_path, content in targets:
        lines = content.splitlines()
        line_count = len(lines)
        is_model = "/models/" in f"/{norm_path.lower()}" or re.search(r"extends\s+(?:Model|Authenticatable|Pivot)\b", content)
        is_controller = "/controllers/" in f"/{norm_path.lower()}" or re.search(r"class\s+\w+Controller\b", content)

        # 1. INV_PHP_01: 檢查 declare(strict_types=1);
        if "<?php" in content and not re.search(r"declare\s*\(\s*strict_types\s*=\s*1\s*\)\s*;", content):
            violations.append(
                f"[INV_PHP_01] {norm_path}: 缺少 `declare(strict_types=1);`。"
                f"FIX: 請在 `<?php` 下方第一行加上 `declare(strict_types=1);`。"
            )

        # 2. INV_LARAVEL_01 ~ 04: Eloquent Model 專屬防呆
        if is_model:
            # 2a. 檢查舊版 $casts 屬性 (INV_LARAVEL_02)
            if re.search(r"protected\s+(?:array\s+)?\$casts\s*=", content):
                violations.append(
                    f"[INV_LARAVEL_02] {norm_path}: 偵測到舊版 `$casts` 屬性。"
                    f"FIX: Laravel 13 規範強制改用方法宣告 `protected function casts(): array {{ return [...]; }}`。"
                )

            # 2b. 檢查 $guarded = [] 資安漏洞 (INV_LARAVEL_04)
            if re.search(r"protected\s+(?:array\s+)?\$guarded\s*=\s*\[\s*\]", content):
                violations.append(
                    f"[INV_LARAVEL_04] {norm_path}: 嚴禁使用 `$guarded = []` 開放全欄位 Mass Assignment。"
                    f"FIX: 請改用 `protected $fillable = [...]` 明確列出允許寫入的欄位。"
                )

            # 2c. 檢查 Eloquent Property Shadowing 屬性遮蔽 (INV_LARAVEL_01)
            prop_pattern = re.compile(
                r"^\s*(?:public|protected|private)\s+(?:private\(set\)\s+|protected\(set\)\s+|readonly\s+)?"
                r"(?:\??[a-zA-Z0-9_\\|]+\s+)?\$([a-zA-Z0-9_]+)",
                re.MULTILINE
            )
            for match in prop_pattern.finditer(content):
                prop_name = match.group(1)
                full_decl = match.group(0).strip()
                if "static " in full_decl:
                    continue
                if prop_name not in ELOQUENT_ALLOWED_PROPS:
                    violations.append(
                        f"[INV_LARAVEL_01] {norm_path}: 偵測到 Eloquent 屬性遮蔽 `{full_decl}`！"
                        f"在 Model 直接宣告 DB 欄位屬性會破壞 Eloquent `$attributes` 動態注水與關聯。"
                        f"FIX: 請移除該屬性宣告，改用 PHPDoc `@property` 註解，並將 `public private(set)` 保留給 DTO 或 Action。"
                    )

        # 3. INV_LARAVEL_03: Thin Controller, Fat Action 檢查
        if is_controller:
            if line_count > 120:
                violations.append(
                    f"[INV_LARAVEL_03] {norm_path}: Controller 行數達 {line_count} 行（上限 120 行），違反 Thin Controller 原則。"
                    f"FIX: 請將業務邏輯抽離至 `app/Actions/` 下的 Invokable Action 類別。"
                )
            if re.search(r"\b(?:DB::table|DB::raw|whereHas|orWhereHas|join|leftJoin)\s*\(", content):
                violations.append(
                    f"[INV_LARAVEL_03] {norm_path}: Controller 內偵測到複雜資料庫查詢 (`DB::table / whereHas / join`)。"
                    f"FIX: Controller 僅負責路由與 FormRequest 轉發，請將查詢邏輯移至 Action 或 Service。"
                )

    return (len(violations) > 0), violations


def check_gate_yaml(changed_files: List[str], repo_root: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """依據 gate.yaml 審查變更檔案是否觸犯 denylist 或超過 maxFiles (autoMergeAllowlist 不佔代碼上限)"""
    gate_file = find_gate_file(repo_root)
    if not gate_file:
        return False, []

    gate_res = parse_gate_yaml_simple(gate_file)
    denylist = gate_res.denylist if hasattr(gate_res, "denylist") else gate_res[0]
    max_files = gate_res.max_files if hasattr(gate_res, "max_files") else gate_res[1]
    allowlist = getattr(gate_res, "allowlist", [])

    violations = []

    # 過濾屬於 autoMergeAllowlist 的文檔/標記檔案 (不計入代碼變更檔案上限)
    code_files = []
    for f in changed_files:
        norm_f = normalize_path(f)
        is_allowed = any(match_glob(pat, norm_f) for pat in allowlist)
        if not is_allowed:
            code_files.append(f)

    # 1. 檢查代碼檔案總數上限
    if len(code_files) > max_files:
        violations.append(f"變更代碼檔案數 ({len(code_files)}) 超過 gate.yaml 上限 ({max_files} 檔案)")

    # 2. 檢查 denylist 敏感路徑 (Globstar 遞迴比對，所有檔案一律嚴禁觸犯)
    for f in changed_files:
        norm_f = normalize_path(f)
        for pattern in denylist:
            if match_glob(pattern, norm_f):
                violations.append(f"禁止自動修改敏感路徑: {norm_f} (符合規則: {pattern})")
                break

    return (len(violations) > 0), violations


def check_decision_regression(
    code_content: str,
    changed_files: Optional[List[str]] = None,
) -> Tuple[bool, List[str]]:
    """
    歷史決策防翻案門禁 (borrowed from Trail-Code local-check.ts):
    掃描 .agent/SNAPSHOT.jsonl 中帶有 `ruled_out` 與 `touches`/`files` 之 decision 快照，
    若當前變更觸及錨定檔案且新增行重現曾被排除的作法/常數，立即攔截並引用原決策理由。
    """
    if not code_content.strip():
        return False, []

    snap_file = next(
        (
            p for base in (Path.cwd(), REPO_ROOT)
            for p in (base / ".agent" / "SNAPSHOT.jsonl", base / ".agents" / "SNAPSHOT.jsonl")
            if p.is_file()
        ),
        None,
    )
    if not snap_file:
        return False, []

    is_diff = any(line.startswith(("@@ ", "+++ ")) for line in code_content.splitlines())
    if is_diff:
        added_lines = [
            line[1:] for line in code_content.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
    else:
        added_lines = code_content.splitlines()

    added_blob = "\n".join(added_lines).lower()
    if not added_blob.strip():
        return False, []

    norm_changed = [normalize_path(f) for f in (changed_files or []) if f]
    violations: List[str] = []

    # OpenMontage 'Re-log Changed Decisions' Contract:
    # Fold append-only SNAPSHOT.jsonl by (category, subject) or touches anchor so revised decisions supersede stale ones.
    active_decisions: Dict[str, Dict[str, Any]] = {}
    for idx, raw in enumerate(snap_file.read_text(encoding="utf-8", errors="replace").splitlines()):
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except Exception:
            continue
        if not isinstance(entry, dict) or entry.get("type") != "decision":
            continue

        touches_raw = entry.get("touches") or entry.get("files") or []
        if isinstance(touches_raw, str):
            touches_raw = [touches_raw]
        norm_touches = ",".join(sorted(normalize_path(str(t)) for t in touches_raw if t))
        subj = entry.get("subject")
        cat = entry.get("category", "default")
        title_str = entry.get("title") or entry.get("summary") or ""

        # Evict prior decision if it shares the same (category, subject), same title,
        # or same touches anchor without a conflicting subject.
        for k, old in list(active_decisions.items()):
            old_subj = old.get("subject")
            old_touches_raw = old.get("touches") or old.get("files") or []
            if isinstance(old_touches_raw, str):
                old_touches_raw = [old_touches_raw]
            old_touches = ",".join(sorted(normalize_path(str(t)) for t in old_touches_raw if t))
            if subj and old_subj:
                if (cat, subj) == (old.get("category", "default"), old_subj):
                    del active_decisions[k]
            elif (title_str and title_str == (old.get("title") or old.get("summary"))) or (norm_touches and norm_touches == old_touches):
                del active_decisions[k]

        d_key = f"{cat}::{subj}" if subj else (f"touches::{norm_touches}" if norm_touches else f"title::{title_str or idx}")
        active_decisions[d_key] = entry

    for entry in active_decisions.values():
        if entry.get("superseded") is True:
            continue
        ruled_out = entry.get("ruled_out") or []
        if isinstance(ruled_out, str):
            ruled_out = [ruled_out]
        if not ruled_out:
            continue

        touches = entry.get("touches") or entry.get("files") or []
        if isinstance(touches, str):
            touches = [touches]

        if touches:
            if not norm_changed:
                continue
            touch_files = [normalize_path(t.split("#")[0]) for t in touches if t]
            file_hit = any(
                cf == tf or cf.endswith("/" + tf) or tf.endswith("/" + cf)
                for cf in norm_changed
                for tf in touch_files
            )
            if not file_hit:
                continue

        title = entry.get("title") or entry.get("subject") or entry.get("summary") or "歷史技術決策"
        reason = entry.get("decision") or ""
        for item in ruled_out:
            pat = str(item).strip()
            if pat and re.search(rf"(?<![a-z0-9_]){re.escape(pat.lower())}(?![a-z0-9_])", added_blob):
                violations.append(
                    f"[INV_DECISION_01] 違反歷史決策《{title}》: 偵測到曾被排除的作法/數值 `{pat}` — {reason}"
                )

    return (len(violations) > 0), violations


from collections import deque
from statistics import median


class MedianRuntimeTracker:
    """
    DeepInfer Sliding-Window Median Runtime Estimator (borrowed from csrc/engine/mtp_varlen.hpp).
    Uses stdlib deque(maxlen) + statistics.median (Ponytail Tier 3 Stdlib) to compute a spike-resistant
    RPC latency baseline without offline Handwired ReLU pollution.
    """
    def __init__(self, window_size: int = 9, min_samples: int = 5) -> None:
        self._samples: deque[float] = deque(maxlen=max(1, window_size))
        self._min_samples = max(1, min(min_samples, self._samples.maxlen or 1))

    def update(self, value_ms: float) -> None:
        self._samples.append(max(0.0, float(value_ms)))

    def get(self) -> Optional[float]:
        return round(float(median(self._samples)), 2) if len(self._samples) >= self._min_samples else None

    def adaptive_timeout_sec(self, default_sec: float = TIMEOUT_SEC) -> float:
        med = self.get()
        return default_sec if med is None else min(default_sec, max(0.25, (med * 3.0) / 1000.0))


_RUNTIME_TRACKER = MedianRuntimeTracker()


def _is_local_endpoint_alive(api_url: str) -> bool:
    """50ms 本地 Loopback TCP 快速探活，消除 Windows 離線 2000ms SYN 重試延遲"""
    try:
        parsed = urlparse(api_url)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if host not in ("127.0.0.1", "localhost", "::1"):
            return True
        cache_key = f"{host}:{port}"
        if cache_key in _LOCAL_ENDPOINT_CACHE:
            return _LOCAL_ENDPOINT_CACHE[cache_key]
        with socket.create_connection((host, port), timeout=0.05):
            _LOCAL_ENDPOINT_CACHE[cache_key] = True
            return True
    except (OSError, ValueError):
        if "cache_key" in locals():
            _LOCAL_ENDPOINT_CACHE[cache_key] = False
        return False


# Handwired Zero-Training ReLU Network Default Compiled Weights (6 features -> seam & bloat)
# Features x = [seam_backdoor, enterprise_bloat, wrapper_indirection, stdlib_reinvention, oneliner_concise, loc_scale]
_DEFAULT_HANDWIRED_WEIGHTS: Dict[str, Any] = {
    "w_seam": [0.78, 0.04, 0.05, 0.0, -0.01, 0.02],
    "b_seam": 0.01,
    "w_bloat": [0.25, 0.48, 0.35, 0.55, -0.15, 0.20],
    "b_bloat": 0.05,
}


def _relu(v: float) -> float:
    return v if v > 0.0 else 0.0


def _ramp(v: float, low: float, high: float) -> float:
    """Handwired step-gate primitive: relu(v - low) - relu(v - high)."""
    return _relu(v - low) - _relu(v - high)


def _handwired_weights_path() -> Optional[Path]:
    for base in (Path.cwd(), REPO_ROOT):
        for sub in (".agent", ".agents"):
            p = base / sub / "handwired_weights.json"
            if p.is_file():
                return p
    return None


def _load_handwired_weights() -> Dict[str, Any]:
    p = _handwired_weights_path()
    if p:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if (
                isinstance(data, dict)
                and isinstance(data.get("w_seam"), list) and len(data["w_seam"]) == 6
                and isinstance(data.get("w_bloat"), list) and len(data["w_bloat"]) == 6
                and isinstance(data.get("b_seam"), (int, float))
                and isinstance(data.get("b_bloat"), (int, float))
            ):
                return {
                    "w_seam": [float(v) for v in data["w_seam"]],
                    "b_seam": float(data["b_seam"]),
                    "w_bloat": [float(v) for v in data["w_bloat"]],
                    "b_bloat": float(data["b_bloat"]),
                }
        except Exception:
            pass
    return {
        "w_seam": list(_DEFAULT_HANDWIRED_WEIGHTS["w_seam"]),
        "b_seam": float(_DEFAULT_HANDWIRED_WEIGHTS["b_seam"]),
        "w_bloat": list(_DEFAULT_HANDWIRED_WEIGHTS["w_bloat"]),
        "b_bloat": float(_DEFAULT_HANDWIRED_WEIGHTS["b_bloat"]),
    }


def _extract_handwired_features(state_text: str) -> List[float]:
    """Extract 6 deterministic code features from production added lines."""
    is_diff = any(line.startswith(("@@ ", "+++ ")) for line in state_text.splitlines())
    prod_lines: List[str] = []
    if is_diff:
        curr_is_test_or_guard = False
        for raw in state_text.splitlines():
            if raw.startswith("+++ "):
                fname = raw[4:].lower()
                curr_is_test_or_guard = ("test" in fname) or ("local_guard.py" in fname) or ("ast_guard.js" in fname)
            elif raw.startswith("+") and not raw.startswith("+++") and not curr_is_test_or_guard:
                stripped = raw[1:].strip()
                if stripped and not stripped.startswith(("#", "//", '"""', "'''", "*")):
                    prod_lines.append(stripped)
    else:
        for raw in state_text.splitlines():
            stripped = raw.strip()
            if stripped and not stripped.startswith(("#", "//", '"""', "'''", "*")):
                prod_lines.append(stripped)

    code_blob = "\n".join(prod_lines)
    seam_hits = len(re.findall(
        r"\b(?:_for_test|_test_only|__test_hook__|inject_mock|set_mock_for_test)\b"
        r"|(?:def|function)\s+(?:mock|stub|fake)_[a-zA-Z0-9_]+",
        code_blob,
    ))
    bloat_hits = len(re.findall(
        r"\b(?:class|interface)\s+\w*(?:FactoryBean|ProxyFactory|Abstract\w*Factory|Singleton\w*Manager|ServiceLocator|BuilderStrategy)\w*",
        code_blob,
    ))
    indirection_hits = max(0, len(re.findall(r"\bclass\s+[A-Z]\w*", code_blob)) - 2)
    stdlib_hits = len(re.findall(r"\b(?:def|function)\s+(?:bubble_sort|manual_left_pad|custom_deep_clone)\b", code_blob))
    is_oneliner = 1.0 if (1 <= len(prod_lines) <= 3 and seam_hits == 0 and bloat_hits == 0 and not re.search(r"\bclass\s+", code_blob)) else 0.0
    loc_scale = min(1.0, len(prod_lines) / 300.0)
    return [float(seam_hits), float(bloat_hits), float(indirection_hits), float(stdlib_hits), is_oneliner, loc_scale]


def handwired_system_one(state_text: str) -> Dict[str, Any]:
    """
    Handwired Zero-Training ReLU Scorer:
    Compiles Ponytail 7-Ladder & Zero-Seam heuristics directly into branchless ReLU algebra
    (h = ReLU(W*x + b)) with 0 tokens and <0.1ms latency, while keeping weights differentiable.
    """
    x = _extract_handwired_features(state_text)
    w = _load_handwired_weights()
    z_seam = sum(wi * xi for wi, xi in zip(w["w_seam"], x)) + w["b_seam"]
    seam_prob = round(min(0.99, _relu(z_seam)), 4)

    z_bloat = sum(wi * xi for wi, xi in zip(w["w_bloat"], x)) + w["b_bloat"]
    bloat_score = round(1.0 + 4.0 * _ramp(z_bloat, 0.0, 1.0), 2)

    # Branchless ReLU Gate for Ponytail Ladder selection
    g_yagni = _ramp(bloat_score, 3.8, 4.0) * 5.0          # [0..1] when bloat_score >= 4.0
    g_stdlib = _ramp(x[3], 0.0, 1.0)                      # [0..1] when stdlib reinvention present
    g_oneliner = _ramp(x[4] - x[0] - x[1], 0.0, 1.0)      # [0..1] when concise 1-3 line snippet
    if g_yagni >= 0.9:
        choice, conf = "1_yagni", min(0.98, 0.85 + 0.03 * x[1])
    elif g_stdlib >= 0.9:
        choice, conf = "3_stdlib", 0.90
    elif g_oneliner >= 0.9:
        choice, conf = "6_oneliner", 0.92
    else:
        choice, conf = "7_mvp", 0.88

    return {
        "has_test_seam": {"noul": seam_prob},
        "ponytail_ladder": {"choice": choice, "confidence": round(conf, 2)},
        "overengineering_score": {"score": bloat_score},
    }


def tune_handwired_weights(
    state_text: str,
    target_seam: float,
    target_bloat: float,
    lr: float = 0.08,
) -> Dict[str, Any]:
    """
    Handwired 'Learned Gallery' Weight Unfreezing:
    Applies analytical gradient descent (dL/dW) through the ReLU network to adapt rule weights
    from human feedback without PyTorch/TensorFlow, persisting to .agent/handwired_weights.json.
    """
    x = _extract_handwired_features(state_text)
    w = _load_handwired_weights()

    z_seam = sum(wi * xi for wi, xi in zip(w["w_seam"], x)) + w["b_seam"]
    pred_seam = min(0.99, _relu(z_seam))
    clamped_seam = max(0.0, min(0.99, target_seam))
    grad_seam = (pred_seam - clamped_seam) * (1.0 if (z_seam > 0.0 or clamped_seam > pred_seam) else 0.1)

    z_bloat = sum(wi * xi for wi, xi in zip(w["w_bloat"], x)) + w["b_bloat"]
    pred_bloat = 1.0 + 4.0 * _ramp(z_bloat, 0.0, 1.0)
    clamped_target_bloat = max(1.0, min(5.0, target_bloat))
    grad_bloat = ((pred_bloat - clamped_target_bloat) / 4.0) * (1.0 if (z_bloat > 0.0 or clamped_target_bloat > pred_bloat) else 0.1)

    w["w_seam"] = [round(wi - lr * grad_seam * xi, 6) for wi, xi in zip(w["w_seam"], x)]
    w["b_seam"] = round(w["b_seam"] - lr * grad_seam * 0.25, 6)
    w["w_bloat"] = [round(wi - lr * grad_bloat * xi, 6) for wi, xi in zip(w["w_bloat"], x)]
    w["b_bloat"] = round(w["b_bloat"] - lr * grad_bloat * 0.25, 6)

    target_dir = Path.cwd() / ".agent"
    target_dir.mkdir(parents=True, exist_ok=True)
    out_file = target_dir / "handwired_weights.json"
    out_file.write_text(json.dumps(w, indent=2), encoding="utf-8")
    return w


def query_system_one(state_text: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    向 System 1 決策端點 (相容 TypeSafe Jev / Ollaya 等開放 /v1/systemone 協議) 發送結構化裁決請求
    依據環境變數動態適配 Provider:
      - 本地端點: Ollaya / vLLM (預設參考模型: laya:multilingual)
      - 雲端端點: Jev Cloud / TypeSafe API (可配置 API Key)
      - 降級引擎: Handwired ReLU 無分支白盒網路 (0-Token, <0.1ms, 支援梯度微調)
    """
    if not _is_local_endpoint_alive(DECISION_API_URL):
        return handwired_system_one(state_text), "Handwired ReLU (0-Token)"

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
        t_req = time.perf_counter()
        with urllib.request.urlopen(req, timeout=_RUNTIME_TRACKER.adaptive_timeout_sec(TIMEOUT_SEC)) as resp:
            if resp.status == 200:
                res_body = json.loads(resp.read().decode("utf-8"))
                provider_tag = "System 1"
                if "11435" in DECISION_API_URL or "ollaya" in DECISION_API_URL.lower():
                    provider_tag = "Ollaya"
                elif "jev" in DECISION_API_URL.lower() or api_key:
                    provider_tag = "Jev Cloud"
                _RUNTIME_TRACKER.update((time.perf_counter() - t_req) * 1000.0)
                return res_body.get("answers", {}), f"{provider_tag} ({DECISION_MODEL})"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"{YELLOW}⚠️  決策端點回傳 HTTP {e.code}: {err_body}{RESET}", file=sys.stderr)
    except urllib.error.URLError:
        pass  # 離線時靜默由 Handwired ReLU 接管
    except Exception as e:
        print(f"{YELLOW}⚠️  決策端點呼叫異常: {e}{RESET}", file=sys.stderr)

    return handwired_system_one(state_text), "Handwired ReLU (0-Token)"


def run_guard(code_content: str, label: str = "Diff/Snippet", changed_files: Optional[List[str]] = None) -> int:
    """執行完整審查並以簡潔表格輸出結果，回傳退出碼 (0: 通過, 1: 攔截)"""
    if not code_content.strip() and not changed_files:
        print(f"{CYAN}ℹ️  [System 1 Guard] 內容為空，無變更需審查。{RESET}")
        return 0

    print(f"\n{BOLD}🛡️  [System 1 Guard] 啟動高速決策門禁審查 ({label})...{RESET}")
    
    is_blocked = False
    block_reasons = []

    # 0. 物理阻斷：Git 安全地基檢查 (INV_SAFE_04)
    if "Git" in label and not is_git_repo():
        is_blocked = True
        block_reasons.append("INV_SAFE_04 違規：未檢測到 Git 存檔點，嚴禁在無時光機保護下修改代碼！請先執行 git init。")

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

    # 2.5 物理阻斷 (Level 0.5)：SWC 確定性 AST 門禁審查
    ast_blocked, ast_violations = check_ast_guard(code_content, changed_files)
    if ast_blocked:
        is_blocked = True
        block_reasons.extend(ast_violations)

    # 2.6 物理阻斷 (Level 0.5)：PHP 8.4 / Laravel 13 確定性門禁審查
    php_blocked, php_violations = check_laravel_php_guard(code_content, changed_files)
    if php_blocked:
        is_blocked = True
        block_reasons.extend(php_violations)

    # 2.7 物理阻斷 (Level 0.5)：歷史決策防翻案門禁 (Trail-Code Decision Regression Check)
    decision_blocked, decision_violations = check_decision_regression(code_content, changed_files)
    if decision_blocked:
        is_blocked = True
        block_reasons.extend(decision_violations)

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
        TEST_SEAM_KEYWORDS = ["mock", "stub", "fake", "spy", "fixture", "backdoor", "dummy", "test_", "__test"]
        has_seam_hint = any(kw in code_content.lower() for kw in TEST_SEAM_KEYWORDS)

        if seam_prob > 0.65:
            if len(code_content.strip()) < 80 and not has_seam_hint:
                pass
            else:
                is_blocked = True
                block_reasons.append(f"違反零生產接縫原則：偵測到測試專用 Mock/後門 (信心 {seam_prob*100:.1f}%)")

        # 判定嚴重肥大/過度工程 (修復: 設定 is_blocked = True)
        if bloat_score >= 4.0:
            is_blocked = True
            block_reasons.append(f"過度工程指數過高 ({bloat_score:.1f}/5)，違反 Ponytail 精簡原則")
    else:
        ladder_choice = "Static-Rules"

    status_header = f"{RED}🛑 BLOCK - 變更遭駁回{RESET}" if is_blocked else f"{GREEN}✅ PASS - 審查通過{RESET}"
    
    print("┌─────────────────────────────────────────────────────────────┐")
    print(f"│ 審查狀態: {status_header:<49} │")
    print(f"│ 決策引擎: {CYAN}{engine_name:<25}{RESET} 耗時: {elapsed_ms:6.1f} ms    │")
    print("├─────────────────────────────────────────────────────────────┤")
    print(f"│  • Git 安全地基 (INV_SAFE_04)  : {format_gate_status(is_git_repo())}                       │")
    print(f"│  • AST 語意門禁 (Level 0.5)      : {format_gate_status(not ast_blocked)}                       │")
    print(f"│  • 歷史決策防翻案 (Trail Check): {format_gate_status(not decision_blocked)}                       │")
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


def is_git_repo() -> bool:
    """檢查當前工作區是否受 Git 時光機保護 (INV_SAFE_04)"""
    try:
        res = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False


def _capture_rollback_incident(diff: str, changed_files: List[str]) -> Optional[Path]:
    """將觸發兩振回滾之失敗 Diff 沉澱至 .agent/eval_incidents.jsonl 並微調 ReLU 權重 (Anthropic Incident-to-Eval)"""
    if not diff.strip():
        return None
    x = _extract_handwired_features(diff)
    if sum(x[:4]) > 0:
        tune_handwired_weights(diff, 0.9 if x[0] > 0 else 0.0, 4.5 if sum(x[1:4]) > 0 else 2.0, lr=0.05)
    target_dir = Path.cwd() / ".agent"
    target_dir.mkdir(parents=True, exist_ok=True)
    inc_file = target_dir / "eval_incidents.jsonl"
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files": changed_files,
        "features": x,
        "diff_snippet": diff[:1000],
    }
    with inc_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return inc_file


def evaluate_incidents() -> int:
    """回放 .agent/eval_incidents.jsonl 驗證當前門禁對歷史事故/Revert 樣本之攔截率"""
    inc_file = Path.cwd() / ".agent" / "eval_incidents.jsonl"
    if not inc_file.is_file():
        print(f"{CYAN}ℹ️  [Incident Eval] 尚無歷史回滾樣本 (.agent/eval_incidents.jsonl)。{RESET}")
        return 0
    records = []
    for ln in inc_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.strip():
            try:
                records.append(json.loads(ln))
            except Exception:
                continue
    caught = sum(1 for r in records if run_guard(r.get("diff_snippet", ""), "Incident Replay", r.get("files")) == 1)
    print(f"{GREEN}📊 [Incident Eval] 歷史事故攔截率: {caught}/{len(records)} ({(caught/len(records)*100 if records else 100):.1f}%){RESET}")
    return 0 if caught == len(records) else 1


def execute_rollback() -> int:
    """執行 0.05 秒物理回滾 (Two-Strike Circuit Breaker, INV_VERIFY_05)"""
    if not is_git_repo():
        print(f"{RED}❌ [INV_SAFE_04 違規] 未檢測到 Git 倉庫，無法執行物理回滾。{RESET}")
        return 1

    print(f"\n{YELLOW}{BOLD}⚡ 正在觸發兩振硬熔斷物理回滾 (INV_VERIFY_05)...{RESET}")
    start = time.perf_counter()
    try:
        diff, changed = get_git_info()
        subprocess.run(["git", "restore", "."], check=True, capture_output=True)
        subprocess.run(["git", "clean", "-fd", "-e", ".agent", "-e", ".agents"], check=True, capture_output=True)
        _capture_rollback_incident(diff, changed)
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"{GREEN}✅ [秒級硬熔斷成功] 工作區已乾淨復原至安全 Commit 基準點！耗時: {elapsed_ms:.1f} ms{RESET}")
        print(f"{CYAN}💡 上下文毒化已阻斷，失敗特徵已沉澱至 .agent/eval_incidents.jsonl。{RESET}\n")
        return 0
    except Exception as e:
        print(f"{RED}❌ 回滾失敗: {e}{RESET}")
        return 1


def check_git_status() -> int:
    """檢驗 Git 安全地基狀態 (INV_SAFE_04)"""
    if not is_git_repo():
        print(f"\n{RED}{BOLD}🛑 [INV_SAFE_04 違規] 當前目錄不是 Git 倉庫！{RESET}")
        print(f"{YELLOW}💡 任何代碼生成或修改前，工作區必須受 Git 時光機保護。")
        print(f"👉 請立即執行：git init && git add -A && git commit -m 'feat: baseline'{RESET}\n")
        return 1

    diff, changed = get_git_info()
    print(f"\n{GREEN}✅ [INV_SAFE_04 合規] Git 時光機正常運作。{RESET}")
    if changed:
        print(f"{YELLOW}ℹ️  當前工作區有 {len(changed)} 個未提交變更檔案。{RESET}")
    else:
        print(f"{GREEN}ℹ️  工作區完全乾淨，隨時可安全動手。{RESET}\n")
    return 0


def get_git_info() -> Tuple[str, List[str]]:
    """獲取當前工作區未提交的 git diff 與變更檔案清單 (包含已暫存、未暫存與未追蹤檔案)"""
    if not is_git_repo():
        return "", []
    try:
        # 1. 抓取已追蹤變更檔案名稱 (diff against HEAD, 排除子模組/目錄)
        name_bytes = subprocess.check_output(["git", "diff", "--name-only", "--ignore-submodules", "HEAD"], stderr=subprocess.DEVNULL)
        changed_files = [
            f.strip() for f in name_bytes.decode("utf-8", errors="replace").splitlines()
            if f.strip() and not Path(f.strip()).is_dir()
        ]

        # 2. 抓取未追蹤檔案清單 (Untracked files, 排除目錄)
        untracked_bytes = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            stderr=subprocess.DEVNULL
        )
        untracked_files = [
            f.strip() for f in untracked_bytes.decode("utf-8", errors="replace").splitlines()
            if f.strip() and not Path(f.strip()).is_dir()
        ]
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
    parser.add_argument("--check-git", action="store_true", help="檢驗 Git 時光機地基狀態 (INV_SAFE_04)")
    parser.add_argument("--rollback", action="store_true", help="觸發兩振硬熔斷 0.05 秒物理回滾 (INV_VERIFY_05)")
    parser.add_argument("--eval-incidents", action="store_true", help="回放 .agent/eval_incidents.jsonl 驗證歷史事故攔截率")
    parser.add_argument("--code", type=str, help="直接傳入要審查的代碼字串")
    parser.add_argument("--file", type=str, help="指定要審查的檔案路徑")
    parser.add_argument("--stdin", action="store_true", help="從標準輸入 (stdin) 讀取內容")
    parser.add_argument("--tune", type=str, help="解凍微調 Handwired ReLU 權重 (格式: target_seam,target_bloat 如 0.0,2.0)")

    args = parser.parse_args()

    if args.check_git:
        sys.exit(check_git_status())
    elif args.rollback:
        sys.exit(execute_rollback())
    elif args.eval_incidents:
        sys.exit(evaluate_incidents())

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

    if args.tune:
        parts = [float(x.strip()) for x in args.tune.split(",")]
        updated = tune_handwired_weights(content, parts[0], parts[1])
        print(f"{GREEN}✅ [Handwired ReLU] 已解凍並更新權重: {json.dumps(updated)}{RESET}")
        sys.exit(0)

    sys.exit(run_guard(content, label, changed_files))

