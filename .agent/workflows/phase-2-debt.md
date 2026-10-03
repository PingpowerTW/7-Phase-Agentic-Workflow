---
# promptscript-generated: 2026-10-03T12:03:42.557Z | source: .promptscript/7phase.prs | target: antigravity
title: "Phase 2 Debt"
description: "Phase 2: Technical Debt & Code Smell Audit"
---

Trigger: Context checklist established.
Objective: Identify pre-existing technical debt, smells, and potential blockers.
Classifications:

- 🔴 Critical: Security vulnerabilities, race conditions, memory leaks.
- 🟡 Warning: Over-coupling, SOLID/DRY violations, missing type definitions.
- 🟢 Minor: Style inconsistencies, dead code.
  Rule: Do NOT refactor unrelated debt in implementation unless < 3 lines or explicitly scoped in Phase 3.
