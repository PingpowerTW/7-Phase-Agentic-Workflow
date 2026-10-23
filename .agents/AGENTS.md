# 🤖 auto-snapshot 專案記憶與上下文管理規則

本專案使用 `auto-snapshot` 進行本地持久化記憶管理。開發時請遵守以下行為規範：

## 1. 記憶自動擷取 (Auto-Capture)

每當完成階段性任務或修復 Bug 時，必須自動執行或建議使用者執行快照擷取：
- **里程碑完成 (Milestone)**:
  `auto-snapshot capture milestone "變更摘要" --files <檔案路徑> --tags <標籤> --skill <關聯Skill>`
- **技術決策 (Decision)**:
  當做出重大架構或技術選型時，必須同步寫入快照：
  `auto-snapshot capture decision "決策標題" --decision "決策細節與原因" --tags architecture,setup`
- **對話交接 (Handoff)**:
  對話結束前，必須建立完整狀態快照：
  `auto-snapshot capture handoff "進度總結" --completed <已完成> --in-progress <進行中> --pending <待辦> --next-action <下一步>`

## 2. 跨 Skill 記憶綁定 (Cross-Skill Binding)

在修改特定功能時，先載入與該 Skill 關聯的歷史踩坑紀錄或技術限制：
- 例如：開始修改 Firebase Security Rules 前，應執行 `auto-snapshot recover --skill firebase-rules` 獲取歷史決策與限制。

## 3. 關鍵字指紋比對、CRAG 雙階段校正重排與 SWA 有界後綴重播 (CRAG & SWA Bounded Replay)

重開對話進行上下文恢復時，採用 **DeepInfer YOCO + SWA Bounded Replay** 與 **CRAG (Corrective RAG) 雙階段校正式重排**，決定是否需要發起遠端 Supabase 記憶庫查詢以節省 Token 消耗：
- **Global Block State（全域共享錨點）**：先讀取 `STATE.md` 掌握全局進行中任務（如同 YOCO Layer 20 全域 KV，跨 Session 持久複用）。
- **SWA Bounded Replay（有界後綴重播，O(1) 成本）**：執行 `auto-snapshot recover --query "當前要問的問題關鍵字"`（預設 `--keep 7` = 最近活躍視窗 $W=5$ + 兩振回退緩衝 $K=2$，嚴禁盲讀整份歷史 JSONL）。
- **CRAG 雙階段校正與重組 (Decompose-Then-Recompose)**：
  - **Stage 1 (粗篩召回)**：自動執行 `NFKC -> NFD 去重音 -> Lowercase -> 空白折疊 -> 3-gram 特徵抽取` 比對本地快照之 `tags` 與 `summary`。
  - **Stage 2 (校正補召回)**：最新 `--keep` 筆一律保留；更舊快照以關鍵字命中數評分，僅在分數**高於視窗內所有快照**時補入（最多 2 筆），輸出維持時間先後順序。降噪效果尚未量測。
- 若顯示 `✅ 本地記憶覆蓋查詢`，則跳過遠端 Supabase 檢索（省下 40%~50% 歷史重讀與檢索 Token）。
- 若顯示 `⚠️ 本地記憶不足`，才向遠端知識庫發起長期記憶查詢。

## 4. 情節壓縮與熱蒸餾 (Episodic Compression & Hot Distillation)

當快照數量累積超過 200 條或對話 Context 逼近上限時，系統會執行壓縮。
依據 **SelfCompact (arXiv:2606.23525)** 原則，執行情節壓縮與熱蒸餾前必須確保：
- **C1 閉環檢驗**：當前執行的任務模組已完成並經過驗證，非推導/除錯中途。
- **N1 卡死阻斷**：若當前處於連續報錯或反覆失敗狀態，**禁止封裝快照/蒸餾**，應先診斷原因並換道修正，避免污染長期記憶。
- 自動將舊有的 150 條紀錄歸檔為 1 條 `compressed_archive` 摘要。
- 壓縮程式會輸出一段結構化的 JSON Payload。此時應主動詢問使用者或由 Agent 判斷，是否將這段精煉的「熱蒸餾知識」寫入長期記憶庫（如 Supabase）。

## 5. Loop Engineering 雙軌記憶與狀態同步 (Dual-Track State Architecture)

本專案採用「雙軌記憶」架構：
- **微觀軌道 (`SNAPSHOT.jsonl`)**：記錄每一個 milestone、decision、handoff 的高頻歷史事件日誌。
- **宏觀軌道 (`STATE.md`)**：作為專案當前的「活體狀態脊椎（State Spine）」，維護進行中任務 (High Priority)、長效觀察清單 (Watch List) 與雜訊過濾 (Recent Noise)。
- **同步原則**：每次完成階段交接或重要里程碑時，除執行 `auto-snapshot capture` 外，必須同步更新 `STATE.md` 的 `Last run` 時間戳記與狀態清單，確保重開對話或更換模型時能以極低 Token 成本瞬間建立專案全局視野。

> 安全門禁、Git 時光機地基、兩振硬熔斷與 Ponytail 規範見根目錄 AGENTS.md（唯一來源）。

