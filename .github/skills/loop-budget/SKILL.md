---
# promptscript-generated: 2026-10-03T12:06:54.220Z | source: .promptscript/7phase.prs | target: github
name: loop-budget
description: "Multi-Agent Loop Budget & Token Quota Management System"
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
