# 🚀 Antigravity SDD & Karpathy 增強開發框架指南

> **版本**：v2.0 (Integrated Spec-Driven Development & Karpathy Behavioral Guidelines)  
> **適用環境**：Antigravity Agentic Coding Assistant  
> **核心理念**：Spec-First（規格優先）、Simplicity-First（簡潔至上）、Surgical-Changes（精準開刀）

---

## 📌 目錄

- [一、整體架構 (Architecture Overview)](#一整體架構-architecture-overview)
- [二、核心七階段協作流程 (7 Collaboration Phases)](#二核心七階段協作流程-7-collaboration-phases)
- [三、操作手冊與使用方法 (Operating Manual)](#三操作手冊與使用方法-operating-manual)
- [四、預期效果與效益 (Impact & Benefits)](#四預期效果與效益-impact--benefits)
- [五、實務演練與範例 (Examples & Walkthrough)](#五實務演練與範例-examples--walkthrough)

---

## 一、整體架構 (Architecture Overview)

本框架結合了 **GitHub Spec Kit** 的 **Spec-Driven Development (SDD)** 流程靈魂與 **Andrej Karpathy** 對於 LLM Coding 陷阱的實戰矯正方針，將其內化至 Antigravity 的大腦規則體系（`GEMINI.md`）與技能模組（`skills/`）中。

### 1.1 系統架構圖

```mermaid
flowchart TD
    User([使用者 User]) -->|觸發 /spec 或大型任務| P0[Phase 0: Spec 規格定義]
    P0 -->|產出 spec.md| P1[Phase 1: Context & Validation]
    P1 --> P2[Phase 2: Debt Audit 債務掃描]
    P2 --> P3[Phase 3: Design Proposal 方案設計]
    P3 -->|產出 implementation_plan.md| P4[Phase 4: Implementation 實作]
    
    subgraph Karpathy_Guardians [🛡️ Karpathy 行為護欄 (Auto-Loaded)]
        K1[1. 主動反駁 Push Back]
        K2[2. 零投機 No Speculation]
        K3[3. 精準開刀 Surgical Precision]
        K4[4. 困惑即停 Stop When Confused]
    end
    
    P4 -.->|受護欄約束| Karpathy_Guardians
    P4 --> P5[Phase 5: Test & Review 測試與審查]
    P5 --> P6[Phase 6: Evolve 回顧與驗證]
    P6 -->|對比 spec.md 成功標準| Done([交付完成 Finished])
```

### 1.2 核心元件說明

1. **`GEMINI.md` (全域大腦規範)**
   - 統籌 7 大協作階段（Phase 0 ~ Phase 6）。
   - 定義巨集指令（如 `/spec`, `/refactor`, `/review`）。
   - 規範 Rule #3 童子軍法則之雙模式切換（「精準開刀模式」與「重構模式」）。
2. **`karpathy-guidelines` (Skill 技能模組)**
   - 自動在所有 Coding / Refactoring / Review 任務中觸發。
   - 提供量化原則（如：200 行改 50 行重寫、禁止為一次性程式碼抽象化、無關 dead code 報告不刪除）。
3. **`spec.md` vs `implementation_plan.md` (雙文件體系)**
   - **`spec.md`**：專注於 **What & Why**（要做什麼、為什麼要做、驗收標準），不涉及具體程式碼。
   - **`implementation_plan.md`**：專注於 **How**（技術選型、檔名變更、程式碼修改計畫）。

---

## 二、核心七階段協作流程 (7 Collaboration Phases)

| Phase | 階段名稱 | 主要動作 (Action) | 產出與交付物 (Output) |
|---|---|---|---|
| **Phase 0** | **Spec (規格定義)** | 用一般語言定義 What & Why，排控範疇，寫出明確可驗證的 Success Criteria。 | `spec.md` |
| **Phase 1** | **Context & Validation** | 透過 Context Sandbox 掃描專案現有結構與相依性，確認無模糊假設。 | Requirement Checklist |
| **Phase 2** | **Debt Audit** | 靜態掃描影響範圍內的 Code Smells (🔴🟡🟢)，評估潛在技術債。 | Debt Summary |
| **Phase 3** | **Design Proposal** | 規劃技術架構與修改檔案清單，提出 Trade-off，請求用戶核准。 | `implementation_plan.md` |
| **Phase 4** | **Implementation** | 進行程式碼實作，遵守 Karpathy 四大護欄與「精準開刀」原則。 | Source Code + Diff Blocks |
| **Phase 5** | **Test & Review** | 執行自動化測試、對抗性審查 (Adversarial Review) 及 Code Walkthrough。 | Test Results + Walkthrough |
| **Phase 6** | **Evolve (回顧演進)** | 對照 `spec.md` 的 Success Criteria 逐項驗收，將 Lessons Learned 寫入經驗庫。 | Updated `spec.md` + ADR |

---

## 三、操作手冊與使用方法 (Operating Manual)

### 3.1 常用巨集指令 (Macro Commands)

你在 Chat 視窗中隨時可以使用以下斜線指令引導 Agent 進入專用流程：

*   **`/spec`**：**進入 Phase 0 規格定義模式**
    *   *時機*：新功能開發、大型任務開工、或當你腦海中只有概念尚未想清楚實作細節時。
    *   *效果*：Agent 會主動以結構化問答引導你產出 `spec.md`。
*   **`/refactor`**：**觸發架構重構模式**
    *   *時機*：需要清理技術債或優化架構時。
    *   *效果*：Rule #3 自動從「精準開刀模式」切換為「積極清理模式」，全域清理死碼與重複邏輯。
*   **`/review`**：**對抗性代碼審查**
    *   *時機*：準備提交 Pull Request 或完成大功能實作時。
    *   *效果*： Agent 會先以「暴躁資深工程師」視角無情挑剔程式碼，再給出具體的平衡建議。
*   **`/fix`**：**深度除錯模式**
    *   *時機*：發生複雜的 Runtime Error、Stack Trace 或死鎖時。
    *   *效果*：自動分析日誌，隔離根本原因，不盲目貼補丁。

---

### 3.2 不同開發情境的最佳實踐 SOP

#### 情境 A：開發全新大型功能 (> 3 個檔案)
1. 輸入 **`/spec`** 告訴 Agent 你的需求點子。
2. Agent 會產出 **`spec.md`**，包含「要做什麼」與「Success Criteria」。
3. 確認 Spec 後，Agent 自動進入 Phase 1~3 產出 **`implementation_plan.md`**。
4. 你輸入「核准」後，Agent 執行 Phase 4 實作與 Phase 5 測試。
5. 實作完成後， Agent 執行 Phase 6 對照 `spec.md` 逐項點收。

#### 情境 B：日常小修正 / 小需求 (1~2 個檔案)
1. 直接口述需求（例如：「幫我在登入頁面加上 Remember Me 選項」）。
2. Agent **自動跳過 Phase 0**，採用 Karpathy 「精準開刀」原則直接進入最小程式碼修改。
3. 僅修改必要檔案，不更動無關的格式或鄰近註解。

#### 情境 C：代碼重構與技術債清理 (Refactoring & Tech Debt Cleanup)
1. 輸入 **`/refactor`** 啟動重構模式（例如：「`/refactor 幫我清理 userService.ts 的重複邏輯`」）。
2. **Rule #3 自動解鎖**：童子軍法則從「精準開刀（只報不刪）」切換為「積極清理模式」。
3. Agent 執行全域 SOLID / DRY 掃描，產出結構化重構計畫書。
4. 用戶確認重構範圍後，Agent 安全安全小步替換代碼，並移除驗證過確認無用的死碼與冗餘註解。

#### 情境 D：深度除錯與緊急 Bug 排查 (Deep Debugging & Emergency Fix)
1. 發生錯誤時輸入 **`/fix`** 並貼上 Error Log 或 Stack Trace（例如：「`/fix 登入時報 NullPointerException`」）。
2. Agent 觸發 `debug-pro` Skill，啟動「先假設，後驗證」流程，絕不隨意猜測貼補丁。
3. 透過 Sandbox 靜態或動態執行隔離根本原因（Root Cause）。
4. 提出至少 2 種修復方案比較其 Trade-offs（如：臨時 Hotfix vs 根本修復），獲准後才動手修改。

#### 情境 E：程式碼對抗性審查與發佈前檢查 (Code Review & Release)
1. 功能開發完成後輸入 **`/review`**。
2. Agent 啟動雙重角色審查：
   - 😈 **暴躁資深工程師**：無情挑剔安全性漏洞、N+1 查詢、無效 catch、缺乏邊界檢查等問題。
   - 😇 **理性架構師**：整理出 Must-Fix (🔴)、Should-Fix (🟡)、Nice-to-Have (🔵) 的優先級分級報告。
3. 搭配觸發 `release-checklist` 技能，檢查版本號、Changelog 與 Rollback 備案。

#### 情境 F：第三方 API / 金流 / 外套件串接 (Third-Party API & Payment)
1. 當告訴 Agent「串接藍新金流/綠界 API」或「整合 OpenAI SDK」時。
2. Agent **強制觸發 `api-connector` 與 `security-best-practices` Skill**。
3. 檢視 API 密鑰管理（絕不寫死在代碼中，要求放置於 `.env`）。
4. 針對網路異常、逾時、簽章驗證失敗等邊界條件建立完備的防禦性機制。

#### 情境 G：新專案接手與架構探索 (Project Onboarding & Exploration)
1. 剛開啟新 Repo 時輸入 **`/onboard`**。
2. Agent 自動調用 Context-Mode Sandbox 执行 `ctx_batch_execute` 靜態掃描。
3. 在不浪費大幅 Token 的情況下，快速解析專案目錄、依賴套件、環境變數與核心進入點。
4. 產出專案導向地圖，並自動與現有 `GEMINI.md` 對齊防護規範。

#### 情境 H：UI/UX 視覺驗收與前端互動檢查 (UI/UX Inspection)
1. 當修改前端畫面或樣式時，輸入 **`/ui-check`**。
2. Agent 自動喚醒 Browser Subagent，使用 Playwright 開啟本機網頁。
3. 自動截圖並進行視覺稽核 (UX Audit)，檢查響應式排版 (Responsive)、字體對比度與按鈕懸停效果。

---

## 四、預期效果與效益 (Impact & Benefits)

本框架直接解決了 Andrej Karpathy 提出的 **LLM Coding 4 大常見陷阱**：

| Karpathy 指出的 LLM 痛點 | 本框架對應之防禦機制 | 預期量化與質化效益 |
|---|---|---|
| **1. 盲目假設與隱藏困惑**<br>*(AI 默默選了一個錯誤解讀就一路寫下去)* | **Think Before Coding & Stop When Confused**<br>要求 Agent 在實作前提出假設；遇到歧義強制停下來詢問。 | 減少 **80%** 因需求誤解造成的無用功重寫。 |
| **2. 過度工程化與過度抽象**<br>*(100 行能寫完的寫了 1000 行)* | **Simplicity First & 量化重寫規則**<br>禁止為一次性代碼建 Class；若 50 行能完成但寫了 200 行必須重寫。 | 減少 **40%~60%** 膨脹程式碼與無用抽象層。 |
| **3. 亂動無關代碼與副作用**<br>*(順手修改/刪除不了解的註解與隔壁程式碼)* | **Surgical Changes (精準開刀)**<br>非 `/refactor` 模式下，無關死碼僅報告不刪除；嚴格鎖定修改範圍。 | 避免 **90%** 意外引發的跨模組 Regression Bug。 |
| **4. 缺乏驗證與偏離目標**<br>*(寫完就宣稱完成，實際根本不能跑)* | **Spec Success Criteria & Verify with Tests**<br>Phase 0 定義成功標準，Phase 5/6 強制自動化測試與回顧驗證。 | 達到 **100%** 可驗收交付，消除「以為做完了」的幻覺。 |

---

## 五、實務演練與範例 (Examples & Walkthrough)

### 範例 1：Karpathy 主動反駁 (Push Back) 實況

#### ❌ 傳統 LLM 容易出現的行為：
> **用戶**：「幫我寫一個複雜的抽象設計模式，建立一個 `UserFactoryManagerProvider` 來處理多種用戶類型的建立。」  
> **LLM**：「沒問題！這是為您建立的 300 行 Factory, Provider, Interface 範例...」（明明整個專案只有兩種 User）

#### ✅ 套用本框架後 Agent 的行為：
> **Agent**：`[Phase: Design Proposal]`  
> ⚠️ **主動反駁 (Push Back)**：盤點專案現況後發現，目前系統僅有 `Admin` 與 `Member` 兩種角色。建立 `UserFactoryManagerProvider` 屬於**過度工程 (Overengineering)**。  
> 建議直接使用簡單的 Factory Function 處理即可（約 30 行）。若您未來擴展至 5 種以上角色，我們再行重構。您是否同意改採簡化方案？

---

### 範例 2：精準開刀 (Surgical Precision) 程式碼修改對比

當要求 Agent 修改 `userService.ts` 中的 `login` 邏輯時：

```diff
  // userService.ts
  export async function login(credentials) {
    const user = await auth.validate(credentials);
+   // [ADDED] 紀錄最後登入時間 (精準修改)
+   await db.users.update(user.id, { lastLogin: new Date() });
    return user;
  }

- // 傳統 LLM 常常會「順便」幫你改寫或刪除底下它看不懂的舊邏輯/註解（本框架嚴格禁止！）
  export function legacyHelper() {
    // DO NOT REMOVE: Needed for v1 fallback
    return process.env.V1_SECRET;
  }
```

> **Agent 的回覆**：
> `[Phase: Implementation]`  
> 已精準修改 `login` 函式完成 `lastLogin` 寫入。  
> 💡 *注意*：檢查過程中發現 `legacyHelper()` 似乎是未使用的死碼，遵照精準開刀原則，我**已為您標記報告但不予刪除**。若需清理請執行 `/refactor`。

---

### 範例 3：`/spec` 產出的 `spec.md` 範例

當輸入 `/spec 幫我做一個匯出 CSV 功能` 時，Agent 產出的 `spec.md`：

```markdown
# Spec: 用戶資料 CSV 匯出功能

## 🎯 What (做什麼)
在用戶管理後台介面新增一個「匯出 CSV」按鈕，允許管理員點擊後將當前篩選條件下的用戶清單下載為 `.csv` 檔案。

## 💡 Why (為什麼)
營運團隊需要將用戶名單匯入第三方 Email 行銷工具中，目前手動複製非常耗時。

## ✅ Success Criteria (成功標準)
- [ ] 點擊「匯出 CSV」按鈕後 3 秒內觸發瀏覽器下載。
- [ ] CSV 包含欄位：`User ID`, `Email`, `Role`, `Created Date`。
- [ ] UTF-8 BOM 編碼（確保 Excel 開啟中文不亂碼）。
- [ ] 若當前列表無資料，按鈕顯示 Disabled 並停用點擊。

## 🚫 Out of Scope (本次不做)
- 不支援背景非同步郵件寄送大檔。
- 不支援自訂匯出欄位選擇。

## ❓ Open Questions
1. 超過 10,000 筆資料時是否要限制單次匯出上限？（假設：預設限制 5,000 筆）
```

---

## 💡 總結

這套框架透過將 **Karpathy 準則** 作為日常開發的「護欄」，並將 **Spec Kit SDD** 作為大型任務的「導航儀」，大幅提升了 AI Pair Programming 的嚴謹度與可預測性。

你現在即可在日常開發中享受這套強化架構帶來的開發效率！
