---
# promptscript-generated: 2026-10-03T12:03:42.557Z | source: .promptscript/7phase.prs | target: factory
description: Run adversarial code review (Rational vs Grumpy Critic)
---

Execute dual-perspective adversarial code review:

- Rational Reviewer: Evaluates SOLID, DRY, typing, and test coverage.
- Grumpy Critic: Stresses unhandled exceptions, race conditions, edge cases, and failure modes.
- Output structured findings (🔴 Critical / 🟡 Warning / 🟢 Suggestion).
