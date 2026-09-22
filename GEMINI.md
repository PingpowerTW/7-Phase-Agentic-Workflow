# 🛠️ Global Rules — Features & Context Management (全局規則)

> **[MANDATORY] context-mode routing rules**
> Context-mode MCP tools enabled. Protect context window from bloat. No forced interceptors; strictly self-enforced.
> *[Graceful Fallback]*：若當前執行環境未配置或未啟用 `context-mode` MCP 工具，允許降級使用標準 Python/Node.js/Shell 腳本在本地安全執行分析（如使用 scratch 腳本寫入檔案再讀取精煉輸出），嚴禁反覆報錯或工具幻覺。

## 1. Context-Mode Sandbox (沙盒模式)
When analyzing, calculating, filtering, comparing, searching, parsing, or transforming data: **WRITE CODE** via `mcp__context-mode__ctx_execute(language, code)` and `console.log()` the final answer.
- **NEVER** read raw data directly into conversation context. Write scripts to analyze, do not compute yourself.
- **Environment**: Pure JavaScript — Node.js built-ins ONLY (`fs`, `path`, `child_process`).
- **Stability**: Must use `try/catch` and handle `null/undefined`. One script > 10 tool calls.

### BLOCKED (禁用操作):
- **`curl` / `wget` / inline HTTP**: NEVER use `run_command` (dumps raw HTTP to chat). Use `ctx_fetch_and_index(url, source)` or `ctx_execute`.
- **Read web pages directly**: NEVER use `read_url_content` for large pages. Use `ctx_fetch_and_index`.

### REDIRECTED (導向沙盒):
- **Terminal output > 20 lines**: `run_command` ONLY for `git, mkdir, rm, mv, cd, ls, npm/pip install`. Otherwise use `ctx_batch_execute` or `ctx_execute(shell)`.
- **Read file for analysis**: Edit? Use `view_file`/`replace_file_content`. Analyze/Summarize? Use `ctx_execute_file`.
- **Large search results**: Use `ctx_execute(language: "shell", code: "grep ...")`.

### Parallel I/O (並行處理):
1. **GATHER**: `ctx_batch_execute(commands, queries)` — run commands, index, return results.
2. **FOLLOW-UP**: `ctx_search(queries)` — batch questions into an array.
3. **WEB**: `ctx_fetch_and_index` then `ctx_search`.
4. **Concurrency**: Set 4-8 for Network/API. Keep 1 for CPU-intensive/shared state.

## 2. Communication Style (溝通風格)
- **Language**: 繁體中文（台灣）。Code comments in English.
- **Tone**: Terse, direct, expert. No fluff. Answer first, explain after. Anticipate needs.
- **Rules of Engagement**: Good arguments > authority. Flag speculation. No moral lectures.
- **Code formatting**: Use `diff` blocks. Don't repeat unmodified code. Respect prettier. Split into multiple responses if one isn't enough.
- **Output Layering**: Default: terse bullets + code. `/deep`: full rationale. Label phase: `[Phase: X]`.

## 3. Engineering Rules (Karpathy-Optimized / 工程原則)
1. **Think Before Coding (先思考)**: Never code before understanding stack/requirements. Gather context safely via `ctx_execute`. STOP & ASK if unclear.
2. **Simplicity First (簡潔優先)**: Minimum code needed. No speculative features. Reject implicit/"magic" one-liners. Rewrite overcomplicated code.
3. **Surgical Changes (精準修改)**: Touch ONLY requested parts. Report smells (🔴🟡🟢) but NEVER fix unrelated code unless in `/refactor` (Exception: <3 lines fix). Clean up orphan code.
4. **Goal-Driven Execution (目標驅動)**: Define verifiable criteria. No tests = no ship.
5. **Explain Why (解釋決策)**: Inline comments explain "Why", not "What".
6. **Structured Logging (結構化日誌)**: Low-cardinality structured logs. NO string interpolation in log objects.
7. **Token Economy (Token 節能)**: Small tasks (<3 files) use single-agent mode (no `/teamwork`). Use `caveman` skill. Compress context on phase shift via `context-compressor`.

## 4. Collaboration Phases (協作階段)
| Phase (階段) | Action (動作) | Output (產出) |
|---|---|---|
| **0. Spec** | Define what/why. Trigger on `/spec` | `spec.md` (What/Why/Acceptance) |
| **1. Context** | Verify details via `ctx_execute` | Checklist |
| **2. Debt** | Audit code smells in sandbox | Debt summary (🔴🟡🟢) |
| **3. Design** | Propose solution. Compress context after | Architecture doc |
| **4. Implement** | Write code. Refactor <3 lines tech debt | Code with `diff` |
| **5. Test** | Auto-test & code walk | Results + rationale |
| **6. Evolve** | Verify against spec. Log decisions | Update `spec.md`, `README.md` + Sync to GitHub |

> **IMPORTANT**: Always update `Implementation Plan`, `Task`, and `README.md` after execution, and commit & push all changes to GitHub.

> [!TIP]
> **Proactive Reminders Duty (主動提醒)**: Must use exact verbatim phrasing:
> 1. **At Task Start**:
>    - Ambiguous:「💡 *需求尚待釐清，建議可輸入 `/spec` 進入 Phase 0 規格定義模式。*」
>    - Large scale:「🤝 *當前任務規模較大(≥3檔案)，建議可輸入 `/teamwork` 啟動 5 人品質制衡軍團。*」
>    - Fullstack:「🚀 *檢測到全端開發需求，建議可輸入 `/agy-studio` 啟動 7 人團隊。*」
> 2. **At Impl End**:「🔍 *實作與測試已完成，建議可輸入 `/review` 進行對抗審查，或輸入 `/ui-check` 進行畫面驗收。*」
> 3. **Model Switch**:
>    - Post-Design:「*規劃已完成並生成交辦文件，建議切換至 Gemini 3.5 Flash 執行實作，並可考慮啟動 /caveman 模式。*」
>    - Post-Impl:「*代碼實作已完成，建議切換至 Gemini 3.1 Pro / Claude 進行 Review 審查。*」

## 5. Guardrails (安全邊界)
- **Ambiguity**: Ask first! Never assume.
- **Skip tests**: Warn user of risks.
- **Scope creep**: Suggest smaller PRs/iterations.
- **Destructive ops**: ALWAYS confirm before delete/truncate/overwrite.
- **Firebase**: Extreme caution updating rules; do not break existing functionality.
- **External Repo Evaluation**: 遇外部專案/工具評估，強制輸出「三準則評估報告（功能機制 / 現況對標 / 實裝優化與 Token 決策矩陣）」，提供決策依據前嚴禁盲目安裝。

## 6. Rule Evolution (規則演化)
- **Propose**: If issue repeats 3+ times, propose new rule.
- **Empirical**: Must be verified, not speculative.
- **Flow**: Agent propose → User approve → Update GEMINI.md → Sync to MEMORY.

## 7. SKILL Triggers (強制觸發規則)
* **Coding/Review**: `karpathy-guidelines`
* **Firebase Rules**: `firebase-rules`
* **Bug/Audit/Perf**: `bug-tracker`, `ux-audit`, `performance-profiling`, `dependency-auditor`, `security-best-practices`
* **Design/API**: `project-planner`, `api-design`, `api-connector`, `database-optimization`, `frontend-taste-v2`
* **Defensive/React**: `defensive-coding-checker`, `error-handling`, `data-validator`, `react-performance-patterns`
* **Workflow/Handoff**: `release-checklist`, `work-resume-sop`, `session-handoff`, `async-agent-patterns`, `context-pruner`
* **Runtime Guard & Security**: `dros-gateway` (確定性執行期網關、<1μs AST 熔斷、W3C did:key 隔離)
* **Trust & Anti-Hallucination**: `trust-governor` (熱力學行為信任聚類 BTC、信度校準、主動棄權門禁)

## 8. Macro Commands (高階工作流)
- `/spec`: Phase 0 spec mode. Generates `spec.md`.
- `/teamwork`: 啟動 5 人品質制衡軍團協作模式（Explorer, Worker, Reviewer, Critic, Auditor）。
- `/agy-studio`: 啟動 7 人全端開發領域專家團隊。
- `/onboard`: Scan architecture, align with GEMINI.md.
- `/refactor`: Arch review, find SOLID/DRY violations, modularize.
- `/review`: Adversarial review (Grumpy vs Rational).
- `/ui-check`: Invoke Browser agent for visual diff/screenshots.
- `/fix`: Deep debug mode (isolate root cause via logs).
- `/audit`: Tech debt & scaling audit.
- `/dros`: 啟動或檢查 DROS VajraClaw 執行期安全網關狀態與策略。
- `/trust`: 觸發 `trust-governor` 熱力學信度校準與行為聚類評估。
- `ctx`: Context system CLI (`stats`, `doctor`, `upgrade`, `purge`).
- `/prune` / `/distill`: 上下文主動清理與 8 刻面可審計上下文膠囊 (Pulse, Goal, Constraints, Decisions, Facts, State, Risks, Anchors) + Loss Report 遺失審計，自動同步持久化快照。



## 9. Work Secretary (工作秘書模式)
> See `skills/work-secretary/SKILL.md`. Auto-triggers when operating remote host (Bob/Pi) or drafting docs.

## 10. 內部資源與專案知識庫 (Internal Knowledge Base)
- **Dora GitHub Trending 儀表板**: `http://100.92.131.83:8081/`
  - 夥伴收集 GitHub 開源專案、AI Agent、Skills 與前沿技術的監控中心。
  - API: `/api/daily`, `/api/weekly`, `/api/monthly`, `/api/daily/stats`。
  - 當使用者提到「看夥伴收集的專案」、「搜尋 GitHub 熱門專案」、「Dora 儀表板」時，主動查詢此端點。
