# Fleet Registry — Multi-Agent Population & Tool Scoping

本檔案定義本工作區的 AI 代理人兵團編制、角色分工以及遵循**最小權限原則 (Least Privilege)** 的工具授權範疇。

---

## 👥 Fleet Populations (代理人編制)

### 1. `agent-explorer` (探索與架構分析者)
- **職責**：代碼庫調查、依賴掃描、技術文檔研讀與上下文收集。
- **權限層級**：純唯讀 (Read-Only)。
- **授權工具 (Allowed Tools)**：
  - `view_file`, `list_dir`, `grep_search`, `find_by_name`, `search_web`
- **禁限 (Denylist)**：嚴禁寫入、修改檔案或執行非唯讀 shell 指令。

---

### 2. `agent-maker` (代碼實作者 / Worker)
- **職責**：依據核准之 `spec.md` 或任務指派撰寫最小必要代碼與單元測試。
- **權限層級**：受限寫入 (Scoped Write)。
- **授權工具 (Allowed Tools)**：
  - `write_to_file`, `replace_file_content`
  - `run_command` (僅限 `git status`, `git diff`, `npm/pip/cargo build`)
- **安全約束**：
  - 受 `gate.yaml` 物理阻斷約束，嚴禁觸碰機敏路徑（`.env*`, `secrets/**`, `credentials/**`）。
  - 單次變更檔案數上限為 8 檔案 (`maxFiles: 8`)。
  - 嚴禁自行宣告測試通過（由 Checker 裁決）。

---

### 3. `agent-checker` (對抗式驗證者 / loop-verifier)
- **職責**：獨立執行真實測試套件，落實 Falsification Discipline（證偽反例探針），審計覆蓋率與不變量違約。
- **權限層級**：測試與診斷執行 (Test & Verification Execution)。
- **授權工具 (Allowed Tools)**：
  - `run_command` (僅限測試指令：`unittest`, `pytest`, `npm test`, `jest`)
  - `view_file`
- **原則**：預設採 `REJECT` 立場，零容忍假斷言與 Mock 過度假綠燈。

---

### 4. `agent-critic` (審查者 / Adversarial Reviewer)
- **職責**：執行程式碼品質、安全性、可維護性審查（Grumpy vs Rational 對抗式審查）。
- **權限層級**：純唯讀審查 (Read-Only Review)。
- **授權工具 (Allowed Tools)**：
  - `view_file`, `grep_search`
- **原則**：依循 `karpathy-guidelines` 審計代碼異味（🔴🟡🟢），禁止對不相關代碼做非必要微調。

---

### 5. `agent-sentinel` (漂移哨兵與安全稽核者)
- **職責**：定期巡檢專案健康度、偵測代碼與規格漂移、同步狀態脊椎。
- **權限層級**：門禁與狀態同步 (Gate & State Sync)。
- **授權工具 (Allowed Tools)**：
  - `python scripts/loop_drift.py`
  - `python scripts/loop_gate.py`
  - `node loop-engineering/tools/loop-audit/dist/cli.js`
  - `replace_file_content` (僅限 `STATE.md`, `loop-run-log.md`)
