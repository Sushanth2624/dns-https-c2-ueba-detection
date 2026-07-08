"""JA3 / JA4 TLS fingerprint indicator.
Flags: (a) fingerprints rare vs baseline, (b) known-bad fingerprints, (c) JA3<->SNI mismatch.
JA3 is first-class in Zeek (via plugin) and Suricata; JA4 is best-effort.
Data source: Zeek ssl.log (ja3) / Suricata eve.json tls.
"""
from __future__ import annotations
from typing import Mapping, Set, Iterable, Union

# Fill from your lab implant fingerprints during evaluation; a hit here forces max rarity.
KNOWN_BAD_JA3: Set[str] = set()


def rarity_subscore(ja3: str, baseline: Union[Set[str], Mapping[str, int]]) -> float:
    """1.0 if the fingerprint is unseen/rare vs the baseline, lower as it becomes common.

    `baseline` may be either:
      * a set of JA3 hashes seen during the frozen benign baseline -> unseen == 1.0, seen == 0.0
      * a mapping {ja3: count} (e.g. frequencies within the current capture) -> rarity = 1 - freq
    """
    if not ja3:
        return 0.0
    if ja3 in KNOWN_BAD_JA3:
        return 1.0
    if hasattr(baseline, "values") and hasattr(baseline, "get"):
        total = sum(baseline.values())
        if total <= 0:
            return 1.0
        freq = baseline.get(ja3, 0) / total
        return float(max(0.0, min(1.0, 1.0 - freq)))
    # set / iterable membership semantics
    return 0.0 if ja3 in set(baseline) else 1.0


def sni_mismatch(tls_event: Mapping) -> bool:
    """True when a TLS ClientHello carries a JA3 but no SNI (a common evasion / tooling tell)."""
    ja3 = tls_event.get("ja3") or tls_event.get("ja3_hash")
    sni = tls_event.get("server_name") or tls_event.get("sni")
    return bool(ja3) and not sni
