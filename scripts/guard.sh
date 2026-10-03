#!/usr/bin/env bash
# ==============================================================================
# guard.sh - Cross-platform wrapper for local_guard.py (Linux / macOS / Raspberry Pi)
# Part of 7-Phase Agentic Workflow & Ponytail Lazy Senior Dev Mode
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Detect Python interpreter
PYTHON_BIN="python3"
if [ -f "$PROJECT_ROOT/.venv/bin/python3" ]; then
    PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python3"
elif [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
fi

# Run local_guard.py
if [ $# -eq 0 ]; then
    exec "$PYTHON_BIN" "$SCRIPT_DIR/local_guard.py" --git
else
    exec "$PYTHON_BIN" "$SCRIPT_DIR/local_guard.py" "$@"
fi
