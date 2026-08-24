# diagrams-skill

[English](README.md) | [繁體中文](README.zh-TW.md)

![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-2ea44f)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A highly **token-efficient** and professional diagram-generation skill for AI Agents (Antigravity, Claude Code, Cursor, etc.). Instead of forcing the LLM to output verbose and brittle XML (like native `.drawio` files), this skill uses the declarative [Python diagrams](https://diagrams.mingrammer.com/) library to draw architectures. 

It keeps your LLM context window clean, prevents hallucinations caused by excessive token output, and still generates stunning PNG/SVG architectures featuring official AWS, GCP, Azure, and K8s icons.

## ✨ Highlights

- **Token Economy (省 Token)**: AI writes ~15 lines of Python code instead of 1500 lines of XML.
- **Context-Mode Sandbox**: Executes in the local sandbox to generate the diagram, keeping the main context clean.
- **Official Icons**: Built-in support for major cloud providers (AWS, Azure, GCP), open-source frameworks, and databases.
- **Reverse Engineering**:
  - **SQL to ERD**: Reads your `.sql` files and auto-generates entity-relationship diagrams.
  - **Code to Architecture**: Scans your Python or Node.js (`.js`, `.ts`) projects and generates module dependency graphs.

## 🚀 Installation

### 1. Prerequisites (Host Machine)
This skill requires Python and Graphviz installed on the machine running the agent.

1. **Graphviz**: 
   - **macOS**: `brew install graphviz`
   - **Windows**: `winget install graphviz` (⚠️ *Ensure the `bin` directory is added to your system `PATH`*)
   - **Linux**: `sudo apt install graphviz`
2. **Python Requirements**:
   ```bash
   pip install diagrams
   ```

### 2. Install the Skill

Clone this repository into your agent's skills directory:
```bash
git clone https://github.com/PingpowerTW/diagrams-skill.git ~/.gemini/config/skills/diagrams-skill
```
*(Path depends on your specific agent, e.g., Antigravity, OpenClaw, or Autohand)*

## ⚡ Quick Start

Just ask your agent:
> *"Draw a web architecture with an API Gateway routing traffic to a React frontend, a Node.js backend, and a PostgreSQL database."*

The agent will automatically write the script, render it, and present the finished image to you.

### Reverse Engineering
> *"Visualize the module dependencies of my Python project in `./src`"*

> *"Convert `./schema.sql` into an ERD diagram"*

## 🛠️ How it works
Under the hood, `SKILL.md` acts as the system prompt for the agent. When asked to draw a diagram, it imports the `diagrams` python module, sets up the nodes, and executes the script. For reverse engineering, it leverages the bundled helper scripts in the `scripts/` directory.

## License
MIT License
