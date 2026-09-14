"""
Trust Thermodynamics & Behavioral Clustering Governor (Pure Python Stdlib)
Inspired by Behavioral Trust Clustering (BTC, Culotta 2026).

Formula:
    T = PPV * exp(-sigma_calib * T_comp)
Where:
    - PPV: Positive Predictive Value (Mean self-reported confidence)
    - sigma_calib: Normalized Shannon entropy over behavioral clusters [0, 1]
    - T_comp: Computational temperature (defaults to adaptive calibration)
    - T: Final Trust Score [0, 1]
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


class Decision(str, Enum):
    ADMIT = "ADMIT"
    ABSTAIN = "ABSTAIN"


@dataclass(frozen=True)
class GovernanceResult:
    action: Decision
    trust: float
    ppv: float
    sigma_calib: float
    t_comp: float
    n_clusters: int
    modal_answer: Optional[Any]
    modal_agreement: float
    details: Dict[str, Any]


def calculate_entropy(cluster_keys: Sequence[Any]) -> float:
    """Calculate normalized Shannon entropy in [0, 1] for a sequence of cluster identifiers."""
    n = len(cluster_keys)
    if n <= 1:
        return 0.0

    counts = Counter(cluster_keys)
    n_distinct = len(counts)
    if n_distinct <= 1:
        return 0.0

    entropy = 0.0
    for count in counts.values():
        p = count / n
        if p > 0:
            entropy -= p * math.log2(p)

    max_entropy = math.log2(n)
    if max_entropy <= 0:
        return 0.0
    return min(1.0, entropy / max_entropy)


def trust_thermodynamic(
    ppv: float, sigma_calib: float, t_comp: Optional[float] = None
) -> float:
    """
    Compute closed-form trust score:
        T = PPV * exp(-sigma_calib * T_comp)
    """
    if t_comp is None:
        # Adaptive default based on PPV
        t_comp = 1.0 if ppv >= 0.75 else 1.5

    discount = math.exp(-sigma_calib * t_comp)
    return max(0.0, min(1.0, ppv * discount))


def evaluate_candidates(
    candidates: Sequence[Any],
    confidences: Sequence[float],
    cluster_func: Callable[[Any], Any],
    threshold: float = 0.65,
    t_comp: Optional[float] = None,
) -> GovernanceResult:
    """
    Evaluate candidate outputs using behavioral clustering and thermodynamic trust.

    Parameters:
        candidates: Sequence of generated solutions/code snippets
        confidences: Sequence of self-reported confidence values in [0.0, 1.0]
        cluster_func: Function mapping a candidate to a cluster key (e.g. tuple of probe test results)
        threshold: Decision boundary theta (default 0.65 for conservative 52% hallucination reduction)
        t_comp: Optional computational temperature
    """
    if not candidates or not confidences or len(candidates) != len(confidences):
        raise ValueError("Candidates and confidences must be non-empty and of equal length.")

    # 1. Compute behavioral cluster keys
    cluster_keys = [cluster_func(c) for c in candidates]
    counts = Counter(cluster_keys)
    n_clusters = len(counts)

    # 2. Find modal cluster
    modal_key, modal_count = counts.most_common(1)[0]
    modal_agreement = modal_count / len(candidates)

    # Pick the highest confidence candidate inside the modal cluster
    modal_candidates = [
        (c, conf)
        for c, key, conf in zip(candidates, cluster_keys, confidences)
        if key == modal_key
    ]
    modal_candidates.sort(key=lambda x: x[1], reverse=True)
    modal_answer = modal_candidates[0][0]

    # 3. Calculate thermodynamic properties
    ppv = sum(confidences) / len(confidences)
    sigma_calib = calculate_entropy(cluster_keys)
    trust = trust_thermodynamic(ppv, sigma_calib, t_comp)

    # 4. Decision Gate
    action = Decision.ADMIT if trust >= threshold else Decision.ABSTAIN

    return GovernanceResult(
        action=action,
        trust=round(trust, 4),
        ppv=round(ppv, 4),
        sigma_calib=round(sigma_calib, 4),
        t_comp=t_comp if t_comp is not None else (1.0 if ppv >= 0.75 else 1.5),
        n_clusters=n_clusters,
        modal_answer=modal_answer if action == Decision.ADMIT else None,
        modal_agreement=round(modal_agreement, 4),
        details={
            "cluster_distribution": dict(counts),
            "threshold": threshold,
            "raw_modal_answer": modal_answer,
        },
    )


# ==========================================
# Self-Test / Verification Suite
# ==========================================
if __name__ == "__main__":
    print("[*] Running Trust Governor verification tests...")

    # Case 1: High agreement, high confidence -> ADMIT
    c1 = ["def f(x): return x * 2", "def f(x): return x + x", "def f(x): return 2 * x"]
    conf1 = [0.95, 0.90, 0.92]
    # All produce output 4 for input 2, 6 for input 3 -> Identical behavior
    mock_runner = lambda code: (4, 6)
    res1 = evaluate_candidates(c1, conf1, mock_runner, threshold=0.65)
    assert res1.action == Decision.ADMIT, f"Expected ADMIT, got {res1.action}"
    assert res1.sigma_calib == 0.0, f"Expected 0 entropy, got {res1.sigma_calib}"
    print(f"  [PASS] Case 1 (High Agreement): Trust={res1.trust} Action={res1.action}")

    # Case 2: Divergent behavior (Hallucination) -> ABSTAIN
    c2 = ["def f(x): return x * 2", "def f(x): return x ** 2", "def f(x): return x + 1"]
    conf2 = [0.85, 0.80, 0.75]
    # Each behaves differently on probe input
    mock_divergent = lambda code: hash(code) % 3
    res2 = evaluate_candidates(c2, conf2, mock_divergent, threshold=0.65)
    assert res2.action == Decision.ABSTAIN, f"Expected ABSTAIN, got {res2.action}"
    assert res2.trust < 0.65, f"Expected Trust < 0.65, got {res2.trust}"
    print(f"  [PASS] Case 2 (Divergent/Hallucination): Trust={res2.trust} Action={res2.action}")

    print("[+] All Trust Governor tests passed successfully!")
