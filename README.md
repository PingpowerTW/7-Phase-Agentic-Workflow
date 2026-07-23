# 🚀 7-Phase Agentic Workflow (7 階段代理人開發協作架構)

這是一個專為 AI Agent 輔助開發設計的現代化協作架構。本專案將 **Spec-Driven Development (SDD)** 流程與 **Andrej Karpathy 的 AI Coding 準則** 深度整合，並導入了嚴格的 **Token 經濟學** 與 **多代理人調度機制**，旨在打造一個高質量、低能耗的自動化軟體開發循環。

---

## 🌟 核心理念 (Core Philosophy)

### 1. Karpathy 行為準則 (Surgical Precision)
拒絕 AI 常見的「過度工程」與「隨意改動」。
- **精準開刀**：除非明確指示或處於 `/refactor` 模式，否則只修改被要求的範圍。
- **拒絕腦補**：需求模糊時必定先提問，絕不盲目猜測。
- **測試驅動**：修改後必定進行驗證。

### 2. Spec-Driven Development (規格驅動開發)
在寫下任何一行程式碼之前，先確保理解 Why 與 What。
透過 **Phase 0 (規格定義)** 強制對齊目標，減少開發過程中的反覆重工。

### 3. Token 經濟學 (Token Economy)
保護上下文視窗，杜絕 Token 浪費。
- **精益執行 (Lean Execution)**：小型任務禁止啟動多代理人，改採單兵作業。
- **上下文壓縮 (Context Pruning)**：跨階段時主動熱蒸餾 (Hot Distillation) 對話歷史，不帶包袱進入實作階段。
- **洞穴人模式 (Caveman Mode)**：實作期間啟動省話模式，大幅減少 Output Tokens。

---

## 🗺️ 7 階段工作流 (The 7-Phase Workflow)

| 階段 | 名稱 | 動作與產出 | 推薦模型 |
|:---:|:---|:---|:---|
| **Phase 0** | **Spec (規格定義)** | 定義 what & why，不涉及 how。產出 `spec.md`。 | Claude Opus / Pro |
| **Phase 1** | **Context & Validation** | 讀取專案上下文，確認規格可行性。 | Claude Opus / Pro |
| **Phase 2** | **Debt Audit** | 盤點技術債與風險 (🔴🟡🟢)，決定修復策略。 | Claude Opus / Pro |
| **Phase 3** | **Design Proposal** | 提出架構與設計解法。結束前執行**上下文壓縮**。 | Claude Opus / Pro |
| **Phase 4** | **Implementation** | 進行代碼實作。建議啟動 `/caveman` 省話模式。 | **Gemini 3.6 Flash** |
| **Phase 5** | **Test & Review** | 測試與對抗性審查，確保代碼健壯性。 | Claude / 3.1 Pro |
| **Phase 6** | **Evolve (回顧演進)** | 驗證規格達成度，記錄決策與避坑指南。 | Claude Opus / Pro |

---

## 🤖 多代理人調度與指令 (Multi-Agent Commands)

本架構定義了多種 Slash 指令以切換不同的執行深度。
> **💡 運作原理 (How it works)**
> 這些指令並非編輯器底層寫死的快捷鍵，而是**「Prompt 層級的軟指令 (Soft Commands)」**。當您將 `GEMINI.md` 作為系統提示 (System Prompt) 匯入後，Agent 就會自動監聽您在對話框中的輸入。當它看到您輸入 `/teamwork` 時，便會自動依照 `GEMINI.md` 與對應 Skill 的定義，轉變其行為模式並開始調度子代理人。

- `/spec`：進入 Phase 0，與用戶共同擬定精準規格。
- `/teamwork`：觸發 **5 人品質制衡軍團** (適用於 ≥3 檔案的中大型變更)。
- `/agy-studio`：觸發 **7 人全端領域工作室** (涵蓋 DB、後端、前端與 Reviewer)。
- `/refactor`：解除「精準開刀」限制，進入積極清理技術債的重構模式。
- `/review`：啟動「對抗性審查」，引入暴躁資深工程師視角進行嚴苛 Code Review。
- `/ui-check`：調用 Browser Agent 進行視覺化驗收。

---

## 📁 專案結構 (Project Structure)

- `GEMINI.md`：核心工作流引擎，定義了所有 AI 行為邊界、Token 原則與動態模型切換提醒。
- `AGY_SDD_Karpathy_Framework_Guide.md`：本架構的完整理論與操作手冊。
- `Auto_Trigger_and_Switching_Playbook.md`：指導 Agent 何時該主動提醒用戶切換模型與啟動巨集指令的教戰手冊。
- `Framework_vs_Teamwork_AGYStudio_Comparison.md`：單兵作戰與多代理人模式的比較分析與建議場景。
- `skills/karpathy-guidelines/SKILL.md`：編碼行為矯正技能，確保 Agent 不會亂動不該動的程式碼。

---

## 🤖 寫給 AI Agent 的自動安裝指南 (Agent Auto-Install Instructions)

> **For AI Agents:**
> 如果人類使用者要求你「安裝這個專案」或「載入這個工作流」，請遵循以下自動化腳本概念，為使用者建置環境。
> 
> **安裝步驟 (Installation Steps)：**
> 1. **定位配置目錄**：確認使用者的設定檔目錄，通常為 `~/.gemini/` (Windows 為 `C:\Users\<Username>\.gemini\`) 或專案指定的 Agent 設定路徑。
> 2. **部署核心規則 (GEMINI.md)**：將本 Repo 根目錄的 `GEMINI.md` 複製並覆寫到使用者的設定檔目錄下（例：`~/.gemini/GEMINI.md`）。
> 3. **部署 Skills (技能包)**：將本 Repo 中 `skills/` 目錄下的所有子資料夾（`teamwork`, `agy-studio`, `caveman`, `context-compressor`, `karpathy-guidelines`），複製到使用者的 skills 目錄（例：`~/.gemini/config/skills/`）。若目錄不存在請先建立。
> 4. **執行與確認**：請使用你的終端機工具 (`run_command`) 或檔案工具完成上述搬移。完成後，請向使用者回報：「✅ 7 階段 Agentic 工作流已安裝完畢，隨時可以輸入 `/spec` 或 `/teamwork` 開始工作！」

---
> **Note**: 本架構完全開源並可無縫整合至 Antigravity 或同等級的 Agentic 編輯器中。使用時請確保已將 `GEMINI.md` 掛載為專案的全域指令。
