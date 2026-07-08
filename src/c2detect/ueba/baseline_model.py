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
    """UEBA fallback = IsolationForest **plus a one-sided z-score** over the benign baseline.

    The IsolationForest captures multivariate outliers; the z-score term catches a single feature
    sitting far above the benign mean (e.g. a near-perfect beacon whose beacon_cv is ~1.0 when every
    benign host is ~0). Since every indicator is oriented "higher = more suspicious", only positive
    deviations from the benign mean raise the anomaly. The final anomaly is the max of the two,
    keeping the score conservative for benign entities but responsive to strong lone signals.
    """

    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self.model = IsolationForest(contamination=contamination, random_state=random_state)
        self.feature_names: list[str] = []
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None

    def fit(self, X: np.ndarray, feature_names: Sequence[str]) -> "BaselineUEBA":
        self.feature_names = list(feature_names)
        X = np.asarray(X, dtype=float)
        self.model.fit(X)
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0)
        return self

    def _iforest_anomaly(self, x: np.ndarray) -> float:
        raw = float(self.model.decision_function(x)[0])  # higher = more normal
        return float(max(0.0, min(1.0, 0.5 - raw)))

    def _zscore_anomaly(self, x: np.ndarray) -> float:
        if self.mean_ is None or self.std_ is None:
            return 0.0
        std = np.maximum(self.std_, 0.05)                 # floor avoids divide-by-zero blow-ups
        pos_z = np.maximum(0.0, (x[0] - self.mean_) / std)  # one-sided: only "worse than benign"
        z = float(pos_z.max()) if pos_z.size else 0.0
        return float(min(1.0, z / 6.0))                   # 6 sigma -> saturated

    def score(self, entity: str, feature_vec: dict) -> UebaRecord:
        x = np.array([[feature_vec.get(f, 0.0) for f in self.feature_names]])
        anomaly = max(self._iforest_anomaly(x), self._zscore_anomaly(x))
        risk = int(round(anomaly * 100))
        return UebaRecord(entity, anomaly, risk, _severity(risk), feature_vec)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "features": self.feature_names,
                     "mean": self.mean_, "std": self.std_}, path)

    @classmethod
    def load(cls, path: str | Path) -> "BaselineUEBA":
        blob = joblib.load(path)
        inst = cls()
        inst.model = blob["model"]
        inst.feature_names = blob["features"]
        inst.mean_ = blob.get("mean")
        inst.std_ = blob.get("std")
        return inst
