---
name: auto-snapshot
description: >
  Phase 6 與跨階段本地持久化 AI 記憶引擎（整合 auto-snapshot、session-handoff 對話交接、context-recovery 記憶恢復、decision-logger ADR 決策紀錄與 work-resume-sop 恢復健康檢查）。
  自動擷取 milestone, phase_switch, handoff, decision, periodic 五種結構化快照至 .agent/SNAPSHOT.jsonl，並同步維護 STATE.md 狀態脊椎。
  觸發詞：/snapshot, /recover, auto-snapshot, 快照, 存檔, 恢復記憶, 交接, 記錄決策, 繼續, resume, session-handoff, context-recovery, decision-logger.
---

# ⚡ auto-snapshot — 7-Phase 本地持久化記憶、交接與恢復引擎 (5-in-1 Edition)

> **核心理念**：雙軌記憶架構——微觀事件寫入 `.agent/SNAPSHOT.jsonl`（Append-Only SHA-256 Merkle 鏈），宏觀現況同步至 `STATE.md`（活體狀態脊椎）。

---

## 1. 五大快照時機與標準指令 (Capture & ADR Decision Logging)

| 類型 | 觸發時機 | 標準執行指令 |
|:---|:---|:---|
| **`milestone`** | 完成功能、修復 Bug 或通過 Phase 5 | `auto-snapshot capture milestone "變更摘要" --files "a.ts,b.ts" --tags "feat"` |
| **`decision`**<br>*(ADR 決策)* | 做出技術選型、架構取捨或安全規範定案 | `auto-snapshot capture decision "決策標題" --decision "背景Context + 決策內容 + 取捨後果(Trade-offs)" --tags "arch,adr"` |
| **`handoff`**<br>*(Session 交接)* | 完成階段準備開新對話、或上下文達 10~15 輪 | `auto-snapshot capture handoff "進度總結" --completed "已完成" --in-progress "進行中" --pending "待辦" --next-action "下一步"` |
| **`phase_switch`** | 跨 Phase 切換（如 Phase 3 規劃 ➔ Phase 4 實作） | `auto-snapshot capture phase_switch "Phase 3 -> 4" --summary "規格已鎖定"` |
| **`periodic`** | 長對話超過 15 輪之自動安全備份 | 自動觸發，防止意外中斷失憶 |

> **雙軌同步鐵律**：每次執行 `milestone` 或 `handoff` 時，必須同步更新根目錄 `STATE.md` 的 `Last run` 時間戳記、`High Priority` 與 `Watch List`，讓下次新對話能以 0 探索成本瞬間掌握全局。

---

## 2. 新對話恢復與健康檢查 SOP (`context-recovery` + `work-resume-sop`)

當開啟新對話、使用者輸入 `/recover`、或說「繼續 / 繼續處理 / resume」時，依序執行以下 3 步：

1. **瞬間載入本地記憶（免盲目探索）**：
   - 先讀 `STATE.md` 掌握當前進行中任務與觀察清單。
   - 執行關鍵字指紋檢索：`auto-snapshot recover --query "<當前任務關鍵字>"`（或 `--skill <關聯技能>`）。若顯示 `✅ 本地記憶覆蓋查詢`，直接採用本地記憶，跳過遠端檢索以節省 Token。
2. **工作恢復健康快檢 (Work Resume Health Check)**：
   - 在動手寫新代碼前，先確認 `git status --short` 工作區是否乾淨，並對受影響範圍跑一次輕量門禁（如 `python scripts/local_guard.py --git` 或既有單元測試），確認基準線為綠燈後再繼續未完成任務。
3. **報到格式（控制在 8 行內）**：
   - 簡報：`[上次完成項目] ➔ [工作區健康狀態] ➔ [本輪即將執行的 Next Action]`，隨即開工。

---

## 3. 情節壓縮與 SHA-256 Merkle 審計鏈

- **C1 / N1 壓縮防線**：累積超過 200 筆快照觸發壓縮前，必須確保當前任務已閉環 (**C1**) 且非處於連續報錯卡死狀態 (**N1**)，避免將錯誤試錯過程寫入長期記憶（如 `memory-engine` Supabase）。
- **防篡改校驗**：執行 `auto-snapshot verify` 可遍歷校驗 JSONL 的 `prev_hash -> hash -> merkle_root` 雜湊鏈完整性。
