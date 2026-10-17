---
name: test-audit
description: >
  Phase 4 & 5 測試驅動開發 (TDD) 與測試品質稽核全集（整合 test-audit、tdd 垂直切片紅綠循環與 testing 策略）。
  提供垂直切片 TDD 迴圈、新增測試門禁四問 (Authoring Gate)、15 種垃圾模式掃描 (Junk Patterns)、零生產接縫原則 (No Production Seams)、先紅後綠驗證與戰役級測試修剪 (Campaign Mode)。
  觸發詞：/test-audit, /tdd, test-audit, tdd, red-green-refactor, 測試稽核, 清理測試, 垃圾測試, 測試重構, 撰寫測試.
---

# 🧪 Test Audit & TDD — 垂直切片紅綠開發與測試品質稽核指南 (3-in-1 Edition)

> **核心原則**：為信心最佳化，而非為覆蓋率數字或刪除數最佳化。測試只驗證**公開邊界 (Public Seams)** 的可觀察行為；任何在「不改變外部行為的重構」下會壞掉的測試，斷言的是內部實作，必須重寫或刪除。
> **參考範例**：[`references/tests.md`](references/tests.md)（好壞測試對比）、[`references/mocking.md`](references/mocking.md)（Mock 邊界守則）。

---

## 0. 垂直切片 TDD 紅綠循環 (`/tdd` — Phase 4 撰寫新測試守則)

當開發新功能或以測試先行時，強制採用**垂直切片 (Vertical Slicing)**，嚴禁「先一口氣寫完所有測試、再寫所有實作（Horizontal Slicing）」：

1. **鎖定公開邊界 (Pre-agreed Seams)**：測試只寫在真實公開介面（API、CLI、核心模組入口），絕不測私有內部函式。
2. **一次一片（One Slice at a Time）**：寫 1 個會紅燈的測試 ➔ 寫剛好讓它綠燈的最小實作 ➔ 下一片。
3. **獨立真相來源（No Tautology）**：期望值必須來自規格或已知常數，嚴禁把受測代碼的算法抄進測試算期望值。

---

## 1. 新增測試門禁四問 (Authoring Gate)

在新增或修改任何測試前，必須先通過以下四問；**只要有一題答不出來，禁止新增此測試**：

1. **這個測試保護的是哪一個可觀察的行為、不變量或獨立契約？**
2. **什麼樣的可信退化 (Credible Regression) 會讓它失敗？**
3. **為什麼現有的測試邊界無法抓到那個失敗？**
   - 每個契約只由最強邊界的一處 Owner 守護，禁止跨層重複重播相同測試場景。
   - 優先擴充既有的 Table-driven 測試或共用 Fixture。
4. **它是否需要任何生產環境不需要的接縫（接縫/旗標/匯出/注入掛鉤）？**
   - 若答案為「是」，**強制將測試移到真實公開邊界**，絕對嚴禁為了測試在生產代碼開洞 (`INV_VERIFY_04`)。

### Bug 回歸測試的「先紅後綠」原則 (Fail-Before-Pass)
- Bug 修復測試必須在**修復前的源碼上明確失敗**，且失敗原因與回報的 Bug 完全一致；修復後在真實邊界通過。

---

## 2. 十五種垃圾測試模式檢核表 (Junk Patterns — `INV_VERIFY_02`)

Authoring Gate 拒絕符合以下模式的新測試；Audit 模式則主動獵殺既有的此類測試：

1. **無斷言覆蓋率探針**：只有執行語句，沒有斷言或只有 `expect(true).toBe(true)`。
2. **自我比較與身分複製**：拿物件跟自己比對，或對輸入值做無意義的恆等檢查。
3. **複製固定資料或清單**：將生產代碼的 export 清單或常數字典複製一份到測試中比對。
4. **原始碼/引用語法/字串精確比對**：用正則或字串檢查源碼是否包含某文字或 import。
5. **邊界已有覆蓋的私有述詞測試**：公開 API 已驗證，卻針對內部 private function 寫大量重複測試。
6. **同一契約的重複呼叫**：在不同檔案對同一邊界反覆進行相同的斷言。
7. **共用 Helper 的模組本地重播**：Helper 本身已有測試，各業務模組又各寫一套測 Helper。
8. **僅為保護測試接縫而生的測試**：代碼的存在只是為了讓測試呼叫，測試的存在只是為了覆蓋代碼。
9. **唯一呼叫者是測試的死程式碼**：生產環境無任何調用，僅被測試引用的過期函數。
10. **受測者自己算期望值**：呼叫受測函數本身來產生期望值，循環論證。
11. **Mock 實作了被斷言的行為**：Mock 寫了運算邏輯，最後測的是 Mock 而非真實代碼。
12. **假造所有回執的 Fixture**：系統應即時產生的 receipt 或狀態完全由 fixture 假造。
13. **旗標聲明測試**：只測試 config flag 是否為 `true`，未驗證啟用後的實際行為。
14. **因無關原因通過的負面控制**：錯誤處理看似通過，實際上是因為前置參數攔截報錯，沒走到受測路徑。
15. **名不副實的測試**：測試名稱宣稱完整流程，斷言卻只檢查表層屬性。

---

## 3. 保留標準與修剪原則 (Retention Bar & Net-Negative LOC)

- **必須保留**：獨立保護公開 API、網路協定、資料庫遷移、安全邊界或具備真實失敗場景的回歸測試。若既有測試失敗，優先視為**潛在產品真 Bug**。
- **修剪目標**：刪除無效測試時，**同步拔除**生產代碼中僅為測試而開的接縫（test-only exports, wrappers, mock params），追求**生產代碼淨減少 (Net-negative production LOC)**。
- **戰役模式 (Campaign Mode)**：針對大型子系統修剪時，遵循 [CAMPAIGN.md](CAMPAIGN.md) 的 8 步流水線（`Baseline → Lanes → Ledger(R/F/C/D) → Keepers → Cutover → Mutation Testing → Product Defects → Reconcile`）。
