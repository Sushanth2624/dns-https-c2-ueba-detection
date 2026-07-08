"""DGA likelihood — combines entropy, domain length, digit ratio, and (low) vowel ratio.

Algorithmically-generated domains tend to be long, high-entropy, digit-heavy and vowel-poor
compared with human-registered domains. We score the most suspicious (longest) label so a benign
parent zone with a random subdomain still scores high.

Data source: Zeek dns.log `query`.
"""
from __future__ import annotations
from .entropy import shannon_entropy

_VOWELS = set("aeiou")


def _label_features(label: str) -> dict:
    n = len(label)
    if n == 0:
        return {"len": 0, "entropy": 0.0, "digit_ratio": 0.0, "vowel_ratio": 0.0}
    digits = sum(c.isdigit() for c in label)
    vowels = sum(c in _VOWELS for c in label.lower())
    return {
        "len": n,
        "entropy": shannon_entropy(label),
        "digit_ratio": digits / n,
        "vowel_ratio": vowels / n,
    }


def subscore(domain: str) -> float:
    """Return 0..1 DGA likelihood for the most suspicious label in `domain`."""
    labels = [lbl for lbl in domain.split(".") if lbl]
    if not labels:
        return 0.0
    # Prefer labels longer than a typical TLD so the random part, not "com", is scored.
    candidates = [lbl for lbl in labels if len(lbl) > 3] or labels
    label = max(candidates, key=len)
    f = _label_features(label)
    if f["len"] == 0:
        return 0.0

    ent_score = min(1.0, f["entropy"] / 4.0)                 # ~4 bits/char is near-random for a-z0-9
    len_score = min(1.0, max(0.0, (f["len"] - 7) / 15.0))    # length starts mattering past ~7 chars
    digit_score = min(1.0, f["digit_ratio"] / 0.30)          # digit-heavy is a DGA tell
    vowel_penalty = 1.0 - min(1.0, f["vowel_ratio"] / 0.40)  # vowel-poor -> higher

    score = 0.40 * ent_score + 0.20 * len_score + 0.20 * digit_score + 0.20 * vowel_penalty
    return float(max(0.0, min(1.0, score)))
