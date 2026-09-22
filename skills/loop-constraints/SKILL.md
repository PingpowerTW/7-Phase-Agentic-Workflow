---
name: loop-constraints
description: >
  Read loop-constraints.md at the start of every run and enforce every rule.
  This skill runs BEFORE triage or any action skill. Constraints are binding.
user_invocable: true
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
