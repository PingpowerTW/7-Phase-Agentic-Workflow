#!/usr/bin/env python3
"""
Unit tests for loop_graph.py (Architecture Knowledge Graph & Blast Radius Engine)
Pure Python standard library unittest.
"""

import os
import sys
import math
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

    def _build_pagerank_sample_graph(self):
        g = ArchitectureGraph()
        g.add_node("fn:a", "funcA", "function", "src/a.py")
        g.add_node("fn:b", "funcB", "function", "src/b.py")
        g.add_node("fn:c", "funcC", "function", "src/c.py")
        g.add_node("fn:d", "funcD", "function", "src/d.py")
        g.add_edge("fn:a", "fn:b", "calls")
        g.add_edge("fn:c", "fn:b", "calls")
        g.add_edge("fn:b", "fn:d", "calls")
        return g

    def test_pagerank_sums_to_one_and_ranks_hub(self):
        g = self._build_pagerank_sample_graph()
        ranks = g.compute_pagerank()
        self.assertAlmostEqual(sum(ranks.values()), 1.0, places=4)
        self.assertGreater(ranks["fn:b"], ranks["fn:a"])

    def test_pagerank_focus_personalization(self):
        g = self._build_pagerank_sample_graph()
        ranks_no_focus = g.compute_pagerank()
        ranks_focused = g.compute_pagerank(focus=["src/a.py"])
        self.assertGreater(ranks_focused["fn:a"], ranks_no_focus["fn:a"])

    def test_repo_map_respects_budget(self):
        g = self._build_pagerank_sample_graph()
        ranks = g.compute_pagerank()
        out_small = g.render_repo_map(ranks, budget=10)
        self.assertLessEqual(math.ceil(len(out_small) / 4) if out_small else 0, 10)

        out_large = g.render_repo_map(ranks, budget=10000)
        self.assertIn("funcA", out_large)
        self.assertIn("funcB", out_large)
        self.assertIn("funcC", out_large)
        self.assertIn("funcD", out_large)

    def test_pagerank_conserves_mass_with_external_targets(self):
        # Real scans contain edges to nodes outside the graph (e.g. stdlib imports).
        g = self._build_pagerank_sample_graph()
        g.add_edge("fn:a", "mod:os", "imports")
        g.add_node("fn:x", "funcX", "function", "src/data_runner.py")
        ranks = g.compute_pagerank(focus=["runner.py"])
        self.assertAlmostEqual(sum(ranks.values()), 1.0, places=4)
        # "runner.py" must not match "data_runner.py" (path-boundary), so no focus boost on funcX
        self.assertAlmostEqual(ranks["fn:x"], g.compute_pagerank()["fn:x"], places=6)
        # Nodes unreachable from focus still get non-zero rank
        focused = g.compute_pagerank(focus=["src/a.py"])
        self.assertTrue(all(v > 0 for v in focused.values()))

    def test_pagerank_empty_graph(self):
        g = ArchitectureGraph()
        ranks = g.compute_pagerank()
        self.assertEqual(ranks, {})
        self.assertEqual(g.render_repo_map({}, 100), "")

    def test_innermost_symbol_diff_blast_and_test_signal(self):
        py_file = self.test_dir / "service.py"
        py_file.write_text(
            "class OrderEngine:\n"
            "    def calc_tax(self, amount):\n"
            "        return amount * 0.05\n"
            "\n"
            "    def cancel_order(self, oid):\n"
            "        return True\n",
            encoding="utf-8",
        )
        test_file = self.test_dir / "test_order.py"
        test_file.write_text(
            "import service\n"
            "def test_tax():\n"
            "    e = service.OrderEngine()\n"
            "    return e.calc_tax(100)\n",
            encoding="utf-8",
        )
        test_cancel = self.test_dir / "test_cancel.py"
        test_cancel.write_text(
            "import service\n"
            "def test_cancel():\n"
            "    e = service.OrderEngine()\n"
            "    return e.cancel_order(1)\n",
            encoding="utf-8",
        )
        scanner = CodeAstScanner(self.test_dir, self.graph)
        scanner.parse_python_file(py_file, "service.py")
        scanner.parse_python_file(test_file, "test_order.py")
        scanner.parse_python_file(test_cancel, "test_cancel.py")

        diff_stale = (
            "--- a/service.py\n"
            "+++ b/service.py\n"
            "@@ -2,2 +2,2 @@\n"
            "     def calc_tax(self, amount):\n"
            "-        return amount * 0.05\n"
            "+        return amount * 0.08\n"
        )
        res = self.graph.compute_diff_blast_radius(diff_stale)
        self.assertEqual(res["seeds"], ["fn:service.py::calc_tax"])
        self.assertEqual(res["test_signal"], "stale")
        self.assertEqual(res["impacted_tests"], ["test_order.py"])

        diff_changed = diff_stale + (
            "--- a/test_order.py\n"
            "+++ b/test_order.py\n"
            "@@ -4,1 +4,1 @@\n"
            "-    return e.calc_tax(100)\n"
            "+    return e.calc_tax(200)\n"
        )
        res2 = self.graph.compute_diff_blast_radius(diff_changed)
        self.assertEqual(res2["test_signal"], "changed")

    def test_cross_layer_http_env_and_dead_code(self):
        api_py = self.test_dir / "api.py"
        api_py.write_text(
            "import os\n"
            "def init_env():\n"
            "    os.environ['PAYMENT_KEY'] = 'live'\n"
            "\n"
            "def callback_sorter(x):\n"
            "    return x\n"
            "\n"
            "def charge_card():\n"
            "    sorted([1, 2], key=callback_sorter)\n"
            "    return os.getenv('PAYMENT_KEY')\n"
            "\n"
            "@app.get('/api/orders/<int:order_id>')\n"
            "def get_order(order_id):\n"
            "    return charge_card()\n"
            "\n"
            "def orphan_helper():\n"
            "    return 42\n"
            "\n"
            "def main():\n"
            "    pass\n",
            encoding="utf-8",
        )
        ui_js = self.test_dir / "client.js"
        ui_js.write_text(
            "function loadOrder() {\n"
            "  return fetch('/api/orders/42');\n"
            "}\n"
            "function unrelatedUiFn() {\n"
            "  return 1;\n"
            "}\n",
            encoding="utf-8",
        )
        scanner = CodeAstScanner(self.test_dir, self.graph)
        scanner.parse_python_file(api_py, "api.py")
        scanner.parse_js_file(ui_js, "client.js")

        # 1. Cross-layer HTTP route blast radius: backend get_order -> route:/api/orders/{} -> frontend loadOrder (not unrelatedUiFn)
        blast_http = self.graph.compute_blast_radius("fn:api.py::get_order")
        dep_labels = {d["label"] for d in blast_http["dependents"]}
        self.assertIn("/api/orders/{}", dep_labels)
        self.assertIn("loadOrder", dep_labels)
        self.assertNotIn("unrelatedUiFn", dep_labels)

        # 2. Cross-layer CONFIGURES blast radius: env:PAYMENT_KEY -> charge_card -> get_order -> loadOrder
        blast_env = self.graph.compute_blast_radius("env:PAYMENT_KEY")
        env_deps = {d["label"] for d in blast_env["dependents"]}
        self.assertIn("charge_card", env_deps)
        self.assertIn("get_order", env_deps)

        # 3. Dead code candidates: orphan_helper is flagged, while route handler, direct callee, callback reference, and main are excluded
        dead_labels = {c["label"] for c in self.graph.find_dead_code_candidates()}
        self.assertIn("orphan_helper", dead_labels)
        self.assertNotIn("get_order", dead_labels)        # Protected by route:/api/orders/{}
        self.assertNotIn("charge_card", dead_labels)      # Called by get_order
        self.assertNotIn("callback_sorter", dead_labels)  # Passed as CALL_REFERENCE (key=callback_sorter)
        self.assertNotIn("main", dead_labels)             # Entry point

    def test_jsx_tsx_resolution_and_component_edges(self):
        comp_dir = self.test_dir / "src" / "components"
        comp_dir.mkdir(parents=True)
        btn_jsx = comp_dir / "Button.jsx"
        btn_jsx.write_text(
            "export const ActionButton = ({ label }) => {\n"
            "  return <button>{label}</button>;\n"
            "};\n",
            encoding="utf-8",
        )
        app_tsx = self.test_dir / "src" / "pages" / "App.tsx"
        app_tsx.parent.mkdir(parents=True, exist_ok=True)
        app_tsx.write_text(
            "import { ActionButton } from '@/components/Button';\n"
            "import { MissingUtil } from '../utils/helper';\n"
            "export function AppView() {\n"
            "  return <div><ActionButton label='Save' /></div>;\n"
            "}\n",
            encoding="utf-8",
        )
        scanner = CodeAstScanner(self.test_dir, self.graph)
        scanner.scan_repository()

        self.assertIn("mod:src/components/Button.jsx", self.graph.nodes)
        self.assertIn("mod:src/pages/App.tsx", self.graph.nodes)
        self.assertIn("fn:src/components/Button.jsx::ActionButton", self.graph.nodes)
        self.assertIn("fn:src/pages/App.tsx::AppView", self.graph.nodes)

        # '@/components/Button' resolves to 'mod:src/components/Button.jsx' and '../utils/helper' collapses '..'
        self.assertIn("mod:src/components/Button.jsx", self.graph.adj_out["mod:src/pages/App.tsx"])
        self.assertIn("mod:src/utils/helper", self.graph.adj_out["mod:src/pages/App.tsx"])

        # JSX <ActionButton /> creates call edge from AppView to ActionButton
        blast = self.graph.compute_blast_radius("fn:src/components/Button.jsx::ActionButton")
        dep_ids = {d["id"] for d in blast["dependents"]}
        self.assertIn("fn:src/pages/App.tsx::AppView", dep_ids)

    def test_scoped_call_disambiguation_prevents_false_positives(self):
        pkg = self.test_dir / "pkg"
        pkg.mkdir(parents=True, exist_ok=True)
        a_py = pkg / "a.py"
        a_py.write_text("def save():\n    return 'a'\n", encoding="utf-8")
        b_py = pkg / "b.py"
        b_py.write_text("def save():\n    return 'b'\n", encoding="utf-8")
        caller_a = pkg / "caller_a.py"
        caller_a.write_text(
            "from .a import save\n"
            "def run_a():\n"
            "    return save()\n",
            encoding="utf-8",
        )
        scanner = CodeAstScanner(self.test_dir, self.graph)
        scanner.scan_repository()

        # Modifying pkg/b.py::save must NOT falsely flag pkg/caller_a.py::run_a
        blast_b = self.graph.compute_blast_radius("fn:pkg/b.py::save")
        b_deps = {d["id"] for d in blast_b["dependents"]}
        self.assertNotIn("fn:pkg/caller_a.py::run_a", b_deps)

        # Modifying pkg/a.py::save MUST flag pkg/caller_a.py::run_a
        blast_a = self.graph.compute_blast_radius("fn:pkg/a.py::save")
        a_deps = {d["id"] for d in blast_a["dependents"]}
        self.assertIn("fn:pkg/caller_a.py::run_a", a_deps)

    def test_shortest_path_between_nodes(self):
        self.graph.add_node("fn:a.py::funcA", "funcA", "function", "a.py")
        self.graph.add_node("fn:b.py::Order.calc_tax", "Order.calc_tax", "function", "b.py")
        self.graph.add_node("fn:c.py::funcC", "funcC", "function", "c.py")
        # Unqualified method call edge fn:calc_tax bridged to Order.calc_tax
        self.graph.add_edge("fn:a.py::funcA", "fn:calc_tax", "calls")
        self.graph.add_edge("fn:b.py::Order.calc_tax", "fn:c.py::funcC", "calls")

        fwd_path = self.graph.find_shortest_path("funcA", "funcC")
        self.assertIsNotNone(fwd_path)
        self.assertEqual([step["node"]["id"] for step in fwd_path], ["fn:a.py::funcA", "fn:b.py::Order.calc_tax", "fn:c.py::funcC"])
        self.assertEqual(fwd_path[1]["direction"], "->")

        rev_path = self.graph.find_shortest_path("funcC", "funcA")
        self.assertIsNotNone(rev_path)
        self.assertEqual([step["node"]["id"] for step in rev_path], ["fn:c.py::funcC", "fn:b.py::Order.calc_tax", "fn:a.py::funcA"])
        self.assertEqual(rev_path[2]["direction"], "<-")

    def test_incremental_cache_load_and_invalidation(self):
        p = self.test_dir / "mod1.py"
        p.write_text("def hello():\n    return 1\n", encoding="utf-8")
        cache_file = self.test_dir / "graph-out" / "graph.json"

        g1 = ArchitectureGraph()
        s1 = CodeAstScanner(self.test_dir, g1)
        s1.scan_or_load_cached(cache_file)
        self.assertTrue(cache_file.exists())
        self.assertIn("fn:mod1.py::hello", g1.nodes)

        # Second load with unchanged mtime hits cache
        g2 = ArchitectureGraph()
        s2 = CodeAstScanner(self.test_dir, g2)
        loaded_from_cache = s2.scan_or_load_cached(cache_file)
        self.assertTrue(loaded_from_cache)
        self.assertIn("fn:mod1.py::hello", g2.nodes)

        # Adding a new file invalidates cache and triggers rescan
        p2 = self.test_dir / "mod2.py"
        p2.write_text("def world():\n    return 2\n", encoding="utf-8")
        g3 = ArchitectureGraph()
        s3 = CodeAstScanner(self.test_dir, g3)
        loaded_after_change = s3.scan_or_load_cached(cache_file)
        self.assertFalse(loaded_after_change)
        self.assertIn("fn:mod2.py::world", g3.nodes)


if __name__ == "__main__":
    unittest.main()


