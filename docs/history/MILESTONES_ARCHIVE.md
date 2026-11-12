# Milestones Archive — AI 優化 Workspace

本檔案為專案微觀歷史歸檔庫（Level 2 Micro Detail Archive），完整保存已完成里程碑之詳細設計、修復內容與驗證紀錄。
正常開發會話中，LLM 僅需讀取 `STATE.md` 之 Level 1 索引指針；僅在特定回溯或深度審查時，隨選（On-Demand）查閱此檔案或呼叫 `git show`。

---

## Completed Milestones (v1.0 ~ v3.1)

### 1. v3.1 Surgical Patch Stager & 14-Suite Verification Matrix
- **Commit / Scope**: 推播至遠端 GitHub (`PingpowerTW/7-Phase-Agentic-Workflow`)
- **詳細內容**：
  1. **`stage_runner.py` v3.1 外科手術式補丁 (### PATCH:)**：支援 `### FILE:`（新建整檔）與 `### PATCH:`（局部修改）。透過 `<<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE` 語法進行局部替換，Worker 僅需輸出欲修改之行數，省下 85% Output Tokens；內建唯一性檢查與幻覺防禦（SEARCH 不匹配或多重匹配時 0.01 秒攔截拒絕覆寫，徹底杜絕代碼誤刪與功能退化）。
  2. **第 14 套自動化測試 `tests/test_v3_upgrades.py`**：新增 Suite 14 完整覆蓋：PHP 8.4 `INV_PHP_01`、Laravel 13 `INV_LARAVEL_01~04`、SWC AST Guard `INV_TS_01`、`INV_REACT_01~02`，以及 `stage_runner.py` 的 FILE 落地、PATCH 局部替換、PATCH 錯配阻斷與 `..` 路徑穿越防護。
  3. **14 大驗證矩陣 100% 綠燈**：升級 `scripts/verify_all.py` 納管 Suite 14，多執行緒平行驗證耗時僅 5.44s；全平臺技能同步 (`sync_promptscript.py --hydrate`) 已將 Worker 的 `### PATCH:` 雙模指引注入 `.agents/`, `.claude/`, `.factory/`, `.github/`。

### 2. v3.0 Multi-Agent & Studio Architecture Upgrade (Contract-First Parallel DAG, 0-Token Sieve & Context Tiering)
- **Commit / Scope**: 推播至遠端 GitHub (`PingpowerTW/7-Phase-Agentic-Workflow`)
- **詳細內容**：
  1. **契約並行 DAG & 消除雙倍 Token 稅**：全面重構 `skills/agy-studio/SKILL.md` (7人) 與 `skills/teamwork/SKILL.md` (5人) 為 v3.0；引入 Step 1.5 Shared Contract Lock，促成 DB/Backend/Frontend 100% 並行開發；實裝 `scripts/stage_runner.py`（Zero-Token Sandbox Stager 與原子提交器），徹底消除主代理人手抄代碼之雙倍 Output Token 稅。
  2. **Step 2.5 0-Token 物理快篩**：在 `scripts/local_guard.py` 植入 Level 0.5 PHP 8.4 / Laravel 13 確定性門禁 (`check_laravel_php_guard`，防 Eloquent 屬性遮蔽、舊版 $casts、未宣告 strict_types 與胖 Controller)；在 `scripts/ast_guard.js` 植入 React 19、TypeScript any 阻斷 (`INV_TS_01`)、200 行上限 (`INV_REACT_01`) 與 GSAP StrictMode 安全檢查 (`INV_REACT_02`)，於短路階段直接攔截不消耗 AI 審查 Token。
  3. **Context Tiering 規則瘦身**：將 `STUDIO_RULES.md` 從 42.2KB 縮減 94% 至 2.5KB；理論白皮書（第 12~22 節）移出至 `docs/architecture/ARCHITECTURE_WHITEPAPER.md`；語言特定規範抽離至 `rules/stacks/laravel-php84.md` 與 `rules/stacks/react-typescript.md` 支援按需動態掛載。
  4. **全平臺同步與驗證**：升級 `scripts/sync_promptscript.py --hydrate` 自動同步至 `.agents/`, `.claude/`, `.factory/`, `.github/` 目標；13 大測試矩陣全部通過 (`verify_all.py` 5.70s 100% 綠燈)；`local_guard.py --git` 驗證通過；已成功 Push 至遠端 main 分支。

### 3. Phase 3 Token Economy, Skill Hydration & Parallel Gate Optimization
- **Commit / Scope**: 雙 Commit (`5bab490`, `b9faa16`) 推播至遠端 main 分支
- **詳細內容**：依據 Gemini 4 優化規劃，完成 7-Phase 工作流之架構升級並推播遠端 GitHub (`PingpowerTW/7-Phase-Agentic-Workflow`)。更新 `.promptscript`（注入 PageRank 1000-token 地圖規則與 Tier 0 Fast-Track 豁免）、實裝 `scripts/sync_promptscript.py --hydrate` 補齊 92 個 Skill 實體說明、升級 `scripts/verify_all.py` 為 `ThreadPoolExecutor` 平行執行（13 Suites 耗時降至 7.62s）、回補 Globstar 邊界防禦與 `gate.yaml` 之 `autoMergeAllowlist` 支援。

### 4. Git Safety Net & Two-Strike Circuit Breaker Full-Stack Integration
- **詳細內容**：解決 2026 年 Loop Engineering 核心痛點（終結 AI 向前修補之無限補丁死循環與 Token 巨量浪費）。於本專案根目錄完成 `.gitignore` 設置與本地 Git 時光機初始化 (`git init` + 乾淨 baseline commit)；升級 `invariants.yaml` 引入三大硬不變量：`INV_SAFE_04`（Git 時光機地基保證）、`INV_VERIFY_05`（兩振出局與 0.05 秒物理回滾硬熔斷）、`INV_SCOPE_03`（複雜度單調性防線）；增強 `scripts/local_guard.py` 支援 `--check-git`、`--rollback` 與時光機狀態動態評分卡；將「無 Git 禁動手」與「兩振物理復原」規範正式寫入專案憲法 `AGENTS.md` 與 `.agents/AGENTS.md`，實現零摩擦自動化防護。

### 5. Open-Source Pre-Flight Gate & Desktop-Sense Post-Mortem Cleanup
- **詳細內容**：深度覆盤 `desktop-sense` 劣質開源專案引入事件（以過時之 Win32 低解析截圖+WinRT OCR 假冒多模態視覺，噪訊極高且浪費大量 Token/本機系統資源），完成全套反安裝與環境淨化（關閉 daemon、移除機碼開機項、清理 settings.json hooks、清除 /desk skill、完全刪除 `d:\AI\desktop-sense`）。以此為鑑，正式於 `AGENTS.md` 確立《開源專案與新工具引入殘酷審查門禁 (Open-Source Pre-Flight Gate)》，並於 `GEMINI.md` 配置主動提醒：凡遇外部開源庫引入分析，強制執行 Phase 0 四維度殘酷審查（底層本質、原生對比、三代價評估、明確結論），未經人類確認嚴禁自動進入實作與安裝。

### 6. SWC AST Engine & LLMCompiler Parallel DAG Task Scheduler Integration
- **詳細內容**：深度吸收 `swc-project/swc` 與 `SqueezeAILab/LLMCompiler` 之雙引擎架構。底層實裝 `scripts/swc_extractor.js`（Node.js + `@swc/core` AST 特徵抽取，支援批次串流與正則平滑降級）與 Level 0.5 確定性 AST 門禁 `scripts/ast_guard.js`（微秒級物理阻斷生產測試接縫 `INV_VERIFY_03`/`04` 與 15 種垃圾測試模式 `INV_VERIFY_02`，無縫整合至 `scripts/local_guard.py`）；頂層實裝 `scripts/dag_runner.py`（基於純 Python 3.11 標準庫 `graphlib.TopologicalSorter` + `asyncio` 並行排程器，零外部依賴，防 CWE-78 Shell 注入與 Windows 程序樹安全回收）；於 `7-Phase-Agentic-Workflow/STUDIO_RULES.md` 第 22 節建立《LLMCompiler 並行 DAG 工作流與拓撲排程規範》；全套 13 大單元測試 (`tests/test_swc_llmcompiler.py`) 100% 綠燈，`loop_graph.py` 全局呼叫圖譜成功升級生成。

### 7. Ponytail 7-Ladder & Pluggable System 1 Decision Gate Integration
- **詳細內容**：完整將 Ponytail 7 階梯哲學與 TypeSafe Jev / Ollaya 規格之 System 1 決策門禁深度封裝至 7-Phase 工作流。實現模型與引擎解耦（透過環境變數 `DECISION_MODEL` 與 `DECISION_API_URL` 插拔式替換），並內建純靜態正則/`gate.yaml` 離線自動降級 (Static Fallback)，提供 Windows (`guard.ps1`) 與 Linux/PiP06 (`guard.sh`) 雙端執行器。全套 11 大驗證矩陣 100% 綠燈，已成功 Commit 並 Push 推送至 `PingpowerTW/7-Phase-Agentic-Workflow` 遠端主分支。

### 8. Ponytail Lazy Senior Dev Mode & GitHub Repo Publication
- **詳細內容**：吸收 DietrichGebert/ponytail 核心哲學，建立代碼端 Token 抑制體系。落實七層階梯原則 (YAGNI → 現有重用 → 標準庫 → 原生特性 → 已裝套件 → 單行簡潔 → 最小可行) 與根本修復原則；將核心門禁直接寫入專案 `AGENTS.md` 與 `.agents/AGENTS.md` (Always-On)；全量移植五大 Antigravity 專屬 Skill (ponytail, ponytail-review, ponytail-audit, ponytail-debt, ponytail-gain) 至全域技能庫；與現有 RTK (CLI/輸入端) 及 Caveman (對話輸出端) 組成「Token 殺手三位一體」，代碼量降低 54%~94%。已成功於本地建立 `d:\AI\優化\ponytail` 並發布專屬版本至私人 GitHub 倉庫 `PingpowerTW/ponytail-agent`。

### 9. OpenClaw Test-Audit & Zero Production Seams Integration
- **詳細內容**：成功吸收 OpenClaw 刪除 40 萬行無效測試之工程體系，實裝 `test-audit` 技能（Authoring Gate 門禁四問、15 種垃圾模式掃描、8 步戰役級 Campaign Mode）、收緊 `gate.yaml` 測試合流、升級 `invariants.yaml`（INV_SCOPE_02 / INV_VERIFY_02~04）與 `loop-constraints.md`。全套 17 大單元測試 100% 綠燈，已全量同步實裝並推送至 7-Phase 遠端主分支。

### 10. Loop Architecture Initialization
- **詳細內容**：已建立 Loop Engineering 基礎架構（gate.yaml, STATE.md, loop-budget.md, loop-constraints.md）。

### 11. Maker / Checker Hard Split
- **詳細內容**：已引入 loop-verifier 與 gate.yaml 物理門禁。

### 12. TypeSafe AI Jev System 1 Absorption
- **詳細內容**：已吸收 System 1 決策原語 (Noul/Choice/Score) 與 `scripts/system_one.py` 決策閘門，沉澱至 `STUDIO_RULES.md` 第 18 節與 `README.md`。

### 13. Adversarial Review & Suite 9 Matrix
- **詳細內容**：完成對抗審查，修復 Windows 反斜線路徑穿透漏洞，建立 `scripts/loop_gate.py` 並升級為 9 大測試矩陣 100% 通過。

### 14. Loop Sentinel & Invariants Engine
- **詳細內容**：已實裝 `invariants.yaml` 形式化系統不變量與 `scripts/loop_drift.py` 漂移哨兵，10 大單元測試 100% 綠燈。

### 15. Daily Triage Routine
- **詳細內容**：已正式整合由 `scripts/loop_drift.py` 執行之日常架構漂移巡檢與證偽審查協議。

### 16. Loop Fleet & Memory Tiers Full Stack
- **詳細內容**：已建立 `memory-tiers.md` (L1-L3 記憶階層), `memory-budget.md` (Token 預算上限), `fleet-registry.md` (5大 Agent 最小權限授權), `fleet-inbox.md` (跨 Agent 通訊信箱), 與 `LOOP.md` 防卡死斷路器 (Stall Detection & Circuit Breaker)。

### 17. Loop Graph Knowledge & Blast Radius Engine
- **詳細內容**：成功自研純標準庫 AST 圖譜引擎 (`scripts/loop_graph.py`)，秒級萃取 4,484 節點與 9,974 條邊，支援 God Nodes 樞紐識別、衝擊半徑 (Blast Radius) 與離線 Canvas 視覺化。

### 18. json-render Pattern Absorption (Generative UI)
- **詳細內容**：方案 B 落地完成。吸收 Catalog-First SDD、System 1 動態目錄裁剪、SpecStream RFC 6902 容錯修剪與 Anti-Slop 審美門禁，沉澱至 `STUDIO_RULES.md` 第 20 節、`prompts/react-ts/create-generative-catalog.prompt.md` 與 `README.md` 案例 9，11 大驗證矩陣 100% 綠燈，已同步推送遠端。

### 19. shadcn/ui Canonical UI Standard Formalization
- **詳細內容**：方案 B 落地完成。正式確立 `shadcn/ui` 為 React 前端第一推薦組件庫，原始碼置於 `components/ui` 享 100% 控制權；更新 `STUDIO_RULES.md`、`create-component.prompt.md` 與 `README.md` 案例 10，11 大驗證矩陣 100% 綠燈，已同步推送遠端。

### 20. outlines FSM Constrained Decoding Absorption
- **詳細內容**：方案 B 落地完成。吸收 FSM 引導式生成與 Token 級 Logit 遮罩架構，升級 `STUDIO_RULES.md` 第 17 節為四級降級容錯矩陣 (Quad-Tier Hierarchy: Tier 0 Outlines -> Tier 1 Native -> Tier 2 Tool -> Tier 3 Coercion)；更新 `create-feature.prompt.md` 與 `README.md` 案例 11，11 大驗證矩陣 100% 綠燈，已同步推送遠端。

### 21. AGY Studio Tech Debt & Token Economy Optimization
- **詳細內容**：完成全庫 130+ 檔案審查。模組化 `skills/frontend-taste-v2/SKILL.md` (由 90KB/2.5萬 Token 驟降 72% 至 24KB，深度指引抽離至 `references/` 四大分冊)；增強 `scripts/loop_drift.py` 範本與跨層級路徑回退解析，消除 `INV_STATE_01` 誤報；於 `GEMINI.md` 規範 context-mode MCP 優雅降級條款；新增第 11 項單元測試，11 大驗證矩陣 100% 綠燈。

### 22. Agent Substrate On-Premise Deployment & Environment Audit (PiP06)
- **詳細內容**：成功於地端伺服器 PiP06 (100.78.243.14) 部署 Agent Substrate 叢集並完成與 CloudPanel 共存環境深度優化。包括：放行 UFW 5001/8000 通訊埠、建立 systemd 持久化轉發守護程序（`substrate-ingress.service` 綁定 `0.0.0.0:8000`）、配置 Docker Log Rotation 防止磁碟耗盡、設定 Kind 容器 `restart=always` 保障開機自啟、針對 2 核心 CPU 微調 WorkerPool 資源配額，並驗證通過 Tailscale 與 Localhost 雙向 Ingress 呼叫。

### 23. Loop Engineering L3 (100/100) Dogfooding Full Stack
- **詳細內容**：正式將 L3 自治循環體系（`gate.yaml` 物理安全門禁、`invariants.yaml` 形式化不變量、`LOOP.md` 防卡死斷路器、`docs/safety.md`、`loop-budget.md`、`memory-tiers.md`、`fleet-registry.md` 與 4 大治理技能）原生實裝於倉庫根目錄，開箱即用；經 `loop-audit` 官方稽核器驗證達成 **100/100 (Level 3)** 滿分認證；11 大驗證矩陣 100% 全綠燈。

### 24. NCM Concept Tree Alignment (CTAP) & Multi-Scale Memory Architecture
- **詳細內容**：深度吸收 Stanford/Together AI Next-Concept Modeling (NCM)「由粗到細 (Coarse-to-Fine)」與概念錨定思維，完成四大架構落地：
  1. **狀態脊椎極致瘦身 (`STATE.md`)**：重構為 Level 0 宏觀概念錨點與 Level 1 中觀指針索引表，體積由 13.5KB 驟降 81% 至 2.5KB，微觀歷史無損沉澱至 `MILESTONES_ARCHIVE.md`。
  2. **多尺度記憶分級 (`memory-tiers.md`)**：正式將 NCM 階層架構確立為專案規範，嚴格劃分 L0 (<100t)、L1 (<250t) 與 L2 (0t 常駐/隨選真理)。
  3. **多代理人概念樹對齊通訊協定 (`CTAP`)**：升級 `teamwork` (5人) 與 `agy-studio` (7人) 為 NCM 概念樹平行架構；Explorer 產出標準 YAML 概念樹，DB/Backend/Frontend 依節點收斂視角 100% 平行開發，消除 70% 跨進程通訊 Token 冗餘。
  4. **決策門禁強化與測試綠燈**：修復 `local_guard.py` 負向回溯正則防禦誤報，單元測試集擴充至 30 套 100% 綠燈，`loop-audit` 官方評分保持 100/100 L3 滿分認證。


---

## Completed Milestones (v3.2 ~ v3.3.6)

### 25. 7-Phase v3.2 Full-Stack Audit, DRY Consolidation & Speed Polishing
- **詳細內容**：整合 `normalize_path`、`match_glob` 與 `gate.yaml` 解析至 `loop_gate.py`（淨減 ~110 行重複代碼），修正 `check_paths` 排除 `autoMergeAllowlist` 計入 `maxFiles`；修復 `stage_runner.py` 支援無 code fence 之 `### PATCH:` 區塊與 `.php` 門禁掃描；實裝 `local_guard.py` 50ms 本機 TCP 快篩與 `loop_graph.py` `--batch` SWC 批次抽取（耗時由 >60s 降至 <1.2s）；統一 `teamwork` 與 `agy-studio` 為 v3.2，全套 14 Suites 100% 綠燈。

### 26. Trail-Code Core Pattern Absorption (Zero External Dependencies)
- **詳細內容**：拒絕安裝 `@trailhq/trail-code` 重型 npm 套件，以純 Python 標準庫於 `loop_graph.py` 實裝 `parse_diff_ranges()`、`seeds_for_file()` 最內層函數種子鎖定與 `compute_diff_blast_radius()` (`--diff-impact`) 輸出 `TestSignal`；於 `local_guard.py` 實裝 `check_decision_regression()` (`INV_DECISION_01`) 攔截歷史翻案 Diff。

### 27. Handwired Zero-Training ReLU Scorer & Weight Unfreezing (`local_guard.py`)
- **詳細內容**：借鑑 Cheng Lou `Handwired` 技術，將 Ponytail 7 階梯與零生產接縫規則編譯為 6 維特徵無分支 ReLU 線性網路，在 Ollaya 離線時以 `<0.1ms`、0 Token 即時產出 `has_test_seam` 機率、`overengineering_score (1~5)` 與 `ponytail_ladder` 信心度，並實裝 `tune_handwired_weights()` 閉式梯度微調。

### 28. OpenMontage Governance Pattern Absorption (`local_guard.py` & `STUDIO_RULES.md`)
- **詳細內容**：升級 `check_decision_regression()` 支援 Append-Only `(category, subject)` 與 `touches` 錨點之 Latest-Wins 決策修訂折疊；於 `STUDIO_RULES.md` 實裝 `No Unilateral Substitutions` 與 `Templated vs. Atelier` 雙軌創作紀律。

### 29. Agency-Agents Pattern Absorption (`ui_audit.py` & `reflexion.py`)
- **詳細內容**：於 `ui_audit.py` 實裝 `missing-ui-finish-states`（攔截缺漏 `loading/empty/error` 完稿狀態之視圖）；於 `reflexion.py` 實裝 `check_score_plateau()`（連續 2 輪分數高原即熔斷跳出）。

### 30. Codebase-Memory-MCP Graph Intelligence Absorption (`loop_graph.py`)
- **詳細內容**：於 `loop_graph.py` 實裝 `find_dead_code_candidates()` (`--dead-code`) 精準定位零入度孤立函數，並於 `CodeAstScanner` 實裝 `_extract_cross_layer_edges()` 支援跨前後端 `HTTP_CALLS` 與環境變數 `CONFIGURES` 追蹤。

### 31. Anti-Slop Deterministic Gate Absorption (`ui_audit.py`)
- **詳細內容**：於 `ui_audit.py` 實裝 `wcag_contrast_ratio()` (`low-contrast-hex` < 4.5:1)、`excessive-glass-blur` (>2 處 `backdrop-blur`) 與 `ai-copywriting-slop` 確定性門禁。

### 32. v3.3 Token Economy Overhaul & 7-Phase Skill Consolidation
- **詳細內容**：基於 486 份歷史 Transcript 實證分析，升級 `teamwork` 與 `agy-studio` 至 v3.3（取消 ≥3 檔案自動觸發、Direct Surgical Write、Reviewer+Critic+Auditor 三審合一省 67% Context）；停用 `science` 插件、封存 83 個 0 讀取技能、整併 26 個重疊技能為多合一版（全域技能由 216 個收斂至 47 個，減幅 78%）；確立單檔 ≤15 KB 上限與強制平行工具呼叫紀律。

### 33. v3.3 GitHub Publication & Full Documentation Overhaul
- **詳細內容**：建立遠端備份分支 `backup/v3.2-legacy` 與 `v3.2-archive` 標籤，重構 v3.3 `README.md`，14 大整合驗證套件 100% 綠燈並發佈 `v3.3.0` 標籤。

### 34. Anthropic Code Review Pattern Absorption (`local_guard.py` & `code-review/SKILL.md`)
- **詳細內容**：於 `local_guard.py` 實裝 `_capture_rollback_incident()` 與 `evaluate_incidents()` (`--eval-incidents`)；於 `code-review/SKILL.md` 實裝 Incremental & Anti-Loop Gate（最多 2 輪收斂、豁免已標註 `shortcut:`/`ponytail:` 項目）。

### 35. Harness² Self-Evolving Experience Library & Dynamic Composer (`reflexion.py`)
- **詳細內容**：實裝 `record_experience()`、`compose_domain_harness()` 與 `assert_no_grader_leakage()`，將 `<cue, lesson, evidence>` 結構化經驗寫入 `.agent/library/<domain>/EXPERIENCE.md`。

### 36. Astute RAG Dual-Source Reconciliation & Garbage Eviction (`memory-engine` & `trust-governor`)
- **詳細內容**：實裝 Astute RAG 雙源對帳協議與 SHARS 來源感知動態重寫（`[Internal]` vs `[External]` 標籤對齊，衝突時以 AST/單變數探針為物理裁判）。

### 37. DeepInfer 4-Pillar Algorithm Absorption (`auto-snapshot`, `trust-governor`, `local_guard.py`)
- **詳細內容**：吸收 YOCO + SWA Bounded Replay (`SWA_BOUNDED_REPLAY_LIMIT = 7`)、DSpark Confidence-Scheduled Verification (`schedule_dspark_verification()`)、Engram Normalized N-gram Fingerprinting (`normalizeEngramText()`) 與 `MedianRuntimeTracker`。

### 38. Alice Hermes 5-Pillar Absorption & Full Workspace Convergence (2026-10-23)
- **詳細內容**：實裝 `--rollback --reflexion` 雙軌寫入 `eval_incidents.jsonl` 與 `SNAPSHOT.jsonl`、`layers.json` 分層宣告、CRAG 校正補召回、`_extract_constrained_json` Fail-Closed 擷取，以及 `INV_VERIFY_07` 防偽執行收據 (`[GUARD-RECEIPT]`) 與 RTK `ok` 零腦補鐵律。

### 39. Editorial Diagram Budget & Microsoft Agensh Typed Notes Absorption (2026-10-25~27)
- **詳細內容**：於 `diagram-generator/SKILL.md` 實裝單圖 ≤9 節點/≤12 連線預算與 Editorial 降噪主題；於 `teamwork` / `agy-studio` / `reflexion.py` 實裝 `[CLAIM]`、`[DEAD_END]`、`[VERIFIED_FACT]` 三元筆記協議。

### 40. ByteDance DeerFlow 2.0, DeepSeek-TUI, Ponytail 5 & UI/UX Pro Max v2.15 Absorption (2026-10-31)
- **詳細內容**：實裝 `SubagentLimitGuard` (≤3)、`Filesystem Offloading`、`Clarification Short-Circuit` (`goto=END`)、`Tool-Call Loop Guard` (≤2)、`check_config_overlay_poisoning()` (`INV_SAFE_05`)、Ponytail 5 `shortcut:` 帳本與跨群組連續編號、以及 `ui-ux-pro-max` WCAG 2.2 AA 與 BM25 單次重試棄權。

### 41. RTK-OSS v1.1.0, Graphify v0.9.x, Agent-Autoloop v1.1.0, Archify v3.2 & LSA Absorption (2026-10-31~11-05)
- **詳細內容**：升級本機 `rtk` 至 `v1.1.0`；於 `loop_graph.py` 實裝 React JSX/TSX 掃描、`--path <A> <B>` 最短拓撲路徑与 `mtime_ns` O(1) 快取；吸收 Functional Core 純度守衛、裸 Git 審查盲審三問與資料/指令物理隔離；於 `sql_to_erd.py` 實裝複合鍵與領域分欄；於 `auto-snapshot` 實裝 LSA Ward 語義桶壓縮、`Sink` 加權與 `Top-p` 輪詢展開。
