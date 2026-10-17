---
name: diagnosing-bugs
description: >
  Phase 1 & 4 系統化 6 階段除錯迴圈與 Bug 根因追蹤技能（整合 diagnosing-bugs、bug-tracker 嚴重度分級與 quick-fix-patterns 常見錯誤速查）。
  觸發詞：/diagnosing-bugs, /fix, diagnose, debug this, bug-tracker, quick-fix, 除錯, 抓蟲, 效能退化.
---

# 🐛 Diagnosing Bugs — 6 階段科學除錯迴圈與根因追蹤 (3-in-1 Edition)

> **核心紀律**：先建立會變紅的回饋迴圈 (Tight Red-Capable Loop)，再提假設與修復；嚴守兩振出局硬熔斷 (`INV_VERIFY_05`：連續兩次修復未收斂即刻物理回滾並向人類 Escalation)。
> **常見錯誤速查庫**：若遇到明確框架/環境錯誤碼，可按需查閱 [`references/quick-fix-patterns.md`](references/quick-fix-patterns.md)。

---

## Phase 0 — 嚴重度分級與衝擊定位 (Bug Triage & Blast Radius)

在動手前先標記嚴重度並以 `loop_graph.py --impact` 確認呼叫端範圍：
- **🔴 P0 (Blocker)**：生產崩潰、資料損毀、資安/金流漏洞 ➔ 立即止血與建立最小重現。
- **🟠 P1 (High)**：核心功能失效、無替代路徑 ➔ 優先排入當前周期。
- **🟡 P2 (Medium)**：邊界異常、有 Workaround ➔ 與關聯模組一併收斂修復。
- **🟢 P3 (Low)**：UI 微瑕、提示文字 ➔ 順手單行修補。

---

## Phase 1 — 建立緊湊回饋迴圈 (Build a Tight Feedback Loop)

**這是除錯成敗的唯一關鍵**。在還沒做出一個「能穩定重現此 Bug 並亮紅燈」的單一指令前，**嚴禁靠肉眼讀代碼猜測原因**。

優先嘗試順序：
1. **真實邊界失敗測試**（Unit / Integration / E2E）
2. **Curl / CLI 腳本**（餵入固定 Fixture 比對輸出）
3. **Playwright 無頭瀏覽器腳本**（驅動 UI 並斷言 DOM/Console/Network）
4. **Trace 重播或最小隔離 Harness**
5. **Bisection (`git bisect run`)** 或新舊版本對比

**Phase 1 完成條件（四項全勾才准進入 Phase 2）**：
- [ ] **Red-capable**：精準觸發使用者回報的真實症狀並亮紅燈（修復後變綠燈）。
- [ ] **Deterministic**：每次執行結果一致（若為偶發 Flaky Bug，先加壓循環提高重現率至 ≥50%）。
- [ ] **Fast**：數秒內跑完。
- [ ] **Agent-runnable**：可由終端機一行指令自動執行。

---

## Phase 2 — 重現與最小化 (Reproduce & Minimise)

1. 執行迴圈確認紅燈症狀與使用者描述 100% 吻合。
2. **剝離最小化**：每次砍掉一個無關輸入、設定或步驟並重跑，直到「再拿掉任何一項，紅燈就會變綠燈」。這個最小化場景就是 Phase 5 的回歸測試雛形。

---

## Phase 3 — 提出可證偽假設 (Hypothesise — 3~5 Ranked)

在測試任何假設前，先列出 **3~5 個排序假設**，每個假設必須具備**可證偽預測**：
> 格式：「若 `<X>` 是根因，則 `<改變 Y>` 會使 Bug 消失 / `<改變 Z>` 會使症狀惡化。」

---

## Phase 4 — 單變數探針驗證 (Instrument)

- **一次只改一個變數**驗證假設。
- 精準在邊界打日誌，所有除錯日誌強制加上唯一標籤（如 `[DEBUG-a4f2]`），結束後一鍵 `grep` 清除。
- **效能退化分支**：不靠日誌，先建立基準計時（Profiler / `EXPLAIN ANALYZE` / `performance.now()`）再二分法定位。

---

## Phase 5 — 源頭修復與「先紅後綠」回歸測試 (Root-Cause Fix)

1. **Ponytail 源頭收斂 (`INV_SCOPE_03`)**：先 `grep` 共用函式所有呼叫端，在源頭修復一次，禁止散落補丁或單次暴增 >20 行無關包裝。
2. **先紅後綠 (`Fail-Before-Pass`)**：在真實公開邊界將最小重現轉為回歸測試（**嚴禁開生產測試接縫 `INV_VERIFY_04`**），確認先紅 ➔ 套用修復 ➔ 變綠。
3. **兩振出局熔斷 (`INV_VERIFY_05`)**：同一問題若連續 2 次修改仍未變綠，**嚴禁第 3 次硬修**！立即執行 `python scripts/local_guard.py --rollback` 物理回滾並向人類報告已排除的假設。

---

## Phase 6 — 清理與結構反思 (Cleanup & Post-Mortem)

- [ ] 原始完整場景重跑通過、回歸測試綠燈。
- [ ] 所有 `[DEBUG-...]` 探針與臨時腳本 100% 清除（`git diff` 乾淨）。
- [ ] 若發現架構缺乏可測試邊界或耦合過深，修復完成後交棒建議 `/improve-codebase-architecture`。
