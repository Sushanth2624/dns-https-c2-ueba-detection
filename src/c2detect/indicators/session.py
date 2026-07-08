"""Session-shape indicator — small, steady, long-lived flows with even up/down byte ratio look
like encrypted C2 rather than human browsing.
Data source: Zeek conn.log (duration, orig_bytes, resp_bytes, packet counts).
"""
from __future__ import annotations
from typing import Mapping


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def subscore(conn_event: Mapping) -> float:
    """1.0 = C2-like session shape (long-lived, low-throughput, even byte ratio), 0.0 = human-like."""
    duration = _num(conn_event.get("duration"))
    orig_bytes = _num(conn_event.get("orig_bytes"))
    resp_bytes = _num(conn_event.get("resp_bytes"))
    if duration <= 0:
        return 0.0

    total = orig_bytes + resp_bytes
    # long-lived: a flow held open for minutes is unusual for a single human page load
    dur_score = min(1.0, duration / 300.0)                     # >= 5 min -> 1.0
    # low throughput: little data spread over a long time = trickle (beacon/keepalive)
    throughput = total / duration                              # bytes/sec
    low_vol_score = 1.0 - min(1.0, throughput / 500.0)         # < 500 B/s -> high
    # even up/down: browsing is download-heavy; C2 request/response is more balanced
    hi = max(orig_bytes, resp_bytes)
    even_score = (min(orig_bytes, resp_bytes) / hi) if hi > 0 else 0.0

    score = 0.40 * dur_score + 0.40 * low_vol_score + 0.20 * even_score
    return float(max(0.0, min(1.0, score)))
