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

## Strategic Compact — 何時壓縮

> 不只是**怎麼壓縮**，更重要的是**何時壓縮**。

### ✅ 應該壓縮的時機

| 時機                           | 原因                                    |
| ------------------------------ | --------------------------------------- |
| 研究/探索後 → 實作前           | 研究 context 很大，但計畫才是實作需要的 |
| 完成 milestone 後 → 下個階段前 | 給新階段乾淨的 context                  |
| Debug 後 → 繼續功能前          | debug traces 污染不相關的工作           |
| 嘗試失敗的方案後 → 換方案前    | 清除 dead-end 推理                      |

### ❌ 不應該壓縮的時機

| 時機                   | 原因                             |
| ---------------------- | -------------------------------- |
| 實作到一半             | 會失去變數名、檔案路徑、部分狀態 |
| 正在處理多檔案關聯修改 | context 間有依賴                 |

### 壓縮前必做

1. 把重要結論寫入檔案（plan.md / task.md）
2. 確認 TodoWrite 已記錄待辦
3. 把口頭約定的偏好寫入 rules/config

## Troubleshooting

| 問題               | 解法                           |
| ------------------ | ------------------------------ |
| 壓縮後少了關鍵資訊 | 用 Level 2/3 補回              |
| 不確定什麼是噪訊   | 問：移除後問題還能被理解嗎？   |
| 長對話歷史         | 只保留最後結論，不保留中間推理 |
