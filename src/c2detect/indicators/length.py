"""Query length / subdomain depth indicator — long labels and deep names carry tunneled data.

Data source: Zeek dns.log `query`.
"""
from __future__ import annotations


def subscore(domain: str, max_label: int = 30, max_depth: int = 5) -> float:
    """0..1 based on the longest label length and subdomain depth of a DNS name."""
    labels = [lbl for lbl in domain.split(".") if lbl]
    if not labels:
        return 0.0
    longest = max(len(lbl) for lbl in labels)
    depth = len(labels)
    len_score = min(1.0, longest / max_label)
    depth_score = min(1.0, depth / max_depth)
    return float(max(0.0, min(1.0, max(len_score, depth_score))))
