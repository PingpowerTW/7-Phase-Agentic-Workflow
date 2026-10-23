# 🛡️ Scripts 模組 AI Agent 指南 (Module-Level AGENTS.md)

本目錄為系統 Layer 1 核心安全與決策閘門，所有 AI Agent 在修改或擴充此目錄代碼時必須遵守以下硬性契約：

## 1. 架構層級與單向依賴約束 (Layer 1 Boundary)
- 參照根目錄 [`layers.json`](file:///d:/AI/優化/layers.json)，本模組屬於 `l1_scripts_core`。
- **避免向上依賴**（建議級，無自動檢查）：本目錄代碼絕對禁止引用 `auto-snapshot/`、`skills/` 或業務應用層代碼。
- **依賴限制**：優先使用 Python/Node.js 標準庫；嚴禁隨意新增第三方 pip/npm 依賴。

## 2. 核心檔案職責矩陣
- [`local_guard.py`](file:///d:/AI/優化/scripts/local_guard.py): System 1 秒級高速決策門禁、零生產接縫檢查、Ponytail 階梯定位、兩振回滾與 Reflexion 口語反思閉環。
- [`loop_gate.py`](file:///d:/AI/優化/scripts/loop_gate.py): gate.yaml 物理阻斷器（Denylist 路徑保護、maxFiles 限制、路徑正規化）。
- [`loop_graph.py`](file:///d:/AI/優化/scripts/loop_graph.py): 程式碼依賴拓撲地圖，探索程式前強制導航以止血 Token。
- [`loop_drift.py`](file:///d:/AI/優化/scripts/loop_drift.py): 規格與意圖漂移偵測。
- [`ast_guard.js`](file:///d:/AI/優化/scripts/ast_guard.js) / [`swc_extractor.js`](file:///d:/AI/優化/scripts/swc_extractor.js): AST 點陣語義硬熔斷。

## 3. 修改防護要求
- 任何對 `scripts/` 的修改必須保持向前相容性，且不得明顯拖慢門禁（靜態 ReLU 判定為毫秒級；`--rollback` 含 git 子行程，實測約 300ms）。
- 實作完成後必須通過 `python -m pytest tests/test_local_guard.py` 驗證。
