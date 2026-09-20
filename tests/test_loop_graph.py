#!/usr/bin/env python3
"""
Unit tests for loop_graph.py (Architecture Knowledge Graph & Blast Radius Engine)
Pure Python standard library unittest.
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from loop_graph import (
    ArchitectureGraph,
    CodeAstScanner,
    GraphVisualizer,
    generate_markdown_report,
    normalize_path
)


class TestLoopGraph(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="graph_test_"))
        self.graph = ArchitectureGraph()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_graph_node_and_edge_addition(self):
        self.graph.add_node("mod:a.py", "a.py", "module", "a.py")
        self.graph.add_node("mod:b.py", "b.py", "module", "b.py")
        self.graph.add_edge("mod:a.py", "mod:b.py", "imports")

        self.assertIn("mod:a.py", self.graph.nodes)
        self.assertIn("mod:b.py", self.graph.nodes)
        self.assertEqual(len(self.graph.edges), 1)
        self.assertEqual(len(self.graph.adj_out["mod:a.py"]), 1)
        self.assertEqual(len(self.graph.adj_in["mod:b.py"]), 1)

    def test_god_nodes_ranking(self):
        # Create a hub node with multiple dependents
        self.graph.add_node("hub", "Hub", "module", "hub.py")
        for i in range(5):
            nid = f"client_{i}"
            self.graph.add_node(nid, nid, "module", f"{nid}.py")
            self.graph.add_edge(nid, "hub", "calls")

        gods = self.graph.get_god_nodes(top_n=1)
        self.assertEqual(len(gods), 1)
        hub_id, hub_node, deg = gods[0]
        self.assertEqual(hub_id, "hub")
        self.assertEqual(deg, 5)

    def test_blast_radius_calculation(self):
        # A -> B -> C (A depends on B, B depends on C)
        self.graph.add_node("c", "ServiceC", "module", "c.py")
        self.graph.add_node("b", "ServiceB", "module", "b.py")
        self.graph.add_node("a", "AppA", "module", "a.py")
        self.graph.add_node("t", "TestA", "test", "tests/test_a.py")

        self.graph.add_edge("b", "c", "imports")  # b depends on c
        self.graph.add_edge("a", "b", "imports")  # a depends on b
        self.graph.add_edge("t", "a", "imports")  # t depends on a

        # Changing C should ripple up to B, A, and TestA
        res = self.graph.compute_blast_radius("c.py")
        self.assertEqual(res["direct_count"], 1)  # b
        self.assertEqual(res["transitive_count"], 2)  # a, t
        self.assertEqual(res["total_blast_radius"], 3)
        self.assertIn("tests/test_a.py", res["impacted_tests"])

    def test_python_ast_scanner(self):
        py_file = self.test_dir / "sample.py"
        py_file.write_text("""
import os
from math import sqrt

class Calculator:
    def compute(self, x):
        return sqrt(x)

def run():
    c = Calculator()
    c.compute(4)
""", encoding="utf-8")

        scanner = CodeAstScanner(self.test_dir, self.graph)
        scanner.parse_python_file(py_file, "sample.py")

        # Verify module, class, functions
        self.assertIn("mod:sample.py", self.graph.nodes)
        self.assertIn("cls:sample.py::Calculator", self.graph.nodes)
        self.assertIn("fn:sample.py::run", self.graph.nodes)

    def test_js_lexical_scanner(self):
        js_file = self.test_dir / "service.js"
        js_file.write_text("""
import { db } from './db.js';
const logger = require('./logger.js');

function fetchUsers() {
    return db.query();
}

class UserService {}
""", encoding="utf-8")

        scanner = CodeAstScanner(self.test_dir, self.graph)
        scanner.parse_js_file(js_file, "service.js")

        self.assertIn("mod:service.js", self.graph.nodes)
        self.assertIn("fn:service.js::fetchUsers", self.graph.nodes)
        self.assertIn("cls:service.js::UserService", self.graph.nodes)

    def test_report_and_html_generation(self):
        self.graph.add_node("mod:core.py", "core.py", "module", "src/core.py")
        self.graph.add_node("policy:INV_01", "INV_01 (Safety)", "policy", "invariants.yaml")
        self.graph.add_edge("policy:INV_01", "mod:core.py", "governs")

        # Test report
        md = generate_markdown_report(self.graph)
        self.assertIn("Loop Graph", md)
        self.assertIn("core.py", md)

        # Test HTML rendering
        html = GraphVisualizer.render_html(self.graph)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("canvas id=\"graphCanvas\"", html)
        self.assertIn("INV_01", html)


if __name__ == "__main__":
    unittest.main()
