# Loop State — AI 優化 Workspace

Last run: 2026-11-12T21:20:00+08:00 (完成 Karpathy Guidelines v3.3.6 社群實戰精華吸收、DAG Runner Windows 子程序非阻塞回收修復、以及本機 Token 經濟與驗證矩陣加速手術)

## Level 0: Macro Concept Anchor (Current Active Goal)

- **Active Goal**: 維持本機 Token 經濟與 7-Phase 工作流 v3.3.6+ 零漂移高效運行，並透過 Phase 0 前置殘酷審查以「純吸收優化」方式提煉業界頂尖 AI 工程護欄（最新吸收：`multica-ai/andrej-karpathy-skills` 風險分級追問與目標驅動公式、`Prefrontal-AI/latent-sparse-attention` LSA 語義分桶、`tt-a1i/archify` v3.2、`KKKKhazix/agent-autoloop` v1.1.0、`Graphify-Labs/graphify` v0.9.x、`rtk-oss` v1.1.0、`DietrichGebert/ponytail` v5）。
- **Invariants Guard**: 保持 Git 時光機保護 (`INV_SAFE_04`)、專案配置防投毒 (`INV_SAFE_05`)、兩振硬熔斷 (`INV_VERIFY_05`)、Reflexion 反思協議 (`INV_VERIFY_06`)、防偽執行收據 (`INV_VERIFY_07`)、分層宣告 (`INV_ARCH_01`, advisory)、零生產接縫 (`INV_VERIFY_03`) 與零漂移狀態。

---

## High Priority (In-Flight Tasks / Waiting on Human)

- [x] **Karpathy Guidelines v3.3.6 Absorption, CI Fix & Token Economy Surgery (`karpathy-guidelines/SKILL.md`, `dag_runner.py`, `local_guard.py`, `sync_promptscript.py`, `STATE.md`, 2026-11-12)**:
  1. **Karpathy Guidelines 實戰補強 (`1f327f4`)**：吸收上游與社群 PR (#186, #213, #215) 五大精髓：權衡宣告 (Tradeoff)、資深工程師自省鏡、孤兒清理与 Diff 溯源、禁盲改 (`Never-Edit-Blind`)、依風險分級反詰問（低風險沿用慣例推進 vs 高風險強制 `goto=END` 尾端短路追問）、`/spec` 收斂邊界 (What/Why/Non-Goals) 與三大模糊任務轉化公式（新增功能/修 Bug Fail-Before-Pass/重構）。
  2. **DAG Runner Windows CI 修復與非阻塞收斂 (`0c91d6a`, `f5ebda9`)**：修復 `_terminate_process_tree` 在 Windows 下未呼叫 `proc.kill()` 導致 `ProactorEventLoop` 等待 `proc.wait()` 3.0s 逾時之 Bug；改以 `asyncio.to_thread` 非阻塞執行 `taskkill`、於 `finally:` 保證回收子程序，並合併重複 `proc.kill()`（GitHub Actions 6/6 跨平台矩陣全綠）。
  3. **Token 經濟與驗證加速三手術（A+B+C）**：(A) 將 `STATE.md` 內 21 條歷史 `[x]` 長文歸檔至 [`docs/history/MILESTONES_ARCHIVE.md`](file:///d:/AI/優化/docs/history/MILESTONES_ARCHIVE.md#completed-milestones-v32--v336)，`STATE.md` 體積由 `35.7 KB` 降至 `< 5 KB`（單次讀取立省 ~87% / ~9,000 Tokens）；(B) 修復 `local_guard.py` 之 `check_ast_guard` 對非 JS/TS 變更誤啟動 `node ast_guard.js` 子程序風暴並加上 Git 狀態短效快取，`test_local_guard.py` 耗時由 `9.63s` 驟降至 `< 1.0s`；(C) 精簡 `agy-cli-statusline` 冗長 `description` 並於 `sync_promptscript.py` 實裝 `--sync` 一鍵鏡像同步。

---

## Level 1: Meso Milestone Index (Completed Milestones)

| Version / Tag | Core Intent & Scope | Key Invariants Preserved | Detail Pointer |
| :--- | :--- | :--- | :--- |
| **v3.3.6 Karpathy & Speed** | Karpathy Risk-Based Clarification, DAG Non-Blocking Cleanup, `local_guard` Fast-Cache & `STATE.md` Slimming | `INV_SAFE_04`, `INV_VERIFY_05~07`, `goto=END` | [High Priority #1](file:///d:/AI/優化/STATE.md#high-priority-in-flight-tasks--waiting-on-human) |
| **LSA + Archify + Autoloop** | Ward Semantic Bucket Recall (`arXiv:2610.42147v2`), Archify v3.2 ERD/Delta, Agent-Autoloop v1.1.0 Purity & Bare-Diff Review | `INV_SAFE_04~05`, `INV_VERIFY_02~07` | [Archive #41](docs/history/MILESTONES_ARCHIVE.md#41-rtk-oss-v110-graphify-v09x-agent-autoloop-v110-archify-v32--lsa-absorption-2026-10-3111-05) |
| **Graphify + RTK v1.1.0** | JSX/TSX Alias Graph, Shortest Path BFS (`--path`), `mtime_ns` Cache & `rtk-oss v1.1.0` | `INV_VERIFY_07`, `GRAPH_SCHEMA_2.0` | [Archive #41](docs/history/MILESTONES_ARCHIVE.md#41-rtk-oss-v110-graphify-v09x-agent-autoloop-v110-archify-v32--lsa-absorption-2026-10-3111-05) |
| **DeerFlow + Ponytail 5** | SubagentLimitGuard (≤3), Overlay Poison Guard (`INV_SAFE_05`), Ponytail 5 `shortcut:` & UI/UX Pro Max v2.15 | `INV_SAFE_05`, `WCAG 2.2 AA` | [Archive #40](docs/history/MILESTONES_ARCHIVE.md#40-bytedance-deerflow-20-deepseek-tui-ponytail-5--uiux-pro-max-v215-absorption-2026-10-31) |
| **Editorial + Agensh Notes** | Diagram Complexity Budget (≤9 nodes) & DeLM `[CLAIM]/[DEAD_END]/[VERIFIED_FACT]` Typed Notes | `CTAP`, `VALID_NOTE_TYPES` | [Archive #39](docs/history/MILESTONES_ARCHIVE.md#39-editorial-diagram-budget--microsoft-agensh-typed-notes-absorption-2026-10-2527) |
| **Hermes + Receipt Guard** | Reflexion Rollback, CRAG Recall, Fail-Closed JSON & `[GUARD-RECEIPT]` Anti-Hallucination (`INV_VERIFY_07`) | `INV_SAFE_04`, `INV_VERIFY_05~07`, `INV_ARCH_01` | [Archive #38](docs/history/MILESTONES_ARCHIVE.md#38-alice-hermes-5-pillar-absorption--full-workspace-convergence-2026-10-23) |
| **DeepInfer + Astute + Harness²**| YOCO+SWA Replay (`W=5,K=2`), DSpark Schedule, Astute RAG Reconciliation & Experience Library | `SWA_BOUNDED_REPLAY`, `SHARS` | [Archive #35~37](docs/history/MILESTONES_ARCHIVE.md#35-harness-self-evolving-experience-library--dynamic-composer-reflexionpy) |
| **v3.3 Token Overhaul** | Direct Surgical Write, 3-in-1 Adversarial Audit, Skill Consolidation (216→47) & Handwired ReLU | `INV_SAFE_04`, `INV_VERIFY_03`, `INV_DECISION_01` | [Archive #27~34](docs/history/MILESTONES_ARCHIVE.md#32-v33-token-economy-overhaul--7-phase-skill-consolidation) |
| **v3.2 NCM & DRY** | NCM Concept Tree Alignment (CTAP), DRY Gate & 50ms Fast-Probe | `CTAP`, `INV_SAFE_04`, `INV_VERIFY_05`, NCM L0-L2 | [Archive #24~25](docs/history/MILESTONES_ARCHIVE.md#24-ncm-concept-tree-alignment-ctap--multi-scale-memory-architecture) |
| **v3.0 ~ v3.1** | Contract-First DAG, Surgical Patch Stager (`### PATCH:`), Step 2.5 0-Token Sieve & Suite 14 | `INV_PHP_01`, `INV_LARAVEL_01~04`, `INV_TS_01` | [Archive #1~2](docs/history/MILESTONES_ARCHIVE.md#1-v31-surgical-patch-stager--14-suite-verification-matrix) |
| **v1.0 ~ v2.x Foundation** | Git Safety Net, Pre-Flight Gate, SWC+LLMCompiler, Ponytail 7-Ladder, Test-Audit & Loop L3 (100/100) | `INV_SAFE_04`, `INV_SCOPE_02~03`, `INV_VERIFY_02~05` | [Archive #3~23](docs/history/MILESTONES_ARCHIVE.md#3-phase-3-token-economy-skill-hydration--parallel-gate-optimization) |

---

## Watch List

- [ ] **God Nodes Hub Monitoring**: 監控 God Nodes 關鍵中樞（如 gateguard, dashboard, instinct-cli），避免高耦合單點崩潰。
- [ ] **Invariants Drift Monitor**: 定期透過 `scripts/loop_drift.py` 確保程式碼、測試與系統不變量無脫節。
- [ ] **Loop Readiness Score**: 保持 100/100 (L3) 狀態，定期透過 loop-audit 巡檢。
- [ ] **auto-snapshot vs STATE.md 同步**: 確保本地快照與專案狀態脊椎保持一致（單檔嚴控 < 6 KB）。
- [ ] **SelfCompact 記憶熱蒸餾門檻**: 監控快照數量，累積接近 200 條時觸發情節壓縮。
- [ ] **Ponytail Debt Ledger 監控**: 定期透過 `/ponytail-debt` 檢視代碼中的刻意捷徑與升級路徑，防止技術債默默腐爛。
- [ ] **Open-Source Pre-Flight Gate 執行監控**: 嚴格把關後續所有外部開源 Repo 與工具引入，禁止跳過 Phase 0 四維度殘酷審查直接動手實作。

---

## Recent Noise (ignored this run)

- 忽略 `.venv` 及暫存檔案的變動。

---
Run log: Maintained as the durable memory spine of the workspace. Level 2 details archived in `docs/history/MILESTONES_ARCHIVE.md`.
