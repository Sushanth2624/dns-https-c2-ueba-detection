"""Run the A/B/C comparison that answers the research question.

  A. Signature-only     — Suricata rules alone (rules/suricata/local.rules)
  B. Single indicator   — each behavioral indicator used on its own
  C. Multi + UEBA       — the full correlation + UEBA pipeline (this project)

Produces precision/recall/F1/FP-rate for each config, plus detection latency for C.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np

from ..config import Config
from ..correlation.engine import correlate
from ..correlation.rules import HOT
from ..ueba.baseline_model import BaselineUEBA
from .. import pipeline
from ..parsers import zeek as zeek_parser
from . import metrics


def _corpus_config(corpus_dir: Path, base: Config) -> Config:
    raw = dict(base.raw)
    raw["paths"] = {"zeek_log_dir": str(corpus_dir),
                    "ja3_baseline": str(corpus_dir / "ja3_baseline.txt")}
    return Config(raw=raw)


def _train_ueba(features: dict, truth: dict, weight_keys: list[str],
                contamination: float, model_path: str | None) -> BaselineUEBA:
    benign = [features[e] for e, g in truth.items() if g["label"] == 0 and e in features]
    model = BaselineUEBA(contamination=contamination)
    if benign:
        X = np.array([[fv.get(k, 0.0) for k in weight_keys] for fv in benign])
        model.fit(X, weight_keys)
    else:
        model.fit(np.zeros((1, len(weight_keys))), weight_keys)
    if model_path:
        model.save(model_path)
    return model


def _latency_for_scenario(scenario_dir: Path, entity: str, weights, ueba_weight, ueba_anomaly,
                          min_conf, thresholds) -> float | None:
    """Incrementally replay one attack capture's events in time order (single capture epoch, no
    cross-capture background) and return seconds from the first packet to the moment correlation
    confidence first crosses the alert threshold."""
    eh = float(thresholds.get("entropy_high", 3.5))
    nx = float(thresholds.get("nxdomain_ratio_high", 0.2))
    cv = float(thresholds.get("beacon_cv_low", 0.10))

    stream = []
    for kind in ("dns", "ssl", "conn", "http"):
        p = scenario_dir / f"{kind}.log"
        if not p.exists():
            continue
        for r in zeek_parser.read_log(p):
            try:
                ts = float(r.get("ts"))
            except (TypeError, ValueError):
                ts = 0.0
            stream.append((ts, kind, r))
    if not stream:
        return None
    stream.sort(key=lambda x: x[0])
    t0 = stream[0][0]

    dns, ssl, http, conns, ja3 = [], [], [], [], []
    conn_ts: dict[str, list] = {}
    sni_ts: dict[str, list] = {}
    for ts, kind, r in stream:
        if kind == "dns":
            dns.append(r)
        elif kind == "ssl":
            ssl.append(r)
            if r.get("ja3") and r.get("ja3") != "-":
                ja3.append(r["ja3"])
            if r.get("server_name"):
                sni_ts.setdefault(r["server_name"], []).append(ts)
        elif kind == "http":
            http.append(r)
        elif kind == "conn":
            conns.append(r)
            dst = r.get("id.resp_h") or "?"
            conn_ts.setdefault(dst, []).append(ts)
        subs = pipeline.entity_subscores(dns, ssl, http, conns, conn_ts, ja3, set(),
                                         eh, nx, cv, sni_ts)
        corr = correlate(entity, ueba_anomaly, subs, weights, ueba_weight)
        if corr.confidence >= min_conf:
            return round(ts - t0, 3)
    return None


def evaluate(captures_dir: str | Path, corpus_dir: str | Path, base_cfg: Config,
             model_path: str | None = None) -> dict:
    corpus_dir = Path(corpus_dir)
    cfg = _corpus_config(corpus_dir, base_cfg)

    truth = json.loads((corpus_dir / "ground_truth.json").read_text())
    signature_hits = json.loads((corpus_dir / "signature_hits.json").read_text())
    truth_labels = {e: g["label"] for e, g in truth.items()}

    weights = base_cfg.weights
    weight_keys = list(weights.keys())
    ueba_weight = base_cfg.ueba_weight
    thresholds = base_cfg.thresholds
    min_conf = float(thresholds.get("alert_confidence_min", 0.6))
    contamination = float(base_cfg.get("ueba", "baseline", "contamination", default=0.05))

    # ---- features (config C uses these; B thresholds them) ----
    features = pipeline.build_feature_vectors(cfg)
    ueba = _train_ueba(features, truth, weight_keys, contamination, model_path)
    ueba_scores = {e: ueba.score(e, fv).anomaly_score for e, fv in features.items()}

    # ---- Config C: multi-indicator + UEBA correlation ----
    c_pred, c_conf = {}, {}
    for e, fv in features.items():
        corr = correlate(e, ueba_scores[e], fv, weights, ueba_weight)
        c_conf[e] = round(corr.confidence, 3)
        c_pred[e] = 1 if corr.confidence >= min_conf else 0
    c_metrics = metrics.score(c_pred, truth_labels)

    # ---- Config B: each single indicator, thresholded at HOT ----
    b_results = {}
    for key in weight_keys:
        pred = {e: (1 if fv.get(key, 0.0) >= HOT else 0) for e, fv in features.items()}
        b_results[key] = metrics.score(pred, truth_labels).as_dict()
    best_b = max(b_results, key=lambda k: b_results[k]["f1"])

    # ---- Config A: signature-only (Suricata) ----
    a_pred = {}
    for e, g in truth.items():
        scenario = g["attack_type"] if g["label"] == 1 else "benign"
        a_pred[e] = 1 if signature_hits.get(scenario, 0) > 0 else 0
    a_metrics = metrics.score(a_pred, truth_labels)

    # ---- detection latency for C (measured within each attack's own capture) ----
    latency = {}
    captures_dir = Path(captures_dir)
    for e, g in truth.items():
        if g["label"] == 1:
            latency[e] = _latency_for_scenario(
                captures_dir / g["attack_type"], e, weights, ueba_weight,
                ueba_scores.get(e, 0.0), min_conf, thresholds)

    return {
        "n_entities": len(truth_labels),
        "n_benign": sum(1 for v in truth_labels.values() if v == 0),
        "n_attacks": sum(1 for v in truth_labels.values() if v == 1),
        "config_A_signature": a_metrics.as_dict(),
        "config_B_single": b_results,
        "config_B_best": {"indicator": best_b, **b_results[best_b]},
        "config_C_multi_ueba": c_metrics.as_dict(),
        "C_confidence": c_conf,
        "C_predictions": c_pred,
        "detection_latency_sec": latency,
        "ueba_anomaly": {e: round(s, 3) for e, s in ueba_scores.items()},
        "ground_truth": {e: g["label"] for e, g in truth.items()},
    }
