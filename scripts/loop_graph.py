#!/usr/bin/env python3
"""
Loop Graph — Deterministic Architecture Knowledge Graph & Blast Radius Engine
Pure Python Standard Library (Zero External Dependencies, Zero Token Cost).

Inspired by Graphify:
1. Deterministic AST & Lexical Extraction for Python, JS, and TS.
2. Invariants & Gate Integration: Links policy constraints (invariants.yaml, gate.yaml) to code.
3. Graph Topology Metrics: Identifies "God Nodes" (central hubs) and orphaned modules.
4. Blast Radius Calculator: Computes transitive downstream impact for any modified file or function.
5. Multi-format Exporters:
   - graph-out/graph.json: Machine-readable graph for AI agents (L3 Semantic Memory).
   - graph-out/GRAPH_REPORT.md: Architectural summary and God Nodes analysis.
   - graph-out/graph.html: Standalone, 100% offline interactive Canvas force-directed graph.
"""

import sys
import os
import re
import ast
import json
import math
import collections
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directories to ignore during scanning
IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".agent",
    ".agents", "dist", "build", ".gemini", "skills_backup", ".studio",
    "7-Phase-Agentic-Workflow", "ECC", "selfcompact_repo", "loop-engineering",
    "stock", "stock-autoresearch"
}

try:
    from loop_gate import normalize_path
except ImportError:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from loop_gate import normalize_path


class ArchitectureGraph:
    """Graph data structure holding nodes and directed edges."""

    def __init__(self):
        # node_id -> {id, label, type, file, details}
        self.nodes: Dict[str, Dict[str, Any]] = {}
        # list of {source, target, relation, confidence}
        self.edges: List[Dict[str, Any]] = []
        # Adjacency structures for fast graph traversal
        self.adj_out: Dict[str, Set[str]] = collections.defaultdict(set)
        self.adj_in: Dict[str, Set[str]] = collections.defaultdict(set)

    def add_node(self, node_id: str, label: str, node_type: str, file_path: str, **kwargs):
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "label": label,
                "type": node_type,  # 'module', 'class', 'function', 'policy', 'test'
                "file": normalize_path(file_path),
                **kwargs
            }

    def add_edge(self, source: str, target: str, relation: str, confidence: str = "EXTRACTED"):
        # Prevent exact duplicate edges
        edge_data = {
            "source": source,
            "target": target,
            "relation": relation,  # 'imports', 'calls', 'defines', 'governs', 'protects'
            "confidence": confidence
        }
        for e in self.edges:
            if e["source"] == source and e["target"] == target and e["relation"] == relation:
                return

        self.edges.append(edge_data)
        self.adj_out[source].add(target)
        self.adj_in[target].add(source)

    def compute_degree_metrics(self) -> Dict[str, Dict[str, int]]:
        """Calculate in-degree, out-degree, and total degree for each node."""
        metrics = {}
        for nid in self.nodes:
            in_deg = len(self.adj_in[nid])
            out_deg = len(self.adj_out[nid])
            metrics[nid] = {
                "in_degree": in_deg,
                "out_degree": out_deg,
                "total_degree": in_deg + out_deg
            }
        return metrics

    def get_god_nodes(self, top_n: int = 5) -> List[Tuple[str, Dict[str, Any], int]]:
        """Identify high-centrality God Nodes (system hubs)."""
        metrics = self.compute_degree_metrics()
        sorted_nodes = sorted(
            metrics.items(),
            key=lambda item: item[1]["total_degree"],
            reverse=True
        )
        god_nodes = []
        for nid, m in sorted_nodes[:top_n]:
            if m["total_degree"] > 0 and nid in self.nodes:
                god_nodes.append((nid, self.nodes[nid], m["total_degree"]))
        return god_nodes

    def compute_pagerank(
        self,
        focus: Optional[List[str]] = None,
        damping: float = 0.85,
        max_iter: int = 50,
        tol: float = 1e-6
    ) -> Dict[str, float]:
        """
        Compute Personalized PageRank over the architecture graph.
        Ranks flow along edges (A -> B means B is depended upon / called).
        """
        if not self.nodes:
            return {}

        n_nodes = len(self.nodes)
        node_keys = list(self.nodes.keys())
        uniform = 1.0 / n_nodes

        # Only edges between known nodes carry rank; external targets (e.g. stdlib imports) would leak mass.
        outs = {nid: [t for t in self.adj_out[nid] if t in self.nodes] for nid in node_keys}

        # Personalization: blend focus with uniform so nodes unreachable from focus still get a meaningful rank.
        # ponytail: fixed 0.7/0.3 blend, expose as CLI flag only if tuning is actually needed
        norm_focus = [normalize_path(f) for f in (focus or []) if f]
        hits = {
            nid for nid, ndata in self.nodes.items()
            if any(ndata.get("file", "") == f or ndata.get("file", "").endswith("/" + f) for f in norm_focus)
        }
        if hits:
            p = {nid: 0.7 * (1.0 / len(hits) if nid in hits else 0.0) + 0.3 * uniform for nid in node_keys}
        else:
            p = {nid: uniform for nid in node_keys}

        r = dict(p)
        for _ in range(max_iter):
            dangling_sum = sum(r[nid] for nid in node_keys if not outs[nid])
            r_new = {nid: (1.0 - damping + damping * dangling_sum) * p[nid] for nid in node_keys}
            for src in node_keys:
                if outs[src]:
                    share = damping * r[src] / len(outs[src])
                    for t in outs[src]:
                        r_new[t] += share

            diff = sum(abs(r_new[nid] - r[nid]) for nid in node_keys)
            r = r_new
            if diff < tol:
                break

        return r

    def render_repo_map(self, ranks: Dict[str, float], budget: int = 1024) -> str:
        """
        Render a token-budgeted repo map using PageRank scores.
        Only symbols with type in ('class', 'function') are candidate symbol lines.
        """
        if not ranks:
            return ""

        candidates = [
            nid for nid, ndata in self.nodes.items()
            if ndata.get("type") in ("class", "function") and nid in ranks
        ]
        if not candidates:
            return ""

        sorted_symbols = sorted(candidates, key=lambda nid: ranks.get(nid, 0.0), reverse=True)

        def format_for_k(k: int) -> str:
            if k <= 0:
                return ""
            chosen = sorted_symbols[:k]
            file_groups: Dict[str, List[Tuple[str, str, float]]] = collections.defaultdict(list)
            for nid in chosen:
                ndata = self.nodes[nid]
                fpath = ndata.get("file", "unknown")
                stype = ndata.get("type", "function")
                slabel = ndata.get("label", nid)
                srank = ranks.get(nid, 0.0)
                file_groups[fpath].append((stype, slabel, srank))

            # Sort files descending by the sum of ranks of chosen symbols in that file
            sorted_files = sorted(
                file_groups.items(),
                key=lambda item: sum(s[2] for s in item[1]),
                reverse=True
            )

            lines = []
            for fpath, syms in sorted_files:
                lines.append(fpath)
                syms_sorted = sorted(syms, key=lambda s: s[2], reverse=True)
                for stype, slabel, _ in syms_sorted:
                    lines.append(f"  - {stype} {slabel}")
            return "\n".join(lines)

        # Binary search for maximum K such that token estimate <= budget
        # ponytail: chars/4 heuristic, 換成真 tokenizer 時再改
        low = 0
        high = len(sorted_symbols)
        best_text = ""

        while low <= high:
            mid = (low + high) // 2
            rendered = format_for_k(mid)
            est_tokens = math.ceil(len(rendered) / 4) if rendered else 0
            if est_tokens <= budget:
                best_text = rendered
                low = mid + 1
            else:
                high = mid - 1

        return best_text

    def _bfs_dependents(self, seed_ids: List[str]) -> Dict[str, Any]:
        """BFS backwards along incoming edges (including unqualified fn:<label> call edges)."""
        visited = set(seed_ids)
        queue = collections.deque(seed_ids)
        direct_dependents: Set[str] = set()
        transitive_dependents: Set[str] = set()
        depth_map = {nid: 0 for nid in seed_ids}

        while queue:
            curr = queue.popleft()
            curr_depth = depth_map[curr]
            incoming = set(self.adj_in[curr])
            if curr in self.nodes and self.nodes[curr].get("type") in ("function", "class", "test"):
                lbl = self.nodes[curr].get("label", "")
                if lbl:
                    incoming |= self.adj_in.get(f"fn:{lbl}", set())
                    if "." in lbl:
                        incoming |= self.adj_in.get(f"fn:{lbl.split('.')[-1]}", set())

            for parent in incoming:
                # Do not walk backwards along `mod -> fn/cls` ('defines' containment edges),
                # otherwise editing one method leaks into its module node and flags every importer.
                if curr.startswith(("fn:", "cls:")) and parent.startswith("mod:"):
                    for pol in self.adj_in.get(parent, set()):
                        if pol.startswith("policy:") and pol not in visited:
                            visited.add(pol)
                            depth_map[pol] = curr_depth + 1
                            direct_dependents.add(pol)
                    continue
                if parent not in visited:
                    visited.add(parent)
                    depth_map[parent] = curr_depth + 1
                    queue.append(parent)
                    if curr_depth == 0:
                        direct_dependents.add(parent)
                    else:
                        transitive_dependents.add(parent)

        all_affected_nodes = [
            {
                "id": nid,
                "label": self.nodes[nid]["label"],
                "type": self.nodes[nid]["type"],
                "file": self.nodes[nid]["file"],
                "depth": depth_map.get(nid, 1)
            }
            for nid in (direct_dependents | transitive_dependents)
            if nid in self.nodes
        ]
        impacted_tests = list({
            n["file"] for n in all_affected_nodes
            if n["type"] == "test" or "test" in n["file"].lower()
        })
        governing_policies = list({
            n["label"] for n in all_affected_nodes
            if n["type"] == "policy"
        })
        return {
            "direct_count": len(direct_dependents),
            "transitive_count": len(transitive_dependents),
            "total_blast_radius": len(all_affected_nodes),
            "impacted_tests": impacted_tests,
            "governing_policies": governing_policies,
            "dependents": all_affected_nodes,
        }

    def compute_blast_radius(self, target_query: str) -> Dict[str, Any]:
        """
        Perform BFS traversal backwards along incoming edges (who depends on target?)
        to determine blast radius of changes.
        """
        norm_query = normalize_path(target_query).lower()
        matched_query_ids = [
            nid for nid, data in self.nodes.items()
            if norm_query in nid.lower() or norm_query in data.get("file", "").lower() or norm_query == data["label"].lower()
        ]
        if not matched_query_ids:
            return {"target": target_query, "matched_nodes": [], "blast_radius_count": 0, "dependents": []}

        bfs = self._bfs_dependents(matched_query_ids)
        return {
            "target": target_query,
            "matched_nodes": matched_query_ids,
            **bfs,
        }

    def seeds_for_file(self, file_path: str, ranges: List[Tuple[int, int]]) -> List[str]:
        """
        Innermost-symbol seeding (inspired by Trail-Code blast.ts):
        Given modified line ranges in `file_path`, return only the innermost symbols
        whose spans overlap the edit (dropping outer classes when a method is edited).
        Falls back to module node if edit is outside all symbols.
        """
        norm_file = normalize_path(file_path)
        symbols = [
            data for data in self.nodes.values()
            if data.get("file") == norm_file
            and data.get("type") in ("function", "class", "test")
            and isinstance(data.get("start_line"), int)
            and isinstance(data.get("end_line"), int)
        ]
        overlapping = [
            s for s in symbols
            if any(s["start_line"] <= r_end and s["end_line"] >= r_start for r_start, r_end in ranges)
        ]
        hit_ids = [
            s["id"] for s in overlapping
            if not any(
                o["id"] != s["id"]
                and o["start_line"] >= s["start_line"]
                and o["end_line"] <= s["end_line"]
                and (o["start_line"] > s["start_line"] or o["end_line"] < s["end_line"])
                for o in overlapping
            )
        ]
        if not hit_ids and f"mod:{norm_file}" in self.nodes:
            hit_ids.append(f"mod:{norm_file}")
        return hit_ids

    def compute_diff_blast_radius(self, diff_text: str) -> Dict[str, Any]:
        """
        Compute symbol-precise blast radius and TestSignal ('changed' | 'stale' | 'none' | 'na')
        directly from a unified git diff.
        """
        changed_map = parse_diff_ranges(diff_text)
        changed_files = list(changed_map.keys())
        seeds: List[str] = []
        for fpath, line_ranges in changed_map.items():
            for sid in self.seeds_for_file(fpath, line_ranges):
                if sid not in seeds:
                    seeds.append(sid)

        bfs = self._bfs_dependents(seeds) if seeds else {
            "direct_count": 0, "transitive_count": 0, "total_blast_radius": 0,
            "impacted_tests": [], "governing_policies": [], "dependents": []
        }

        changed_test_files = [
            f for f in changed_files
            if "test" in f.lower() or self.nodes.get(f"mod:{f}", {}).get("type") == "test"
        ]
        behavioral_seeds = [
            sid for sid in seeds
            if self.nodes.get(sid, {}).get("type") in ("function", "class")
        ]

        if changed_test_files:
            test_signal = "changed"
        elif bfs["impacted_tests"]:
            test_signal = "stale"
        elif behavioral_seeds:
            test_signal = "none"
        else:
            test_signal = "na"

        return {
            "changed_files": changed_files,
            "seeds": seeds,
            "seed_labels": [self.nodes[s]["label"] for s in seeds if s in self.nodes],
            "test_signal": test_signal,
            "changed_test_files": changed_test_files,
            **bfs,
        }

    def find_dead_code_candidates(self) -> List[Dict[str, Any]]:
        """
        Identify functions with zero incoming callers (excluding entry points, tests, dunders, and route handlers).
        Inspired by codebase-memory-mcp Dead Code Candidates.
        """
        entry_names = {"main", "setup", "teardown", "setUp", "tearDown", "run_self_tests"}
        candidates: List[Dict[str, Any]] = []
        for nid, data in self.nodes.items():
            if data.get("type") != "function":
                continue
            lbl = data.get("label", "")
            short_name = lbl.split(".")[-1]
            if (
                lbl in entry_names
                or short_name in entry_names
                or short_name.startswith("test_")
                or (short_name.startswith("__") and short_name.endswith("__"))
            ):
                continue
            callers = {p for p in self.adj_in.get(nid, set()) if not p.startswith("mod:")} - {nid}
            callers |= self.adj_in.get(f"fn:{lbl}", set()) - {nid}
            if "." in lbl:
                callers |= self.adj_in.get(f"fn:{short_name}", set()) - {nid}
            if not callers:
                candidates.append({
                    "id": nid,
                    "label": lbl,
                    "file": data.get("file", ""),
                    "start_line": data.get("start_line", 1),
                })
        return sorted(candidates, key=lambda c: (c["file"], c["start_line"], c["label"]))


def _normalize_route(raw_path: str) -> str:
    """Normalize dynamic route placeholders (:id, {id}, <int:id>, ${id}, /123) to '{}' for cross-service matching."""
    path = raw_path.split("?")[0].strip()
    if not path.startswith("/"):
        m = re.search(r"(/api/[^\s'\"`?#]+)", path)
        path = m.group(1) if m else "/" + path
    path = re.sub(r"\$\{[^}]+\}|\{[^{}]+\}|<[^>]+>|:[A-Za-z_][A-Za-z0-9_]*|(?<=/)\d+(?=/|$)", "{}", path)
    return path.rstrip("/") or "/"


def parse_diff_ranges(diff_text: str) -> Dict[str, List[Tuple[int, int]]]:
    """Parse unified diff into {normalized_file_path: [(start_line, end_line), ...]} of actual modified lines."""
    ranges: Dict[str, List[Tuple[int, int]]] = collections.defaultdict(list)
    curr_file: Optional[str] = None
    new_line = 0
    in_hunk = False

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("+++ "):
            target = raw_line[4:].split("\t")[0].strip()
            if target == "/dev/null":
                curr_file = None
            else:
                if target.startswith("b/"):
                    target = target[2:]
                curr_file = normalize_path(target)
            in_hunk = False
        elif raw_line.startswith("@@ ") and curr_file:
            m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", raw_line)
            if m:
                new_line = int(m.group(1))
                new_len = int(m.group(2)) if m.group(2) is not None else 1
                in_hunk = True
                if new_len == 0:
                    ranges[curr_file].append((max(1, new_line), max(1, new_line)))
        elif in_hunk and curr_file:
            if raw_line.startswith("+"):
                ranges[curr_file].append((new_line, new_line))
                new_line += 1
            elif raw_line.startswith("-"):
                ranges[curr_file].append((max(1, new_line - 1), max(1, new_line)))
            elif raw_line.startswith(" "):
                new_line += 1
            elif raw_line.startswith("\\"):
                pass
            else:
                in_hunk = False

    return dict(ranges)


class CodeAstScanner:
    """Deterministic AST & Lexical scanner for Python and JavaScript/TypeScript."""

    def __init__(self, root_dir: Path, graph: ArchitectureGraph):
        self.root = root_dir
        self.graph = graph

    def scan_repository(self):
        """Walk repo and parse code files, policies, and tests."""
        js_files: List[Tuple[Path, str]] = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            # Filter out ignored directories
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]

            for fname in filenames:
                full_path = Path(dirpath) / fname
                rel_path = normalize_path(str(full_path.relative_to(self.root)))

                if fname.endswith(".py"):
                    self.parse_python_file(full_path, rel_path)
                elif fname.endswith((".js", ".ts", ".mjs")):
                    js_files.append((full_path, rel_path))

        if js_files:
            self.parse_js_files_batch(js_files)

        # Parse system policies
        self.parse_system_policies()

    def parse_js_files_batch(self, js_files: List[Tuple[Path, str]]):
        """Batch-extract AST from all JS/TS files in a single Node process."""
        swc_script = REPO_ROOT / "scripts" / "swc_extractor.js"
        if swc_script.exists() and js_files:
            try:
                payload = json.dumps([str(fp) for fp, _ in js_files])
                proc = subprocess.run(
                    ["node", str(swc_script), "--batch"],
                    input=payload,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=20
                )
                if proc.returncode == 0:
                    results = json.loads(proc.stdout)
                    if isinstance(results, list):
                        by_path = {
                            normalize_path(str(r.get("file", ""))): r
                            for r in results if isinstance(r, dict)
                        }
                        for full_path, rel_path in js_files:
                            data = by_path.get(normalize_path(str(full_path)))
                            if data and not data.get("error"):
                                self._integrate_swc_results(data, rel_path)
                            else:
                                self._parse_js_lexical_fallback(full_path, rel_path)
                        return
            except Exception:
                pass

        for full_path, rel_path in js_files:
            self._parse_js_lexical_fallback(full_path, rel_path)

    def _extract_cross_layer_edges(self, snippet: str, rel_path: str, owner_id: str):
        """Extract cross-layer CONFIGURES (env:<KEY>) and HTTP_CALLS (route:/...) edges."""
        # 1. CONFIGURES: Env Var writers (env:KEY -> owner) & readers (owner -> env:KEY)
        for m in re.findall(r"""(?:os\.environ\s*\[\s*['"]([A-Z0-9_]+)['"]\s*\]|process\.env\.([A-Z0-9_]+))\s*=(?!=)""", snippet):
            key = m[0] or m[1]
            env_id = f"env:{key}"
            self.graph.add_node(env_id, label=key, node_type="env", file_path=rel_path)
            self.graph.add_edge(env_id, owner_id, relation="configures")
        for m in re.findall(
            r"""(?:os\.getenv\s*\(\s*['"]([A-Z0-9_]+)['"]|os\.environ\.get\s*\(\s*['"]([A-Z0-9_]+)['"]|os\.environ\s*\[\s*['"]([A-Z0-9_]+)['"]\s*\](?!\s*=(?!=))|(?:process\.env|import\.meta\.env)\.([A-Z0-9_]+)(?!\s*=(?!=)))""",
            snippet,
        ):
            key = next((k for k in m if k), "")
            if key:
                env_id = f"env:{key}"
                self.graph.add_node(env_id, label=key, node_type="env", file_path=rel_path)
                self.graph.add_edge(owner_id, env_id, relation="configures")

        # 2. HTTP_CALLS: Server route definitions (route:/... -> owner) & client calls (owner -> route:/...)
        for raw_route in re.findall(
            r"""(?:@(?:app|router|bp|api)\.(?:route|get|post|put|delete|patch)|\b(?:app|router|Route)\s*(?:\.|::)\s*(?:get|post|put|delete|patch))\s*\(\s*['"]([^'"]+)['"]""",
            snippet,
        ):
            norm_r = _normalize_route(raw_route)
            rid = f"route:{norm_r}"
            self.graph.add_node(rid, label=norm_r, node_type="route", file_path=rel_path)
            self.graph.add_edge(rid, owner_id, relation="http_route")

        for raw_url in re.findall(
            r"""\b(?:fetch|(?:axios|requests|http|client)\.(?:get|post|put|delete|patch))\s*\(\s*[`'"]([^`'"]*?/api/[^`'"]*)[`'"]""",
            snippet,
        ):
            norm_r = _normalize_route(raw_url)
            rid = f"route:{norm_r}"
            self.graph.add_node(rid, label=norm_r, node_type="route", file_path=rel_path)
            self.graph.add_edge(owner_id, rid, relation="http_calls")

    def parse_python_file(self, full_path: Path, rel_path: str):
        """Use Python's built-in AST parser to extract symbols and dependencies."""
        try:
            source = full_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(full_path))
        except SyntaxError:
            return

        source_lines = source.splitlines()
        covered_lines: Set[int] = set()
        is_test = "test" in rel_path.lower()
        mod_type = "test" if is_test else "module"
        mod_id = f"mod:{rel_path}"
        self.graph.add_node(mod_id, label=Path(rel_path).name, node_type=mod_type, file_path=rel_path)

        for node in ast.walk(tree):
            # 1. Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target_mod = f"mod:{alias.name.replace('.', '/')}.py"
                    self.graph.add_edge(mod_id, target_mod, relation="imports")
            elif isinstance(node, ast.ImportFrom) and node.module:
                target_mod = f"mod:{node.module.replace('.', '/')}.py"
                self.graph.add_edge(mod_id, target_mod, relation="imports")

            # 2. Classes
            elif isinstance(node, ast.ClassDef):
                cls_id = f"cls:{rel_path}::{node.name}"
                self.graph.add_node(
                    cls_id,
                    label=node.name,
                    node_type="class",
                    file_path=rel_path,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                )
                self.graph.add_edge(mod_id, cls_id, relation="defines")

            # 3. Functions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_id = f"fn:{rel_path}::{node.name}"
                fn_type = "test" if node.name.startswith("test_") or is_test else "function"
                end_l = getattr(node, "end_lineno", node.lineno)
                dec_start = min([node.lineno] + [getattr(d, "lineno", node.lineno) for d in getattr(node, "decorator_list", [])])
                self.graph.add_node(
                    func_id,
                    label=node.name,
                    node_type=fn_type,
                    file_path=rel_path,
                    start_line=dec_start,
                    end_line=end_l,
                )
                self.graph.add_edge(mod_id, func_id, relation="defines")
                covered_lines.update(range(dec_start, end_l + 1))
                fn_src = "\n".join(source_lines[max(0, dec_start - 1) : end_l])
                self._extract_cross_layer_edges(fn_src, rel_path, func_id)

                # Function calls & callback references (CALL_REFERENCE) inside function
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            self.graph.add_edge(func_id, f"fn:{child.func.id}", relation="calls")
                        elif isinstance(child.func, ast.Attribute):
                            self.graph.add_edge(func_id, f"fn:{child.func.attr}", relation="calls")
                        for arg in list(child.args) + [kw.value for kw in child.keywords]:
                            if isinstance(arg, ast.Name):
                                self.graph.add_edge(func_id, f"fn:{arg.id}", relation="calls")

        top_src = "\n".join(line for idx, line in enumerate(source_lines, 1) if idx not in covered_lines)
        if top_src:
            self._extract_cross_layer_edges(top_src, rel_path, mod_id)

    def parse_js_file(self, full_path: Path, rel_path: str):
        """
        Deterministic AST Parsing for JavaScript / TypeScript files via @swc/core.
        Fallback gracefully to lexical regex scanning if Node or @swc/core is unavailable.
        Zero test mocks. Zero artificial hooks.
        """
        # 1. 若環境中存在 swc_extractor.js，優先以單檔 AST 抽取
        swc_script = REPO_ROOT / "scripts" / "swc_extractor.js"
        if swc_script.exists():
            try:
                proc = subprocess.run(
                    ["node", str(swc_script), str(full_path)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=10
                )
                if proc.returncode == 0:
                    data = json.loads(proc.stdout)
                    if not data.get("error"):
                        self._integrate_swc_results(data, rel_path)
                        return
            except Exception:
                pass  # Node 或依賴未就緒時，由純標準庫正則引擎自動接管

        # 2. 純標準庫正則引擎平滑降級 (100% 零崩潰保證)
        self._parse_js_lexical_fallback(full_path, rel_path)

    def _integrate_swc_results(self, data: Dict[str, Any], rel_path: str):
        """將 swc_extractor.js 回傳之 AST 拓撲實體整合入架構圖譜"""
        is_test = "test" in rel_path.lower()
        mod_type = "test" if is_test else "module"
        mod_id = f"mod:{rel_path}"
        self.graph.add_node(mod_id, label=Path(rel_path).name, node_type=mod_type, file_path=rel_path)

        full_path = self.root / rel_path
        source_lines = full_path.read_text(encoding="utf-8", errors="replace").splitlines() if full_path.exists() else []
        covered_lines: Set[int] = set()

        for imp in data.get("imports", []):
            target = imp.get("source", "")
            if target.startswith("."):
                resolved = (Path(rel_path).parent / target).as_posix()
                target_id = f"mod:{normalize_path(resolved)}"
            else:
                target_id = f"mod:{target}"
            self.graph.add_edge(mod_id, target_id, relation="imports")

        for d in data.get("definitions", []):
            name = d.get("name")
            dtype = d.get("type")
            s_line = d.get("line")
            e_line = d.get("endLine", s_line)
            if dtype == "class":
                cid = f"cls:{rel_path}::{name}"
                self.graph.add_node(cid, label=name, node_type="class", file_path=rel_path, start_line=s_line, end_line=e_line)
                self.graph.add_edge(mod_id, cid, relation="defines")
            else:
                fid = f"fn:{rel_path}::{name}"
                fn_type = "test" if "test" in name.lower() or is_test else "function"
                self.graph.add_node(fid, label=name, node_type=fn_type, file_path=rel_path, start_line=s_line, end_line=e_line)
                self.graph.add_edge(mod_id, fid, relation="defines")
                if isinstance(s_line, int) and isinstance(e_line, int) and source_lines:
                    covered_lines.update(range(s_line, e_line + 1))
                    self._extract_cross_layer_edges("\n".join(source_lines[max(0, s_line - 1) : e_line]), rel_path, fid)

        if source_lines:
            top_src = "\n".join(line for idx, line in enumerate(source_lines, 1) if idx not in covered_lines)
            if top_src:
                self._extract_cross_layer_edges(top_src, rel_path, mod_id)

        for c in data.get("calls", []):
            caller = c.get("caller")
            callee = c.get("callee")
            if caller and callee and caller != "(top-level)":
                caller_id = f"fn:{rel_path}::{caller}"
                callee_id = f"fn:{callee}"
                self.graph.add_edge(caller_id, callee_id, relation="calls")

    def _parse_js_lexical_fallback(self, full_path: Path, rel_path: str):
        """保留原有正則表達式掃描機制作為純標準庫穩定 Fallback"""
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return

        is_test = "test" in rel_path.lower()
        mod_type = "test" if is_test else "module"
        mod_id = f"mod:{rel_path}"
        self.graph.add_node(mod_id, label=Path(rel_path).name, node_type=mod_type, file_path=rel_path)

        import_matches = re.findall(r"""(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\))""", content)
        for m in import_matches:
            target = m[0] or m[1]
            if target.startswith("."):
                resolved = (Path(rel_path).parent / target).as_posix()
                target_id = f"mod:{normalize_path(resolved)}"
            else:
                target_id = f"mod:{target}"
            self.graph.add_edge(mod_id, target_id, relation="imports")

        decl_matches = list(re.finditer(r"""(?:function\s+([A-Za-z0-9_]+)|class\s+([A-Za-z0-9_]+))""", content))
        if not decl_matches:
            self._extract_cross_layer_edges(content, rel_path, mod_id)
            return
        if decl_matches[0].start() > 0:
            self._extract_cross_layer_edges(content[: decl_matches[0].start()], rel_path, mod_id)
        for idx, m in enumerate(decl_matches):
            fn_name, cls_name = m.group(1), m.group(2)
            end_pos = decl_matches[idx + 1].start() if idx + 1 < len(decl_matches) else len(content)
            chunk = content[m.start() : end_pos]
            if fn_name:
                fid = f"fn:{rel_path}::{fn_name}"
                fn_type = "test" if "test" in fn_name.lower() or is_test else "function"
                self.graph.add_node(fid, label=fn_name, node_type=fn_type, file_path=rel_path)
                self.graph.add_edge(mod_id, fid, relation="defines")
                self._extract_cross_layer_edges(chunk, rel_path, fid)
            elif cls_name:
                cid = f"cls:{rel_path}::{cls_name}"
                self.graph.add_node(cid, label=cls_name, node_type="class", file_path=rel_path)
                self.graph.add_edge(mod_id, cid, relation="defines")
                self._extract_cross_layer_edges(chunk, rel_path, cid)

    def parse_system_policies(self):
        """Parse invariants.yaml, gate.yaml, and link policy nodes to code."""
        # 1. Invariants
        invariants_file = self.root / "invariants.yaml"
        if invariants_file.exists():
            content = invariants_file.read_text(encoding="utf-8", errors="replace")
            # Extract invariant IDs and names
            inv_matches = re.findall(r"""-\s*id:\s*([A-Z0-9_]+)\s*\n\s*name:\s*["']?([^"'\n]+)""", content)
            for inv_id, inv_name in inv_matches:
                policy_id = f"policy:{inv_id}"
                self.graph.add_node(
                    policy_id,
                    label=f"{inv_id} ({inv_name.strip()})",
                    node_type="policy",
                    file_path="invariants.yaml"
                )
                # Link policy to relevant modules heuristic
                if "SAFE" in inv_id or "SECURITY" in inv_id:
                    self.graph.add_edge(policy_id, "mod:scripts/loop_drift.py", relation="governs")
                    self.graph.add_edge(policy_id, "mod:scripts/loop_gate.py", relation="governs")
                elif "STATE" in inv_id:
                    self.graph.add_edge(policy_id, "mod:STATE.md", relation="governs")
                elif "SCOPE" in inv_id:
                    self.graph.add_edge(policy_id, "mod:gate.yaml", relation="governs")

        # 2. Gatekeeper
        gate_file = self.root / "gate.yaml"
        if gate_file.exists():
            self.graph.add_node("policy:GATE_KEEPER", label="gate.yaml (Physical Denylist)", node_type="policy", file_path="gate.yaml")
            self.graph.add_edge("policy:GATE_KEEPER", "mod:scripts/loop_gate.py", relation="protects")
            self.graph.add_edge("policy:GATE_KEEPER", "mod:scripts/loop_drift.py", relation="protects")


class GraphVisualizer:
    """Generates a standalone, zero-dependency, 100% offline interactive Canvas HTML graph."""

    @staticmethod
    def render_html(graph: ArchitectureGraph) -> str:
        nodes_data = []
        # Assign colors based on node type
        color_map = {
            "module": "#3b82f6",     # Blue
            "function": "#06b6d4",   # Cyan
            "class": "#8b5cf6",      # Purple
            "policy": "#f59e0b",     # Amber / Gold
            "test": "#10b981"        # Emerald Green
        }

        for nid, data in graph.nodes.items():
            nodes_data.append({
                "id": nid,
                "label": data["label"],
                "type": data["type"],
                "file": data.get("file", ""),
                "color": color_map.get(data["type"], "#6b7280"),
                "radius": 14 if data["type"] in ["module", "policy"] else 8
            })

        edges_data = [
            {"source": e["source"], "target": e["target"], "relation": e["relation"]}
            for e in graph.edges
            if e["source"] in graph.nodes and e["target"] in graph.nodes
        ]

        # Embedded standalone HTML5 Canvas simulation with physics, search, and Macro/Micro mode
        return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <title>Loop Graph — Architecture Knowledge Graph</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #0f172a; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; overflow: hidden; display: flex; height: 100vh; }}
    #canvas-container {{ flex: 1; position: relative; height: 100%; }}
    canvas {{ width: 100%; height: 100%; display: block; }}
    #sidebar {{ width: 360px; background: #1e293b; border-left: 1px solid #334155; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; box-shadow: -4px 0 24px rgba(0,0,0,0.4); }}
    h1 {{ font-size: 1.15rem; color: #38bdf8; display: flex; align-items: center; justify-content: space-between; }}
    .stats-badge {{ background: #0ea5e9; color: #fff; font-size: 0.75rem; padding: 2px 8px; border-radius: 12px; }}
    
    /* Search Bar */
    .search-box {{ position: relative; }}
    .search-input {{ width: 100%; background: #0f172a; border: 1px solid #334155; color: #f8fafc; padding: 8px 12px; border-radius: 6px; font-size: 0.85rem; outline: none; transition: border-color 0.2s; }}
    .search-input:focus {{ border-color: #38bdf8; box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2); }}
    
    /* View Mode Switcher */
    .mode-switcher {{ display: flex; background: #0f172a; border-radius: 8px; padding: 3px; border: 1px solid #334155; gap: 4px; }}
    .mode-btn {{ flex: 1; padding: 6px 10px; font-size: 0.78rem; border: none; border-radius: 6px; background: transparent; color: #94a3b8; cursor: pointer; transition: all 0.2s; font-weight: 500; text-align: center; }}
    .mode-btn.active {{ background: #38bdf8; color: #0f172a; font-weight: 600; shadow: 0 2px 8px rgba(56,189,248,0.3); }}

    /* Legend & Filter */
    .legend {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 0.78rem; background: #0f172a; padding: 10px; border-radius: 8px; border: 1px solid #334155; }}
    .legend-item {{ display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none; }}
    .legend-item.dimmed {{ opacity: 0.35; text-decoration: line-through; }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; }}
    
    .info-card {{ background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155; font-size: 0.85rem; }}
    .info-card h3 {{ font-size: 0.85rem; color: #94a3b8; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; display: flex; justify-content: space-between; }}
    .tag {{ display: inline-block; background: #334155; color: #cbd5e1; font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; margin-right: 4px; }}
    .instructions {{ font-size: 0.75rem; color: #64748b; line-height: 1.4; border-top: 1px solid #334155; padding-top: 10px; margin-top: auto; }}
    .action-btn {{ background: #334155; color: #f1f5f9; border: 1px solid #475569; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; cursor: pointer; }}
    .action-btn:hover {{ background: #475569; }}
  </style>
</head>
<body>
  <div id="canvas-container">
    <canvas id="graphCanvas"></canvas>
  </div>
  <div id="sidebar">
    <h1>
      <span>🕸️ Loop Graph</span>
      <span class="stats-badge" id="visibleCount">{len(nodes_data)} Nodes</span>
    </h1>

    <!-- Mode Switcher -->
    <div class="mode-switcher">
      <button class="mode-btn active" id="btnMacro" onclick="switchMode('macro')">🌐 鳥瞰模式 (Macro)</button>
      <button class="mode-btn" id="btnMicro" onclick="switchMode('micro')">🌌 全息星系 (Micro)</button>
    </div>

    <!-- Search Box -->
    <div class="search-box">
      <input type="text" id="searchInput" class="search-input" placeholder="🔍 搜尋模組、函數或政策 (Enter)..." />
    </div>

    <!-- Legend -->
    <div class="legend">
      <div class="legend-item" id="flt-module" onclick="toggleType('module')"><span class="dot" style="background:#3b82f6;"></span> Module</div>
      <div class="legend-item" id="flt-policy" onclick="toggleType('policy')"><span class="dot" style="background:#f59e0b;"></span> Policy/Gate</div>
      <div class="legend-item" id="flt-test" onclick="toggleType('test')"><span class="dot" style="background:#10b981;"></span> Test</div>
      <div class="legend-item dimmed" id="flt-class" onclick="toggleType('class')"><span class="dot" style="background:#8b5cf6;"></span> Class</div>
      <div class="legend-item dimmed" id="flt-function" onclick="toggleType('function')"><span class="dot" style="background:#06b6d4;"></span> Function</div>
    </div>
    
    <div class="info-card" id="node-info">
      <h3>節點檢視 (Inspector)</h3>
      <p style="color:#94a3b8; font-size:0.8rem;">點選任一節點以檢視關聯鏈條，或透過搜尋聚焦。</p>
    </div>

    <div class="info-card">
      <h3>圖譜統計 (Stats) <button class="action-btn" onclick="resetView()">重設視角</button></h3>
      <p style="font-size:0.8rem;">全庫實體總數：<strong>{len(nodes_data)}</strong></p>
      <p style="font-size:0.8rem;">拓撲關聯邊數：<strong>{len(edges_data)}</strong></p>
      <p style="font-size:0.8rem; color:#38bdf8; margin-top:4px;" id="modeHint">當前處於：鳥瞰架構模式 (聚焦核心模組與政策)</p>
    </div>

    <div class="instructions">
      💡 <strong>操作指南</strong>：<br>
      • 鳥瞰模式：自動隱藏細碎函式，清晰閱覽晶片級架構<br>
      • 全息模式：展開 4,484 節點完整呼叫網絡<br>
      • 滾輪縮放 / 拖曳平移 / 點擊節點高亮鄰接鏈條
    </div>
  </div>

  <script>
    const rawNodes = {json.dumps(nodes_data, ensure_ascii=False)};
    const rawEdges = {json.dumps(edges_data, ensure_ascii=False)};

    const canvas = document.getElementById('graphCanvas');
    const ctx = canvas.getContext('2d');
    const container = document.getElementById('canvas-container');

    let width, height;
    function resize() {{
      width = container.clientWidth;
      height = container.clientHeight;
      canvas.width = width * window.devicePixelRatio;
      canvas.height = height * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }}
    window.addEventListener('resize', resize);
    resize();

    // Node state with random circle distribution
    const allNodes = rawNodes.map((n, i) => {{
      const angle = (i / rawNodes.length) * 2 * Math.PI;
      const r = 220 + Math.random() * 200;
      return {{
        ...n,
        x: width / 2 + r * Math.cos(angle),
        y: height / 2 + r * Math.sin(angle),
        vx: 0,
        vy: 0
      }};
    }});

    const nodeMap = new Map(allNodes.map(n => [n.id, n]));
    const allEdges = rawEdges.map(e => ({{
      ...e,
      sourceNode: nodeMap.get(e.source),
      targetNode: nodeMap.get(e.target)
    }})).filter(e => e.sourceNode && e.targetNode);

    // View state
    let viewMode = 'macro'; // 'macro' or 'micro'
    const typeFilters = {{
      module: true,
      policy: true,
      test: true,
      class: false,
      function: false
    }};

    function isNodeVisible(n) {{
      if (viewMode === 'macro') {{
        return n.type === 'module' || n.type === 'policy' || n.type === 'test';
      }}
      return typeFilters[n.type] === true;
    }}

    let scale = 1;
    let offsetX = 0;
    let offsetY = 0;
    let selectedNode = null;
    let draggedNode = null;
    let isPanning = false;
    let startX, startY;

    function switchMode(mode) {{
      viewMode = mode;
      document.getElementById('btnMacro').classList.toggle('active', mode === 'macro');
      document.getElementById('btnMicro').classList.toggle('active', mode === 'micro');
      
      const hint = document.getElementById('modeHint');
      if (mode === 'macro') {{
        hint.innerText = "當前處於：鳥瞰架構模式 (聚焦核心模組與政策)";
        ['class', 'function'].forEach(t => {{
          typeFilters[t] = false;
          const el = document.getElementById('flt-' + t);
          if (el) el.classList.add('dimmed');
        }});
      }} else {{
        hint.innerText = "當前處於：全息星系模式 (4,484 完整節點)";
        ['module', 'policy', 'test', 'class', 'function'].forEach(t => {{
          typeFilters[t] = true;
          const el = document.getElementById('flt-' + t);
          if (el) el.classList.remove('dimmed');
        }});
      }}
      updateNodeCount();
    }}

    function toggleType(type) {{
      if (viewMode === 'macro') {{
        switchMode('micro');
      }}
      typeFilters[type] = !typeFilters[type];
      const el = document.getElementById('flt-' + type);
      if (el) el.classList.toggle('dimmed', !typeFilters[type]);
      updateNodeCount();
    }}

    function updateNodeCount() {{
      const count = allNodes.filter(isNodeVisible).length;
      document.getElementById('visibleCount').innerText = count + " Nodes";
    }}

    function resetView() {{
      scale = 1;
      offsetX = 0;
      offsetY = 0;
      selectedNode = null;
    }}

    function focusNode(node) {{
      selectedNode = node;
      scale = 1.6;
      offsetX = (width / 2) - node.x * scale;
      offsetY = (height / 2) - node.y * scale;
      updateInspector(node);
    }}

    // Search Box
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('keydown', e => {{
      if (e.key === 'Enter') {{
        const q = searchInput.value.trim().toLowerCase();
        if (!q) return;
        const match = allNodes.find(n => n.label.toLowerCase().includes(q) || n.file.toLowerCase().includes(q));
        if (match) {{
          if (!isNodeVisible(match)) {{
            switchMode('micro');
          }}
          focusNode(match);
        }} else {{
          alert('查無符合節點: ' + q);
        }}
      }}
    }});

    // Force simulation step
    function stepSimulation(visNodes, visEdges) {{
      const nLen = visNodes.length;
      const k = Math.min(nLen, 400); // cap computation for ultra large set
      for (let i = 0; i < k; i++) {{
        for (let j = i + 1; j < k; j++) {{
          const dx = visNodes[j].x - visNodes[i].x;
          const dy = visNodes[j].y - visNodes[i].y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          if (dist < 260) {{
            const force = 100 / (dist * dist);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            visNodes[i].vx -= fx;
            visNodes[i].vy -= fy;
            visNodes[j].vx += fx;
            visNodes[j].vy += fy;
          }}
        }}
      }}

      visEdges.forEach(e => {{
        const dx = e.targetNode.x - e.sourceNode.x;
        const dy = e.targetNode.y - e.sourceNode.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const spring = (dist - 90) * 0.005;
        e.sourceNode.vx += (dx / dist) * spring;
        e.sourceNode.vy += (dy / dist) * spring;
        e.targetNode.vx -= (dx / dist) * spring;
        e.targetNode.vy -= (dy / dist) * spring;
      }});

      visNodes.forEach(n => {{
        if (n === draggedNode) return;
        n.vx += (width / 2 - n.x) * 0.0008;
        n.vy += (height / 2 - n.y) * 0.0008;
        n.vx *= 0.88;
        n.vy *= 0.88;
        n.x += n.vx;
        n.y += n.vy;
      }});
    }}

    function draw() {{
      const visNodes = allNodes.filter(isNodeVisible);
      const visEdges = allEdges.filter(e => isNodeVisible(e.sourceNode) && isNodeVisible(e.targetNode));

      stepSimulation(visNodes, visEdges);
      ctx.clearRect(0, 0, width, height);
      ctx.save();
      ctx.translate(offsetX, offsetY);
      ctx.scale(scale, scale);

      // Draw Edges
      visEdges.forEach(e => {{
        const isHighlight = selectedNode && (e.sourceNode === selectedNode || e.targetNode === selectedNode);
        ctx.strokeStyle = isHighlight ? '#38bdf8' : '#334155';
        ctx.lineWidth = isHighlight ? 2 : 1;
        ctx.beginPath();
        ctx.moveTo(e.sourceNode.x, e.sourceNode.y);
        ctx.lineTo(e.targetNode.x, e.targetNode.y);
        ctx.stroke();
      }});

      // Draw Nodes
      visNodes.forEach(n => {{
        const isSelected = n === selectedNode;
        ctx.fillStyle = n.color;
        ctx.beginPath();
        ctx.arc(n.x, n.y, isSelected ? n.radius + 5 : n.radius, 0, 2 * Math.PI);
        ctx.fill();

        if (isSelected) {{
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 2.5;
          ctx.stroke();
        }}

        // Label
        ctx.fillStyle = '#f1f5f9';
        ctx.font = isSelected ? 'bold 11px monospace' : '10px monospace';
        ctx.fillText(n.label, n.x + n.radius + 4, n.y + 3);
      }});

      ctx.restore();
      requestAnimationFrame(draw);
    }}

    draw();
    updateNodeCount();

    // Mouse interactions
    canvas.addEventListener('mousedown', e => {{
      const rect = canvas.getBoundingClientRect();
      const mx = (e.clientX - rect.left - offsetX) / scale;
      const my = (e.clientY - rect.top - offsetY) / scale;

      const visNodes = allNodes.filter(isNodeVisible);
      draggedNode = visNodes.find(n => Math.hypot(n.x - mx, n.y - my) <= n.radius + 5);
      if (draggedNode) {{
        selectedNode = draggedNode;
        updateInspector(draggedNode);
      }} else {{
        isPanning = true;
        startX = e.clientX - offsetX;
        startY = e.clientY - offsetY;
      }}
    }});

    window.addEventListener('mousemove', e => {{
      if (draggedNode) {{
        const rect = canvas.getBoundingClientRect();
        draggedNode.x = (e.clientX - rect.left - offsetX) / scale;
        draggedNode.y = (e.clientY - rect.top - offsetY) / scale;
      }} else if (isPanning) {{
        offsetX = e.clientX - startX;
        offsetY = e.clientY - startY;
      }}
    }});

    window.addEventListener('mouseup', () => {{
      draggedNode = null;
      isPanning = false;
    }});

    canvas.addEventListener('wheel', e => {{
      e.preventDefault();
      const zoom = e.deltaY < 0 ? 1.12 : 0.88;
      scale = Math.min(Math.max(0.25, scale * zoom), 3.5);
    }});

    function updateInspector(node) {{
      const connectedEdges = allEdges.filter(e => e.sourceNode === node || e.targetNode === node);
      const info = document.getElementById('node-info');
      info.innerHTML = `
        <h3>${{node.label}}</h3>
        <p><strong>類型</strong>: <span class="tag">${{node.type}}</span></p>
        <p><strong>檔案</strong>: <code style="font-size:0.75rem; color:#38bdf8;">${{node.file}}</code></p>
        <p style="margin-top:6px;"><strong>關聯度 (Degree)</strong>: ${{connectedEdges.length}}</p>
        <div style="margin-top:8px; max-height:140px; overflow-y:auto;">
          ${{connectedEdges.map(e => `
            <div style="font-size:0.75rem; color:#94a3b8; border-bottom:1px solid #1e293b; padding:2px 0;">
              ${{e.sourceNode.label}} ➔ <em>${{e.relation}}</em> ➔ ${{e.targetNode.label}}
            </div>
          `).join('')}}
        </div>
      `;
    }}
  </script>
</body>
</html>
"""


def generate_markdown_report(graph: ArchitectureGraph) -> str:
    """Generate GRAPH_REPORT.md containing God Nodes and architecture summary."""
    god_nodes = graph.get_god_nodes(top_n=7)
    metrics = graph.compute_degree_metrics()

    # Subsystem grouping
    subsystems = collections.defaultdict(list)
    for nid, data in graph.nodes.items():
        top_folder = data["file"].split("/")[0] if "/" in data["file"] else "root"
        subsystems[top_folder].append(data)

    lines = []
    lines.append("# 🕸️ Loop Graph — Architecture Topology & Impact Report\n")
    lines.append(f"> **實體節點總數**: {len(graph.nodes)}  |  **拓撲關係邊總數**: {len(graph.edges)}\n")

    lines.append("## 👑 關鍵中樞節點 (God Nodes — High Centrality Hubs)")
    lines.append("以下節點具備全系統最高出入度，牽一髮動全身，修改時應強制落實 Checker 證偽審查：\n")
    lines.append("| 排名 | 節點識別碼 | 類型 | 檔案路徑 | 關聯度 (Degree) |")
    lines.append("| :--- | :--- | :--- | :--- | :---: |")
    for idx, (nid, node, deg) in enumerate(god_nodes, start=1):
        lines.append(f"| #{idx} | `{node['label']}` | `{node['type']}` | `{node['file']}` | **{deg}** |")

    lines.append("\n## 🏛️ 子系統分佈 (Subsystem Clusters)")
    for sub, items in sorted(subsystems.items(), key=lambda x: len(x[1]), reverse=True):
        lines.append(f"- **`{sub}/`** ({len(items)} 節點): 包含 {', '.join(set(x['type'] for x in items))}")

    lines.append("\n## 🛡️ 系統不變量與門禁覆蓋 (Policy & Invariants Coverage)")
    policy_nodes = [n for n in graph.nodes.values() if n["type"] == "policy"]
    for p in policy_nodes:
        governed = [e["target"] for e in graph.edges if e["source"] == p["id"]]
        lines.append(f"- **{p['label']}** ➔ 約束了 {len(governed)} 個目標模組/目錄")

    lines.append("\n---\n*Report generated deterministically by Loop Graph Engine.*")
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Loop Graph: Deterministic Architecture Knowledge Graph Engine")
    parser.add_argument("--scan", action="store_true", help="Scan repository and output graph artifacts")
    parser.add_argument("--impact", type=str, help="Calculate blast radius and impacted dependents for a file/function")
    parser.add_argument("--diff-impact", action="store_true", help="Calculate innermost-symbol blast radius & TestSignal from git diff HEAD")
    parser.add_argument("--dead-code", action="store_true", help="Find unreferenced dead-code function candidates")
    parser.add_argument("--god-nodes", action="store_true", help="Display top God Nodes (central hubs)")
    parser.add_argument("--map", action="store_true", help="Output token-budgeted repo map (personalized PageRank)")
    parser.add_argument("--focus", action="append", default=[], help="Focus file(s) for personalized ranking; repeatable")
    parser.add_argument("--budget", type=int, default=1024, help="Token budget for --map (chars/4 estimate)")
    parser.add_argument("--out-dir", type=str, default="graph-out", help="Output directory for graph artifacts")
    parser.add_argument("--root", type=str, default=None, help="Root repository directory")

    args = parser.parse_args()

    root_dir = Path(args.root).resolve() if args.root else REPO_ROOT
    graph = ArchitectureGraph()
    scanner = CodeAstScanner(root_dir=root_dir, graph=graph)
    scanner.scan_repository()

    out_dir = root_dir / args.out_dir

    if args.dead_code:
        dead = graph.find_dead_code_candidates()
        print(f"🧹 DEAD CODE CANDIDATES ({len(dead)} unreferenced functions):")
        for c in dead:
            print(f"  - {c['file']}:{c['start_line']} -> {c['label']}()")
        return

    if args.diff_impact:
        try:
            diff_text = subprocess.check_output(
                ["git", "diff", "HEAD"], cwd=str(root_dir), text=True, encoding="utf-8", errors="replace"
            )
        except Exception:
            diff_text = ""
        res = graph.compute_diff_blast_radius(diff_text)
        print("=" * 64)
        print(f"🎯 DIFF BLAST RADIUS (Innermost Symbols) | TestSignal: [{res['test_signal'].upper()}]")
        print(f"Seeds ({len(res['seeds'])}): {', '.join(res['seed_labels']) or 'None'}")
        print(f"Direct Dependents: {res['direct_count']} | Transitive: {res['transitive_count']} | Total Blast: {res['total_blast_radius']}")
        print("=" * 64)
        if res["impacted_tests"]:
            print(f"🧪 Impacted Tests ({res['test_signal']}):")
            for t in res["impacted_tests"]:
                print(f"  - {t}")
        return

    if args.impact:
        res = graph.compute_blast_radius(args.impact)
        print("=" * 64)
        print(f"💥 BLAST RADIUS REPORT — Target: {args.impact}")
        print(f"Direct Dependents: {res['direct_count']} | Transitive: {res['transitive_count']} | Total Blast: {res['total_blast_radius']}")
        print("=" * 64)
        if res["impacted_tests"]:
            print("🧪 Impacted Tests:")
            for t in res["impacted_tests"]:
                print(f"  - {t}")
        if res["governing_policies"]:
            print("🛡️ Governing Invariants/Policies:")
            for p in res["governing_policies"]:
                print(f"  - {p}")
        print("\nAll Dependents:")
        for dep in res["dependents"]:
            print(f"  [Depth {dep['depth']}] ({dep['type']}) {dep['label']} in {dep['file']}")
        print("-" * 64)
        return

    if args.god_nodes:
        gods = graph.get_god_nodes(top_n=5)
        print("👑 TOP GOD NODES (Central Hubs):")
        for idx, (nid, node, deg) in enumerate(gods, start=1):
            print(f"  #{idx} {node['label']} ({node['type']}) - Degree: {deg} | {node['file']}")
        return

    if args.map:
        ranks = graph.compute_pagerank(focus=args.focus)
        repo_map_str = graph.render_repo_map(ranks, budget=args.budget)
        tokens = math.ceil(len(repo_map_str) / 4) if repo_map_str else 0
        if repo_map_str:
            print(repo_map_str)
        print(f"# ~{tokens} tokens / budget {args.budget}")
        return

    # Default or --scan: Export full graph artifacts
    out_dir.mkdir(parents=True, exist_ok=True)
    # 1. graph.json
    graph_json_data = {
        "nodes": list(graph.nodes.values()),
        "edges": graph.edges
    }
    (out_dir / "graph.json").write_text(json.dumps(graph_json_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2. GRAPH_REPORT.md
    report_md = generate_markdown_report(graph)
    (out_dir / "GRAPH_REPORT.md").write_text(report_md, encoding="utf-8")

    # 3. graph.html
    html_content = GraphVisualizer.render_html(graph)
    (out_dir / "graph.html").write_text(html_content, encoding="utf-8")

    print(f"✅ Loop Graph generated successfully in {out_dir}/:")
    print(f"  - graph.json (Machine-readable topological memory)")
    print(f"  - GRAPH_REPORT.md (God nodes & architecture report)")
    print(f"  - graph.html (100% offline interactive Canvas visualization)")


if __name__ == "__main__":
    main()
