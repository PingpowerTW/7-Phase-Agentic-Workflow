---
name: dros-gateway
description: >
  DROS VajraClaw 確定性執行期安全與 Docker 治理網關技能。
  提供微秒級 (<1μs) AST 點陣硬熔斷、W3C did:key 代理人身分通行證 (RFC-010)、SHA-256 Merkle 審計鏈與跨生態 (Antigravity/Claude/Cursor) 執行攔截。
  觸發詞：/dros, dros-gateway, 執行期安全, 安全網關, vajraclaw, runtime guard, did:key.
---

# ⚡ DROS VajraClaw — 確定性執行期安全與治理網關

> **核心理念**：從機率型 Prompt 軟約束升級為**「確定性執行期硬熔斷」**。將安全規範移至編譯期點陣圖，在系統呼叫 (Syscall) 與 Tool Call 發生前以常數時間 $\mathcal{O}(1)$ 物理切斷未授權或破壞性操作。

---

## 🎯 When to Use

- 專案需要最高等級防禦（避免誤下 `rm -rf`、機密金鑰 `.env` 洩漏、惡意腳本注入）
- 啟動多代理人（`/teamwork`, `/agy-studio`）需要嚴格的身分隔離（W3C `did:key`）
- 需要法律級/歐盟 AI 法案第 12 條標準的不可篡改 SHA-256 Merkle 審計日誌
- 接入 Cursor / VS Code / Claude Code / Antigravity 作為本機安全網關 (`localhost:8080`)

---

## 🚀 快速啟動 Docker 網關 (One-Command Startup)

```bash
# 1. 啟動本機 DROS Hacker 網關 (免金鑰，個人永久免費)
docker run -d -p 8080:8080 --name dros-gateway \
  -v $(pwd)/Vajra.md:/app/Vajra.md \
  -v $(pwd)/dros_policy.yaml:/app/demo_policy.yaml \
  dros/hacker-gateway:v1.0.0

# 2. 檢驗網關健康狀態
curl http://localhost:8080/health
```

---

## 🔑 W3C `did:key` 角色身分通行證 (RFC-010)

DROS 為每個 Subagent 派發獨立的 Ed25519 身分憑證，杜絕代理人越權操作：

| 角色 (Role) | 派發 DID 識別碼 | 允許能力 (Capabilities) | 物理限制 (Hard Invariant) |
| :--- | :--- | :--- | :--- |
| **Orchestrator** | `did:key:z6MkuOrchestrator...` | 檔案讀寫、指令執行、交付驗收 | 嚴禁直接刪除專案根目錄或修改 DROS 內核 |
| **Explorer** | `did:key:z6MkuExplorer...` | `view_file`, `list_dir`, `grep_search` | **嚴禁寫入任何檔案與執行 Shell** |
| **Worker** | `did:key:z6MkuWorker...` | 文字碼塊產出、沙盒純計算 | **嚴禁直接落地至正式檔案系統** |
| **Reviewer / Critic** | `did:key:z6MkuReviewer...` | 唯讀代碼分析、對抗性壓力測試 | **唯讀權限，嚴禁寫入與網路外聯** |
| **Auditor** | `did:key:z6MkuAuditor...` | 靜態代碼與測試覆蓋度稽核 | **唯讀權限，嚴禁修改代碼** |

---

## 🛡️ 策略配置雙軌規範

### 1. 人類直覺白話文 (`Vajra.md`)
```markdown
# 🛡️ DROS 執行守護策略 (Vajra.md)

## 1. 允許執行的工具 (Allowed Capabilities)
- 允許讀取當前工作區檔案 (`file_read`, `view_file`)
- 允許搜尋 codebase (`grep_search`, `find_by_name`)
- 允許一般終端唯讀指令 (`git status`, `npm test`, `cargo check`)

## 2. 嚴格禁止的破壞性操作 (Strict Blocks)
- 永久禁止遞迴刪除根目錄 (`rm -rf /`, `rmdir /s`)
- 永久禁止讀取或外洩 `.env`, `id_rsa`, `credentials.json`
- 永久禁止執行未授權的資料庫刪庫操作 (`DROP DATABASE`, `DROP TABLE`)
```

### 2. 結構化機器點陣策略 (`dros_policy.yaml`)
```yaml
vajra_version: "1.0"
security_level: STRICT
rules:
  - id: R001_READ_TOOLS
    action: ALLOW
    tool: ["view_file", "list_dir", "grep_search", "find_by_name"]
  - id: R002_ORCHESTRATOR_WRITE
    action: ALLOW
    tool: ["write_to_file", "replace_file_content"]
    condition: "principal.role == 'Orchestrator' and not payload.path.endswith('.env')"
  - id: R003_DESTRUCTIVE_BLOCK
    action: BLOCK
    tool: "run_command"
    condition: "any(cmd in payload.command for cmd in ['rm -rf', 'drop table', 'format', 'git push --force'])"
  - id: R_DEFAULT_FALLBACK
    action: BLOCK
    tool: "*"
```

---

## 🔌 整合 Antigravity / Claude Code / Cursor

### 1. MCP 設定 (`mcp_settings.json` 或 `claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "dros-vajraclaw": {
      "url": "http://localhost:8080/mcp",
      "transport": "http"
    }
  }
}
```

### 2. 評估 API 呼叫 (`POST http://localhost:8080/evaluate`)
在執行任何特權 Tool Call 前，向 DROS 網關提交評估：
```json
{
  "principal": {
    "did": "did:key:z6MkuExplorer...",
    "role": "Explorer"
  },
  "action": "write_to_file",
  "payload": {
    "path": "src/main.ts"
  }
}
```
**DROS 判定回應**：
```json
{
  "decision": "BLOCK",
  "reason": "Principal did:key:z6MkuExplorer has ReadOnly clearance. Action write_to_file denied.",
  "latency_us": 0.42,
  "merkle_root": "a8f3b2c..."
}
```
