---
name: karpathy-guidelines
description: >
  LLM coding 行為矯正與 Phase 0/3 規格反詰問守則（整合 karpathy-guidelines、grilling 壓力測試式需求追問與 project-planner 里程碑拆解）。
  防止 AI 過度假設、過度工程化、動到不該動的 code。
  觸發詞：/spec, /grill, grilling, project-planner, karpathy-guidelines, 精準開刀, 困惑即停, 壓力測試追問.
---

# 🧠 Karpathy Guidelines & Phase 0/3 Spec Grilling — LLM 行為矯正核心 (3-in-1 Edition)

源自 [Andrej Karpathy 對 LLM Coding 陷阱的觀察](https://x.com/karpathy/status/2015883857489522876)，並融合 **Phase 0 Grilling 反詰問法** 與 **Phase 3 最小里程碑規劃**。

---

## 1. 主動反駁 (Push Back)

**當存在更簡單的方案時，你必須直言反駁。**
- 不要盲從使用者過度複雜的提案——若既有的 API、標準庫或原生特性就能解決，主動提出簡化方案。
- **量化門檻**：若寫了 200 行但其實 50 行就能寫完，**強制重寫**。
- 若需求存在多種合理解讀，列出選項與推薦解，絕不私自盲猜。

## 2. 零投機 (No Speculation)

**只寫解決當下問題的最少代碼，零預留投機。**
- ❌ 禁止為單一用途代碼建立抽象層或 Factory
- ❌ 禁止加入未被要求的「彈性配置」與「未來擴充性」
- ❌ 禁止處理不可能發生的假想錯誤情境

## 3. 精準開刀 (Surgical Precision)

**只動必須修改的區域，只清自己製造的垃圾。**
- 編輯既有檔案時：不順手美化鄰近格式、不重構沒壞的代碼、完全遵循原檔命名與風格。
- 發現無關的既有死代碼時：**僅提報，不擅自刪除**（除非使用者明確啟動 `/refactor` 積極清理模式）。

## 4. 困惑即停與 Grilling 決策樹追問 (Stop When Confused & `/spec` / `/grill`)

**不假設、不掩飾困惑、一次只問一個關鍵決策。**
- **環境事實自己查 (`Facts via Tools`)**：凡是能透過讀檔、搜尋 codebase 或查環境得知的「客觀事實」，自己用工具查明，**嚴禁伸手問使用者**。
- **設計決策逐一追問 (`Decisions to User`)**：當進入 Phase 0 (`/spec`)、使用者要求 `/grill` 壓力測試想法、或遇到需求矛盾時：
  1. 沿著決策樹的依賴分支逐一深挖，戳破模糊假設。
  2. **一次只問 1~2 個最關鍵的決策問題**（附上你的 `(Recommended)` 推薦選項與理由），等待使用者拍板後再推進下一層，禁止一次丟出十幾個問題轟炸。
  3. **BTC 熱力學門禁**：面臨核心演算法或複雜邊界時，若信任評分 $T < 0.65$（或行為探針熵值 $\sigma_{\text{calib}} > 0.4$），**強制觸發主動棄權 (ABSTAIN)**，停下提問，絕不硬寫幻覺代碼。

## 5. Phase 3 最小垂直里程碑拆解 (`project-planner` 精髓)

當規劃跨模組任務時，依「相依性拓撲 + 垂直可驗證切片」拆解為 **最多 3 個里程碑 (Milestones)**：
- 每個里程碑必須有明確的 **輸入前提**、**修改檔案清單** 與 **一行可執行驗收標準 (Success Criterion)**。
- 在使用者確認規格與計畫前，嚴禁直接跨入 Phase 4 動手改代碼。
