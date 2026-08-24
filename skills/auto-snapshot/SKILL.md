---
name: auto-snapshot
description: >
  本地持久化 AI 記憶引擎與專案快照管理技能。
  自動在開發過程中擷取 milestone, phase_switch, handoff, decision, periodic 等五種結構化快照至 .agent/SNAPSHOT.jsonl，
  並在對話開始時自動恢復 (recover) 上次工作斷點、決策與未完成任務。
  觸發詞：/snapshot, auto-snapshot, 快照, 存檔, 恢復記憶, 交接, 記錄決策, /recover.
---

# ⚡ auto-snapshot — 本地持久化 AI 記憶引擎

> **核心理念**：零基礎架構、本地持久化記憶。透過 Append-Only 的 JSONL 快照日誌，精確追蹤專案開發里程碑、架構決策與任務交接狀態。

---

## 🎯 觸發時機與五大快照類型

| 快照類型 (Type) | 觸發時機 | 典型用途與欄位 |
|:---|:---|:---|
| `milestone` | 完成一項核心功能或修復重大 Bug | 記錄完成的工作摘要與修改檔案清單 (`--files`) |
| `phase_switch` | 開發重心或階段切換 (如從研究切換到實作) | 記錄階段轉移與上下文演進 |
| `handoff` | 工作即將結束或對話準備中斷時 | 記錄完整的 `completed`, `in_progress`, `pending`, `blockers`, `next_action` |
| `decision` | 做出重要技術選型或架構調整 | 記錄決策原因 (`--decision`) 與標籤 (`--tags`) |
| `periodic` | 長時間對話 (超過 15 輪) 且無任何快照 | 自動備份，防止意外中斷失憶 |

---

## 🛠️ CLI 常用指令

```bash
# 1. 專案初始化（建立 .agent/ 目錄與 PROJECT_CONTEXT.md）
auto-snapshot init

# 2. 記錄里程碑快照
auto-snapshot capture milestone "完成使用者註冊與 Email 驗證 API" \
  --files "src/routes/auth.ts,src/services/mail.ts" \
  --tags "auth,api"

# 3. 記錄架構決策
auto-snapshot capture decision "選擇 Prisma 作為 ORM" \
  --decision "因其具備型別安全與易於遷移特性" \
  --tags "database,prisma"

# 4. 工作結束前記錄交接狀態 (Handoff)
auto-snapshot capture handoff "完成認證 API，準備切換到前端頁面" \
  --completed "Auth 路由,Mail 服務" \
  --in-progress "前端登入表單元件" \
  --pending "忘記密碼流程,整合測試" \
  --next-action "完成 LoginPage.tsx 的表單驗證"

# 5. 新對話開啟時恢復記憶
auto-snapshot recover

# 6. 指定 Skill 或查詢關鍵字進行恢復
auto-snapshot recover --skill firebase-rules --query "auth token"
```

---

## 🔌 MCP 工具整合 (MCP Server)

若已啟用 MCP 伺服器，Agent 可直接在對話中呼叫下列工具：
- `snapshot_init`：初始化專案記憶
- `snapshot_capture`：寫入快照
- `snapshot_recover`：查詢與恢復歷史上下文
- `snapshot_compress`：手動觸發情節壓縮
