# 專案級主動提醒設定 (Proactive Reminders)

本設定將自動覆寫或補充系統的全域規則，指示 AI 在特定階段主動給予操作建議。

> [!TIP]
> **Proactive Reminders Duty (主動提醒)**: Must use exact verbatim phrasing:
> 1. **At Task Start**:
>    - Ambiguous:「💡 *需求尚待釐清，建議可輸入 `/spec` 進入 Phase 0 規格定義模式。*」
>    - Large scale:「🤝 *當前任務規模較大(≥3檔案)，建議可輸入 `/teamwork` 啟動 5 人品質制衡軍團。*」
>    - Fullstack:「🚀 *檢測到全端開發需求，建議可輸入 `/agy-studio` 啟動 7 人團隊。*」
>    - Repo/Tool:「🛡️ *檢測到外部開源專案/工具引入需求，已啟動 Phase 0【前置殘酷審查】，在確認實質價值與風險前禁止安裝。*」
> 2. **At Bug Report (回報異常時)**:
>    - Hard Bug:「🐛 *遇到難以重現或不明的 Bug，建議輸入 `/diagnosing-bugs` 啟動嚴格的 6 階段除錯迴圈。*」
> 3. **At Code Smell / High Complexity (發現架構過於肥大或難以測試時)**:
>    - Architecture:「🏗️ *檢測到模組可能過度耦合，建議輸入 `/improve-codebase-architecture` 產出架構重構 HTML 報表。*」
>    - Test Bloat:「🗑️ *檢測到測試檔案臃腫或執行過慢，建議輸入 `/test-audit` 啟動戰役級修剪 (Campaign Mode)。*」
>    - Over-Engineering:「✂️ *檢測到可能過度工程化或依賴冗餘，建議輸入 `/ponytail-review` 進行簡化審查，或輸入 `/ponytail-audit` 進行全庫瘦身。*」
> 4. **At Impl End**:
>    - Testing:「🧪 *準備撰寫測試，建議觸發 `/tdd` 進入垂直切片的紅綠開發循環。*」
>    - Test Audit:「🧹 *檢測到新增或修改測試，建議輸入 `/test-audit` 進行門禁四問與垃圾模式稽核，確保零生產接縫。*」
>    - Code Review:「🔍 *實作已完成，建議可輸入 `/review` 進行對抗審查，或輸入 `/ui-check` 進行畫面驗收。*」
> 5. **At Milestone / Pre-Release (里程碑達成或準備上線時)**:
>    - Full Audit:「🩺 *即將發佈或達成里程碑，建議啟動『全域掃描矩陣』(defensive-coding + security + dependency) 進行深度體檢。*」
> 6. **Model Switch (跨模型防破快取)**:
>    - Post-Design:「*規劃已完成並寫入交辦文件。⚠️ 同視窗切換模型會導致 100% Cache Miss 重算，請開啟【New Session】再切換至 Flash 執行實作（並可啟動 `/caveman`）。*」
>    - Post-Impl:「*代碼實作已完成並同步狀態。⚠️ 如需切換至 Pro / Claude / Argon 進行 `/review` 審查，請開啟【New Session】避免舊對話歷史重算。*」
> 7. **At Loop Health / Handoff (巡檢或會話交接時)**:
>    - State Sync:「🔄 *已完成階段性工作，請確認 `STATE.md` 狀態脊椎已同步更新，並可隨時執行 loop-audit 評估專案健康度。*」

---

## 8. 測試重構與清掃 Prompt 範本 (Steinberger 式量化邊界指令)

當專案測試膨脹或需要瘦身時，直接套用此標準指令發送給 Agent：

```text
請調用 test-audit skill 針對 [目標目錄或模組] 執行修剪任務：
在「程式碼覆蓋率變動 <= 2%」的前提下，找出並移除 20% 最沒價值的無效測試，
並同步拔除生產代碼中僅為測試而開的接縫（test-only exports、wrapper、可選 mock 參數），追求生產行數淨減少（net-negative LOC）。
```
