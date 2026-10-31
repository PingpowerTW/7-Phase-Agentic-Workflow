import sys
import os
import ast
import re
import shutil

# Dynamically locate Graphviz on Windows if not already on PATH
if os.name == 'nt' and not shutil.which('dot'):
    pf = os.environ.get("ProgramFiles")
    if pf:
        default_gv = os.environ.get("GRAPHVIZ_DOT", os.path.join(pf, "Graphviz", "bin"))
        if os.path.exists(default_gv):
            os.environ["PATH"] += os.pathsep + default_gv

from diagrams import Diagram
from diagrams.programming.language import Python, Nodejs

EDITORIAL_GRAPH_ATTR = {
    "fontname": "Microsoft JhengHei",
    "fontsize": "13",
    "splines": "ortho",
    "nodesep": "0.60",
    "ranksep": "0.75",
    "pad": "0.4",
    "bgcolor": "#f5f5f5",
}
EDITORIAL_NODE_ATTR = {"fontname": "Microsoft JhengHei", "fontsize": "12"}
EDITORIAL_EDGE_ATTR = {"fontname": "Microsoft JhengHei", "fontsize": "11", "color": "#5c6378"}


def parse_python_imports(filepath):
    deps = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    deps.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                deps.append(node.module.split('.')[0])
    except (SyntaxError, UnicodeDecodeError, OSError):
        pass
    return deps


def parse_node_imports(filepath):
    deps = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            imports = re.findall(r'import\s+(?:.*?from\s+)?[\'"]([^\'"]+)[\'"]', content)
            requires = re.findall(r'require\([\'"]([^\'"]+)[\'"]\)', content)
            deps.extend(imports + requires)
    except (UnicodeDecodeError, OSError):
        pass

    return [
        (os.path.basename(d) if d.startswith('.') else d).replace('.js', '').replace('.ts', '')
        for d in deps
    ]


def generate_deps(project_path, output_name):
    if not os.path.isdir(project_path):
        print(f"Error: Directory not found {project_path}")
        sys.exit(1)

    raw_deps = []
    modules = set()
    node_types = {}

    for root, _, files in os.walk(project_path):
        if 'node_modules' in root or '.venv' in root:
            continue
        for file in files:
            filepath = os.path.join(root, file)
            module_name = os.path.splitext(file)[0]
            if file.endswith('.py'):
                modules.add(module_name)
                node_types[module_name] = Python
                raw_deps.extend((module_name, d) for d in parse_python_imports(filepath))
            elif file.endswith(('.js', '.ts', '.jsx', '.tsx')):
                modules.add(module_name)
                node_types[module_name] = Nodejs
                raw_deps.extend((module_name, d) for d in parse_node_imports(filepath))

    # Prefer internal module edges to respect Editorial complexity budget; fallback to all unique edges
    internal_deps = sorted({(s, d) for s, d in raw_deps if d in modules and s != d})
    dependencies = internal_deps or sorted({(s, d) for s, d in raw_deps if s != d})

    if not dependencies:
        print("No dependencies found.")
        sys.exit(0)

    all_nodes = sorted({n for edge in dependencies for n in edge})
    default_type = Python if any(t is Python for t in node_types.values()) else Nodejs

    with Diagram(
        output_name,
        show=False,
        direction="LR",
        graph_attr=EDITORIAL_GRAPH_ATTR,
        node_attr=EDITORIAL_NODE_ATTR,
        edge_attr=EDITORIAL_EDGE_ATTR,
    ):
        node_map = {n: node_types.get(n, default_type)(n) for n in all_nodes}
        for src, dst in dependencies:
            node_map[src] >> node_map[dst]

    print(f"Successfully generated {output_name}.png with {len(all_nodes)} modules.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python project_deps.py <project_directory> <output_name>")
        sys.exit(1)
    generate_deps(sys.argv[1], sys.argv[2])
