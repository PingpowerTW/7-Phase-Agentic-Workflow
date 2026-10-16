# 📐 Studio Rules — 專案級開發補充規範 (v3.0 精簡版)

> 本文件為 **專案級 (Project-Level)** 補充規則，僅在專案掛載時載入。
> 全域行為規範與巨集指令定義在 `GEMINI.md` 中。
> 
> 💡 **Token 經濟學提示 (Context Tiering)**：詳細的各語言規範（TypeScript、PHP 8.4/Laravel 13、Python 等）與宏觀架構白皮書已移至 `./rules/stacks/` 與 `./docs/architecture/`，支援按需動態載入，大幅降低常駐 Token 開銷。

---

## 1. 📋 Review Intensity Modes

控制審查嚴格度，可依專案階段動態切換：

| Mode | 行為 | 適用情境 |
|------|------|---------|
| `full` | 每個 checkpoint 都執行完整審查 | 正式開發、多人協作 |
| `lean` | 跳過 per-task review，只在 milestone 審查 | 快速迭代、原型期 |
| `solo` | 最低限度審查，只驗證 artifacts 存在 | 個人 side project、hackathon |

設定方式：在專案根目錄 `.studio/review-mode.txt` 中寫入 `full`、`lean` 或 `solo`。

---

## 2. 📊 Decision Framework (ADL Priority)

做技術決策時，優先順序：

> **Stability > Explainability > Reusability > Scalability > Novelty**

- ❌ 不要為了「看起來聰明」增加複雜度
- ❌ 不要做無法驗證的改動
- ❌ 不要犧牲穩定性追求新潮

### VFM Scoring (Value-First Modification)

非 trivial 改動前，評分：

| 維度 | 權重 | 問題 |
|------|------|------|
| High Frequency | 3x | 每天都會用到？ |
| Failure Reduction | 3x | 防止重複性故障？ |
| User Burden | 2x | 減少使用者負擔？ |
| Self Cost | 2x | 節省未來的 tokens/time？ |

**Score < 50 → 不要做。**

---

## 3. 📂 File-backed State & Memory

```text
.studio/
├── stage.txt           # Current pipeline stage (phase0~phase6)
├── review-mode.txt     # Review intensity (full|lean|solo)
├── memory/             # Teamwork execution memory
│   ├── BRIEFING.md     # Project requirements & AC (created by Sentinel)
│   ├── prompt_draft.md # Phase 1 requirements draft
│   ├── plan.md         # Milestones & Tasks status tracking
│   └── progress.log    # MessageBus time-series event log
├── staging/            # Zero-Token sandboxed output directory (Step 2.5 Sieve)
├── backlog/            # Epic and story markdown files
├── sprints/            # Sprint plan and retro documents
├── adrs/               # Architecture Decision Records (ADR)
└── reviews/            # Code review, audit, and quality reports
```

---

## 4. ⚡ 執行順序優先級 (Execution Precedence Hierarchy)

面對任何 Agent 動作，嚴格依循由硬至軟、由快至慢的四級執行時序：

- **Level 0 (Zero-Order Physical Gate — 最高物理優先級)**：`scripts/loop_gate.py` 與 `scripts/local_guard.py`。在任何實體變更寫入沙盒或合流前執行，強制檢驗 `gate.yaml` 之 Denylist、變更上限（`maxFiles: 8`）、硬編碼金鑰、以及 Level 0.5 確定性 AST/PHP 門禁。
- **Level 1 (System 1 Fast Classifier)**：`scripts/system_one.py`。非自回歸快初篩（Noul / Choice / Score），延遲 <5ms，Token 消耗 $0。
- **Level 2 (System 2 Deep Reasoning & Worker)**：交由 Frontier LLM 遵循 Phase 0-6 與 `/teamwork` / `/agy-studio` 規範產出實質代碼。
- **Level 3 (Loop Verifier & State Spine Sync)**：獨立 Checker 跑真實 test suite (`verify_all.py`)，驗證通過後原子合流至正式工作區並同步 `STATE.md`。

---

## 5. 🌲 NCM 概念樹對齊通訊協定 (Concept Tree Alignment Protocol, CTAP)

為根絕多代理人（Multi-Agent）協作中的廣播風暴與雙倍 Token 稅，全面落實 Next-Concept Modeling (NCM) 由粗到細與節點收斂原則：

1. **Step 1.5 概念樹錨定 (Level 0 Concept Tree Anchor, CTA)**：
   - 進入實作前，主代理人或 Explorer 必須產出標準 YAML 概念樹（預算 < 120 Tokens），包含：`domain`、`invariants`、`entities`、`contracts`。
   - 概念樹是全體 Agent 的「唯一真理骨架（Single Source of Truth）」，禁止在跨 Agent 通訊中塞入長篇對話散文。
2. **節點收斂視角 (Node-Scoped Context Injection)**：
   - **DB Architect**：僅訂閱 `entities` 與 `invariants` 分支，杜絕無關的前端樣式文字。
   - **Backend Lead**：僅訂閱 `contracts` 與 `invariants` 分支，專注於 API 路由與業務驗證。
   - **Frontend Master**：僅訂閱 `contracts.ui_types` 與介面契約，專注於組件與互動狀態。
   - **成效**：消除 70% 跨代理人無效 Context 廣播。
3. **雙模外科手術式交付 (Dual-Mode Surgical Patch)**：
   - Worker 交付一律採用 `### PATCH: <path>`（局部替換）或 `### FILE: <path>`（新建整檔），禁止整檔重抄。
4. **概念樹驗收對齊 (Concept-Tree Driven Verification)**：
   - Reviewer / Critic / Auditor 審查時，直接以 Level 0 概念樹作為不變量契約檢驗，未滿足 contracts 或違反 invariants 者直接一票否決。
