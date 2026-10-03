# phase-2-debt

<!-- PromptScript 2026-10-03T12:03:42.557Z | source: .promptscript/7phase.prs | target: claude - do not edit -->

> Phase 2: Technical Debt & Code Smell Audit

Trigger: Context checklist established.
Objective: Identify pre-existing technical debt, smells, and potential blockers.
Classifications:

- 🔴 Critical: Security vulnerabilities, race conditions, memory leaks.
- 🟡 Warning: Over-coupling, SOLID/DRY violations, missing type definitions.
- 🟢 Minor: Style inconsistencies, dead code.
  Rule: Do NOT refactor unrelated debt in implementation unless < 3 lines or explicitly scoped in Phase 3.
