import sys
import re
import os

# Auto-inject Graphviz path for Windows
if os.name == 'nt':
    os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

from diagrams import Diagram, Edge
from diagrams.onprem.database import PostgreSQL

def parse_sql_and_generate_erd(sql_path, output_name):
    if not os.path.exists(sql_path):
        print(f"Error: File not found {sql_path}")
        sys.exit(1)

    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # TODO: This is a very basic regex parser for quick-start. 
    # For robust parsing of comments and complex constraints, consider refactoring 
    # this script to use `pip install sqlparse` in the future.
    tables = []
    fks = []
    
    table_pattern = re.compile(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\w`"]*\.?[\'"`]?(\w+)[\'"`]?', re.IGNORECASE)
    for match in table_pattern.finditer(sql_content):
        tables.append(match.group(1))

    # Basic FK matching: FOREIGN KEY (col) REFERENCES table (col)
    fk_pattern = re.compile(r'FOREIGN\s+KEY\s*\([^)]+\)\s*REFERENCES\s+[\'"`]?(\w+)[\'"`]?', re.IGNORECASE)
    # This just links whatever table is currently being parsed to the referenced table
    # We split by CREATE TABLE to know which table owns the FK
    statements = re.split(r'CREATE\s+TABLE', sql_content, flags=re.IGNORECASE)[1:]
    for i, stmt in enumerate(statements):
        match_table = re.search(r'(?:IF\s+NOT\s+EXISTS\s+)?[\w`"]*\.?[\'"`]?(\w+)[\'"`]?', stmt, re.IGNORECASE)
        if match_table:
            table_name = match_table.group(1)
            for fk_match in fk_pattern.finditer(stmt):
                fks.append((table_name, fk_match.group(1)))

    if not tables:
        print("No CREATE TABLE statements found.")
        sys.exit(0)

    print(f"Found {len(tables)} tables and {len(fks)} relationships.")

    with Diagram(output_name, show=False, direction="LR"):
        node_map = {}
        for t in tables:
            node_map[t] = PostgreSQL(t)
        
        for source, target in fks:
            if source in node_map and target in node_map:
                node_map[source] >> Edge(label="FK") >> node_map[target]

    print(f"Successfully generated {output_name}.png")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python sql_to_erd.py <path_to_sql_file> <output_name>")
        sys.exit(1)
    parse_sql_and_generate_erd(sys.argv[1], sys.argv[2])
