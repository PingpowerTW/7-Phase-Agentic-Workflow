---
name: loop-budget
description: Check token budget and run-log spend before and after a loop run. Enforces early exit when over budget or when there is no actionable work.
---

# Loop Budget Guard

Run at the **start** and **end** of every loop iteration.

## Start of run

1. Read `loop-budget.md` for daily caps and kill-switch flags.
2. Read recent entries in `loop-run-log.md` (last 24h).
3. If spend ≥ 80% of daily cap → **report-only mode** (no sub-agents, no auto-fix).
4. If spend ≥ 100% or `loop-pause-all` is set → **exit immediately** with a note in STATE.md.
5. If watchlist/state has no actionable items → **exit in <5k tokens**.

## End of run

Append entry to `loop-run-log.md`.
