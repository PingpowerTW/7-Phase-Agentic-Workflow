# diagrams-skill

[English](README.md) | [繁體中文](README.zh-TW.md)

![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-2ea44f)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

這是一個高度**節省 Token** 且專業的 AI Agent 繪圖技能 (支援 Antigravity, Claude Code, Cursor 等)。此技能不強迫 LLM 輸出冗長且容易出錯的 XML（如原生的 `.drawio` 檔案），而是使用宣告式的 [Python diagrams](https://diagrams.mingrammer.com/) 函式庫來繪製架構圖。

它能保持你的 LLM 上下文視窗乾淨，避免過多 Token 輸出導致的幻覺，同時還能產出包含官方 AWS、GCP、Azure 及 K8s 圖示的精美 PNG/SVG 架構圖。

## ✨ 核心特色

- **省 Token (Token Economy)**：AI 只需要寫約 15 行的 Python 程式碼，而不是 1500 行的 XML。
- **沙盒執行 (Context-Mode Sandbox)**：在本地沙盒環境中執行並產出圖表，保持主要對話上下文的純淨。
- **官方圖示支援**：內建主流雲端供應商 (AWS, Azure, GCP)、開源框架與資料庫的官方圖示。
- **逆向工程**：
  - **SQL 轉 ERD**：讀取你的 `.sql` 檔案並自動生成實體關聯圖 (ERD)。
  - **程式碼轉架構圖**：掃描你的 Python 或 Node.js (`.js`, `.ts`) 專案，自動生成模組依賴關係圖。

## 🚀 安裝方式

### 1. 前置需求 (宿主機)
此技能需要執行 Agent 的主機上已經安裝好 Python 與 Graphviz。

1. **Graphviz**: 
   - **macOS**: `brew install graphviz`
   - **Windows**: `winget install graphviz` (⚠️ *新版腳本已支援自動注入環境變數，但仍建議手動將 `bin` 目錄加入系統 `PATH`*)
   - **Linux**: `sudo apt install graphviz`
2. **Python 依賴**:
   ```bash
   pip install diagrams
   ```

### 2. 安裝 Skill

將此儲存庫 Clone 到你的 Agent skills 目錄中：
```bash
git clone https://github.com/PingpowerTW/diagrams-skill.git ~/.gemini/config/skills/diagrams-skill
```
*(實際路徑取決於你使用的 Agent 平台，例如 Antigravity、OpenClaw 或 Autohand)*

## ⚡ 快速開始

只要對你的 Agent 說：
> *"幫我畫一個 Web 架構圖，包含一個 API Gateway 路由流量到 React 前端、Node.js 後端，以及 PostgreSQL 資料庫。"*

Agent 就會自動幫你撰寫腳本、渲染圖表，並將完成的高畫質圖片直接展示給你。

### 逆向工程
> *"視覺化 `./src` 專案目錄中的模組依賴關係"*

> *"將 `./schema.sql` 轉換成實體關聯圖 (ERD)"*

## 🛠️ 運作原理
在底層架構中，`SKILL.md` 做為 Agent 的系統提示詞 (System prompt)。當被要求畫圖時，Agent 會動態寫出包含 `diagrams` 模組的 Python 腳本，設定節點與連線並執行它。針對逆向工程，則會呼叫 `scripts/` 目錄下預先寫好的 AST 解析腳本來達成。

## 授權條款
MIT License
