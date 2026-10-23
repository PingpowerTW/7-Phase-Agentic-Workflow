# Memory Tiers Specification — AI 優化 Workspace

本規範定義 AI Agent 記憶生命週期與多尺度分級機制，整合 **Next-Concept Modeling (NCM)** 粗到細原則、**SelfCompact (arXiv:2606.23525)** 情節蒸餾與雙軌記憶架構。

---

## 🟢 Level 0: Macro-scale Concept Anchor (宏觀概念錨點 / L1)
- **概念核心**：只保留「當前意圖（Current Goal）」與「進行中最高優先級（In-Flight Priorities）」，抑制一切非必要歷史。
- **生命週期**：單次對話 Session / 即時推導過程。
- **儲存載體**：
  - `STATE.md` 頂部：Active Goal 錨點與 High Priority 清單（預算 < 500 Tokens）。
  - 當前 Git 工作區狀態 (`git status`, Unstaged diff)。
- **更新原則**：高頻、低延遲，每次任務階段切換時即時同步。

---

## 🟡 Level 1: Meso-scale Milestone Index (中觀里程碑指針 / L2)
- **概念核心**：已完成之歷史任務不堆疊長篇大論，一律採用 **Hash + Intent + Invariants** 之單行索引指針（每筆約 10~20 Tokens）。
- **生命週期**：數天至數週（任務演進、Bug 修復、對話交接）。
- **儲存載體**：
  - `STATE.md` 中部：Milestone Index Pointers 表格。
  - 微觀歷史日誌：`.agent/SNAPSHOT.jsonl` (milestone, decision, handoff)。
  - 迴圈運行紀錄：`loop-run-log.md` (執行紀錄、審核歷程)。
- **容量治理**：
  - 當快照數量累積接近 200 條時，觸發 SelfCompact 熱蒸餾（保留最新 50 條，前 150 條精煉為 `compressed_archive`）。

---

## 🔵 Level 2: Micro-scale On-Demand Deep Truth (微觀隨選真理庫 / L3)
- **概念核心**：**0 Token 常駐佔用**。長篇詳細記錄與完整 Diff 物理沉澱於檔案庫與 Git 時光機，僅在 Agent 明確需要調試或回溯時，透過 `git show <hash>` 或文件指針隨選（On-Demand）動態展開。
- **生命週期**：永久持久化（跨專案、跨會話全局複用）。
- **儲存載體**：
  - 詳細歷史歸檔：`docs/history/MILESTONES_ARCHIVE.md`
  - 形式化系統不變量與安全門禁：`invariants.yaml`、`gate.yaml`
  - 核心憲法與決策記錄：`AGENTS.md`、`spec.md`、`GEMINI.md`、ADR
  - Git Commit 時光機（真實代碼狀態）
  - 遠端長期向量知識庫：Supabase Vector Store (`memory-engine`)
- **注入原則**：
  - 唯有通過 C1 閉環檢驗（經過實證之高價值踩坑經驗或架構決策）方可熱蒸餾寫入 L3；處於報錯狀態（N1）嚴禁污染 L3。
