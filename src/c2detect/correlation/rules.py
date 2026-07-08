"""Correlation weights and hard-boost rules. All glass-box and reported in the thesis.

Weights come from config (config/config.yaml -> weights, ueba_weight). Boost rules encode
high-signal indicator combinations that should escalate confidence beyond the linear sum.
"""
from __future__ import annotations
from typing import Mapping


# High-signal combinations -> additive confidence boost (documented, tunable).
BOOST_RULES = [
    # (set of indicators that must all be "hot", boost)
    ({"dns_entropy", "nxdomain_rate"}, 0.10),            # classic DGA
    ({"dga", "nxdomain_rate"}, 0.10),                    # DGA structure + failed lookups
    ({"query_len", "dns_entropy"}, 0.10),               # long high-entropy names -> tunneling
    ({"beacon_cv", "session_shape"}, 0.10),              # automated encrypted beacon
    ({"beacon_cv", "ja3_rarity"}, 0.12),                 # regular call-home + anomalous TLS fingerprint
    ({"dns_entropy", "beacon_cv", "ja3_rarity"}, 0.15),  # tunneling + regular + odd TLS
    ({"doh_endpoint", "beacon_cv"}, 0.10),               # DoH-based beacon
]

HOT = 0.6  # a sub-score at/above this counts as "hot" for boost rules


def apply_boosts(subscores: Mapping[str, float]) -> float:
    hot = {k for k, v in subscores.items() if v >= HOT}
    boost = 0.0
    for needed, amount in BOOST_RULES:
        if needed.issubset(hot):
            boost += amount
    return boost
