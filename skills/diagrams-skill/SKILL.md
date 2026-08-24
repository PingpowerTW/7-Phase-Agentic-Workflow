---
name: diagram-generator
description: Generates professional architecture, structural, and flow diagrams using Python's 'diagrams' package, and performs reverse engineering of SQL and project structures.
---

# Diagram Generator Skill

You are equipped with the capability to generate professional, well-laid-out system architecture diagrams, ERDs, and dependency graphs. You will do this by leveraging the Python `diagrams` library within your Context-Mode Sandbox, completely avoiding raw XML/drawio generation to save tokens.

## 核心原則 (Core Principles)
1. **Token Economy**: NEVER attempt to write raw `.drawio` (XML) or SVG files directly into the context window. It wastes tokens and causes hallucinations.
2. **Context-Mode Sandbox**: ALWAYS write a Python script using the `diagrams` library, run it locally using `ctx_execute` (or terminal if `ctx_execute` is unavailable), and produce a PNG. 
3. **Graphviz Requirement**: This skill requires `Graphviz` and the Python `diagrams` package installed on the host machine.

## 如何用自然語言畫架構圖 (Natural Language to Diagram)
When the user asks you to "draw an architecture diagram" or "visualize this system":
1. Understand the components (e.g., AWS EC2, Postgres, React Frontend).
2. Write a Python script to the workspace scratch directory or execute it directly. Example:
   ```python
   import os
   # Auto-inject Graphviz path on Windows
   if os.name == 'nt':
       os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"
       os.environ["PATH"] += os.pathsep + r"C:\Program Files (x86)\Graphviz\bin"
       
   from diagrams import Diagram, Cluster
   from diagrams.aws.compute import EC2
   from diagrams.aws.database import RDS
   from diagrams.onprem.client import Client
   
   # For Traditional Chinese/CJK support, you MUST define these attributes:
   # (Using a slightly smaller fontsize prevents the CJK text from overlapping with the icon)
   attr = {
       "fontname": "Microsoft JhengHei",
       "fontsize": "12"
   }
   
   with Diagram("Web Architecture", show=False, direction="LR", graph_attr=attr, node_attr=attr, edge_attr=attr):
       user = Client("使用者")
       with Cluster("AWS"):
           web = EC2("Web Server")
           db = RDS("PostgreSQL")
       user >> web >> db
   ```
3. Run the script. It will generate `web_architecture.png` in the current directory.
4. Inform the user and present the generated image using Markdown: `![Web Architecture](file:///absolute/path/to/web_architecture.png)`

## 反向解析功能 (Reverse Engineering)
You have helper scripts located in `scripts/` to generate diagrams from existing code or DB schemas:

1. **SQL DDL to ERD**:
   If the user asks to draw an ERD from a SQL schema:
   - Locate script: `scripts/sql_to_erd.py` (located inside the `diagram_generator` skill folder under `scripts/sql_to_erd.py`).
   - Run: `python <path_to_skill>/scripts/sql_to_erd.py <path_to_sql_file> <output_name>`
   - This script parses basic `CREATE TABLE` and outputs an ERD diagram PNG.

2. **Project Dependency Graph**:
   If the user asks to visualize a Python or Node.js project:
   - Locate script: `scripts/project_deps.py` (located inside the `diagram_generator` skill folder under `scripts/project_deps.py`).
   - Run: `python <path_to_skill>/scripts/project_deps.py <project_directory> <output_name>`
   - This script generates a module dependency graph PNG.

## 注意事項
- If the `diagrams` library is missing, install via `pip install diagrams`.
- If `Graphviz` is missing, install via `winget install graphviz` on Windows or `brew install graphviz` on macOS.
- On Windows, ensure the `bin` directory of Graphviz is added to `PATH` or auto-injected in the Python script via `os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"`.
