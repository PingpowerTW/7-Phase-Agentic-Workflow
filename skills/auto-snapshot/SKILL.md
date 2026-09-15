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

---

## 📜 SHA-256 Merkle 雜湊鏈與防篡改審計 (DROS 級日誌標準)

為確保 AI 記憶與審計紀錄符合不可否認性（歐盟 AI 法案第 12 條標準），快照每筆 JSONL 記錄均支援 Hash-Chaining：

```json
{
  "timestamp": "2026-09-13T15:30:00Z",
  "type": "milestone",
  "summary": "整合 DROS 執行期安全網關",
  "files": ["STUDIO_RULES.md", "skills/dros-gateway/SKILL.md"],
  "prev_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "hash": "8f3b2c140a876a...",
  "merkle_root": "c7a912e..."
}
```

- **驗證命令**：`auto-snapshot verify` 遍歷校驗整條雜湊鏈，防止日誌被意外竄改或覆寫。
- **冷熱分層與熱蒸餾 (SelfCompact arXiv:2606.23525 原則)**：
  - 當超過 200 筆記錄或 Context 逼近上限時，執行情節壓縮與熱蒸餾。
  - **C1 閉環檢驗**：確認當前任務單元已驗收閉環，嚴禁在推導或除錯中途中斷壓縮。
  - **N1 卡死阻斷**：若處於連續報錯或反覆失敗狀態，**強制阻斷壓縮與快照**，先診斷根因並換道排查，嚴防將無效試錯封裝污染長期記憶。
  - 產出結構化熱蒸餾摘要封裝於新的 Merkle Root 節點中並寫入長期記憶。

