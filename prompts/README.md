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
description: 'Generate a new Python feature module with types, docstrings, and tests'
version: '1.0.0'
tags: [feature, scaffolding, pytest, type-hints]
stack: python
patterns: [role-playing, plan-and-execute, btc-calibrated]
eval_criteria: [faithfulness, zero-placeholder, type-safety]
---
```

---

## ⚡ 如何使用

1. **直接引入 Agent Session**：
   在對話中引入特定 `.prompt.md` 作為任務契約。
2. **VS Code / Cursor 整合**：
   可將本目錄模板複製至專案根目錄的 `.github/prompts/`，即可在 IDE Agent 模式中透過 `/` 指令直接調用。
3. **自動化驗證**：
   配合 `skills/promptcraft` 的 LLM-as-a-Judge 評估量表進行驗收。
