"""Beacon-interval regularity — automated call-home has low timing jitter.

We use the coefficient of variation (CV = std/mean) of inter-arrival times; very low CV = very
regular = likely beacon. An optional FFT peak check strengthens the signal. Low volume + high
regularity is the classic stealth-C2 timing fingerprint.

Data source: connection timestamps for a (src -> dst) pair (Zeek conn.log / ssl.log `ts`).
"""
from __future__ import annotations
from typing import Sequence
import numpy as np


def inter_arrivals(timestamps: Sequence[float]) -> np.ndarray:
    ts = np.sort(np.asarray(timestamps, dtype=float))
    return np.diff(ts) if ts.size >= 2 else np.array([])


def coefficient_of_variation(timestamps: Sequence[float]) -> float:
    iat = inter_arrivals(timestamps)
    if iat.size == 0:
        return float("nan")
    mean = iat.mean()
    if mean == 0:
        return float("nan")
    return float(iat.std() / mean)


def subscore(timestamps: Sequence[float], cv_low: float = 0.10, min_events: int = 6) -> float:
    """1.0 = highly regular beacon, 0.0 = irregular/insufficient data."""
    if len(timestamps) < min_events:
        return 0.0
    cv = coefficient_of_variation(timestamps)
    if cv != cv:  # NaN
        return 0.0
    # map: cv <= cv_low -> ~1.0 ; cv >= 3*cv_low -> ~0.0
    return float(max(0.0, min(1.0, 1.0 - (cv / (3 * cv_low)))))
