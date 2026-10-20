---
name: context-pruner
description: >
  長任務上下文主動清理、SelfCompact 第一性原理自適應壓縮與 8 刻面可審計熱蒸餾技能（整合 context-pruner 與 context-compressor）。
  透過 C1-C2-C3-N1 探針阻斷卡死壓縮，產出 8 大核心刻面膠囊與遺失審計報告 (Loss Report)，並聯動 auto-snapshot 持久化交接。
  觸發詞：/prune, /compact, /clean-context, /distill, 整理上下文, 上下文清理, 壓縮上下文, 記憶蒸餾, 上下文膠囊, context-compressor.
---

# 🧹 Context Pruner & SelfCompact — 上下文熱蒸餾與雙向節流引擎 (2-in-1 Edition)

> **核心理念**：結合 **SelfCompact (arXiv:2606.23525)** 第一性原理壓縮門禁、**DeepInfer YOCO SWA Bounded Replay（有界後綴重播）** 與 **Context Diamond 8 刻面膠囊**，清除試錯噪訊並保護 KV Cache 前綴。
> - **YOCO 雙層截斷鐵律**：將長對話狀態切分為 **Global Block State**（寫入 `STATE.md` 與 8 刻面膠囊之不可變契約）與 **SWA Bounded Ring**（僅保留最近 `W=5` 輪活躍細節 + `K=2` 兩振回退緩衝 = 7 個微觀單元），使壓縮與重建成本恆定為 $O(1)$。

---

## 1. 觸發時機與 SelfCompact 第一性原理門禁 (`C1-C2-C3-N1`)

當對話超過 10~15 輪、完成密集除錯、或從 Phase 3 (Design) 切換至 Phase 4 (Implementation) 時觸發。
**執行壓縮前，必須先通過以下四項第一性原理探針（任一不符則禁止壓縮）**：

- **(C1) Closed-Unit（步驟已閉環）**：當前子任務或除錯已得出明確結論，非處於推導半途。
- **(C2) Summarizable（可無損濃縮）**：核心成果能濃縮為具體的檔案路徑、行號與契約事實。
- **(C3) Progress（具實質進展）**：距上次壓縮已有新事實或代碼落盤。
- **(N1) NOT Stuck（未陷入死循環）**：最近連續呼叫**未**處於重複報錯狀態（若卡死應先回滾或換道排錯，嚴禁把失敗過程美化壓縮）。

---

## 2. 輸入側噪訊過濾與廢棄清單 (Input Noise Filter & Pruning)

主動剪除並忽略以下 7 類高耗能無效資訊：
1. ❌ 已放棄的設計方案與草稿
2. ❌ 已解決問題的冗長 Stacktrace 與除錯過程 Log
3. ❌ 重複印出的完整程式碼塊
4. ❌ 已完成且後續無需參考的中間探索步驟
5. ❌ CLI 原始長輸出（搜檔排除 `node_modules/.git/dist/build`；讀取大檔強制指定 `StartLine/EndLine`）
6. ❌ 已被新決策覆蓋的舊參數
7. ❌ 客套話與過渡性鋪陳（搭配 `/caveman`）

---

## 3. 8 大刻面可審計上下文膠囊 (8-Facet Auditable Context Capsule)

```markdown
### 💎 上下文膠囊 (8-Facet Context Capsule)

1. 💓 **當前脈動 (Pulse)**：[任務現況一句話簡報與所處 Phase]
2. 🎯 **目標與驗收 (Goal & Acceptance)**：[核心交付價值與可驗證成功標準]
3. 🛡️ **規則與硬約束 (Rules & Constraints)**：[不可觸碰範圍、依賴限制、安全護欄]
4. ⚖️ **已定案決策 (Decisions Made)**：[已拍板的架構與演算法選型 + Why]
5. 🏛️ **穩定事實 (Stable Facts)**：[已驗證的環境設定、介面簽名與前提]
6. 📈 **目前狀態 (Working State)**：[已修改檔案、剛通過的測試與門禁結果]
7. 🚧 **未決問題與風險 (Open Loops)**：[待確認項目或潛在邊界風險]
8. ⚓ **代碼實體錨點 (Code Anchors)**：[關鍵檔案路徑、Symbol、核心函式與行號]

#### 🔍 遺失審計報告 (Loss Report)
- **已剪除噪訊**：[列出本次丟棄的試錯方案、過期 Log 與無關探索]
- **完整性確認**：[確認無關鍵約束或未存檔變更被誤刪]
```

> **聯動存檔**：輸出膠囊後，同步執行 `auto-snapshot capture handoff` 並更新 `STATE.md`，即可安全開啟全新對話（New Chat），以 10% 的 Token 成本無縫接續開發。
