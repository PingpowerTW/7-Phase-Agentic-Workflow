---
# promptscript-generated: 2026-10-03T12:03:42.557Z | source: .promptscript/7phase.prs | target: antigravity
title: "Phase 1 Context"
description: "Phase 1: Environment & Codebase Context Gathering"
---

Trigger: Approved spec.md.
Objective: Safely discover tech stack, architecture seams, dependencies, and baseline state with minimal token footprint.
Rules:

- Step 1 (0-Token Map): Run `python scripts/loop_graph.py --map --focus <target_file> --budget 1000` and `python scripts/loop_graph.py --impact <target_file>` BEFORE reading full source files.
- Step 2 (Fast-Track Triage): If impact radius <= 2 files and outside gate.yaml denylist, propose Tier 0 Fast-Track (skip Phase 2 & Phase 3 docs, jump to Phase 4 /caveman).
- Read only target functions/classes without making changes.
- Output compact context checklist and dependency blast radius.
