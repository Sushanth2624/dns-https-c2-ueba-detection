"""Domain entropy indicator — high Shannon entropy suggests DGA / DNS tunneling.

Data source: Zeek dns.log `query`.
"""
from __future__ import annotations
import math
from collections import Counter


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def longest_label_entropy(domain: str) -> float:
    """Entropy of the highest-entropy label (subdomains carry tunneled data)."""
    labels = [lbl for lbl in domain.split(".") if lbl]
    return max((shannon_entropy(lbl) for lbl in labels), default=0.0)


def subscore(domain: str, entropy_high: float = 3.5) -> float:
    """Normalized 0..1 sub-score for the correlation engine."""
    e = longest_label_entropy(domain)
    return max(0.0, min(1.0, e / (entropy_high * 1.5)))
