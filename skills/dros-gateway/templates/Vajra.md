# 🛡️ 7-Phase Agentic Workflow 執行期治理守護規範 (Vajra.md)

> 本規範由 DROS VajraClaw 網關即時編譯為 $\mathcal{O}(1)$ 常數時間記憶體位元點陣圖，在 AI Agent 執行系統呼叫 (Syscall) 與 Tool Call 前實施微秒級硬熔斷防護。

---

## 1. 允許執行的能力 (Allowed Capabilities - Whitelist)

### 唯讀與查詢工具 (All Roles)
- 允許讀取工作區檔案 (`view_file`, `ctx_execute_file`, `fs.readFile`)
- 允許列出工作區目錄結構 (`list_dir`, `find_by_name`)
- 允許全文與正規表達式搜尋 (`grep_search`, `search_web`)
- 允許無破壞性終端查詢 (`git status`, `git log`, `npm test`, `cargo test`, `pytest`)

### 寫入與修改工具 (Orchestrator Role Only)
- 允許主代理人 (Orchestrator) 建立與覆寫專案原始碼檔案 (`write_to_file`, `replace_file_content`)
- 允許套件管理與建置編譯 (`npm install`, `npm run build`, `cargo build`, `pip install`)
- 允許建立與刪除本機 Git 工作分支 (`git checkout -b`, `git branch -d`)

---

## 2. 嚴格硬性熔斷邊界 (Strict Fail-Closed Boundaries)

### 🔴 系統級破壞操作 (Critical Kernel Invariants)
- **永久禁止** 遞迴刪除根目錄或磁碟格式化指令（如 `rm -rf /`, `rmdir /s /q C:\`, `mkfs`, `format`）
- **永久禁止** 強制推送覆寫主分支（`git push --force origin main`, `git push -f master`）
- **永久禁止** 破壞性資料庫 DDL（`DROP DATABASE`, `DROP SCHEMA`, `TRUNCATE TABLE`）

### 🟡 敏感憑證與私鑰防護 (Secret Protection)
- **永久禁止** 讀取、導出或外洩機密檔案（包括 `.env`, `.env.local`, `*.pem`, `id_rsa`, `credentials.json`）
- **永久禁止** 向外部未註冊的遠端 IP/域名傳送含有 API Token 或私鑰的明文請求

### 🔵 多代理人角色越權攔截 (Role Enforcement)
- **Explorer / Worker / Reviewer / Critic / Auditor**：呼叫任何寫入工具 (`write_to_file`, `replace_file_content`, `run_command` 寫入指令) 時，一律在 $<1\mu\text{s}$ 內硬性拒絕 (HTTP 403)。
