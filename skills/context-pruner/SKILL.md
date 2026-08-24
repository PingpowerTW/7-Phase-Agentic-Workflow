---
name: context-pruner
description: >
  長任務上下文主動清理與語意熱蒸餾技能（Context Pruner & Active Distillation）。
  清除已廢棄方案、失敗嘗試、過期除錯 Log、重複輸出與過時決策，產出包含 6 大核心要素（目前目標、核心限制、已確認決策、目前進度、尚未解決問題、下一步計畫）的極簡任務摘要，
  並自動聯動 auto-snapshot 本地記憶引擎寫入持久化交接快照。
  觸發詞：/prune, /clean-context, /distill, 整理上下文, 上下文清理, 壓縮上下文, 清理對話, 記憶蒸餾。
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

## 📋 6 大核心要素蒸餾法 (The 6-Factor Distillation)

Agent 必須將整個對話提煉為一份精簡高密度的任務摘要，**僅保留以下 6 項**：

```markdown
### 🧹 上下文熱蒸餾摘要 (Context Distillation Summary)

1. 🎯 **目前目標**：[明確描述當前任務要交付的核心價值與功能]
2. 🛡️ **核心限制與要求**：[技術棧、語言、相容性、不可動到的代碼範圍]
3. ⚖️ **已確認的決策**：[已定案的架構選型與實作方案，附帶簡短 Why]
4. 📈 **目前進度**：[已完成的模組、檔案與測試]
5. 🚧 **尚未解決的問題**：[目前的 Blockers、已知 Bug 或待釐清細節]
6. 🚀 **下一步執行計畫**：[接下來 1~3 個具體且可驗證的動作]
```

> **承諾宣告**：在輸出摘要後加入聲明：
> *「後續執行任務時，將以這份最新摘要作為唯一真理依據 (Single Source of Truth)，不再受已失效或被取代的歷史資訊干擾。」*

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
