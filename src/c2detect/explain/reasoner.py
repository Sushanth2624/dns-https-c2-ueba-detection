"""Explainable-alert builder. Turns a CorrelationResult + UEBA record into an analyst-usable alert
with per-indicator reasons, MITRE mapping, and recommended investigation steps.

Deterministic and template-driven — no LLM, fully auditable (that is the point vs black-box ML).
"""
from __future__ import annotations
import uuid
from typing import Mapping

# Human-readable reason templates per indicator.
WHY = {
    "dns_entropy":  "queried domains are near-random (high entropy), consistent with DGA/tunneling",
    "dga":          "domain structure (length, digits, few vowels) matches algorithmically-generated names",
    "nxdomain_rate": "elevated failed lookups (NXDOMAIN) — a domain-generation hallmark",
    "beacon_cv":    "regular call-home timing with very low jitter — automated beacon",
    "ja3_rarity":   "TLS client fingerprint not seen during baseline",
    "doh_endpoint": "DNS is being tunneled over HTTPS to a DoH resolver, bypassing port-53 inspection",
    "session_shape": "small, steady, long-lived flow — encrypted C2 rather than human browsing",
    "query_len":    "unusually long/deep DNS names — possible data in the query",
}

# Investigation steps triggered by which indicators fired.
ACTIONS = {
    "beacon_cv":    "Map the beaconing process to a PID on the host and capture full pcap of the flow.",
    "dns_entropy":  "Hunt the domain/zone across all hosts; check registration age and TTL.",
    "dga":          "Extract the generated domains and pivot on the DGA family; pre-block predicted domains.",
    "query_len":    "Reassemble the long/deep DNS names; check for encoded/exfiltrated data in the labels.",
    "nxdomain_rate": "Review the failed-lookup domains for algorithmic patterns; block the seed zone.",
    "ja3_rarity":   "Pivot on the JA3/JA4 fingerprint across the fleet to find other implants.",
    "doh_endpoint": "Block the DoH resolver and force DNS back through inspected resolvers.",
    "session_shape": "Baseline the destination; if unknown, block and investigate the initiating host.",
}


def verdict_for(confidence: float, min_conf: float) -> str:
    if confidence >= max(min_conf, 0.85):
        return "likely_c2"
    if confidence >= min_conf:
        return "suspicious"
    return "benign"


def build_alert(corr, ueba, mitre_map: Mapping[str, list], min_conf: float, hot: float = 0.6) -> dict:
    fired = [k for k, v in corr.subscores.items() if v >= hot]
    contributing = [
        {"name": k, "value": round(corr.subscores[k], 3), "why": WHY.get(k, "")}
        for k in fired
    ]
    mitre = sorted({t for k in fired for t in mitre_map.get(k, [])})
    actions = [ACTIONS[k] for k in fired if k in ACTIONS]
    if not actions:
        actions = ["Review entity activity; insufficient corroborating indicators for automated guidance."]

    return {
        "alert_id": str(uuid.uuid4()),
        "entity": corr.entity,
        "verdict": verdict_for(corr.confidence, min_conf),
        "confidence": round(corr.confidence, 3),
        "severity": ueba.severity,
        "ueba": {"anomaly_score": round(ueba.anomaly_score, 3), "risk_score": ueba.risk_score},
        "score_breakdown": {
            "ueba_component": round(corr.ueba_component, 3),
            "indicator_component": round(corr.indicator_component, 3),
            "boost": round(corr.boost, 3),
        },
        "contributing_indicators": contributing,
        "mitre": mitre,
        "recommended_actions": actions,
    }
