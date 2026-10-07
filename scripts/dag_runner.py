#!/usr/bin/env python3
"""
dag_runner.py — High-Performance Parallel DAG Task Scheduler & LLMCompiler Engine
Pure Python 3.11 Standard Library (graphlib.TopologicalSorter + asyncio). Zero External Dependencies.

【安全與架構原則】
1. 徹底根除 Shell 注入 (CWE-78)：嚴禁 asyncio.create_subprocess_shell，強制採用 create_subprocess_exec。
2. 參數化 Token 代換：變數代換 ($k, $task_id) 僅於參數陣列 (Argv) 的獨立 Token 層級替換，無 Shell 次級展開。
3. 跨平台子程序生命週期管理：超時或取消時，Windows 透過 taskkill /F /T 清除整棵程序樹，POSIX 發送 SIGKILL，徹底杜絕殭屍程序。
4. 拓撲排序原生排程：使用 Python 標準庫 graphlib.TopologicalSorter，顯式攔截 CycleError。
5. 電路硬熔斷 (Fail-Fast)：任一任務失敗立即切斷排程並回收所有子程序。
"""

import sys
import os
import re
import time
import json
import shlex
import signal
import shutil
import asyncio
import graphlib
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Awaitable, Set, Union

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class Task:
    """DAG 任務規格定義 (純參數化，無 Shell 媒介)"""
    id: str
    deps: List[str] = field(default_factory=list)
    cmd: Union[List[str], str] = field(default_factory=list)      # 參數化命令陣列或安全指令
    action: Optional[Callable[..., Awaitable[Any]]] = None       # Python 異步協程
    timeout: float = 60.0                                        # 單任務逾時秒數
    env: Dict[str, str] = field(default_factory=dict)            # 獨立環境變數


@dataclass
class TaskResult:
    """任務執行結果矩陣"""
    task_id: str
    status: str                                                  # 'SUCCESS', 'FAILED', 'CANCELLED', 'TIMEOUT'
    output: Any = None                                           # 標準輸出或協程返回值
    error: Optional[str] = None                                  # 錯誤原因
    duration_ms: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0


class DAGExecutionError(Exception):
    """DAG 執行硬熔斷例外"""
    def __init__(self, message: str, task_id: str, results: Dict[str, TaskResult]):
        super().__init__(message)
        self.task_id = task_id
        self.results = results


async def _terminate_process_tree(proc: asyncio.subprocess.Process):
    """跨平台安全回收子程序樹，防止程序洩漏與殭屍程序"""
    if proc.returncode is not None:
        return

    pid = proc.pid
    if sys.platform == "win32":
        try:
            # Windows: 透過 taskkill /F /T 終止整棵程序樹
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    else:
        try:
            # POSIX: 嘗試發送 SIGKILL 至 process group 或 direct kill
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    try:
        await asyncio.wait_for(proc.wait(), timeout=5.0)
    except Exception:
        pass


class DAGRunner:
    """LLMCompiler 拓撲編譯排程執行器"""

    def __init__(self, tasks: List[Task], global_timeout: float = 300.0):
        self.tasks_map: Dict[str, Task] = {t.id: t for t in tasks}
        self.global_timeout = global_timeout
        self.results: Dict[str, TaskResult] = {}
        self._running_subprocesses: Dict[str, asyncio.subprocess.Process] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}

    def _substitute_token(self, token: str, task: Task) -> str:
        """
        在個別參數 Token 層級進行變數代換，絕不拼接出 Shell 字串。
        支援：
        - $task_id / ${task_id}: 上游標準輸出
        - $1, $2: 依 deps 陣列順序代換
        - $task_id.key: 解析上游 JSON 輸出之特定屬性
        """
        def replacer(match: re.Match) -> str:
            var_name = match.group(1) or match.group(2)
            if not var_name:
                return match.group(0)

            # 1. 順序代換 ($1, $2)
            if var_name.isdigit():
                idx = int(var_name) - 1
                if 0 <= idx < len(task.deps):
                    dep_id = task.deps[idx]
                    if dep_id in self.results and self.results[dep_id].output is not None:
                        return str(self.results[dep_id].output).strip()
                return match.group(0)

            # 2. 具名與點狀 JSON 屬性代換
            parts = var_name.split(".")
            dep_id = parts[0]
            if dep_id in self.results and self.results[dep_id].output is not None:
                out = self.results[dep_id].output
                if len(parts) > 1:
                    if isinstance(out, str):
                        try:
                            out = json.loads(out)
                        except Exception:
                            pass
                    if isinstance(out, dict):
                        for p in parts[1:]:
                            if isinstance(out, dict) and p in out:
                                out = out[p]
                            else:
                                return match.group(0)
                return str(out).strip()

            return match.group(0)

        pattern = r"\$\{([a-zA-Z0-9_\.]+)\}|\$([a-zA-Z0-9_\.]+)"
        return re.sub(pattern, replacer, token)

    def _resolve_cmd_args(self, task: Task) -> List[str]:
        """將任務定義的安全轉譯為 argv 參數陣列"""
        raw_cmd = task.cmd
        tokens: List[str] = []

        if isinstance(raw_cmd, list):
            tokens = [str(t) for t in raw_cmd]
        elif isinstance(raw_cmd, str) and raw_cmd.strip():
            # 使用 shlex 安全切分，禁止 Shell 解析次級展開
            tokens = shlex.split(raw_cmd, posix=(sys.platform != "win32"))
        else:
            return []

        resolved: List[str] = []
        for tok in tokens:
            resolved.append(self._substitute_token(tok, task))

        return resolved

    async def _execute_single_task(self, task: Task) -> TaskResult:
        """執行單一 Task，透過 create_subprocess_exec 直接調用二進制執行檔"""
        res = TaskResult(task_id=task.id, status="RUNNING", start_time=time.perf_counter())

        try:
            cmd_args = self._resolve_cmd_args(task)

            # 1. 執行參數化指令 (create_subprocess_exec)
            if cmd_args:
                executable = cmd_args[0]
                # 跨平台路徑定位
                resolved_bin = shutil.which(executable) or executable

                proc = await asyncio.create_subprocess_exec(
                    resolved_bin,
                    *cmd_args[1:],
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ, **task.env}
                )
                self._running_subprocesses[task.id] = proc

                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(),
                        timeout=task.timeout
                    )
                except asyncio.TimeoutError:
                    await _terminate_process_tree(proc)
                    res.status = "TIMEOUT"
                    res.error = f"Task timed out after {task.timeout}s"
                    return res
                finally:
                    self._running_subprocesses.pop(task.id, None)

                stdout_str = stdout_bytes.decode("utf-8", errors="replace").strip()
                stderr_str = stderr_bytes.decode("utf-8", errors="replace").strip()

                if proc.returncode == 0:
                    res.status = "SUCCESS"
                    res.output = stdout_str
                else:
                    res.status = "FAILED"
                    res.error = f"Exit code {proc.returncode}: {stderr_str or stdout_str}"

            # 2. 執行原生 Python 協程
            elif task.action:
                try:
                    output = await asyncio.wait_for(task.action(self.results), timeout=task.timeout)
                    res.status = "SUCCESS"
                    res.output = output
                except asyncio.TimeoutError:
                    res.status = "TIMEOUT"
                    res.error = f"Coroutine timed out after {task.timeout}s"
                except Exception as ex:
                    res.status = "FAILED"
                    res.error = str(ex)

            else:
                res.status = "FAILED"
                res.error = "Neither cmd nor action was provided."

        except asyncio.CancelledError:
            res.status = "CANCELLED"
            res.error = "Task cancelled by circuit breaker."
            raise
        finally:
            res.end_time = time.perf_counter()
            res.duration_ms = (res.end_time - res.start_time) * 1000

        return res

    async def run(self) -> Dict[str, TaskResult]:
        """執行全域 DAG 並行拓撲排程"""
        # 邊界 1: 空 DAG 直接放行
        if not self.tasks_map:
            return {}

        # 邊界 2: 檢查懸空依賴
        dep_graph: Dict[str, Set[str]] = {}
        for tid, t in self.tasks_map.items():
            for d in t.deps:
                if d not in self.tasks_map:
                    raise ValueError(f"Task '{tid}' depends on non-existent task '{d}'")
            dep_graph[tid] = set(t.deps)

        # 邊界 3: 拓撲排序編譯，顯式偵測 CycleError
        try:
            ts = graphlib.TopologicalSorter(dep_graph)
            ts.prepare()
        except graphlib.CycleError as ex:
            raise graphlib.CycleError(f"Cycle detected in task dependencies: {ex}") from ex

        start_all = time.perf_counter()

        while ts.is_active():
            if (time.perf_counter() - start_all) > self.global_timeout:
                await self._abort_all("Global DAG execution timeout exceeded.")
                raise TimeoutError(f"DAG execution exceeded global timeout of {self.global_timeout}s")

            ready_task_ids = ts.get_ready()

            # 並行分發所有無依賴任務
            for tid in ready_task_ids:
                task_def = self.tasks_map[tid]
                coro = self._execute_single_task(task_def)
                async_task = asyncio.create_task(coro, name=f"dag-task-{tid}")
                self._running_tasks[tid] = async_task

            if not self._running_tasks:
                break

            done_set, _ = await asyncio.wait(
                self._running_tasks.values(),
                return_when=asyncio.FIRST_COMPLETED
            )

            for done_future in done_set:
                finished_tid = None
                for tid, atask in list(self._running_tasks.items()):
                    if atask == done_future:
                        finished_tid = tid
                        del self._running_tasks[tid]
                        break

                if finished_tid is None:
                    continue

                try:
                    result = done_future.result()
                except asyncio.CancelledError:
                    result = TaskResult(task_id=finished_tid, status="CANCELLED", error="Cancelled")
                except Exception as ex:
                    result = TaskResult(task_id=finished_tid, status="FAILED", error=str(ex))

                self.results[finished_tid] = result

                # Fail-Fast 電路熔斷：任務未成功時立即回收全部程序
                if result.status != "SUCCESS":
                    await self._abort_all(f"Task '{finished_tid}' failed with status {result.status}: {result.error}")
                    raise DAGExecutionError(
                        f"Fail-Fast Circuit Breaker triggered by task '{finished_tid}': {result.error}",
                        task_id=finished_tid,
                        results=self.results
                    )

                ts.done(finished_tid)

        return self.results

    async def _abort_all(self, reason: str):
        """緊急取消所有任務並殺除所有運作中之子程序樹"""
        for pid_str, proc in list(self._running_subprocesses.items()):
            await _terminate_process_tree(proc)
        self._running_subprocesses.clear()

        for tid, atask in self._running_tasks.items():
            if not atask.done():
                atask.cancel()


def print_dag_summary(results: Dict[str, TaskResult], total_elapsed_ms: float):
    print("\n" + "=" * 70)
    print("⚡ LLMCompiler DAG Execution Report")
    print("=" * 70)
    print(f"{'Task ID':<15} | {'Status':<10} | {'Duration (ms)':<14} | {'Details'}")
    print("-" * 70)
    for tid, res in results.items():
        status_colored = f"✅ {res.status}" if res.status == "SUCCESS" else f"❌ {res.status}"
        details = str(res.output)[:30] if res.status == "SUCCESS" else str(res.error)[:30]
        print(f"{tid:<15} | {status_colored:<10} | {res.duration_ms:12.1f} ms | {details}")
    print("-" * 70)
    print(f"Total Workflow Wall Time: {total_elapsed_ms:.1f} ms | Completed Tasks: {len(results)}\n")


async def main_cli():
    import argparse
    parser = argparse.ArgumentParser(description="DAG Runner: Parallel Topological Task Executor (Exec Only)")
    parser.add_argument("--dag", type=str, help="Path to JSON file defining DAG tasks")
    parser.add_argument("--json", type=str, help="Inline JSON string defining DAG tasks")
    parser.add_argument("--timeout", type=float, default=120.0, help="Global workflow timeout in seconds")

    args = parser.parse_args()

    raw_json = None
    if args.dag:
        raw_json = Path(args.dag).read_text(encoding="utf-8")
    elif args.json:
        raw_json = args.json
    else:
        raw_json = json.dumps({
            "tasks": [
                {"id": "step_a", "cmd": [sys.executable, "-c", "import json; print(json.dumps({'status': 'ready', 'version': 1}))"], "deps": []},
                {"id": "step_b", "cmd": [sys.executable, "-c", "import sys; print(f'Validated version {sys.argv[1]}')", "$step_a.version"], "deps": ["step_a"]}
            ]
        })

    try:
        data = json.loads(raw_json)
    except Exception as ex:
        print(f"❌ [DAG Error] JSON 解析失敗: {ex}", file=sys.stderr)
        sys.exit(2)

    task_objs = []
    for item in data.get("tasks", []):
        cmd_val = item.get("cmd") or item.get("command") or []
        task_objs.append(Task(
            id=item["id"],
            deps=item.get("deps", []),
            cmd=cmd_val,
            timeout=float(item.get("timeout", 60.0))
        ))

    runner = DAGRunner(task_objs, global_timeout=args.timeout)
    t0 = time.perf_counter()
    try:
        results = await runner.run()
        elapsed = (time.perf_counter() - t0) * 1000
        print_dag_summary(results, elapsed)
        sys.exit(0)
    except graphlib.CycleError as ex:
        print(f"\n❌ [DAG Error] CYCLE_ERROR: {ex}", file=sys.stderr)
        sys.exit(2)
    except DAGExecutionError as ex:
        elapsed = (time.perf_counter() - t0) * 1000
        print_dag_summary(ex.results, elapsed)
        print(f"\n🛑 [DAG Circuit Breaker] {ex}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main_cli())
