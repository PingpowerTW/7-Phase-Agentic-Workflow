# 📊 Antigravity SDD & Karpathy 框架 vs /teamwork vs /agy-studio 對比分析報告

> **分析目的**：釐清我們剛建立的 **Antigravity SDD & Karpathy 增強框架** 與既有的 **`/teamwork`**（多代理人品質協作）及 **`/agy-studio`**（全端開發團隊）在定位、運作機制、資源消耗與適用場景上的差異，並說明三者如何協同運作。

---

## 📌 一頁總覽 (Executive Summary)

三者的關係並非替代，而是**三層遞進的架構疊加**：

```mermaid
graph TD
    subgraph Layer1 [1. 底層大腦與行為規範 (Base Engine)]
        Framework[Antigravity SDD & Karpathy 框架<br/>• Phase 0~6 流程<br/>• Karpathy 4 大行為護欄<br/>• 精準開刀 / 重構雙模式]
    end

    subgraph Layer2 [2. 通用品質制衡軍團 (Quality Engine)]
        Teamwork[/teamwork 模式<br/>• 主代理人 + 5 個子代理人<br/>• Explorer / Worker / Reviewer / Critic / Auditor<br/>• 適用於 ≥3 個檔案修改、重要重構]
    end

    subgraph Layer3 [3. 全端領域專業軍團 (Domain Studio)]
        AGYStudio[/agy-studio 模式<br/>• 主代理人 + 7 個子代理人<br/>• DB / Backend / Frontend 專家分工<br/>• 適用於完整全端專案開發]
    end

    Framework -->|作為所有 Agent 的核心紀律| Teamwork
    Framework -->|作為所有 Agent 的核心紀律| AGYStudio
```

---

## 🔍 二、三維核心指標對比 (Comprehensive Comparison)

| 比較維度 | 🛡️ 本框架 (SDD & Karpathy) | 🤝 `/teamwork` 模式 | 🚀 `/agy-studio` 模式 |
|---|---|---|---|
| **核心定位** | **行為紀律與流程規範**<br>(Behavior & Process Rules) | **多角色代碼審查與品質制衡**<br>(Quality Gate & Code Safety) | **全端領域專家協作團隊**<br>(Full-Stack Domain Studio) |
| **執行主體** | 主代理人 (Single Agent / Orchestrator) | 主代理人 + 5 個子代理人<br>(Explorer/Worker/Reviewer/Critic/Auditor) | 主代理人 + 7 個子代理人<br>(含 DB/Backend/Frontend 專家) |
| **關鍵使命** | 防止 AI 盲目假設、過度工程、隨意刪除程式碼、偏離需求 | 徹底消除偷懶代碼 (TODO/假測試)、抓出邊界漏洞與安全隱患 | 從無到有建構完整資料庫、後端 API 與前端 UI/UX |
| **規格定義 (Spec)** | **Phase 0 (`spec.md`)**<br>明確區分 What/Why 與 How | 由主代理人引導 Explorer 拆解里程碑 | 由主代理人繪製全端架構圖與 Milestone |
| **修改權限** | 主代理人擁有寫入權 | **僅主代理人可寫檔案**<br>(5 個子代理人皆為 Read-Only) | **僅主代理人可寫檔案**<br>(7 個子代理人皆為 Read-Only) |
| **代碼保護機制** | Karpathy「精準開刀」<br>(無關死碼僅報告不修改) | Auditor 零容忍假測試/佔位符；<br>Critic 執行壓力測試 | 嚴格防範無用 Mock 資料；<br>要求真串接與真實 API |
| **Token 消耗** | 🟢 **極低** (單 Agent 常駐) | 🟡 **中高** (多子代理人 2 輪 Quality Gate) | 🔴 **高** (全端 7 個 Agent 串行+並行) |
| **自動觸發條件** | 所有開發/修改/審查任務自動啟用 | 修改 ≥3 個檔案、架構變更或重要任務 | 明確要求「開發完整網頁/全端應用/前後端」 |

---

## 🛠️ 三、深度差異分析 (Deep Dive)

### 1. 思考維度 (Thinking Perspective)
*   **本框架**：關注 **「Agent 如何思考與自我約束」**。就算只有一個 Agent 在運作，也不能偷懶、不能多寫無用代碼、不能盲目假設。
*   **`/teamwork`**：關注 **「紅藍對抗與制衡 (Checks and Balances)」**。引入第三方審查者 (Reviewer/Critic/Auditor) 來對抗 Worker 產出的代碼，防止「自我感覺良好」。
*   **`/agy-studio`**：關注 **「領域專業分工 (Domain Specialization)」**。將思考拆解為 DB 架構師、後端 Lead 與前端 Master，解決複雜全端鏈條下的脈絡混亂問題。

### 2. 精準開刀 vs 多角化審查 (Precision vs Review Depth)
*   **本框架的 Surgical Precision** 規定：*「如果改動無關的程式碼或註解，不要碰它。」*
*   **`/teamwork` 的 Critic & Auditor** 補充：*「雖然你只改了 A 函式，但我（Critic）要確認這個修改會不會導致 B 模組溢位；我（Auditor）要抓出你是不是寫了 `assert(true)` 假測試。」*

---

## 💡 四、三者如何協同運作？(Synergy Scenarios)

當你觸發斜線指令時，三者會**自動無縫結合**：

### 協同情境：使用 `/agy-studio` 開發「電商購物車全端系統」

1. **Step 1 (規範生效)**：
   - 觸發 `/agy-studio` 模式，系統自動載入 **Phase 0 Spec**。
   - 產出 `spec.md` 確定購物車成功標準（Success Criteria）。
2. **Step 2 (領域分工)**：
   - **DB Architect** 產出 Schema；**Backend Lead** 產出 API；**Frontend Master** 刻寫 UI。
3. **Step 3 (Karpathy 護欄啟動)**：
   - Backend Lead 在寫 API 時受到 Karpathy 護欄約束：*「不寫任何 TODO 佔位符、50 行能完成的不寫 200 行」*。
4. **Step 4 (Quality Gate 對抗審查)**：
   - **Critic** 進行對抗測試（例如：購物車數量傳入負數 -5 時會怎樣？）。
   - **Auditor** 審計代碼是否寫死 API Key。
5. **Step 5 (Phase 6 演進回顧)**：
   - 所有代碼審查 PASS 後，由主代理人寫入檔案系統，並對照 `spec.md` 點收。

---

## 🎯 五、選擇決策樹 (Decision Tree)

不確定該用哪種模式？跟著這個決策樹走：

```text
你的開發任務是什麼？
├── 1. 修改 1~2 個檔案 / 修正小 Bug / 詢問問題
│   └── 🎯 直接口述 ──> 使用 【Antigravity SDD & Karpathy 框架】 (單 Agent 模式，Token 最省)
│
├── 2. 開發新功能、重構核心模組、改動 ≥3 個檔案
│   └── 🎯 輸入 /teamwork (或使用 /refactor) ──> 開啟 【Teamwork 5 人審查軍團】
│
├── 3. 從零開發完整網頁、前後端整合應用、資料庫+API+前端
│   └── 🎯 輸入 /agy-studio (或 /spec) ──> 開啟 【AGY Studio 7 人全端團隊】
│
└── 4. 想清楚「要做什麼」但還沒搞懂細節
    └── 🎯 輸入 /spec ──> 進入 【Phase 0 Spec 模式】 產出 spec.md
```

---

## 📝 總結

*   **Antigravity SDD & Karpathy 框架** 是 **基礎憲法 (Constitution)**，奠定了規範與品質底線。
*   **`/teamwork`** 是 **品質特警 (QC Police)**，專門防範重構與中大型修改中的死角。
*   **`/agy-studio`** 是 **全端工程師小組 (Full-Stack Squad)**，專門打硬仗、蓋新大樓。

三者相輔相成，共同打造出極度嚴謹且高效的 Agentic Coding 環境！
