# 📘 全自動整合啟動與調度切換手冊 (Auto-Trigger & Switching Playbook)

> **版本**：v1.0  
> **目的**：說明 Antigravity 體系下各模式與指令的啟動時機、自動調度機制、以及 Agent 主動提醒切換的規範。

---

## 📌 目錄

- [一、整體啟動與調度生命週期](#一整體啟動與調度生命週期)
- [二、什麼時候發動哪一個？(模式發動決策矩陣)](#二什麼時候發動哪一個-模式發動決策矩陣)
- [三、Agent 主動提醒與切換對照表](#三agent-主動提醒與切換對照表)
- [四、完整開發生命週期演練範例](#四完整開發生命週期演練範例)

---

## 一、整體啟動與調度生命週期

在我們的架構中，開發生命週期分為 7 個 Phase。 Agent 會在相應節點**主動評估並提示**你切換模式或模型：

```mermaid
flowchart TD
    Start([1. 收到任務需求 Request]) --> CheckReq{需求明確嗎？}
    
    CheckReq -- 模糊/概念階段 --> RemindSpec[💡 提醒：建議輸入 /spec]
    RemindSpec --> P0[Phase 0: Spec (spec.md)]
    
    CheckReq -- 明確需求 --> EvalScale{評估任務規模}
    P0 --> EvalScale
    
    EvalScale -- 1~2 個檔案小改動 --> SingleMode[預設模式: SDD + Karpathy 單 Agent]
    EvalScale -- ≥3 檔案 / 模組重構 --> RemindTeamwork[🤝 提醒：建議輸入 /teamwork]
    EvalScale -- DB+Backend+Frontend --> RemindAGY[🚀 提醒：建議輸入 /agy-studio]
    
    RemindTeamwork --> TeamworkRun[執行 5 人制衡軍團]
    RemindAGY --> AGYRun[執行 7 人全端團隊]
    SingleMode --> SinglePlan[Phase 1~3 Plan 規劃]
    
    SinglePlan --> RemindFlash[⚡ 提醒：切換至 Gemini Flash 模型]
    TeamworkRun --> RemindFlash
    AGYRun --> RemindFlash
    
    RemindFlash --> P4[Phase 4: Implementation 實作]
    P4 --> P5[Phase 5: Test & Review 測試]
    
    P5 --> RemindPro[🔍 提醒：切換至 Pro/Claude 模型 + 提示 /review 或 /ui-check]
    RemindPro --> P6[Phase 6: Evolve (點收與經驗歸檔)]
    P6 --> Finish([交付完成 Delivery])
```

---

## 二、什麼時候發動哪一個？(模式發動決策矩陣)

| 開發場景 | 發動的模式 / 指令 | 啟動機制 | Agent 行為與背後動機 |
|---|---|---|---|
| **剛有構想、需求尚不明確** | **`/spec`** (Phase 0) | **手動** 或 **Agent 主動提示** | 避免直接寫程式碼導致白做工，先用問答確定 **What & Why** 與 Success Criteria。 |
| **日常小改動 (1~2 檔案)** | **預設模式** (SDD + Karpathy) | **全自動** (預設常駐) | 採用 Karpathy **精準開刀**，只改相關部分，不浪費 Token，不濫發子代理人。 |
| **大型改動 (≥3 檔案 / 模組重構)** | **`/teamwork`** (5人軍團) | **自動觸發** 或 **Agent 主動提示** | 開啟 Read-Only 子代理人對抗機制，由 Critic 找壓力點、Auditor 抓假測試，確保零瑕疵。 |
| **全端開發 (DB + API + UI)** | **`/agy-studio`** (7人團隊) | **自動觸發** 或 **Agent 主動提示** | 召喚 DB 架構師、後端 Lead 與前端 Master 專工分詞，實現無縫全端串接。 |
| **遇到複雜 Error / 死鎖** | **`/fix`** (深度除錯) | **手動** | 觸發 `debug-pro` Skill，先建立假設再到 Sandbox 驗證，提出方案 Trade-offs。 |
| **程式碼審查與發佈準備** | **`/review`** (對抗審查) | **手動** 或 **Agent 主動提示** | 啟動資深工程師與理性架構師雙重對抗審查，清理 Must-Fix 漏洞。 |
| **前端畫面排版與互動驗收** | **`/ui-check`** (視覺驗收) | **手動** 或 **Agent 主動提示** | 喚醒 Browser Subagent 使用 Playwright 進行網頁截圖與 RWD 視覺稽核。 |

---

## 三、Agent 主動提醒與切換對照表

現在，Agent 已經內建了 **「主動提醒義務」**。當你在對話中看到 Agent 回覆尾部出現提醒標記時，你可以照著提示進行操作：

### 1. 任務起點 / 需求評估階段 (Phase 0 ~ 1)

*   **當 Agent 偵測到需求模糊時**：
    > 💬 **Agent 提示**：`💡 需求尚待釐清，建議可輸入 /spec 進入 Phase 0 規格定義模式。`  
    > 👉 **你可以做的動作**：直接輸入 `/spec`，Agent 會開始問你需求細節並建立 `spec.md`。
*   **當 Agent 偵測到修改規模大 (≥3 個檔案) 時**：
    > 💬 **Agent 提示**：`🤝 當前任務規模較大(≥3檔案)，建議可輸入 /teamwork 啟動 5 人品質制衡軍團。`  
    > 👉 **你可以做的動作**：輸入 `/teamwork`，Agent 會召喚 Explorer、Worker、Reviewer、Critic、Auditor 團隊。
*   **當 Agent 偵測到全端需求時**：
    > 💬 **Agent 提示**：`🚀 檢測到全端開發需求，建議可輸入 /agy-studio 啟動 7 人團隊。`  
    > 👉 **你可以做的動作**：輸入 `/agy-studio`， Agent 會自動繪製全端架構並啟動專用團隊。

---

### 2. 規劃完成 / 準備實作階段 (Phase 3 結束)

*   **當規劃與 `implementation_plan.md` 完成時**：
    > 💬 **Agent 提示**：`規劃已完成並生成交辦文件，建議切換至 Gemini 3.5 Flash 執行實作。`  
    > 👉 **你可以做的動作**：在 IDE 的 Model 選擇器中將模型切換為 **Flash** (快速、低成本執行實作)，然後輸入「核准實作」。

---

### 3. 實作完成 / 準備測試審查階段 (Phase 4 結束)

*   **當代碼實作完成，本機測試通過時**：
    > 💬 **Agent 提示**：`代碼實作已完成，建議切換至 Gemini 3.1 Pro / Claude 進行 Review 審查。🔍 實作與測試已完成，建議可輸入 /review 進行對抗審查，或輸入 /ui-check 進行畫面驗收。`  
    > 👉 **你可以做的動作**：
    > 1. 將模型切換回 **Pro** 或 **Claude** (具備更強推理能力進行審查)。
    > 2. 輸入 `/review` (若為後端/邏輯) 或 `/ui-check` (若為前端畫面)。

---

## 四、完整開發生命週期演練範例

假設你跟 Agent 說：**「我想做一個線上會員訂閱付費系統」**

1. **Step 1 (需求評估)**：
   * Agent 回覆分析：「這個需求包含金流與資料庫... 🚀 *檢測到全端開發需求，建議可輸入 `/agy-studio` 啟動 7 人團隊。*」
2. **Step 2 (啟動模式)**：
   * 你輸入 `/agy-studio`。
   * Agent 開始進入 Phase 0/1 規劃全端架構圖與計畫。
3. **Step 3 (模型切換提示 1)**：
   * 規劃完成，Agent 提示：「*規劃已完成並生成交辦文件，建議切換至 Gemini 3.5 Flash 執行實作。*」
   * 你切換到 **Flash 模型** 並回覆「核准」。
4. **Step 4 (實作與對抗測試)**：
   * 7 人團隊子代理人完成 DB Schema、Backend API、Frontend UI 撰寫與 Auditor 審計。
5. **Step 5 (模型切換提示 2)**：
   * 實作完成，Agent 提示：「*代碼實作已完成，建議切換至 Pro 模型。🔍 建議可輸入 /ui-check 進行畫面驗收。*」
   * 你切換到 **Pro 模型** 並輸入 `/ui-check`。
6. **Step 6 (演進點收)**：
   * Browser Subagent 截圖驗收成功，Agent 執行 Phase 6 Evolve 結案！
