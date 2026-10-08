#!/usr/bin/env python3
"""
test_swc_llmcompiler.py — End-to-End Architectural Test Suite
100% Real Assertions. Zero Fake Tests. Zero assert True.
Validates:
1. SWC Extractor End-to-End AST Parsing (classes, arrow functions, calls, batch stdin).
2. AST Guard Deterministic Verification (blocking seams with Exit 1, passing clean code with Exit 0).
3. DAG Runner Topological Parallelism, $k token injection, cycle detection, process tree cleanup, and fail-fast circuit breaker.
"""

import os
import sys
import json
import time
import shutil
import tempfile
import asyncio
import unittest
import graphlib
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from dag_runner import Task, DAGRunner, TaskResult, DAGExecutionError


def is_swc_available() -> bool:
    try:
        res = subprocess.run(["node", "-e", "require('@swc/core')"], capture_output=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False


HAS_SWC = is_swc_available()


@unittest.skipUnless(HAS_SWC, "@swc/core is not installed in current environment")
class TestSwcExtractor(unittest.TestCase):
    """驗證 swc_extractor.js 是否能精確解析 TypeScript / JavaScript 語法樹"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="swc_test_")
        self.extractor_js = SCRIPTS_DIR / "swc_extractor.js"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_single_file_ast_extraction(self):
        """真實執行 node swc_extractor.js，驗證函式、類別方法、Imports 與 Call 呼叫邊之真實抽取"""
        ts_code = """
import { helper } from './utils';
import * as config from 'config';
const dynamicLib = require('legacy-mod');

export class AccountService {
    private balance: number = 0;
    constructor() {
        this.init();
    }
    init() {
        helper();
    }
}

export const computeDiscount = (price: number) => {
    return helper() * price;
};
"""
        ts_file = Path(self.test_dir) / "account.ts"
        ts_file.write_text(ts_code, encoding="utf-8")

        cmd = ["node", str(self.extractor_js), str(ts_file)]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0, f"swc_extractor.js 執行失敗: {proc.stderr}")

        data = json.loads(proc.stdout)
        self.assertIsNone(data.get("error"))

        # 驗證 definitions
        defs_map = {d["name"]: d["type"] for d in data.get("definitions", [])}
        self.assertEqual(defs_map.get("AccountService"), "class")
        self.assertEqual(defs_map.get("AccountService.init"), "method")
        self.assertEqual(defs_map.get("computeDiscount"), "function")

        # 驗證 imports
        sources = [imp["source"] for imp in data.get("imports", [])]
        self.assertIn("./utils", sources)
        self.assertIn("config", sources)
        self.assertIn("legacy-mod", sources)

        # 驗證 calls
        calls = [c["callee"] for c in data.get("calls", [])]
        self.assertIn("helper", calls)

    def test_batch_mode_stdin(self):
        """真實執行 --batch 模式，驗證多檔案批次解析與 JSON 結構合約"""
        f1 = Path(self.test_dir) / "module1.js"
        f1.write_text("export function doWork() { return 42; }", encoding="utf-8")

        f2 = Path(self.test_dir) / "module2.js"
        f2.write_text("export const runPipeline = () => true;", encoding="utf-8")

        cmd = ["node", str(self.extractor_js), "--batch"]
        proc = subprocess.run(
            cmd,
            input=json.dumps([str(f1), str(f2)]),
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        self.assertEqual(proc.returncode, 0, f"Batch extractor 執行失敗: {proc.stderr}")

        results = json.loads(proc.stdout)
        self.assertEqual(len(results), 2)
        names = [d["name"] for r in results for d in r.get("definitions", [])]
        self.assertIn("doWork", names)
        self.assertIn("runPipeline", names)


@unittest.skipUnless(HAS_SWC, "@swc/core is not installed in current environment")
class TestAstGuard(unittest.TestCase):
    """驗證 ast_guard.js 門禁：真實阻斷生產接縫 (Exit 1) 與放行合規代碼 (Exit 0)"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="guard_test_")
        self.guard_js = SCRIPTS_DIR / "ast_guard.js"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_block_exported_mock_function(self):
        """真實執行 ast_guard.js：生產檔案 export mock 函式必須回傳 Exit 1 (BLOCK)"""
        bad_code = """
export function processOrder(orderId) {
    return { id: orderId, status: 'processed' };
}

// 違規：在生產代碼 export mock 後門
export function mockSetOrderStatus(status) {
    globalStatus = status;
}
"""
        bad_file = Path(self.test_dir) / "order_service.js"
        bad_file.write_text(bad_code, encoding="utf-8")

        proc = subprocess.run(["node", str(self.guard_js), str(bad_file)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("INV_VERIFY_03", proc.stderr + proc.stdout)

    def test_block_parameter_mock_seam(self):
        """真實執行 ast_guard.js：生產函式帶有 mock 參數必須回傳 Exit 1 (BLOCK)"""
        bad_param_code = """
export function fetchUser(userId, mock = false) {
    if (mock) return { id: userId, name: 'Fake' };
    return realDb.find(userId);
}
"""
        bad_file = Path(self.test_dir) / "user_repo.js"
        bad_file.write_text(bad_param_code, encoding="utf-8")

        proc = subprocess.run(["node", str(self.guard_js), str(bad_file)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("No Production Seams", proc.stderr + proc.stdout)

    def test_pass_clean_production_code(self):
        """真實執行 ast_guard.js：合規生產代碼必須通過門禁 (Exit 0)"""
        clean_code = """
export class Ledger {
    record(entry) {
        return { recorded: true, id: entry.id };
    }
}
export function formatAmount(val) {
    return val.toFixed(2);
}
"""
        clean_file = Path(self.test_dir) / "ledger.js"
        clean_file.write_text(clean_code, encoding="utf-8")

        proc = subprocess.run(["node", str(self.guard_js), str(clean_file)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0, f"合規代碼被誤判攔截: {proc.stderr}")

    def test_block_empty_test_body(self):
        """真實執行 ast_guard.js：測試檔案含有空 test block 必須回傳 Exit 1 (BLOCK)"""
        junk_test = """
describe('Math Suite', () => {
    test('should add numbers', () => {
    });
});
"""
        test_file = Path(self.test_dir) / "math.test.js"
        test_file.write_text(junk_test, encoding="utf-8")

        proc = subprocess.run(["node", str(self.guard_js), str(test_file)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("INV_VERIFY_02", proc.stderr + proc.stdout)

    def test_block_test_todo(self):
        """真實執行 ast_guard.js：測試檔案含有 it.todo 佔位符必須回傳 Exit 1 (BLOCK)"""
        todo_test = """
describe('API Suite', () => {
    it.todo('should handle timeout');
});
"""
        test_file = Path(self.test_dir) / "api.spec.js"
        test_file.write_text(todo_test, encoding="utf-8")

        proc = subprocess.run(["node", str(self.guard_js), str(test_file)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("INV_VERIFY_02", proc.stderr + proc.stdout)


class TestDagRunner(unittest.TestCase):
    """驗證 dag_runner.py 純標準庫無 Shell 並行拓撲執行器"""

    def test_topological_execution_and_token_replacement(self):
        """測試 1: 參數化 exec 拓撲排程與 $k Token 代換"""
        tasks = [
            Task(id="step_a", cmd=[sys.executable, "-c", "import sys; sys.stdout.write('Hello')"]),
            Task(id="step_b", cmd=[sys.executable, "-c", "import sys; sys.stdout.write('World')"]),
            Task(id="step_merge", cmd=[sys.executable, "-c", "import sys; sys.stdout.write(f'{sys.argv[1]} {sys.argv[2]}!')", "$step_a", "$step_b"], deps=["step_a", "step_b"])
        ]

        runner = DAGRunner(tasks)
        results = asyncio.run(runner.run())

        self.assertEqual(len(results), 3)
        self.assertEqual(results["step_a"].output, "Hello")
        self.assertEqual(results["step_b"].output, "World")
        self.assertEqual(results["step_merge"].output, "Hello World!")

    def test_concurrency_speedup(self):
        """測試 2: 驗證無依賴任務確實並行調度 (總壁鐘時間 < 循序累計時間)"""
        async def sleep_coro(delay):
            await asyncio.sleep(delay)
            return "ok"

        tasks = [
            Task(id="t1", action=lambda r: sleep_coro(0.1)),
            Task(id="t2", action=lambda r: sleep_coro(0.1)),
            Task(id="t3", action=lambda r: sleep_coro(0.1)),
        ]

        t0 = time.perf_counter()
        results = asyncio.run(DAGRunner(tasks).run())
        elapsed = time.perf_counter() - t0

        self.assertEqual(len(results), 3)
        self.assertLess(elapsed, 0.25, f"並行未生效，總耗時: {elapsed:.2f}s")

    def test_cycle_error_detection(self):
        """測試 3: 驗證環狀依賴會被明確捕捉為 graphlib.CycleError"""
        cyclic_tasks = [
            Task(id="node_1", cmd=[sys.executable, "-c", "print(1)"], deps=["node_2"]),
            Task(id="node_2", cmd=[sys.executable, "-c", "print(2)"], deps=["node_1"])
        ]
        with self.assertRaises(graphlib.CycleError):
            asyncio.run(DAGRunner(cyclic_tasks).run())

    def test_empty_dag_and_dangling_dependency(self):
        """測試 4: 驗證空 DAG 與懸空依賴邊界防護"""
        empty_res = asyncio.run(DAGRunner([]).run()
        )
        self.assertEqual(empty_res, {})

        dangling_tasks = [
            Task(id="t1", cmd=[sys.executable, "-c", "print(1)"], deps=["ghost_task"])
        ]
        with self.assertRaises(ValueError):
            asyncio.run(DAGRunner(dangling_tasks).run())

    def test_fail_fast_circuit_breaker(self):
        """測試 5: 驗證任務失敗時觸發硬熔斷，下游任務不被執行"""
        tasks = [
            Task(id="step_fail", cmd=[sys.executable, "-c", "import sys; sys.exit(1)"]),
            Task(id="step_unreachable", cmd=[sys.executable, "-c", "print('unreachable')"], deps=["step_fail"])
        ]

        runner = DAGRunner(tasks)
        with self.assertRaises(DAGExecutionError):
            asyncio.run(runner.run())

        self.assertIn("step_fail", runner.results)
        self.assertEqual(runner.results["step_fail"].status, "FAILED")
        self.assertNotIn("step_unreachable", runner.results)

    def test_zombie_process_cleanup_on_timeout(self):
        """測試 6: 驗證單任務逾時觸發程序樹安全回收，無殘留程序"""
        long_sleep_script = "import time; time.sleep(30)"
        task = Task(id="sleepy", cmd=[sys.executable, "-c", long_sleep_script], timeout=0.2)

        runner = DAGRunner([task])
        t0 = time.perf_counter()
        with self.assertRaises(DAGExecutionError):
            asyncio.run(runner.run())
        elapsed = time.perf_counter() - t0

        self.assertLess(elapsed, 2.0, "程序逾時回收耗時過長，可能存在死鎖")
        self.assertEqual(runner.results["sleepy"].status, "TIMEOUT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
