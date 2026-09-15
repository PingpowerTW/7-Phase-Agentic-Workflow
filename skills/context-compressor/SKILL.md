---
name: context-compressor
description: >
  雙向 Token 節省：輸入側壓縮 context 噪訊 + 輸出側刪廢話。
  搭配 caveman skill 使用效果最佳。
  觸發詞：壓縮 context、context 太長、節省 token、減少噪訊。
---

# Context Compressor

> 雙向 token 節省：輸入端清理噪訊 + 輸出端刪廢話。
> 搭配 `caveman` skill 使用：輸入壓縮 + 輸出壓縮，雙管齊下。

## When to Use

- 即將送入大段 code/log/doc 作為 context
- Context 長度超過 500 行
- 使用者貼了整個檔案但只問一個問題
- 重複資訊散落在多處
- 想節省 output token（配合 `/caveman` 指令）

## Core Pattern

### 1. 結構化標籤包裝 (Structural Tagging)

所有 context 輸入前加 XML-like 標籤：

```xml
<code_context file="auth.js" lines="42-80" relevance="high">
  // Only the relevant functions
</code_context>

<error_log timestamp="2026-02-21" source="console">
  Error: Cannot read property 'user' of undefined
</error_log>

<requirements priority="must-have">
  - 使用者必須能登入
  - 登入後跳轉首頁
</requirements>

<history summary="true">
  前次對話結論：auth 模組需重構
</history>
```

### 2. 噪訊刪除清單 (Noise Removal)

送入 context 前移除：

| 移除                        | 保留                  |
| --------------------------- | --------------------- |
| import 區塊（除非問題相關） | 問題相關的 import     |
| 無關的 CSS                  | 相關的 CSS selector   |
| 註解掉的舊 code             | 活躍的 code           |
| 重複的 log 行               | 第一次出現 + 出現次數 |
| 完整 package.json           | 只列相關 dependency   |

### 3. 漸進式載入 (Progressive Loading)

```
Level 1: 檔案大綱（function signatures）→ 定位問題
Level 2: 相關函式全文 → 理解邏輯
Level 3: 呼叫者/被呼叫者 → 追蹤問題根源
```

**規則：每次只載入需要的 Level，不要一次載入全部。**

### 4. Context Budget

每次回應前自問：

```
□ 這段 context 跟問題有關嗎？ → 無關就不送
□ 這段 context 能被摘要嗎？ → 能就壓縮
□ 重複的部分有嗎？ → 有就去重
□ 噪訊比例 > 30% 嗎？ → 是就先清理
```

## Integration with Skills

| 場景                    | 壓縮策略                    |
| ----------------------- | --------------------------- |
| `bug-tracker`           | 只送 error log + 相關 code  |
| `code-review`           | 只送 diff，不送整個檔案     |
| `performance-profiling` | 只送瓶頸函式 + metrics      |
| `api-design`            | 只送 endpoint 定義 + schema |

## Strategic Compact — 何時壓縮 (SelfCompact 第一性原理)

> 不只是**怎麼壓縮**，更重要的是**何時壓縮**。
> 借鑑 [SelfCompact (arXiv:2606.23525)](https://arxiv.org/abs/2606.23525) 的第一性原理自檢機制：**決策壓縮永遠由廉價閘門與 C1~N1 四元規約共同把關**。

### 1. 廉價閘門 (Cheap Gates)
在發動任何大動作總結或壓縮前，必須先滿足前置條件，避免過早或高頻耗損算力：
- **輪數閘門 (Round Gate)**：對話/工具輪數 $\ge 3$ 輪。
- **容量閘門 (Token Gate)**：當前 Context 累積超過閾值（如 $\ge 40,000$ tokens 或視窗 70%）。
- **冷卻週期 (Period Gate)**：距離上次自檢或壓縮至少間隔 2 輪以上。

### 2. 第一性原理四元檢驗規約 (C1-C2-C3-N1 Rubric)
唯有當 **C1=Y 且 C2=Y 且 C3=Y 且 N1=N** 四者皆滿足時，壓縮才是安全且有益的：

| 指標代號 | 檢驗維度 | 判定準則 (Verdict Condition) | 設計目的與防線 |
|:---|:---|:---|:---|
| **C1** | **Closed-unit** (閉環單元) | 當前對話/推論是否已完成一個段落（如 Tool 已回傳、子模組已修復、計畫已定稿）？**非思維半途中** ("Let me now check...")。 | **防中斷**：絕不在推導中途壓縮，避免丟失推論變數。 |
| **C2** | **Summarizable** (可提煉性) | 當前核心成果是否能被無損濃縮為 3~5 條具引用來源的事實/結論？若價值分散在大量除錯盲區試錯邊界中，則答 **N**。 | **防資訊稀釋**：試錯邊界未收斂前壓縮會失去排錯脈絡。 |
| **C3** | **Progress** (實質進展) | 自上次壓縮後，是否獲得了明確新事實、新代碼或推進了子目標？ | **防無效重複**：沒有實質進展則維持原狀，不平白消耗算力。 |
| **N1** | **Not-stuck** (未卡死) | 是否**未**陷入反覆嘗試失敗、重複報錯或相同工具查詢？若卡死則答 **Y**。 | **🛑 卡死阻斷**：**N1=Y 強制否決壓縮**！卡住時應診斷換策略，不可將無效嘗試美化為摘要。 |

### 3. KV Cache 友善原則 (Prefix-Preserving)
- 自檢探針（Probe）評估時，僅在既有對話尾端附加單輪評估訊息，**絕不更動前面歷史前綴**，確保伺服器端 KV Cache 100% 命中。
- 探針呼叫強制關閉工具定義 (`no_tool_calls=True`)，且針對思考型模型（如 GLM、DeepSeek-R1）關閉 Thinking (`enable_thinking=False`)，以防陷入無限思考循環。

### 4. 壓縮前必做
1. 把重要結論寫入檔案（`plan.md` / `task.md` / `spec.md`）
2. 確認 TodoWrite 已記錄待辦
3. 摘要結構只保留 **Essential Information**（確認無誤的事實），嚴格禁止推論與腦補。
4. 歷史替換結構：`[System Prompt, 初始目標/需求, 精煉摘要, 繼續執行指令]`。

## Troubleshooting

| 問題               | 解法                           |
| ------------------ | ------------------------------ |
| 壓縮後少了關鍵資訊 | 用 Level 2/3 補回              |
| 不確定什麼是噪訊   | 問：移除後問題還能被理解嗎？   |
| 長對話歷史         | 只保留最後結論，不保留中間推理 |
