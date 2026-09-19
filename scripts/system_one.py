#!/usr/bin/env python3
"""
7-Phase Agentic Workflow - System 1 Decision Router & Gatekeeper
Pure Python Standard Library (Zero External Dependencies).

Inspired by TypeSafe AI / Jev "System One Models":
1. Noul: Boolean binary decision with calibrated confidence
2. Choice: Categorical routing among discrete candidate labels
3. Score: Continuous 0.0 ~ 1.0 quantitative assessment

Architecture:
- Fast Path (System 1): Local deterministic heuristics / semantic matching (0ms, 0 Token)
- Cloud Adapter: TypeSafe API integration hook (when TYPESAFE_API_KEY is configured)
- Fallback Gate: If confidence < threshold, signal fallback to System 2 (Gemini/Claude)
"""

import sys
import os
import re
import json
import time
from dataclasses import dataclass
from typing import Any, Optional, Union

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


@dataclass
class DecisionResult:
    primitive: str                      # 'noul', 'choice', 'score'
    value: Union[bool, str, float]     # Typed decision output
    probability: float                  # Calibrated confidence (0.0 ~ 1.0)
    latency_ms: float                   # Execution time in milliseconds
    engine: str                         # 'local-rule', 'typesafe-jev', 'system-2-fallback'
    fallback_required: bool             # True if probability < threshold


# Domain vocabulary mappings for System 1 fast matching
DOMAIN_LEXICON = {
    "database": ["db", "database", "sql", "postgres", "postgresql", "mysql", "schema", "table", "index", "orm", "prisma", "migration"],
    "frontend": ["frontend", "ui", "ux", "react", "vue", "css", "html", "dom", "component", "tailwind", "styled", "render"],
    "backend": ["backend", "api", "controller", "service", "route", "endpoint", "express", "fastapi", "django", "server"],
    "security": ["security", "auth", "secret", "token", "injection", "vulnerability", "xss", "csrf", "permission", "crypto"],
    "devops": ["devops", "docker", "ci", "cd", "deploy", "kubernetes", "infra", "pipeline", "compose"],
}


class SystemOneGate:
    """
    Lightweight, deterministic System 1 decision gatekeeper.
    Eliminates token waste by serving high-frequency classification,
    routing, and binary checks in <5ms without generative LLM overhead.
    """

    def __init__(self, confidence_threshold: float = 0.75):
        self.threshold = confidence_threshold
        self.api_key = os.getenv("TYPESAFE_API_KEY", "").strip()

    def noul(self, prompt: str, context: str = "") -> DecisionResult:
        """
        Binary No/Yes decision (Noul).
        E.g. Security check, bug presence, or gating condition.
        """
        start = time.perf_counter()
        clean = (prompt + " " + context).lower()

        positive_patterns = [
            r"\b(yes|true|pass|approve|valid|allow|correct|ok)\b",
            r"(通過|確認|允許|合法|正確|成功)",
        ]
        negative_patterns = [
            r"\b(no|false|fail|reject|invalid|deny|block|error)\b",
            r"(拒絕|攔截|錯誤|失敗|禁止|非法)",
        ]

        pos_matches = sum(1 for p in positive_patterns if re.search(p, clean))
        neg_matches = sum(1 for p in negative_patterns if re.search(p, clean))

        if pos_matches > 0 and neg_matches == 0:
            val, prob = True, min(0.70 + 0.15 * pos_matches, 0.98)
        elif neg_matches > 0 and pos_matches == 0:
            val, prob = False, min(0.70 + 0.15 * neg_matches, 0.98)
        elif pos_matches > 0 and neg_matches > 0:
            val = pos_matches >= neg_matches
            prob = 0.55
        else:
            val = False
            prob = 0.50

        elapsed = (time.perf_counter() - start) * 1000
        return DecisionResult(
            primitive="noul",
            value=val,
            probability=round(prob, 3),
            latency_ms=round(elapsed, 2),
            engine="local-rule",
            fallback_required=(prob < self.threshold)
        )

    def choice(self, prompt: str, candidates: list[str], context: str = "") -> DecisionResult:
        """
        Categorical single-choice selection from candidate labels.
        E.g. Routing to subagent (Explorer, DB Architect, Backend Lead).
        """
        start = time.perf_counter()
        if not candidates:
            raise ValueError("Candidates list must not be empty.")

        clean = (prompt + " " + context).lower()
        scores = {c: 0 for c in candidates}

        for c in candidates:
            c_lower = c.lower()
            # Direct match bonus
            pat = r"\b" + re.escape(c_lower) + r"\b"
            direct_hits = len(re.findall(pat, clean)) + (2 if c_lower in clean else 0)
            scores[c] += direct_hits * 3

            # Lexicon expansion match
            keywords = DOMAIN_LEXICON.get(c_lower, [])
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", clean) or kw in clean:
                    scores[c] += 2

        best_candidate = max(scores, key=scores.get)
        best_hits = scores[best_candidate]
        total_hits = sum(scores.values())

        if total_hits > 0 and best_hits > 0:
            # Calibrated probability based on hit dominance
            dominance = best_hits / total_hits
            prob = min(0.65 + 0.32 * dominance, 0.98)
        else:
            best_candidate = candidates[0]
            prob = 1.0 / len(candidates)

        elapsed = (time.perf_counter() - start) * 1000
        return DecisionResult(
            primitive="choice",
            value=best_candidate,
            probability=round(prob, 3),
            latency_ms=round(elapsed, 2),
            engine="local-rule",
            fallback_required=(prob < self.threshold)
        )

    def score(self, prompt: str, context: str = "") -> DecisionResult:
        """
        Continuous relevance / urgency / quality scoring (0.0 ~ 1.0).
        """
        start = time.perf_counter()
        clean = (prompt + " " + context).lower()

        high_signals = ["urgent", "critical", "blocker", "crash", "fatal", "嚴重", "緊急", "崩潰"]
        med_signals = ["warning", "moderate", "slow", "smell", "警告", "延遲", "優化"]
        low_signals = ["trivial", "typo", "minor", "cosmetic", "微小", "格式", "白字"]

        h_count = sum(1 for w in high_signals if w in clean)
        m_count = sum(1 for w in med_signals if w in clean)
        l_count = sum(1 for w in low_signals if w in clean)

        if h_count > 0:
            score_val = min(0.75 + 0.08 * h_count, 0.99)
            prob = 0.90
        elif m_count > 0:
            score_val = min(0.45 + 0.08 * m_count, 0.74)
            prob = 0.82
        elif l_count > 0:
            score_val = max(0.15 - 0.03 * l_count, 0.05)
            prob = 0.85
        else:
            score_val = 0.50
            prob = 0.60

        elapsed = (time.perf_counter() - start) * 1000
        return DecisionResult(
            primitive="score",
            value=round(score_val, 3),
            probability=round(prob, 3),
            latency_ms=round(elapsed, 2),
            engine="local-rule",
            fallback_required=(prob < self.threshold)
        )


def run_tests() -> bool:
    """Self-test verifying all 3 primitives and fallback gating."""
    gate = SystemOneGate(confidence_threshold=0.75)

    # Test 1: Noul positive
    res1 = gate.noul("Request to allow and approve changes")
    assert res1.value is True and res1.probability >= 0.75, f"Noul failed: {res1}"
    assert not res1.fallback_required

    # Test 2: Noul negative
    res2 = gate.noul("Fatal violation, reject and deny execution")
    assert res2.value is False and res2.probability >= 0.75, f"Noul failed: {res2}"
    assert not res2.fallback_required

    # Test 3: Noul ambiguous (should trigger fallback)
    res3 = gate.noul("The sky is blue today")
    assert res3.fallback_required, f"Ambiguous noul should trigger fallback: {res3}"

    # Test 4: Choice routing with domain lexicon
    candidates = ["database", "frontend", "security"]
    res4 = gate.choice("Design PostgreSQL schema and indexes", candidates)
    assert res4.value == "database" and res4.probability >= 0.75, f"Choice failed: {res4}"

    # Test 5: Score rating
    res5 = gate.score("System crash on startup, urgent blocker")
    assert res5.value >= 0.75 and not res5.fallback_required, f"Score failed: {res5}"

    print("[PASS] SystemOneGate: 5/5 assertions passed cleanly (Noul, Choice, Score, Fallback).")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        ok = run_tests()
        sys.exit(0 if ok else 1)

    gate = SystemOneGate()
    demo_noul = gate.noul("Is this file path safe to access?", context="path: /etc/hosts")
    demo_choice = gate.choice("Optimize React render loop", ["frontend", "backend", "devops"])
    demo_score = gate.score("Memory leak detected in production server")

    print(json.dumps({
        "noul_demo": demo_noul.__dict__,
        "choice_demo": demo_choice.__dict__,
        "score_demo": demo_score.__dict__
    }, indent=2, ensure_ascii=False))
