# 🤖 AI Agent 規範與工作流指南

本專案使用 `auto-snapshot` 與 `Loop Engineering` 進行持久化記憶、安全閘門與工作流管理。

## 1. 記憶自動擷取 (Auto-Capture)
每當完成階段性任務或修復 Bug 時，必須自動執行或建議使用者執行快照擷取：
- **里程碑完成 (Milestone)**: `auto-snapshot capture milestone "變更摘要" --files <檔案路徑> --tags <標籤>`
- **技術決策 (Decision)**: `auto-snapshot capture decision "決策標題" --decision "決策細節與原因"`
- **對話交接 (Handoff)**: `auto-snapshot capture handoff "進度總結" --completed <已完成> --in-progress <進行中> --pending <待辦>`

## 2. 雙軌記憶架構 (Dual-Track State)
- **微觀軌道 (`SNAPSHOT.jsonl`)**：記錄每一個 milestone、decision、handoff 的高頻歷史事件日誌。
- **宏觀軌道 (`STATE.md`)**：專案當前狀態脊椎，維護 High Priority、Watch List 與 Recent Noise。
- **同步原則**：階段交接時同步更新 `STATE.md`，使新會話能在最小 Token 開銷下取得全域狀態。

## 3. 機械化安全門禁與 Maker / Checker 分離 (Safety Gates & Verification)
- **`gate.yaml` 物理阻斷**：
  - 嚴禁自動修改 `denylist` 路徑（`.env*`, `credentials/**`, `secrets/**`, `auth/**`, `billing/**`, `migrations/**`）。
  - 單次修改超過 8 個檔案強制向人類 Escalation。
- **Maker / Checker 角色硬分離**：
  - Maker 負責產出 diff；Checker (loop-verifier) 預設以 REJECT 立場接手跑真實測試與確認 scope。
- **Git Worktree 實體隔離**：
  - 涉及架構調整或跨檔案重構任務，優先於獨立 Git Worktree 進行。
