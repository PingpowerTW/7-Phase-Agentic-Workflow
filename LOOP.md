# LOOP.md — AI 優化 Workspace Loop Specification

This file documents the autonomous and assisted loop operations for the AI optimization workspace.

## Active Loops

### Daily Triage (L1 — Report Only)
- Cadence: 1d
- Tool: `python scripts/loop_drift.py`
- State: `STATE.md`
- Mode: Report-only. Audits architecture drift, code-test co-evolution, gate.yaml compliance, and secret leaks.

### Feature / Refactor Babysitter (L2 — Assisted)
- Cadence: On-demand (e.g. `/agy-studio` or task trigger)
- Strategy: Isolated Git Worktree per task
- Maker/Checker: Implementer creates diff; Verifier enforces Falsification Discipline.
- Hard Gates: `gate.yaml` (physical denylist) & `invariants.yaml` (system invariant matrix).

## Safety & Invariants Gates
- Mechanical enforcement via `gate.yaml` & `invariants.yaml`
- Path denylist: `.env*`, `credentials/**`, `secrets/**`, `auth/**`, `billing/**`, `migrations/**`
- Invariants protocol: Safety (no secrets, path sanitization), State (monotonic timestamp, C1/N1 closed-loop), Scope (max 8 files, code-test parity)
- Checker Falsification Discipline: Verifier must probe at least 1 adversarial boundary counter-example; reject on any invariant breach.
- Default auto-merge: Disabled (requires human review)

## Stall Detection & Circuit Breaker (兩振硬熔斷與口語反思閉環)
- **Two-Strike Condition (`INV_VERIFY_05` & `INV_VERIFY_06`)**:
  - **Strike 1 (初次未收斂)**：禁止盲目重試，必須先產出三段式口語反思 (`[Reflexion] 錯誤假設 | 根因定位 | 修正策略`) 始可進入第 2 次嘗試。
  - **Strike 2 (兩振出局，`max_attempts: 2`)**：若連續 2 次修復未收斂，嚴禁第 3 次向前修補。
- **Circuit Breaker Action**:
  1. 立即於 0.05 秒內執行物理回滾 (`python scripts/local_guard.py --rollback --reflexion "<反思>"`)，抹除失敗代碼與毒化上下文，並沉澱至 `.agent/eval_incidents.jsonl` 與 `.agent/SNAPSHOT.jsonl`。
  2. 激活 `loop-budget.md` 之緊急停止標記 (`loop-pause-all: true`)。
  3. 強制落實 N1 阻斷：禁止封裝長期里程碑快照或執行記憶蒸餾，防止錯誤經驗污染長期知識庫。
  4. 手動更新 `STATE.md` Watch List 並向人類操作員請求協助（Escalate to Human）。

## Governance & Architecture
- **Architecture Knowledge Graph (`scripts/loop_graph.py`)**:
  - 全庫確定性 AST 與政策拓撲掃描：`python scripts/loop_graph.py --scan` (產出 `graph.json`, `graph.html`, `GRAPH_REPORT.md`)
  - 改動衝擊半徑分析：`python scripts/loop_graph.py --impact <file_path>` (計算下游被波及的模組與測試)
  - 核心神節點監控：`python scripts/loop_graph.py --god-nodes`
- **Fleet Registry & Tool Scoping**: 依據 `fleet-registry.md` 實施最小權限代理人分工。
- **Memory Tiers**: 依據 `memory-tiers.md` 維護 L1 (Working), L2 (Episodic), L3 (Semantic) 記憶架構。
- **Budget policy**: `loop-budget.md`
- **Run history log**: `loop-run-log.md`
- **Kill switch**: `loop-pause-all` flag in `loop-budget.md`
