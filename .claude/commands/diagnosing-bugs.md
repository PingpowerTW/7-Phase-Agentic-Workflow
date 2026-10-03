---
# promptscript-generated: 2026-10-03T12:06:54.219Z | source: .promptscript/7phase.prs | target: claude
description: "Trigger 6-Phase Systematic Debugging Loop for hard/flaky bugs"
---

Trigger the 6-Phase Deep Debugging Loop:

1. Isolate minimal reproduction steps.
2. Formulate testable hypothesis.
3. Write failing regression test first (Fail-Before-Pass).
4. Inspect root cause (trace logs & memory state).
5. Apply surgical fix.
6. Verify regression test passes.
