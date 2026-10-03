---
# promptscript-generated: 2026-10-03T12:03:42.557Z | source: .promptscript/7phase.prs | target: github
description: "Evaluate BTC Thermodynamic Trust score and Oxford SHARS hallucination index"
---

Evaluate current session trust metrics:

- Compute Thermodynamic Trust T = PPV * exp(-sigma * T_comp).
- Check against threshold theta = 0.65.
- Decompose latest responses into atomic claims and compute SHARS verification scores.
- Report governance status and credit balance.
