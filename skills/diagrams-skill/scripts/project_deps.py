import sys
import os
import ast
import re

# Auto-inject Graphviz path for Windows
if os.name == 'nt':
    os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

from diagrams import Diagram
from diagrams.programming.language import Python, Nodejs

def parse_python_imports(filepath):
    deps = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    deps.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    deps.append(node.module.split('.')[0])
    except Exception as e:
        pass
    return deps

def parse_node_imports(filepath):
    deps = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # 支援 import ... from 'module' 或 import 'module'
            imports = re.findall(r'import\s+(?:.*?from\s+)?[\'"]([^\'"]+)[\'"]', content)
            # 支援 require('module')
            requires = re.findall(r'require\([\'"]([^\'"]+)[\'"]\)', content)
            deps.extend(imports + requires)
    except Exception as e:
        pass
    
    # 簡化相對路徑
    cleaned_deps = []
    for d in deps:
        if d.startswith('.'):
            d = os.path.basename(d)
        # 移除副檔名
        d = d.replace('.js', '').replace('.ts', '')
        cleaned_deps.append(d)
    return cleaned_deps

def generate_deps(project_path, output_name):
    if not os.path.isdir(project_path):
        print(f"Error: Directory not found {project_path}")
        sys.exit(1)

    dependencies = []
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
                deps = parse_python_imports(filepath)
                for d in deps:
                    dependencies.append((module_name, d))
            elif file.endswith(('.js', '.ts', '.jsx', '.tsx')):
                modules.add(module_name)
                node_types[module_name] = Nodejs
                deps = parse_node_imports(filepath)
                for d in deps:
                    dependencies.append((module_name, d))

    if not dependencies:
        print("No dependencies found.")
        sys.exit(0)

    with Diagram(output_name, show=False, direction="LR"):
        node_map = {}
        all_nodes = set(modules)
        for src, dst in dependencies:
            all_nodes.add(dst)
            
        for n in all_nodes:
            ntype = node_types.get(n, Python if '.py' in project_path else Nodejs) 
            node_map[n] = ntype(n)
            
        for src, dst in dependencies:
            node_map[src] >> node_map[dst]

    print(f"Successfully generated {output_name}.png with {len(all_nodes)} modules.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python project_deps.py <project_directory> <output_name>")
        sys.exit(1)
    generate_deps(sys.argv[1], sys.argv[2])
