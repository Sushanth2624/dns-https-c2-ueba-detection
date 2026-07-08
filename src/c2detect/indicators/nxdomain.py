"""NXDOMAIN behaviour — bursts of failed lookups per host are a DGA hallmark.

Data source: Zeek dns.log `rcode_name`.
"""
from __future__ import annotations
from typing import Iterable, Mapping


def nxdomain_ratio(dns_events: Iterable[Mapping]) -> float:
    total = 0
    nx = 0
    for ev in dns_events:
        total += 1
        if str(ev.get("rcode_name", "")).upper() == "NXDOMAIN":
            nx += 1
    return (nx / total) if total else 0.0


def subscore(dns_events: Iterable[Mapping], ratio_high: float = 0.2) -> float:
    r = nxdomain_ratio(dns_events)
    return max(0.0, min(1.0, r / ratio_high))
