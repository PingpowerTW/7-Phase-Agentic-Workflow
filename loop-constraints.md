# Loop Constraints — AI 優化 Workspace

> 本檔案定義所有 Agent 在本專案工作區執行任務時的強制性約束（Binding Constraints）。

## 1. 物理路徑限制 (Path Denylist)
- 嚴禁未經人類明確確認修改 `gate.yaml` 中列出的敏感路徑（`.env*`, `credentials/**`, `secrets/**`, `auth/**`, `billing/**`, `migrations/**`）。
- 單次改動檔案數量上限嚴格限制為 8 檔以內（`maxFiles: 8`）。

## 2. 代碼品質與測試 (Code & Quality)
- **Maker / Checker 分立**：代碼撰寫者不得自行宣告完成或核准；必須經過 Verifier / Critic / Auditor 獨立檢驗。
- **Authoring Gate（撰寫門禁四問）**：新增測試必須自證：1. 保護何種獨立契約；2. 何種可信退化會使其失敗；3. 現有覆蓋為何無法捕捉；4. 是否需求非必要生產接縫（若需要則禁止）。
- **零非必要生產接縫 (No Production Seams)**：嚴禁為了寫測試而在生產代碼中暴露 private 變數/方法、新增可選 mock 參數、注入包裝函式或全域重置鉤子。
- **先紅後綠自證 (Fail-Before-Pass)**：Bug 修復測試必須在修復前代碼上明確失敗，修復後通過；未曾失敗過的測試證明的只是 Mock，禁止合併。
- **嚴禁 15 種垃圾測試與佔位符**：不允許空斷言、`assert true`、Mock 自身被測行為、自我比較、純字串 grep、受測者自算期望值、空函式、TODO 或省略號 (`...`)。
- **外科手術式修改 (Surgical Changes)**：嚴禁順手修改不相關代碼；單一任務單一職責。
- 單一問題最多嘗試修復 3 次，若無法通過測試即刻向人類 Escalation，嚴禁陷入無效重試迴圈。

## 3. 預算與中斷控制 (Budget & Kill-switch)
- 若當日 Token 消耗達 80% 警戒線，自動降級為 Report-only 模式。
- 若 `loop-budget.md` 中 `loop-pause-all` 為 `true`，立即終止執行。
