---
name: test-audit
description: "測試品質與架構稽核技能。在撰寫、修改、審查或清理測試時調用。提供新增測試的門禁四問 (Authoring Gate)、15 種垃圾模式掃描 (Junk Patterns)、零生產接縫原則 (No Production Seams)、先紅後綠驗證 (Fail-Before-Pass) 以及戰役級模組測試修剪 (Campaign Mode)。觸發詞：/test-audit, test-audit, 測試稽核, 清理測試, 垃圾測試, 測試重構."
---

# Test Audit — 測試品質與架構稽核指南

> 本技能源自 OpenClaw 刪除 40 萬行無效測試的核心工程實踐。
> 核心原則：**為信心最佳化，而非為刪除數最佳化（Optimize for confidence, not deletion count）**。
> 一個在「不改變外部行為的重構」下會壞掉的測試，斷言的是實作而非行為，必須重寫或刪除。

---

## 1. 撰寫門禁 (Authoring Gate)

在新增或修改任何測試前，開發者或 Agent 必須先回答以下四個問題；**只要有一題答不出來，禁止新增此測試**：

1. **這個測試保護的是哪一個可觀察的行為、不變量或獨立契約？**
   *(What observable behavior, invariant, or independent contract does it protect?)*
2. **什麼樣的可信退化會讓它失敗？**
   *(What credible regression makes it fail?)*
3. **為什麼現有的測試邊界無法抓到那個失敗？**
   *(Why does existing coverage not already catch that failure?)*
   - 每個契約只由最強邊界的一處 Owner 守護，禁止跨層重複重播相同測試場景。
   - 優先擴充既有的 Table-driven 測試或共用 Fixture，嚴禁複製貼上近乎重複的測試檔。
4. **它是否需要任何生產環境不需要的接縫（接縫/旗標/匯出/注入掛鉤）？**
   *(Does it need a production seam that no production caller needs?)*
   - 若答案為「是」，**強制將測試移到真實公開邊界**，絕對嚴禁為了測試在生產代碼開洞。

### Bug 回歸測試的「先紅後綠」原則 (Fail-Before-Pass)
- Bug 修復測試必須在**修復前的源碼上明確失敗**，且失敗原因與回報的 Bug 完全一致；修復後在真實邊界通過。
- 一個從未真正失敗過的測試，證明的只是 Mock 的行為，而非 Bug 的修復。
- 每個 Bug 僅在所屬的 Owner 邊界建立一個回歸測試，禁止在它跨越的每一層代碼重複重播。

---

## 2. 十五種垃圾測試模式檢核表 (Junk Patterns)

Authoring Gate 拒絕符合以下模式的新測試；Audit 模式則主動獵殺既有的此類測試：

1. **無斷言覆蓋率探針 (Assertion-free coverage probes)**：只有執行語句，沒有斷言或只有 `expect(true).toBe(true)`。
2. **自我比較與身分複製 (Self-comparisons and identity copiers)**：拿物件跟自己比對，或對輸入值做無意義的恆等檢查。
3. **複製固定資料或清單 (Copied fixtures, inventories, manifests, or export lists)**：將生產代碼的 export 清單或常數字典複製一份到測試中比對。
4. **原始碼/引用語法/字串精確比對 (Exact source, import, or string greps)**：用正則或字串檢查代碼是否包含某特定文字或 import，把程式文本當作行為。
5. **邊界已有覆蓋的私有述詞測試 (Private predicate or call-shape tests duplicated at real boundaries)**：外部公開 API 已驗證，卻針對內部 private function 寫了大量重複測試。
6. **同一契約的重複呼叫 (Duplicate invocations of the same contract)**：在不同檔案對同一邊界反覆進行相同的斷言。
7. **共用 Helper 的模組本地重播 (Provider-local replays of shared helpers)**：Helper 本身已有測試，各業務模組又各寫一套測 Helper。
8. **僅為保護測試接縫而生的測試 (Tests whose only purpose is preserving test-only exports, globals, or wrappers)**：代碼的存在只是為了讓測試呼叫，測試的存在只是為了覆蓋代碼。
9. **唯一呼叫者是測試的死程式碼 (Dead production code whose only callers are tests)**：生產環境中根本沒人生產調用，僅被測試引用的過期函數。
10. **受測者自己算期望值 (Expected values produced by the helper or renderer under test)**：期望值不是靜態定義，而是呼叫受測函數本身來產生，循環論證。
11. **Mock 實作了被斷言的行為 (Mocks that implement the asserted behavior)**：Mock 物件寫了複雜運算邏輯，測試最後測的是 Mock 而非真實邏輯；或拿同一套 Mock 假扮不同 API。
12. **假造所有回執的 Fixture (Fixtures that supply receipts/ordering the owner should produce)**：原本應由系統即時產生的 receipt、序號或 callback，全部由測試 fixture 假造並直接通過。
13. **旗標聲明測試 (Capability tests that restate declared flags)**：只測試某個 config flag 是否為 `true`，完全未驗證旗標啟用後的實際交付。
14. **因無關原因通過的負面控制 (Negative controls passing for an unrelated reason)**：錯誤處理看似通過，實際上是因為其他無關的攔截器報錯，根本沒走到受測路徑。
15. **名不副實的測試 (Names or fixtures that promise more than the input exercises)**：測試名稱冠冕堂皇（例如 `testRetiresWindow`），斷言卻只檢查視窗屬性未變。

---

## 3. 保留標準 (Retention Bar)

符合以下條件的測試必須保留，禁止盲目刪除：
- 獨立強制執行公開 API、外掛 SDK、網路協定、設定、資料庫遷移、儲存、安全邊界、預設值或架構契約。
- 呼叫順序本身即是可觀察業務行為。
- 具備真實可信失敗場景的 Bug 回歸測試。
- 原始碼檢查是成本最低的獨立防護者（例如使用者面對的金鑰或路徑變更）。
- **基準失敗處置**：若既有測試失敗，優先視為**潛在的產品真 Bug**，重現並修復生產代碼，而非直接刪除測試。

---

## 4. 稽核修改原則 (Edit Shape)

- 追求**生產代碼淨減少 (Net-negative production LOC)**。
- 刪除無效測試時，**同步拔除**生產代碼中僅為測試而開的接縫（test-only exports, wrappers, injection parameters, reset hooks）。
- 嚴禁為了「增加刪除行數」而將有價值的邊界測試刪除。

---

## 5. 戰役模式 (Campaign Mode)

當需要針對整套子系統進行大規模測試修剪時，必須遵循 [CAMPAIGN.md](CAMPAIGN.md) 的 8 步流水線：
`Baseline (基準) → Lanes (車道) → Ledger(R/F/C/D) (唯讀手帳) → Keepers (指定守護者) → Cutover (切除與拔接縫) → Mutation Testing (突變驗證) → Product Defects (修復真Bug) → Reconcile (合流交接)`。
