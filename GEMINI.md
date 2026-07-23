# Programmer's Studio — 專案規則

> 本文件定義 Programmer's Studio 的專案級規則與工作流程。
> 全域 skills 安裝在 `~/.gemini/config/plugins/programmers-studio/`。
> 整合 **Spec-Driven Development (SDD)** 與 **Karpathy 行為護欄**，導入 **Token 經濟學**與**多代理人調度機制**。

---

## 1. Context-Mode Sandbox (Think in Code) — MANDATORY

> **[MANDATORY] context-mode Routing Rules**
> context-mode MCP tools are available. Rules protect the context window from flooding. Follow strictly.

Analyze/count/filter/compare/search/parse/transform data: **write code** via `mcp__context-mode__ctx_execute(language, code)`, `console.log()` only the answer. Do NOT read raw data into context. PROGRAM the analysis, not COMPUTE it. Pure JavaScript — Node.js built-ins only (`fs`, `path`, `child_process`). `try/catch`, handle `null`/`undefined`. One script replaces ten tool calls.

### BLOCKED — do NOT use:
- **curl / wget**: FORBIDDEN via `run_command`. Dumps raw HTTP into context. Use `mcp__context-mode__ctx_fetch_and_index(url, source)` or `ctx_execute`.
- **Inline HTTP**: FORBIDDEN via `run_command`. Use `ctx_execute`.
- **Direct web fetching**: FORBIDDEN for large pages via `read_url_content`. Use `ctx_fetch_and_index`.

### REDIRECTED — use sandbox:
- **Shell (>20 lines output)**: `run_command` ONLY for `git`, `mkdir`, `rm`, `mv`, `cd`, `ls`, `npm install`, `pip install`. Otherwise use `ctx_batch_execute` or `ctx_execute(language: "shell")`.
- **File reading (for analysis)**: Reading to **edit** → `view_file`/`replace_file_content` correct. Reading to **analyze/explore/summarize** → `ctx_execute_file`.
- **Search (large results)**: Use `ctx_execute(language: "shell", code: "grep ...")` in sandbox.

### Tool Selection & Parallel I/O:
1. **GATHER**: `ctx_batch_execute(commands, queries)` — runs commands, auto-indexes, returns search.
2. **FOLLOW-UP**: `ctx_search(queries)` — all questions as array, ONE call.
3. **WEB**: `ctx_fetch_and_index` then `ctx_search`.
4. **Concurrency**: Use `concurrency: 4-8` for I/O-bound (network, API). Keep `concurrency: 1` for CPU-bound or shared state.

---

## 2. 🏗️ Production Pipeline (7-Phase Collaboration)

專案開發遵循 7 個階段，狀態追蹤在 `.studio/stage.txt`：

| Phase | 階段名稱 | 動作與產出 | Gate |
|-------|----------|-----------|------|
| **Phase 0** | **Spec (規格定義)** | 定義 what & why（不管 how），大型任務或 `/spec` 時觸發。產出 `spec.md` | → User 確認 Spec |
| **Phase 1** | **Context & Validation** | 透過 `ctx_execute` / `ctx_batch_execute` 掃描專案、確認規格可行性 | → Requirement checklist |
| **Phase 2** | **Debt Audit** | 靜態掃描 Code Smells (🔴🟡🟢)，評估潛在技術債 | → Debt summary |
| **Phase 3** | **Design Proposal** | 提出架構與設計解法，產出 `implementation_plan.md`。結束後執行**上下文壓縮** | → Architect 審查 |
| **Phase 4** | **Implementation** | 進行代碼實作，遵守 Karpathy 護欄與精準開刀原則 | → Tech Lead code review |
| **Phase 5** | **Test & Review** | 自動化測試 + 對抗性審查 (Adversarial Review) + Code Walkthrough | → QA Lead sign-off |
| **Phase 6** | **Evolve (回顧演進)** | 對照 `spec.md` 驗證成果、記錄 Lessons Learned、更新決策日誌 | → Release checklist 完成 |

切換 stage：
```bash
echo "build" > .studio/stage.txt
```

> **IMPORTANT**: Always update `Implementation Plan` & `Task` artifacts after executing a task.

---

## 3. 📋 Review Intensity Modes

控制審查嚴格度，設定在 `.studio/review-mode.txt`：

| Mode | 行為 | 適用情境 |
|------|------|---------|
| `full` | 每個 checkpoint 都執行完整審查 | 正式開發、多人協作 |
| `lean` | 跳過 per-task review，只在 milestone 審查 | 快速迭代、原型期 |
| `solo` | 最低限度審查，只驗證 artifacts 存在 | 個人 side project、hackathon |

---

## 4. 🔧 Engineering Rules

### Rule #1: Context First (先理解，再動手)
Never write code until you understand tech stack, requirements, and testing state.
*Optimization:* Use `ctx_batch_execute` or `ctx_execute` to gather project context without flooding tokens.

### Rule #2: Spot the Debt (識別技術債)
Before adding features, scan for code smells (🔴 Critical, 🟡 Medium, 🟢 Low).
*Optimization:* Perform debt scans strictly inside the sandbox via `ctx_execute(language: "shell", code: "grep ...")`.

### Rule #3: Boy Scout Rule (童子軍法則 — 精準開刀雙模式)
**預設（精準開刀）**：只改被要求的部分。發現 code smell 或 dead code 時，**報告但不修改**，除非：
- 用戶明確要求 refactor
- 修改範圍 < 3 行且不影響邏輯
- 正在執行 `/refactor` 或 Phase 5 Review

**重構模式**（觸發 `/refactor` 時）：Always leave code cleaner than you found it.

### Rule #4: Verify with Tests (測試驅動交付)
No tests = no shipping. A feature isn't done until automated tests pass.

### Rule #5: Explain the Why (解釋設計決策)
Code includes inline comments explaining *why*, not just *what*.

### Rule #6: Readability > Cleverness (可讀性優先)
"Readability and Order > Speed and Complex Interconnections". Reject implicit or "magic" one-liners. Use explicit, clear code even if slightly longer.

### Rule #7: Structured Logging (結構化日誌)
Use low-cardinality structured logging. Do NOT use string interpolation for variables in log messages (e.g., `logger.info({ userId: id }, "User fetched")`, not `logger.info("User ${id} fetched")`).

### Rule #8: Token Economy (Token 節能原則)
- **精益執行 (Lean Execution)**：對於修改範圍 < 3 個檔案，且不涉及架構變更的中小型任務，**禁止**啟動 `/teamwork` 或 `/agy-studio` 多代理人模式，以避免 5-7 倍的 Token 消耗。使用單兵作業即可。
- **省話模式 (Caveman Mode)**：在 Phase 4 (實作) 階段或處理常規任務時，建議觸發 `caveman` skill 減少 Output Tokens。
- **上下文壓縮 (Context Pruning)**：跨階段時（特別是進入 Phase 4 之前），應使用 `context-compressor` 產出濃縮摘要 (Mini-brief)，不再來回傳遞早期的討論細節。

---

## 5. 🔧 Coding Standards

### 通用規則
- **No magic numbers** — 所有常數必須有命名
- **Comments explain WHY, not WHAT** — 程式碼本身應自解釋
- **Single Responsibility** — 一個函數做一件事
- **Error handling is not optional** — 每個可能失敗的操作都要處理

### TypeScript / JavaScript
- Strict mode enabled (`strict: true` in tsconfig)
- No `any` — use `unknown` + type guards
- Prefer `const` over `let`, never `var`
- Use named exports over default exports
- Async/await over raw promises

### Python
- Type hints on all public functions
- Use `pathlib` over `os.path`
- Prefer `dataclass` or `pydantic` over raw dicts
- Use `logging` module, not `print()`
- Handle exceptions with specific types, never bare `except:`

### Go
- Always wrap errors with `fmt.Errorf("context: %w", err)`
- Use `context.Context` as first parameter
- Check goroutine leaks — use `errgroup` or `sync.WaitGroup`
- Prefer interfaces for dependencies (dependency injection)

### Rust
- Minimize `unsafe` blocks — document WHY when needed
- Use `thiserror` for library errors, `anyhow` for applications
- Prefer `&str` over `String` in function parameters
- Use `clippy` lints as CI gate

### React / Vue
- Components < 200 lines — split if larger
- No business logic in components — extract to hooks/composables
- Proper key props on lists (no index-as-key unless static)
- Use React.memo / computed wisely — profile before optimizing

### Firebase
- Security rules MUST be tested before deploy
- Never trust client-side data — validate in rules AND functions
- Use batched writes for multi-document operations
- Index composite queries

---

## 6. 📝 Git Conventions

### Branch Naming
```
feature/PS-{id}-{short-description}
bugfix/PS-{id}-{short-description}
hotfix/PS-{id}-{short-description}
chore/{description}
```

### Commit Messages (Conventional Commits)
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`

### PR Checklist
- [ ] Tests added/updated
- [ ] No console.log / print() left
- [ ] Error handling in place
- [ ] Types are correct (no `any`)
- [ ] Breaking changes documented
- [ ] Self-reviewed diff

---

## 7. 📊 Decision Framework (ADL Priority)

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

## 8. 🎯 巨集指令與高階工作流 (Macro Commands)

當使用者輸入以下 Slash Commands 時，請執行對應的複雜 Agentic 流程：

- `/spec`: 進入 Phase 0 規格定義模式。引導用戶定義 what & why，產出 `spec.md`。適用於新功能開發、大型任務起始、用戶說「我想做 X」但尚未想清楚 how。`spec.md` 格式：What（做什麼）→ Why（為什麼）→ Success Criteria（可驗證條件）→ Out of Scope → Open Questions。
- `/onboard`: 掃描並理解專案結構與相依性，並與 GEMINI.md 對齊當前狀態。
- `/refactor`: 執行架構審查，尋找 SOLID/DRY 違反處，並產出模組化重構計畫。此模式下 Rule #3 切換為積極清理模式。
- `/review`: 觸發「對抗性審查 (Adversarial Review)」。先以「暴躁資深工程師」視角無情挑剔程式碼與計畫的漏洞與效率，再以「理性工程師」給出平衡建議。
- `/ui-check`: 強制呼叫 Browser Subagent 來進行畫面的視覺化驗證，並擷取截圖/錄影作為 Artifacts。
- `/fix`: 進入深度除錯模式：分析終端機/控制台日誌，系統性隔離根本原因。
- `/audit`: 針對技術債與擴展性瓶頸進行深度盤點，提出架構優化藍圖。

---

## 9. 💡 主動提醒義務 (Proactive Reminders Duty)

### 模式與指令切換提醒 (Command & Mode Switching)

- **任務起點 / 評估時**：
  - 發現需求模糊：在回覆尾部提示：「💡 *需求尚待釐清，建議可輸入 `/spec` 進入 Phase 0 規格定義模式。*」
  - 預估修改 ≥3 檔案 / 重構：在回覆尾部提示：「🤝 *當前任務規模較大(≥3檔案)，建議可輸入 `/teamwork` 啟動 5 人品質制衡軍團。*」
  - 全端需求 (DB+Backend+Frontend)：在回覆尾部提示：「🚀 *檢測到全端開發需求，建議可輸入 `/agy-studio` 啟動 7 人團隊。*」
- **實作完成時 (Phase 4 結束)**：
  - 在回覆尾部提示：「🔍 *實作與測試已完成，建議可輸入 `/review` 進行對抗審查，或輸入 `/ui-check` 進行畫面驗收。*」

### 模型切換提醒 (Model Switching)

- **規劃結束時 (Phase 3 結束)**：在回覆尾部提示：「*規劃已完成並生成交辦文件，建議切換至 Gemini 3.6 Flash (依任務難度選擇 High/Medium/Low) 執行實作，並可考慮啟動 /caveman 模式。*」
- **實作結束時 (Phase 4 結束)**：在回覆尾部提示：「*代碼實作已完成，建議切換至 Gemini 3.1 Pro / Claude (High) 進行 Review 審查。*」

---

## 10. 🗂️ File-backed State & Memory

```
.studio/
├── stage.txt           # Current pipeline stage (phase0~phase6 或 discovery|design|build|test|release)
├── review-mode.txt     # Review intensity (full|lean|solo)
├── memory/             # Teamwork execution memory
│   ├── BRIEFING.md     # Project requirements & AC (created by Sentinel)
│   ├── prompt_draft.md # Phase 1 requirements draft
│   ├── plan.md         # Milestones & Tasks status tracking (created by Orchestrator)
│   └── progress.log    # MessageBus time-series event log
├── backlog/            # Epic and story markdown files
│   ├── epics/
│   └── stories/
├── sprints/            # Sprint plan and retro documents
├── adrs/               # Architecture Decision Records (ADR)
└── reviews/            # Code review, audit, and quality reports
```

---

## 11. 🔗 SKILL 強制觸發規則

當處理以下類型任務時，**MUST** 先讀取對應的 SKILL.md：

| 任務類型 | Skill Path |
|----------|-----------|
| Coding/Refactoring/Review | `skills/karpathy-guidelines/SKILL.md` |
| Firebase Rules | `skills/development/firebase-rules/SKILL.md` |
| Bug 分析/盤點 | `skills/development/bug-tracker/SKILL.md` |
| UX 審查 | `skills/development/ux-audit/SKILL.md` |
| 專案規劃 | `skills/development/project-planner/SKILL.md` |
| 效能分析 | `skills/development/performance-profiling/SKILL.md` |
| 防禦性編程 | `skills/development/defensive-coding-checker/SKILL.md` |
| API 設計 | `skills/development/api-design/SKILL.md` |
| API 串接 | `skills/development/api-connector/SKILL.md` |
| 資料庫優化 | `skills/development/database-optimization/SKILL.md` |
| 安全性檢查 | `skills/development/security-best-practices/SKILL.md` |
| 錯誤處理 | `skills/development/error-handling/SKILL.md` |
| 資料驗證 | `skills/development/data-validator/SKILL.md` |
| React 效能 | `skills/development/react-performance-patterns/SKILL.md` |
| 發佈檢查 | `skills/development/release-checklist/SKILL.md` |
| 依賴審計 | `skills/development/dependency-auditor/SKILL.md` |
| 恢復工作 | `skills/development/work-resume-sop/SKILL.md` |
| 對話交接 | `skills/development/session-handoff/SKILL.md` |
| Async/Agent 長任務 | `skills/async-agent-patterns/SKILL.md` |

---

## 12. 👥 Available Subagents (自主子代理人)

當執行 `/teamwork` 或複雜任務時，系統會自動在背景啟動或調度以下代理人角色：

| Agent 名稱 | 角色職責 | 主要工具 / 運作 |
|------------|----------|-----------------|
| `sentinel` | 專案指揮官 (Command) | 釐清需求，產出 `.studio/memory/BRIEFING.md` 專案任務書 |
| `orchestrator` | 協調大腦 (Orchestration) | 拆解任務為 `plan.md`，平行調度子 Lead，監控狀態與重試 |
| `auditor` | 獨立驗收稽核 (Audit) | 核對 `BRIEFING.md` 驗收標準，執行測試門禁，發出 PASS/REJECT |

---

## 13. 🛡️ Guardrails (安全邊界)

- **Unclear requirements**: Ask first. Never assume.
- **Skip tests request**: Issue risk warning. Explain consequences.
- **Large scope creep**: Suggest splitting into smaller PRs / iterations.
- **Destructive operations**: Always confirm before deleting files, dropping tables, or overwriting data.
- **Firebase rules**: 注意 Firebase 規則的設定，不可造成功能異常。

---

## 14. 🛡️ 自動化驗收門禁 (Hooks)

本專案在 `hooks/` 目錄下實作了自動化門禁驗證。當執行特定操作時會觸發這些腳本：

1. **機密靜態掃描器 (`validate-secrets.js`)**：在寫入代碼或推送前掃描 API Key 與明文密碼，避免安全洩漏。
2. **資料庫遷移校驗 (`validate-db-migrations.js`)**：驗證 SQL Migration 檔案名稱格式，禁止 `DROP DATABASE/TABLE` 等破壞性 DDL。
3. **API 契約校驗 (`validate-api-schema.js`)**：檢查 API YAML Spec 結構與 TypeScript 型別介面的語法及括號完整性。

---

## 15. 📐 Rule Evolution (規則演化)

- 當同一個問題在 **3+ 次對話**中重複出現，**提議**加入新規則
- 新規則必須基於已驗證的經驗，不可基於推測
- 移除不再適用的規則（rules 只增不減 = token 成本膨脹）
- **流程**：Agent 提議 → User 批准 → 更新 GEMINI.md → User 同步 MEMORY
- 每季檢視：哪些規則從未被觸發？考慮移除

---

*Commands Reference:*
`ctx stats` (Usage stats), `ctx doctor` (Diagnostics), `ctx upgrade` (Update plugin), `ctx purge` (Clear DB)
