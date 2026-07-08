"""Correlation engine — fuse the UEBA anomaly score with weighted behavioral indicators into a
single confidence. Glass-box: every term is inspectable and reported.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from .rules import apply_boosts


@dataclass
class CorrelationResult:
    entity: str
    confidence: float               # 0..1
    ueba_component: float
    indicator_component: float
    boost: float
    subscores: dict                 # indicator -> 0..1


def correlate(
    entity: str,
    ueba_anomaly: float,
    subscores: Mapping[str, float],
    weights: Mapping[str, float],
    ueba_weight: float,
) -> CorrelationResult:
    # weighted indicator bundle (normalize by weight sum actually used)
    used = {k: subscores.get(k, 0.0) for k in weights}
    wsum = sum(weights.values()) or 1.0
    indicator_component = sum(weights[k] * used[k] for k in weights) / wsum

    ueba_component = ueba_weight * ueba_anomaly
    base = ueba_component + (1 - ueba_weight) * indicator_component
    boost = apply_boosts(subscores)
    confidence = float(max(0.0, min(1.0, base + boost)))
    return CorrelationResult(
        entity=entity,
        confidence=confidence,
        ueba_component=ueba_component,
        indicator_component=indicator_component,
        boost=boost,
        subscores=dict(subscores),
    )
