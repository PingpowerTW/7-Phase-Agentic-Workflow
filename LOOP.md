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

## Stall Detection & Circuit Breaker (防卡死斷路器)
- **Stall Condition**: 若同一任務或子步驟連續報錯/失敗達 3 次（`max_attempts: 3`），判定為陷入思維死循環。
- **Circuit Breaker Action**:
  1. 立即中斷（Halt）自治迴圈，禁止反覆重試。
  2. 激活 `loop-budget.md` 之緊急停止標記 (`loop-pause-all: true`)。
  3. 強制落實 N1 阻斷：禁止封裝快照或執行記憶蒸餾，防止錯誤經驗污染長期知識庫。
  4. 產出失敗根因報告並向人類操作員請求協助（Escalate to Human）。

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
