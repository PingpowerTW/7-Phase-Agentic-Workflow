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
- Negation Engine: 25-char prefix window to prevent semantic inversion blindspots
- Cloud Adapter: Native urllib integration hook for TypeSafe API (with auto-fallback)
- Fallback Gate: If confidence < threshold, signal fallback to System 2 (Gemini/Claude)
"""

import sys
import os
import re
import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any, Optional, Union, List

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

# Negation indicators for context window analysis
NEGATION_TOKENS = ["not", "no", "never", "without", "none", "neither", "nor", "非", "不", "無", "未", "別"]


def is_negated(match_start: int, text: str, window_chars: int = 25) -> bool:
    """Check if a keyword match is immediately preceded by a negation token."""
    start = max(0, match_start - window_chars)
    prefix = text[start:match_start].lower()
    for neg in NEGATION_TOKENS:
        # Match English word boundary or direct Chinese character
        if re.search(r"\b" + re.escape(neg) + r"\b", prefix) or (len(neg) == 1 and neg in prefix):
            return True
    return False


class SystemOneGate:
    """
    Lightweight, deterministic System 1 decision gatekeeper.
    Eliminates token waste by serving high-frequency classification,
    routing, and binary checks in <5ms without generative LLM overhead.
    """

    def __init__(self, confidence_threshold: float = 0.75, custom_lexicon: Optional[dict] = None):
        self.threshold = confidence_threshold
        self.api_key = os.getenv("TYPESAFE_API_KEY", "").strip()
        self.lexicon = dict(DOMAIN_LEXICON)
        if custom_lexicon:
            self.lexicon.update(custom_lexicon)

    def _call_cloud_adapter(self, endpoint: str, payload: dict) -> Optional[dict]:
        """
        Cloud adapter calling TypeSafe AI Jev endpoint via standard urllib.
        Returns None on timeout or error to trigger seamless local fallback.
        """
        if not self.api_key:
            return None

        url = f"https://api.typesafe.ai/v1/systemone/{endpoint}"
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Antigravity-SystemOne-Client/1.0"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=0.8) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            return None
        return None

    def noul(self, prompt: str, context: str = "") -> DecisionResult:
        """
        Binary No/Yes decision (Noul).
        Handles negation prefixes and provides graceful cloud fallback.
        """
        start = time.perf_counter()

        # Try cloud adapter if configured
        cloud_res = self._call_cloud_adapter("noul", {"prompt": prompt, "context": context})
        if cloud_res and "decision" in cloud_res and "probability" in cloud_res:
            elapsed = (time.perf_counter() - start) * 1000
            prob = float(cloud_res["probability"])
            return DecisionResult(
                primitive="noul",
                value=bool(cloud_res["decision"]),
                probability=prob,
                latency_ms=round(elapsed, 2),
                engine="typesafe-jev",
                fallback_required=(prob < self.threshold)
            )

        # Local deterministic heuristic with negation awareness
        clean = (prompt + " " + context).lower()

        positive_patterns = [
            r"\b(yes|true|pass|approve|valid|allow|correct|ok)\b",
            r"(通過|確認|允許|合法|正確|成功)",
        ]
        negative_patterns = [
            r"\b(no|false|fail|reject|invalid|deny|block|error)\b",
            r"(拒絕|攔截|錯誤|失敗|禁止|非法)",
        ]

        pos_matches, neg_matches = 0, 0

        for pat in positive_patterns:
            for m in re.finditer(pat, clean):
                if is_negated(m.start(), clean):
                    neg_matches += 1
                else:
                    pos_matches += 1

        for pat in negative_patterns:
            for m in re.finditer(pat, clean):
                if is_negated(m.start(), clean):
                    pos_matches += 1
                else:
                    neg_matches += 1

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

    def choice(self, prompt: str, candidates: List[str], context: str = "") -> DecisionResult:
        """
        Categorical single-choice selection from candidate labels.
        Deduplicates candidate names and handles domain vocabulary.
        """
        start = time.perf_counter()

        # Deduplicate candidates while preserving order and non-empty strings
        normalized_candidates = []
        seen = set()
        for c in candidates:
            cleaned_c = str(c).strip()
            if cleaned_c and cleaned_c.lower() not in seen:
                seen.add(cleaned_c.lower())
                normalized_candidates.append(cleaned_c)

        if not normalized_candidates:
            raise ValueError("Candidates list must contain at least one non-empty string.")

        # Try cloud adapter if configured
        cloud_res = self._call_cloud_adapter("choice", {
            "prompt": prompt,
            "candidates": normalized_candidates,
            "context": context
        })
        if cloud_res and "decision" in cloud_res and "probability" in cloud_res:
            elapsed = (time.perf_counter() - start) * 1000
            prob = float(cloud_res["probability"])
            return DecisionResult(
                primitive="choice",
                value=str(cloud_res["decision"]),
                probability=prob,
                latency_ms=round(elapsed, 2),
                engine="typesafe-jev",
                fallback_required=(prob < self.threshold)
            )

        clean = (prompt + " " + context).lower()
        scores = {c: 0 for c in normalized_candidates}

        for c in normalized_candidates:
            c_lower = c.lower()
            # Direct match bonus
            pat = r"\b" + re.escape(c_lower) + r"\b"
            direct_hits = len(re.findall(pat, clean)) + (2 if c_lower in clean else 0)
            scores[c] += direct_hits * 3

            # Lexicon expansion match
            keywords = self.lexicon.get(c_lower, [])
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", clean) or kw in clean:
                    scores[c] += 2

        best_candidate = max(scores, key=scores.get)
        best_hits = scores[best_candidate]
        total_hits = sum(scores.values())

        if total_hits > 0 and best_hits > 0:
            dominance = best_hits / total_hits
            prob = min(0.65 + 0.32 * dominance, 0.98)
        else:
            best_candidate = normalized_candidates[0]
            prob = 1.0 / len(normalized_candidates)

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
        Includes negation compensation to avoid misclassifying negated severity.
        """
        start = time.perf_counter()

        # Try cloud adapter if configured
        cloud_res = self._call_cloud_adapter("score", {"prompt": prompt, "context": context})
        if cloud_res and "score" in cloud_res and "probability" in cloud_res:
            elapsed = (time.perf_counter() - start) * 1000
            prob = float(cloud_res["probability"])
            return DecisionResult(
                primitive="score",
                value=float(cloud_res["score"]),
                probability=prob,
                latency_ms=round(elapsed, 2),
                engine="typesafe-jev",
                fallback_required=(prob < self.threshold)
            )

        clean = (prompt + " " + context).lower()

        high_signals = ["urgent", "critical", "blocker", "crash", "fatal", "嚴重", "緊急", "崩潰"]
        med_signals = ["warning", "moderate", "slow", "smell", "警告", "延遲", "優化"]
        low_signals = ["trivial", "typo", "minor", "cosmetic", "微小", "格式", "白字"]

        h_count, m_count, l_count = 0, 0, 0

        for w in high_signals:
            for m in re.finditer(re.escape(w), clean):
                if is_negated(m.start(), clean):
                    l_count += 1
                else:
                    h_count += 1

        for w in med_signals:
            for m in re.finditer(re.escape(w), clean):
                if is_negated(m.start(), clean):
                    l_count += 1
                else:
                    m_count += 1

        for w in low_signals:
            for m in re.finditer(re.escape(w), clean):
                if is_negated(m.start(), clean):
                    m_count += 1
                else:
                    l_count += 1

        # Calculate balanced score with net weighting
        if h_count > 0 and h_count > l_count:
            score_val = min(0.75 + 0.08 * (h_count - l_count), 0.99)
            prob = 0.90
        elif m_count > 0:
            score_val = min(0.45 + 0.08 * m_count, 0.74)
            prob = 0.82
        elif l_count > 0 or (h_count > 0 and l_count >= h_count):
            score_val = max(0.15 - 0.03 * l_count, 0.05)
            prob = 0.88
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
    """Adversarial test suite verifying edge cases, negation, and duplicate protection."""
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

    # Test 5: Score rating standard
    res5 = gate.score("System crash on startup, urgent blocker")
    assert res5.value >= 0.75 and not res5.fallback_required, f"Score failed: {res5}"

    # Adversarial Test 6: Semantic negation blindspot
    # "not a fatal crash" should NOT be scored as critical urgency
    res6 = gate.score("This is not a fatal crash, it is just a minor cosmetic typo")
    assert res6.value <= 0.30, f"Negation blindspot triggered! Score was {res6.value}"

    # Adversarial Test 7: Duplicate and mixed-case candidate list
    res7 = gate.choice("PostgreSQL migration", ["Database", "database", "DATABASE", "frontend"])
    assert res7.value.lower() == "database" and not res7.fallback_required, f"Duplicate candidates broke choice: {res7}"

    # Adversarial Test 8: Noul negation ("not allowed")
    res8 = gate.noul("This action is not allowed under any circumstances")
    assert res8.value is False, f"Negated positive should be false: {res8}"

    print("[PASS] SystemOneGate: 8/8 adversarial assertions passed cleanly (Negation, Deduplication, Fallbacks).")
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
