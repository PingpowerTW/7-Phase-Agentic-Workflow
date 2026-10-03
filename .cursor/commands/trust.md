<!-- PromptScript 2026-10-03T12:03:42.557Z | source: .promptscript/7phase.prs | target: cursor - do not edit -->

Evaluate current session trust metrics:

- Compute Thermodynamic Trust T = PPV * exp(-sigma * T_comp).
- Check against threshold theta = 0.65.
- Decompose latest responses into atomic claims and compute SHARS verification scores.
- Report governance status and credit balance.
