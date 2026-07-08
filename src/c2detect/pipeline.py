"""End-to-end orchestration: parse logs -> per-entity features -> UEBA -> correlate -> explain
-> store. Feature aggregation reads Zeek logs (with Suricata eve.json as a fallback) and produces
one normalized 0..1 sub-score vector per entity (source host). Keys match config `weights`.
"""
from __future__ import annotations
import json
from collections import defaultdict, Counter
from pathlib import Path
from typing import Iterable

from .config import Config
from .correlation.engine import correlate
from .explain.reasoner import build_alert
from .ueba.baseline_model import BaselineUEBA, UebaRecord
from .parsers import zeek as zeek_parser
from .parsers import suricata as suri_parser
from .indicators import entropy, nxdomain, beaconing, dga, ja3ja4, doh, session, length


def _orig_h(rec: dict) -> str | None:
    return rec.get("id.orig_h") or rec.get("orig_h") or rec.get("src_ip")


def _resp_h(rec: dict) -> str | None:
    return rec.get("id.resp_h") or rec.get("resp_h") or rec.get("dest_ip")


def _load_zeek(log_dir: Path, name: str) -> list[dict]:
    for candidate in (log_dir / f"{name}.log", log_dir / name):
        if candidate.exists():
            return list(zeek_parser.read_log(candidate))
    return []


def _load_ja3_baseline(path: str | None) -> set[str]:
    if not path:
        return set()
    p = Path(path)
    if not p.exists():
        return set()
    seen: set[str] = set()
    for line in p.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            seen.add(line)
    return seen


def build_feature_vectors(cfg: Config) -> dict[str, dict]:
    """Aggregate Zeek/Suricata logs into {entity: {indicator: subscore, ...}}.

    entity = source host IP. Each indicator is reduced to the most-suspicious value observed for
    that entity within the capture (max sub-score), which is what the correlation layer weights.
    """
    th = cfg.thresholds
    entropy_high = float(th.get("entropy_high", 3.5))
    nx_high = float(th.get("nxdomain_ratio_high", 0.2))
    cv_low = float(th.get("beacon_cv_low", 0.10))

    log_dir = Path(cfg.get("paths", "zeek_log_dir", default="") or ".")
    eve_path = cfg.get("paths", "suricata_eve", default="")
    ja3_baseline = _load_ja3_baseline(cfg.get("paths", "ja3_baseline", default=None))

    dns_events: dict[str, list[dict]] = defaultdict(list)
    ssl_events: dict[str, list[dict]] = defaultdict(list)
    http_events: dict[str, list[dict]] = defaultdict(list)
    conn_recs: dict[str, list[dict]] = defaultdict(list)
    conn_ts: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    entity_ja3: dict[str, list[str]] = defaultdict(list)
    ja3_counts: Counter = Counter()

    # ---- Zeek ingest ----
    for rec in _load_zeek(log_dir, "dns"):
        ent = _orig_h(rec)
        if ent:
            dns_events[ent].append(rec)
    for rec in _load_zeek(log_dir, "ssl"):
        ent = _orig_h(rec)
        if not ent:
            continue
        ssl_events[ent].append(rec)
        j = rec.get("ja3")
        if j and j != "-":
            entity_ja3[ent].append(j)
            ja3_counts[j] += 1
    for rec in _load_zeek(log_dir, "http"):
        ent = _orig_h(rec)
        if ent:
            http_events[ent].append(rec)
    for rec in _load_zeek(log_dir, "conn"):
        ent = _orig_h(rec)
        if not ent:
            continue
        conn_recs[ent].append(rec)
        try:
            conn_ts[ent][_resp_h(rec) or "?"].append(float(rec.get("ts")))
        except (TypeError, ValueError):
            pass

    # ---- Suricata eve.json fallback (only if the matching Zeek log was absent) ----
    if eve_path and Path(eve_path).exists():
        if not any(ssl_events.values()):
            for ev in suri_parser.read_eve(eve_path, "tls"):
                ent = _orig_h(ev)
                tls = ev.get("tls", {})
                if not ent:
                    continue
                j = (tls.get("ja3") or {}).get("hash")
                rec = {"id.orig_h": ent, "id.resp_h": _resp_h(ev),
                       "server_name": tls.get("sni"), "ja3": j}
                ssl_events[ent].append(rec)
                if j:
                    entity_ja3[ent].append(j)
                    ja3_counts[j] += 1
        if not any(dns_events.values()):
            for ev in suri_parser.read_eve(eve_path, "dns"):
                ent = _orig_h(ev)
                d = ev.get("dns", {})
                if ent and d.get("type") in ("query", None):
                    dns_events[ent].append({
                        "query": d.get("rrname", ""),
                        "rcode_name": d.get("rcode", ""),
                        "qtype_name": d.get("rrtype", ""),
                    })

    baseline_for_rarity = ja3_baseline if ja3_baseline else ja3_counts

    entities = set(dns_events) | set(ssl_events) | set(http_events) | set(conn_recs)
    features: dict[str, dict] = {}
    for ent in entities:
        dns = dns_events.get(ent, [])
        queries = [str(r.get("query", "")) for r in dns if r.get("query")]
        ssl = ssl_events.get(ent, [])
        http = http_events.get(ent, [])
        conns = conn_recs.get(ent, [])

        subs = {
            "dns_entropy": max((entropy.subscore(q, entropy_high) for q in queries), default=0.0),
            "dga": max((dga.subscore(q) for q in queries), default=0.0),
            "query_len": max((length.subscore(q) for q in queries), default=0.0),
            "nxdomain_rate": nxdomain.subscore(dns, nx_high),
            "beacon_cv": max((beaconing.subscore(ts, cv_low)
                              for ts in conn_ts.get(ent, {}).values()), default=0.0),
            "ja3_rarity": max((ja3ja4.rarity_subscore(j, baseline_for_rarity)
                               for j in entity_ja3.get(ent, [])), default=0.0),
            "doh_endpoint": max([doh.subscore(r) for r in ssl] + [doh.subscore(r) for r in http],
                                default=0.0),
            "session_shape": max((session.subscore(r) for r in conns), default=0.0),
        }
        features[ent] = subs
    return features


def get_ueba(cfg: Config):
    """Return a UEBA producer honoring the contract (OpenUBA adapter or fallback)."""
    source = cfg.get("ueba", "source", default="baseline")
    if source == "openuba":
        from .ueba.openuba_client import OpenUBAClient
        return OpenUBAClient(
            es_index=cfg.get("ueba", "openuba", "es_index"),
            hosts=cfg.get("elasticsearch", "hosts"),
        )
    model_path = cfg.get("ueba", "baseline", "model_path", default="models/isoforest.joblib")
    if Path(model_path).exists():
        return BaselineUEBA.load(model_path)
    # No frozen model yet: fit a fresh IsolationForest on the current feature vectors so the
    # pipeline is runnable out-of-the-box. Phase 2 replaces this with a benign-frozen baseline.
    return _fit_adhoc_ueba(cfg)


def _fit_adhoc_ueba(cfg: Config) -> BaselineUEBA:
    import numpy as np
    features = build_feature_vectors(cfg)
    weight_keys = list(cfg.weights.keys()) or ["dns_entropy", "nxdomain_rate", "beacon_cv"]
    contamination = float(cfg.get("ueba", "baseline", "contamination", default=0.05))
    model = BaselineUEBA(contamination=contamination)
    if features:
        X = np.array([[fv.get(k, 0.0) for k in weight_keys] for fv in features.values()])
        model.fit(X, weight_keys)
    else:
        model.feature_names = weight_keys
        model.fit(np.zeros((1, len(weight_keys))), weight_keys)
    return model


def run(cfg: Config) -> list[dict]:
    weights = cfg.weights
    ueba_weight = cfg.ueba_weight
    min_conf = float(cfg.thresholds.get("alert_confidence_min", 0.6))
    mitre_map = cfg.mitre_map

    features = build_feature_vectors(cfg)     # {entity: {indicator: subscore}}
    ueba = get_ueba(cfg)

    alerts: list[dict] = []
    for entity, subscores in features.items():
        rec: UebaRecord = ueba.score(entity, subscores)
        corr = correlate(entity, rec.anomaly_score, subscores, weights, ueba_weight)
        if corr.confidence >= min_conf:
            alerts.append(build_alert(corr, rec, mitre_map, min_conf))
    return alerts
