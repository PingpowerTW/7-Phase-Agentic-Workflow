---
name: code-review
description: >
  Phase 5 全維度程式碼審查技能（整合通用審查、防禦性編程 defensive-coding、資安與密鑰掃描 security/secret-scanner、架構檢查 architecture-checklist 與 Ponytail 過度工程獵殺）。
  觸發詞：/review, code-review, 程式碼審查, defensive-coding, 資安審查, secret-scanner, architecture-checklist, 全域掃描矩陣.
---

# 🔍 Code Review — Phase 5 全維度對抗審查 (6-in-1 Unified Edition)

> **核心理念**：單次讀取變更檔案，一次完成「正確性、防禦性邊界、OWASP 資安與密鑰、架構狀態契約、Ponytail 精簡度、前端 Anti-Slop」六維度審查。
> **Confidence Gate**：僅報告 **>80% 確信** 的真實問題；跳過未修改區域的風格偏好；同類問題強制合併報告。
> **Incremental & Anti-Loop Gate**：二輪複審僅針對新提交之 Incremental Diff 驗證（最多 2 輪即強制收斂）；對已標註刻意捷徑（`ponytail:`）或已附理由豁免（Wontfix）之項目，嚴禁重複報警。

## 📚 深度參考庫 (`./references/` 按需讀取)
- [`references/defensive-coding.md`](references/defensive-coding.md)：JS/TS/Python 空值、非同步與邊界修復範本
- [`references/security-owasp.md`](references/security-owasp.md)：OWASP Top 10 與 ggshield 密鑰正則細節
- [`references/architecture-checklist.md`](references/architecture-checklist.md)：認證、狀態同步、CRUD 與快取設計清單

---

## 1. 資安與密鑰防護 (Security & Secret Scanner — CRITICAL)

- [ ] **零硬編碼機密 (Secret Scan)**：嚴禁在源碼、測試或 Log 中出現 API Key (`AIza...`, `sk-...`, `ghp_...`)、JWT Secret、DB 連線字串或私鑰；敏感設定一律走環境變數且 `.env*` 已列入 `.gitignore`。
- [ ] **認證與授權 (AuthN / AuthZ)**：受保護路由具備 Middleware；資料讀寫強制檢驗資源所有權與多租戶隔離（防範 BOLA / IDOR 越權）。
- [ ] **注入與跨站防護**：100% 參數化查詢（禁字串拼接 SQL/NoSQL）；使用者輸入長度與型別經 Schema (Zod/Pydantic/FormRequest) 嚴格驗證；輸出具備 XSS 轉義與 CSRF 保護。
- [ ] **命令行與路徑安全**：禁止將未淨化輸入傳入 `shell=True` / `exec`（防 CWE-78）；檔案路徑防範 `../` 目錄遍歷。

## 2. 防禦性編程與正確性 (Defensive Coding & Correctness — HIGH)

- [ ] **Null / Undefined 防護**：外部 API 回傳、深層物件解構與鏈式存取必須使用 Optional Chaining (`?.`) 與 Nullish Coalescing (`??`)，禁止裸取屬性。
- [ ] **陣列與數值邊界**：存取 `items[0]` 前確認非空陣列；除法防範除以 0；金額/數量防範負數、NaN 與浮點數精度遺失。
- [ ] **非同步與競態條件 (Async & Race Conditions)**：所有 `async/await` 具備明確錯誤捕捉與超時 (`timeout`) 機制；前端狀態更新與後端扣款/庫存寫入防範連點或併發 Race Condition（使用 Transaction / 冪等鍵 / AbortController）。
- [ ] **資源釋放**：檔案 Handle、DB 連線、Timer、Event Listener 與 WebSocket 於結束或組件卸載時確保關閉清理。

## 3. 架構契約與效能 (Architecture & Performance — HIGH)

- [ ] **前後端狀態與資料契約**：API Request/Response 欄位命名、錯誤格式與狀態碼前後端 100% 對齊；樂觀更新失敗具備回滾機制；表單提交期間鎖定按鈕防重複送出。
- [ ] **資料庫與查詢效能**：消除迴圈內查詢 (N+1 Query，強制 Eager Loading / Batch)；高頻查詢欄位具備複合索引；列表查詢強制分頁 (`limit/offset` 或 cursor)。
- [ ] **演算法與結構**：避免熱路徑上不必要的 $O(n^2)$ 巢狀迴圈（改用 `Map` / `Set` $O(1)$ 查找）；快取具備明確 TTL 與失效更新策略。

## 4. Ponytail 過度工程獵殺 (Simplicity & Anti-Bloat — MEDIUM)

掃描 Diff 中的非必要複雜度，能用更少代碼解決者直接標記：
- `delete:` 死代碼、未使用的彈性參數、投機性預留配置。
- `stdlib:` / `native:` 自造輪子但語言標準庫或平台原生（如 HTML/CSS/DB Constraint）已內建。
- `yagni:` 僅有單一實作的 Interface/Factory、僅轉發一行的無意義 Wrapper。
- `shrink:` 可用標準內建語法（如 `Object.fromEntries`、列表推導式）單行精簡的冗長手寫迴圈。

## 5. 測試與前端品質 (Testing & UI/UX — MEDIUM)

- [ ] **測試無接縫 (`test-audit`)**：具備真實邊界測試；**零生產接縫**（禁止為測試在生產代碼 export 私有函式或加 mock 參數）；無 15 種垃圾測試模式（無斷言、測 Mock 本身）。
- [ ] **前端 Anti-Slop (`frontend-taste-v2`)**：禁止 `#6366f1` 萬用紫藍漸層、假數據、標題亂塞 Emoji、高度跳動 `h-screen`（改用 `min-h-[100dvh]`）；互動元件具備 `min-h-[44px]` 熱區、Loading Skeleton、Error 態與 `prefers-reduced-motion` 支援。

---

## 輸出格式 (Output Format)

```markdown
## 🔍 Phase 5 全維度程式碼審查報告

### 摘要
- **審查檔案**：[檔案列表]
- **發現統計**：🔴 嚴重 (Must Fix) X | 🟡 警告 (Should Fix) X | ✂️ Ponytail 可精簡 -N 行

### 🔴 嚴重問題（資安漏洞 / 崩潰風險 / 契約破壞）
- `[檔案:行號]` **[類別]**：問題描述與觸發條件 ➔ **修復建議**

### 🟡 警告（防禦性邊界 / 效能 N+1 / 錯誤處理缺失）
- `[檔案:行號]` **[類別]**：問題描述 ➔ **修復建議**

### ✂️ Ponytail 精簡清單（過度工程獵殺）
- `[檔案:行號]`: `<delete|stdlib|native|yagni|shrink>` 欲砍除內容 ➔ 替換方案（預計淨減 `-N` 行）
```
