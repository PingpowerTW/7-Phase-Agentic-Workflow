# Memory Tiers Specification — AI 優化 Workspace

本規範定義 AI Agent 記憶生命週期與三層分級機制，符合 SelfCompact (arXiv:2606.23525) 與雙軌記憶架構。

---

## 🟢 L1: Working Memory (即時工作記憶)
- **生命週期**：單次對話 Session / 即時推導過程。
- **儲存載體**：
  - 當前 LLM 對話 Context Window
  - 專案活體狀態脊椎：`STATE.md` (High Priority, Watch List, Recent Noise)
  - 當前 Git 工作區狀態 (`git status`, Unstaged diff)
- **更新原則**：高頻、低延遲，每次任務階段切換時即時同步。

---

## 🟡 L2: Episodic Memory (短期情節記憶)
- **生命週期**：數天至數週（任務演進、Bug 修復、對話交接）。
- **儲存載體**：
  - 微觀歷史日誌：`.agent/SNAPSHOT.jsonl` (milestone, decision, handoff)
  - 迴圈運行紀錄：`loop-run-log.md` (執行紀錄、審核歷程)
  - 最近 Git Commit 歷史 (Last 7 days)
- **容量治理**：
  - 當快照數量累積接近 200 條時，觸發 SelfCompact 熱蒸餾（保留最新 50 條，前 150 條精煉為 `compressed_archive`）。

---

## 🔵 L3: Semantic & Systemic Memory (長期語意與系統知識)
- **生命週期**：永久持久化（跨專案、跨會話全局複用）。
- **儲存載體**：
  - 形式化系統不變量與安全門禁：`invariants.yaml`、`gate.yaml`
  - 核心規格與決策記錄：`AGENTS.md`、`spec.md`、`GEMINI.md`、ADR
  - 遠端長期向量知識庫：Supabase Vector Store (`memory-engine`)
- **注入原則**：
  - 唯有通過 C1 閉環檢驗（經過實證之高價值踩坑經驗或架構決策）方可熱蒸餾寫入 L3；處於報錯狀態（N1）嚴禁污染 L3。
