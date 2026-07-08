"""Self-contained UEBA fallback: IsolationForest over per-entity feature vectors.

This is the SAME model OpenUBA ships as its default, so using it is still legitimately
"UEBA-based anomaly detection" (defensible in the viva). It implements the UEBA contract
(see RESEARCH_AND_PLAN.md section 6): anomaly_score, risk_score, severity per entity.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib


def _severity(risk: int) -> str:
    if risk >= 75:
        return "high"
    if risk >= 50:
        return "medium"
    if risk >= 25:
        return "low"
    return "info"


@dataclass
class UebaRecord:
    entity: str
    anomaly_score: float   # 0..1, higher = more anomalous
    risk_score: int        # 0..100
    severity: str
    features: dict


class BaselineUEBA:
    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self.model = IsolationForest(contamination=contamination, random_state=random_state)
        self.feature_names: list[str] = []

    def fit(self, X: np.ndarray, feature_names: Sequence[str]) -> "BaselineUEBA":
        self.feature_names = list(feature_names)
        self.model.fit(X)
        return self

    def score(self, entity: str, feature_vec: dict) -> UebaRecord:
        x = np.array([[feature_vec.get(f, 0.0) for f in self.feature_names]])
        # decision_function: higher = more normal. Convert to 0..1 anomaly.
        raw = float(self.model.decision_function(x)[0])
        anomaly = float(max(0.0, min(1.0, 0.5 - raw)))  # simple, monotonic mapping
        risk = int(round(anomaly * 100))
        return UebaRecord(entity, anomaly, risk, _severity(risk), feature_vec)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "features": self.feature_names}, path)

    @classmethod
    def load(cls, path: str | Path) -> "BaselineUEBA":
        blob = joblib.load(path)
        inst = cls()
        inst.model = blob["model"]
        inst.feature_names = blob["features"]
        return inst
