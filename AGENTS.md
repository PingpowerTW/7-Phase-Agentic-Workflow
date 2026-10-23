# 🤖 AI Agent 規範與工作流指南（治理規則）

本專案使用 `auto-snapshot` 與 `Loop Engineering` 進行持久化記憶、安全閘門與工作流管理。記憶與快照規則請參閱 `.agents/AGENTS.md`。

## 1. 機械化安全門禁與 Maker / Checker 分離 (Safety Gates & Verification)
- **`gate.yaml` 物理阻斷**：
  - 嚴禁自動修改 `denylist` 路徑（`.env*`, `credentials/**`, `secrets/**`, `auth/**`, `billing/**`, `migrations/**`）。
  - 單次修改超過 8 個檔案強制向人類 Escalation。
- **分層宣告與模組級 AGENTS.md (INV_ARCH_01，建議級)**：
  - `layers.json` 宣告單向階層（L0 治理 → L1 核心腳本 → L2 技能與記憶 → L3 應用），修改時應避免向上與環狀依賴；**目前無自動檢查器**，由 Reviewer 人工核對。
  - 核心子目錄建議配備模組級 `AGENTS.md`（現有：`scripts/AGENTS.md`）。
- **Git 時光機安全地基 (INV_SAFE_04)**：
  - 任何寫入操作前，工作區必須受 Git 版本控制保護且具備安全 baseline commit；未受 Git 保護時嚴禁動手改代碼。
- **兩振出局與秒級物理回滾 (Two-Strike Circuit Breaker, INV_VERIFY_05) 與 Reflexion 口語反思閉環**：
  - **Strike 1 (初次未收斂)**：嚴禁未分析即盲目向前修補。必須套用 `LAST_ATTEMPT_AND_REFLEXION` 策略，輸出三段式結構化口語反思：`[Reflexion] 錯誤假設: <原因> | 根因定位: <機制> | 修正策略: <Ponytail最小收斂路徑>`，帶著口語反思進入第 2 次嘗試。
  - **Strike 2 (兩振出局)**：若連續兩次修復未收斂，**嚴禁第 3 次向前修補**。
  - 必須在 0.05 秒內執行物理回滾 (`python scripts/local_guard.py --rollback` 或 `git restore . && git clean -fd`)，徹底抹除失敗代碼與毒化上下文。
  - 回滾時以 `python scripts/local_guard.py --rollback --reflexion "<反思>"` 傳入反思，腳本會寫入 `.agent/eval_incidents.jsonl` 與 `.agent/SNAPSHOT.jsonl` (type: `failure_reflection`)；`STATE.md` Watch List 需**手動**補記，隨後立即向人類 Escalation。
- **複雜度單調性防線 (Complexity Monotonicity, INV_SCOPE_03)**：
  - 單次 Bug 修復之有效 Diff 必須符合 Ponytail 收斂原則；禁止單次修復代碼暴增（>20行或>2檔案）或新增非必要包裝層。
- **Maker / Checker 角色硬分離**：
  - Maker 負責產出 diff；新增測試必須符合 Authoring Gate（保護契約、可信退化、非重複覆蓋、零生產接縫），嚴禁自行宣稱「測試已通過」或打勾結案。
  - Checker (loop-verifier) 預設以 REJECT 立場接手跑真實測試、確認 scope、掃描 15 種垃圾模式，並檢驗 Bug 修復之「先紅後綠 (Fail-Before-Pass)」，零容忍假測試與佔位符。
- **零非必要生產接縫 (Zero Production Seams)**：
  - 嚴禁為了寫單元測試而在生產代碼開洞（如 export private、加 optional mock 參數、wrapper）。測試必須位於真實邊界。
- **本機 System 1 決策門禁自動化與防偽執行收據 (System 1 Decision Gate & Execution Receipt, INV_VERIFY_07)**：
  - 代碼實作完成後，優先執行本機 System 1 決策門禁審查 (`python scripts/local_guard.py --git`)。
  - 0 Token 秒級檢驗「零生產接縫」、「硬編碼憑證」與「Ponytail 階梯定位」；支援插拔式後端（相容 TypeSafe/Ollaya 規範，當前預設模型為 Laya，未啟動時自動降級至靜態規則）；若回傳 BLOCK 嚴禁結案並立即重構。
  - **防偽收據與零腦補鐵律（專治 Flash 虛假回報，INV_VERIFY_07）**：
    1. **結案必貼真實收據**：凡宣稱「已完成修改 / 測試通過 / 門禁合規」，回覆結尾**必須原封不動貼上** `local_guard.py --git` 實際輸出的 `🧾 [GUARD-RECEIPT] HEAD=... | Dirty=... | Gate=PASS | Latency=...` 簽章與真實測試結果行；未執行指令或偽造收據視為嚴重違規。
    2. **RTK `ok` 零腦補原則**：當指令被 RTK 壓縮為 `ok`（如 `git commit`、`git push`）時，**必須如實回報 `ok`**，或執行 `git log -n 1 --oneline` / `rtk proxy <cmd>` 查驗真實輸出；**嚴禁在看到 `ok` 後自行編造假 Commit Hash、假差異行數或假測試統計**。
    3. **先讀後標 (Read-Before-Claim)**：凡在回覆中標註 `[檔案](file:///...#L行號)` 或引用函數名，該回合或本會話內**必須有實際 `read_file` / `grep` 紀錄**，嚴禁憑印象盲猜行號或捏造不存在之 API。
    4. **Flash 認知半徑限制**：使用 Flash 模型執行實作時，單回合最多修改 `≤ 3` 個檔案，且每次 `edit_file` / `write_file` 後必須緊接 `run_command` 驗證。
- **Git Worktree 實體隔離**：
  - 涉及架構調整或跨檔案重構任務，優先於獨立 Git Worktree 進行。

## 2. Ponytail 精簡代碼階梯 (Lazy Senior Dev Mode)
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
- **代碼探索前導與 Token 止血紀律**：
  - 探索不熟悉的程式碼前，先執行 `python scripts/loop_graph.py --map --focus <目標檔案>`，依地圖決定要讀哪些檔案，避免整檔盲讀。
  - **強制平行工具呼叫 (Parallel Tool Calls)**：同階段可併發的讀檔、搜尋或驗證，必須在**單一回合內同時呼叫**，嚴禁分多步串行呼叫（消除推理模型每步 2k~4k Thinking 轉入下一步 Input 之雙重複利稅）。
  - **精準讀檔邊界**：讀原始碼應指定 `StartLine`/`EndLine`（單次 ≤200 行）；**嚴禁對 `.jsonl` / `.log` / 巨型 dump 檔使用 `view_file`**（避免單次頂滿 46KB 塞爆上下文）；在 Windows PowerShell 避免使用複雜巢狀引號之單行 `python -c`。

## 3. 開源專案、新工具與 Skill 引入殘酷審查門禁 (Open-Source & Skill Pre-Flight Gate)
凡使用者提供外部 GitHub 連結、套件、新工具或 **Skill / Plugin / Rule 規則集** 要求「分析、整合、改寫或引入」時，**嚴禁直接進入 clone、安裝或寫入 `~/.gemini/config/skills/` 獨立全域技能階段**。必須優先於第 1 個回合出具《前置殘酷審查報告》，在獲得使用者明確批准前，物理阻斷任何實作動手行為：

1. **底層實作本質**：拆穿行銷包裝，用 2–3 句話揭露其底層真實技術原理（是否為劣質拼湊、淺層包裝或過時解法）。
2. **原生能力與 7-Phase 覆蓋對比**：優先對比目前環境（Antigravity 原生能力與既有 `7-Phase-Agentic-Workflow` / `teamwork` / `agy-studio` 核心工作流）是否已涵蓋，拒絕重複造輪子。
3. **三代價綜合評估**：
   - **Token 額度代價**：是否會長期在 System Prompt 塞入冗餘技能描述底噪、偷吃上下文或引發多輪重試浪費額度？
   - **系統與硬體負擔**：是否需要常駐背景行程、寫註冊表、佔用硬碟或吃 CPU？
   - **安全與隱私風險**：是否過度索取權限、有洩漏機敏資料或引入攻擊面之風險？
4. **殘酷裁定與「純吸收優化」鐵律**：明確給出【★★★ 建議採用 / ⚠️ 純吸收優化（汲取精華併入 7-Phase 核心工作流或 `references/`，嚴禁新裝獨立全域 Skill） / ❌ 強烈勸退】。核心 `SKILL.md` 吸收新長處時須遵循「替換淘汰」原則（單檔守住 ≤15 KB 上限），未獲明確同意，嚴禁自動寫入系統或安裝。


