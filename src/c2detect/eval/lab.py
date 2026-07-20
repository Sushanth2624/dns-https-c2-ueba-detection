"""Evaluate the container-lab inline capture directly.

Unlike eval/corpus.py (which relabels single-host captures onto synthetic IPs), the container lab
produces ONE mixed capture whose entities are already real, distinct source IPs. So we evaluate it
as-is: real per-host feature vectors, ground truth from the capture manifest, per-entity Suricata
hits (mapped by src_ip), and A/B/C metrics + detection latency.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np

from ..config import Config
from ..correlation.engine import correlate
from ..correlation.rules import HOT
from .. import pipeline
from ..parsers import zeek as zeek_parser
from ..parsers import suricata as suri_parser
from .evaluate import _train_ueba
from . import metrics


def _freeze_benign_ja3(lab_dir: Path, benign_entities: set) -> Path:
    seen = set()
    ssl = lab_dir / "ssl.log"
    if ssl.exists():
        for r in zeek_parser.read_log(ssl):
            if r.get("id.orig_h") in benign_entities and r.get("ja3") and r.get("ja3") != "-":
                seen.add(r["ja3"])
    out = lab_dir / "ja3_baseline.txt"
    out.write_text("\n".join(sorted(seen)) + ("\n" if seen else ""))
    return out


def _entity_signature_hits(lab_dir: Path) -> dict:
    hits: dict[str, int] = {}
    eve = lab_dir / "eve.json"
    if eve.exists():
        for ev in suri_parser.read_eve(eve, "alert"):
            src = ev.get("src_ip")
            if src:
                hits[src] = hits.get(src, 0) + 1
    return hits


def _latency(lab_dir: Path, entity: str, weights, ueba_weight, ueba_anom, min_conf, th):
    eh = float(th.get("entropy_high", 3.5)); nx = float(th.get("nxdomain_ratio_high", 0.2))
    cv = float(th.get("beacon_cv_low", 0.10))
    stream = []
    for kind in ("dns", "ssl", "conn", "http"):
        p = lab_dir / f"{kind}.log"
        if not p.exists():
            continue
        for r in zeek_parser.read_log(p):
            if r.get("id.orig_h") != entity:
                continue
            try:
                ts = float(r.get("ts"))
            except (TypeError, ValueError):
                ts = 0.0
            stream.append((ts, kind, r))
    if not stream:
        return None
    stream.sort(key=lambda x: x[0]); t0 = stream[0][0]
    dns, ssl, http, conns, ja3 = [], [], [], [], []
    conn_ts, sni_ts = {}, {}
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
            conn_ts.setdefault(r.get("id.resp_h") or "?", []).append(ts)
        subs = pipeline.entity_subscores(dns, ssl, http, conns, conn_ts, ja3, set(),
                                         eh, nx, cv, sni_ts)
        corr = correlate(entity, ueba_anom, subs, weights, ueba_weight)
        if corr.confidence >= min_conf:
            return round(ts - t0, 3)
    return None


def evaluate_lab(lab_dir: str | Path, base_cfg: Config, model_path: str | None = None) -> dict:
    lab_dir = Path(lab_dir)
    manifest = json.loads((lab_dir / "manifest.json").read_text())
    ent_map = manifest["entities"]                       # ip -> role ("benign"/"dga"/...)
    truth = {ip: {"label": 0 if role == "benign" else 1,
                  "attack_type": None if role == "benign" else role}
             for ip, role in ent_map.items()}
    benign = {ip for ip, g in truth.items() if g["label"] == 0}

    ja3_file = _freeze_benign_ja3(lab_dir, benign)
    cfg = Config(raw={**base_cfg.raw,
                      "paths": {"zeek_log_dir": str(lab_dir), "ja3_baseline": str(ja3_file)}})
    weights = base_cfg.weights; weight_keys = list(weights.keys())
    ueba_weight = base_cfg.ueba_weight; th = base_cfg.thresholds
    min_conf = float(th.get("alert_confidence_min", 0.6))
    contamination = float(base_cfg.get("ueba", "baseline", "contamination", default=0.05))

    features = pipeline.build_feature_vectors(cfg)
    # keep only labelled lab entities
    features = {e: v for e, v in features.items() if e in truth}
    truth_labels = {e: g["label"] for e, g in truth.items()}

    # UEBA anomaly per entity — from OpenUBA (the configured engine) or the IsolationForest fallback.
    ueba_source = base_cfg.get("ueba", "source", default="baseline")
    if ueba_source == "openuba":
        from ..ueba.openuba_client import OpenUBAClient
        ou = base_cfg.get("ueba", "openuba", default={}) or {}
        client = OpenUBAClient(
            api_url=ou.get("api_url", "http://localhost:8000"),
            username=ou.get("username", "openuba"), password=ou.get("password", "password"),
            model_id=ou.get("model_id"),
            saved_models_dir=ou.get("saved_models_dir",
                                    "/home/analysis/openuba-src/core/storage/saved_models"),
            runner_dir=ou.get("runner_dir", "/opt/openuba/saved_models"),
            train_on_benign=bool(ou.get("train_on_benign", False)))
        client.prime(features, benign_entities=benign, feature_keys=weight_keys)
        ueba_scores = {e: client.score(e, fv).anomaly_score for e, fv in features.items()}
    else:
        ueba = _train_ueba(features, truth, weight_keys, contamination, model_path)
        ueba_scores = {e: ueba.score(e, fv).anomaly_score for e, fv in features.items()}

    # Config C
    c_pred, c_conf = {}, {}
    for e, fv in features.items():
        corr = correlate(e, ueba_scores[e], fv, weights, ueba_weight)
        c_conf[e] = round(corr.confidence, 3)
        c_pred[e] = 1 if corr.confidence >= min_conf else 0
    c_metrics = metrics.score(c_pred, truth_labels)

    # Config B
    b_results = {k: metrics.score(
        {e: (1 if fv.get(k, 0.0) >= HOT else 0) for e, fv in features.items()},
        truth_labels).as_dict() for k in weight_keys}
    best_b = max(b_results, key=lambda k: b_results[k]["f1"])

    # Config A (per-entity Suricata hits by src_ip)
    sig = _entity_signature_hits(lab_dir)
    a_pred = {e: (1 if sig.get(e, 0) > 0 else 0) for e in truth}
    a_metrics = metrics.score(a_pred, truth_labels)

    latency = {e: _latency(lab_dir, e, weights, ueba_weight, ueba_scores.get(e, 0.0),
                           min_conf, th) for e, g in truth.items() if g["label"] == 1}

    return {
        "source": "container-lab-inline", "n_entities": len(truth_labels),
        "n_benign": sum(1 for v in truth_labels.values() if v == 0),
        "n_attacks": sum(1 for v in truth_labels.values() if v == 1),
        "config_A_signature": a_metrics.as_dict(),
        "config_B_single": b_results,
        "config_B_best": {"indicator": best_b, **b_results[best_b]},
        "config_C_multi_ueba": c_metrics.as_dict(),
        "C_confidence": c_conf, "C_predictions": c_pred,
        "detection_latency_sec": latency,
        "attack_type": {e: g["attack_type"] for e, g in truth.items()},
        "ueba_anomaly": {e: round(s, 3) for e, s in ueba_scores.items()},
        "ground_truth": {e: g["label"] for e, g in truth.items()},
        "signature_hits_by_entity": sig,
    }
