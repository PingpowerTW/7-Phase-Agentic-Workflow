# 📚 7-Phase Prompt Template Catalog (標準化 Prompt 模板庫)

本目錄提供符合 **YAML Frontmatter 規範** 與 **Agentic 認知範式**（Plan-and-Execute、Reflexion、BTC 信度校準）的跨技術棧提示詞資產庫，相容於 VS Code Copilot、Claude Code、Cursor 與 Antigravity。

---

## 📂 目錄結構

```
prompts/
├── shared/
│   └── prompt-schema.json          # Frontmatter JSON Schema 驗證規範
├── python/                         # Python 3.12+ 專用模板 (Pytest, Ruff, Mypy)
│   ├── create-feature.prompt.md    # 新功能模組開發
│   ├── debug-issue.prompt.md       # 根因隔離與除錯
│   ├── refactor-code.prompt.md     # Karpathy 精準重構
│   └── write-tests.prompt.md       # 單元與整合測試
├── react-ts/                       # React 19 + TypeScript + Tailwind 模板
│   ├── create-component.prompt.md  # 防模板化 UI 元件 (frontend-taste-v2)
│   ├── create-hook.prompt.md       # 帶 Cleanup 的自訂 Hook
│   └── debug-ui.prompt.md          # 佈局與無障礙性除錯
├── nodejs-ts/                      # Node.js + TypeScript 服務端模板
│   ├── create-service.prompt.md    # 依賴注入式商業邏輯服務
│   └── create-middleware.prompt.md # 具備安全性與錯誤傳遞的中間件
├── laravel/                        # Laravel 13+ / PHP 8.4+ 企業級後端模板
│   ├── create-feature.prompt.md    # Action + FormRequest + Resource + Pest 3+ 完整切片
│   ├── create-migration.prompt.md  # 冪等性索引優化與安全 Rollback
│   ├── write-pest-tests.prompt.md  # Pest PHP 3+ Feature 測試與 Mock
│   └── refactor-action.prompt.md   # 臃腫 Controller 重構為 Invokable Action
└── fullstack/                      # 全端 (Next.js / FastAPI / Database) 模板
    ├── create-api-route.prompt.md  # 帶 Schema 驗證的 API 端點
    └── db-migration-schema.prompt.md # 冪等性資料庫 Schema 與遷移
```

---

## 📝 `.prompt.md` 規範與 Frontmatter 範例

每份 Prompt 檔案皆包含嚴格的 YAML 標頭：

```markdown
---
mode: 'agent'
description: 'Generate a new Laravel feature module with Action, FormRequest, and Pest tests'
version: '1.0.0'
tags: [laravel, php8.2, eloquent, pest, action-pattern]
stack: laravel
patterns: [role-playing, plan-and-execute, btc-calibrated]
eval_criteria: [strict-types, form-request-validation, pest-coverage]
---
```

---

## ⚡ 自動化驗證 (Automated Validation)

專案內建純 Python 標準庫校驗腳本，可於本機或 CI 門禁中一鍵驗證所有 Prompt 檔案：

```bash
python scripts/validate_prompts.py
```
