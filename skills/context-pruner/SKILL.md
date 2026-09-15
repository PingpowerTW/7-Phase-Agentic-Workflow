---
name: context-pruner
description: >
  長任務上下文主動清理與 8 刻面可審計熱蒸餾技能（Context Pruner & 8-Facet Auditable Capsule）。
  清除已廢棄方案、失敗嘗試、過期除錯 Log、重複輸出與過時決策，產出包含 8 大核心刻面（脈動概況、目標驗收、硬性約束、已定案決策、穩定事實、進行中狀態、未決問題與風險、代碼實體錨點）與遺失審計報告 (Loss Report) 的高密度上下文膠囊，
  並自動聯動 auto-snapshot 本地記憶引擎寫入持久化交接快照。
  觸發詞：/prune, /clean-context, /distill, 整理上下文, 上下文清理, 壓縮上下文, 清理對話, 記憶蒸餾, 上下文膠囊。
---

# 🧹 Context Pruner — 上下文主動清理與熱蒸餾技能

> **核心理念**：
> 「你缺的不是更多 Token，而是一個乾淨、精簡，而且仍然有效的 Context。」
> 適用於 Antigravity、Codex、Claude Code、Cursor 等所有 AI Agent 環境。

---

## 🎯 觸發時機 (When to Use)

- 使用者輸入 `/prune`、`/clean-context`、`/distill` 或說「整理上下文」、「清理對話」、「壓縮歷史」。
- **長任務中途主動建議**：
  - 當對話輪數超過 10~15 輪。
  - 當經過密集的除錯 (Debug) 或排錯後，問題已解決且留下大量冗長日誌。
  - 當任務從 Phase 3 (Design) 即將切換到 Phase 4 (Implementation)。
  - 當使用者更換了架構或推翻了先前的實作方案。

---

## 🗑️ 上下文垃圾清單 (What to Prune)

執行本技能時，主動忽略並宣告廢棄以下 7 類無效資訊：
1. ❌ **已放棄的方案與設計草稿**
2. ❌ **失敗的嘗試與除錯過程日誌 (Debug Logs)**
3. ❌ **重複產生的程式碼區塊與模板**
4. ❌ **已經完成且後續無需參考的中間步驟**
5. ❌ **與當前開發方向無關的發散歷史紀錄**
6. ❌ **已經被新決策取代的舊設定與參數**
7. ❌ **非必要的客套話與過渡性說明**

---

## 📋 8 大刻面可審計上下文膠囊 (8-Facet Auditable Context Capsule)

汲取 Context Diamond 確定性架構並針對繁體中文語意優化，Agent 必須將對話提煉為一份高密度、可審計的**上下文膠囊 (Context Capsule)**，包含 8 大刻面與遺失審計報告：

```markdown
### 💎 上下文膠囊 (8-Facet Context Capsule)

1. 💓 **當前脈動 (Pulse)**：[任務現況的一句話簡報與所處 Phase]
2. 🎯 **目標與驗收 (Goal & Acceptance)**：[當前任務的核心交付價值、成功標準與驗收條件]
3. 🛡️ **規則與硬約束 (Rules & Constraints)**：[不可動到的代碼範圍、依賴限制、安全護欄 (must/never/avoid)]
4. ⚖️ **已定案決策 (Decisions Already Made)**：[已拍板的架構選型、演算法取捨，附帶 Why]
5. 🏛️ **穩定事實 (Stable Facts)**：[已驗證的環境變數、相容版本、系統前提條件]
6. 📈 **目前狀態 (Current Working State)**：[進行中的檔案、分支狀態、剛通過的測試]
7. 🚧 **未決問題與風險 (Open Loops & Risks)**：[目前的 Blockers、潛在死角、待確認外部依賴]
8. ⚓ **代碼實體與錨點 (Entities & Anchors)**：[關鍵檔案路徑、Symbol 符號、核心函數/類別名稱]

---
#### 🔍 遺失審計報告 (Loss Report)
- **已剪除噪訊**：[列出本次刻意丟棄的項目：如重複 stacktrace、已排除的試錯方案、無效探索路徑]
- **剪除判定**：[確認無關鍵約束或未存檔代碼被誤刪]
```

> **承諾宣告**：在輸出膠囊後加入聲明：
> *「後續執行任務時，將以這份最新膠囊作為唯一真實來源 (Single Source of Truth)，不再受已失效或被取代的歷史資訊干擾。」*

---

## ⚡ 與 `auto-snapshot` 自動聯動

產出摘要後，Agent 應自動調用 `auto-snapshot` CLI 記錄持久化快照，確保跨 Session 記憶同步：

```bash
auto-snapshot capture handoff "<目前目標摘要>" \
  --completed "<已完成進度清單>" \
  --in-progress "<進行中項目與卡點>" \
  --pending "<尚未解決的問題>" \
  --next-action "<下一步執行計畫>"
```

若有新定案的重大架構，同步寫入：
```bash
auto-snapshot capture decision "<決策標題>" --decision "<決策理由與背景>" --tags "<關鍵字標籤>"
```
