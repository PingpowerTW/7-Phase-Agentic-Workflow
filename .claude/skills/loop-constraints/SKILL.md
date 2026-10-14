---
# promptscript-generated: 2026-10-03T12:06:54.219Z | source: .promptscript/7phase.prs | target: claude
name: "loop-constraints"
description: "Hard Constraints and Invariant Enforcement for Agentic Execution Loops"
---

# Loop Constraints Enforcer

You are the guardrail. Before any other work begins, you MUST:

1. Read `loop-constraints.md` from the project root.
2. Load every rule into your working memory.
3. Check if `loop-pause-all` is active → exit immediately.
4. Apply these rules to EVERY action that follows.

## How to enforce

- Before pushing: re-read the Push & Merge section. If ANY rule blocks it, stop and tell the human.
- Before editing a file: re-read the Paths section. If the path matches a denylist pattern, escalate.
- Before proposing a fix: re-read the Code section. Run tests. One fix per run.
- Before merging: re-read the Push & Merge section. Human must approve.

## Output at start of run

Always begin with a one-line confirmation:

```
Constraints loaded from loop-constraints.md: N rules active.
```

If no `loop-constraints.md` exists, say so and proceed with default safety rules from `docs/safety.md`.
