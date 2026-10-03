# 🤖 AI Agent 規範與工作流指南

本專案使用 `auto-snapshot` 與 `Loop Engineering` 進行持久化記憶、安全閘門與工作流管理。

## 1. 記憶自動擷取 (Auto-Capture)
每當完成階段性任務或修復 Bug 時，必須自動執行或建議使用者執行快照擷取：
- **里程碑完成 (Milestone)**: `auto-snapshot capture milestone "變更摘要" --files <檔案路徑> --tags <標籤>`
- **技術決策 (Decision)**: `auto-snapshot capture decision "決策標題" --decision "決策細節與原因"`
- **對話交接 (Handoff)**: `auto-snapshot capture handoff "進度總結" --completed <已完成> --in-progress <進行中> --pending <待辦>`

## 2. 雙軌記憶架構 (Dual-Track State)
- **微觀軌道 (`SNAPSHOT.jsonl`)**：記錄每一個 milestone、decision、handoff 的高頻歷史事件日誌。
- **宏觀軌道 (`STATE.md`)**：專案當前狀態脊椎，維護 High Priority、Watch List 與 Recent Noise。
- **同步原則**：階段交接時同步更新 `STATE.md`，使新會話能在最小 Token 開銷下取得全域狀態。

## 3. 機械化安全門禁與 Maker / Checker 分離 (Safety Gates & Verification)
- **`gate.yaml` 物理阻斷**：
  - 嚴禁自動修改 `denylist` 路徑（`.env*`, `credentials/**`, `secrets/**`, `auth/**`, `billing/**`, `migrations/**`）。
  - 單次修改超過 8 個檔案強制向人類 Escalation。
- **Maker / Checker 角色硬分離**：
  - Maker 負責產出 diff；新增測試必須符合 Authoring Gate（保護契約、可信退化、非重複覆蓋、零生產接縫）。
  - Checker (loop-verifier) 預設以 REJECT 立場接手跑真實測試、確認 scope、掃描 15 種垃圾模式，並檢驗 Bug 修復之「先紅後綠 (Fail-Before-Pass)」。
- **零非必要生產接縫 (Zero Production Seams)**：
  - 嚴禁為了寫單元測試而在生產代碼開洞（如 export private、加 optional mock 參數、wrapper）。
- **本機 System 1 決策門禁自動化 (System 1 Decision Gate)**：
  - 代碼實作完成後，Checker 優先執行本機 System 1 決策門禁審查 (`python scripts/local_guard.py --git`)。
  - 0 Token 秒級檢驗「零生產接縫」、「硬編碼憑證」與「Ponytail 階梯定位」；支援插拔式後端（相容 TypeSafe/Ollaya 規範，當前預設模型為 Laya，未啟動時自動降級至靜態規則）；若回傳 BLOCK 嚴禁結案並立即重構。
- **Git Worktree 實體隔離**：
  - 涉及架構調整或跨檔案重構任務，優先於獨立 Git Worktree 進行。

## 4. Ponytail 精簡代碼階梯 (Lazy Senior Dev Mode)
如同房間裡最偷懶的資深工程師：**最好的代碼就是從未寫過的代碼**。
寫代碼前必須停在第一個可行的階梯（先讀懂問題與全域調用流，再挑選最偷懶且正確的解法）：
1. **YAGNI (是否需要存在)**：投機性、未明確要求的需求直接略過，一行告知。
2. **現有重用 (Already in Codebase)**：優先重用專案內既有 helper、util 或 pattern，嚴禁重複造輪子。
3. **標準庫優先 (Stdlib)**：語言標準庫能做到的，一律使用標準庫。
4. **原生平台優先 (Native)**：平台或瀏覽器原生特性優先（如 `<input type="date">` 代替組件庫、CSS 代替 JS、DB Constraint 代替業務層重複校驗）。
5. **已裝套件優先 (Existing Deps)**：只用現有依賴，絕不隨意新增套件依賴。
6. **單行簡潔 (One-Liner)**：能一行解決就寫一行。
7. **最小可行 (Minimum Viable)**：只有上述皆不可行時，寫出能動的最小代碼。

- **根本修復原則 (Root Cause)**：Bug 回報常只是症狀。修改前先 grep 該共用函式的所有呼叫端，直接在源頭修復一次（收斂 Diff），避免在各呼叫處打散落補丁。
- **極簡輸出規範**：代碼優先，說明至多三行（格式：`[代碼] → 省略了: [X], 當 [Y] 時再考慮擴充`）。若未明確要求，嚴禁產出架構巡禮或長篇論述；若說明比代碼長，刪除說明。
- **刻意捷徑標記 (Debt Tracking)**：若為精簡而暫採有上限的解法（如全局鎖、O(n²) 掃描），註記 `ponytail: <極限門檻>, <升級重構路徑>`，便於納入 `STATE.md` 追蹤。
- **不可妥協之安全底線**：信任邊界輸入驗證、防資料遺失錯誤處理、系統安全性與無障礙基礎絕對不省；非平凡邏輯必須留下一段最小 runnable assert 檢驗。
