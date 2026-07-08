"""Confusion-matrix metrics for the A/B/C comparison."""
from __future__ import annotations
from dataclasses import dataclass, asdict


@dataclass
class Metrics:
    tp: int
    fp: int
    fn: int
    tn: int

    @property
    def precision(self) -> float:
        d = self.tp + self.fp
        return self.tp / d if d else 0.0

    @property
    def recall(self) -> float:
        d = self.tp + self.fn
        return self.tp / d if d else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    @property
    def fpr(self) -> float:
        d = self.fp + self.tn
        return self.fp / d if d else 0.0

    def as_dict(self) -> dict:
        d = asdict(self)
        d.update(precision=round(self.precision, 3), recall=round(self.recall, 3),
                 f1=round(self.f1, 3), fpr=round(self.fpr, 3))
        return d


def score(predictions: dict[str, int], truth: dict[str, int]) -> Metrics:
    """predictions/truth: {entity: 0|1}. Returns confusion metrics over shared entities."""
    tp = fp = fn = tn = 0
    for ent, y in truth.items():
        yhat = predictions.get(ent, 0)
        if y == 1 and yhat == 1:
            tp += 1
        elif y == 0 and yhat == 1:
            fp += 1
        elif y == 1 and yhat == 0:
            fn += 1
        else:
            tn += 1
    return Metrics(tp, fp, fn, tn)
