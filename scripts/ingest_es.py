#!/usr/bin/env python3
"""Ingest the real container-lab inline capture into Elasticsearch so every stage is explorable:

  c2-alerts         explainable alerts (also written by the pipeline `run`)
  c2-entity-scores  per-entity scores for ALL real hosts (benign + attack) — the separation
  zeek-dns / zeek-ssl / zeek-conn   raw Zeek telemetry, tagged with the real host + label
  suricata-alerts   Suricata rule hits, tagged by src_ip

Entities are the real distinct source IPs captured inline on the lab bridge (no relabeling).
Usage: ingest_es.py [--lab data/captures/lab] [--config config/config.lab.yaml] [--es URL]
"""
from __future__ import annotations
import argparse
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from elasticsearch import Elasticsearch, helpers


def _es_password():
    """ELASTIC_PASSWORD from env, else parsed from config/secrets.env (gitignored)."""
    pw = os.environ.get("ELASTIC_PASSWORD")
    if pw:
        return pw
    sec = Path(__file__).resolve().parent.parent / "config" / "secrets.env"
    if sec.exists():
        for line in sec.read_text().splitlines():
            if line.startswith("ELASTIC_PASSWORD="):
                return line.split("=", 1)[1].strip()
    return None


def make_es(host):
    pw = _es_password()
    if host.startswith("https") or pw:
        return Elasticsearch(host, basic_auth=("elastic", pw or ""),
                             verify_certs=False, ssl_show_warn=False)
    return Elasticsearch(host)

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from c2detect.config import Config
from c2detect.eval.lab import evaluate_lab
from c2detect.parsers import zeek as zeek_parser
from c2detect.parsers import suricata as suri_parser


def recreate(es, index, mapping):
    es.indices.delete(index=index, ignore_unavailable=True)
    es.indices.create(index=index, mappings=mapping)


# ---- time spreading: map the compressed capture window onto the last SPREAD_HOURS so Kibana
# time-series have realistic shape while preserving each host's relative timing (e.g. beacons). ----
SPREAD_HOURS = 24.0


class TimeSpread:
    def __init__(self, lab_dir):
        ts = []
        for kind in ("dns", "ssl", "conn"):
            p = lab_dir / f"{kind}.log"
            if p.exists():
                for r in zeek_parser.read_log(p):
                    try:
                        ts.append(float(r.get("ts")))
                    except (TypeError, ValueError):
                        pass
        self.lo = min(ts) if ts else 0.0
        self.hi = max(ts) if ts else 1.0
        self.span = max(self.hi - self.lo, 1e-6)
        self.now = datetime.now(timezone.utc)

    def iso(self, ts):
        try:
            frac = (float(ts) - self.lo) / self.span
        except (TypeError, ValueError):
            frac = 1.0
        frac = min(1.0, max(0.0, frac))
        dt = self.now - timedelta(hours=SPREAD_HOURS * (1.0 - frac))
        return dt.isoformat()


def _iso(ts):
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
    except (TypeError, ValueError):
        return datetime.now(timezone.utc).isoformat()


def _host_last_ts(lab_dir):
    """Latest event ts per host (used to time-place its detection on the axis)."""
    last = {}
    for kind in ("dns", "ssl", "conn"):
        p = lab_dir / f"{kind}.log"
        if p.exists():
            for r in zeek_parser.read_log(p):
                e = r.get("id.orig_h")
                try:
                    t = float(r.get("ts"))
                except (TypeError, ValueError):
                    continue
                if e and (e not in last or t > last[e]):
                    last[e] = t
    return last


def ingest_entity_scores(es, lab_dir, cfg, spread):
    results = evaluate_lab(lab_dir, cfg, model_path=cfg.get(
        "ueba", "baseline", "model_path", default="models/isoforest.joblib"))
    recreate(es, "c2-entity-scores", {"properties": {
        "@timestamp": {"type": "date"}, "entity": {"type": "keyword"},
        "label": {"type": "keyword"}, "attack_type": {"type": "keyword"},
        "verdict": {"type": "keyword"}, "confidence": {"type": "float"},
        "ueba_anomaly": {"type": "float"}, "risk": {"type": "integer"}}})
    last = _host_last_ts(lab_dir)
    docs = []
    gt = results["ground_truth"]
    for e in gt:
        docs.append({"_index": "c2-entity-scores", "_id": e, "_source": {
            "@timestamp": spread.iso(last.get(e)), "entity": e,
            "label": "attack" if gt[e] == 1 else "benign",
            "attack_type": results["attack_type"].get(e),
            "verdict": "flagged" if results["C_predictions"][e] == 1 else "clear",
            "confidence": results["C_confidence"][e],
            "ueba_anomaly": results["ueba_anomaly"][e],
            "risk": int(round(results["C_confidence"][e] * 100))}})
    helpers.bulk(es, docs)
    return len(docs), results


def ingest_zeek(es, lab_dir, spread):
    manifest = json.loads((lab_dir / "manifest.json").read_text())
    ent_map = manifest["entities"]
    label_of = {ip: ("attack" if role != "benign" else "benign") for ip, role in ent_map.items()}
    role_of = ent_map
    total = {}
    for kind in ("dns", "ssl", "conn"):
        idx = f"zeek-{kind}"
        recreate(es, idx, {"properties": {"@timestamp": {"type": "date"},
                 "entity": {"type": "keyword"}, "label": {"type": "keyword"},
                 "role": {"type": "keyword"}, "query": {"type": "keyword"},
                 "server_name": {"type": "keyword"}, "ja3": {"type": "keyword"},
                 "rcode_name": {"type": "keyword"}, "id.resp_h": {"type": "keyword"}}})
        p = lab_dir / f"{kind}.log"
        if not p.exists():
            continue
        docs = []
        for r in zeek_parser.read_log(p):
            ent = r.get("id.orig_h")
            docs.append({"_index": idx, "_source": {**r, "@timestamp": spread.iso(r.get("ts")),
                         "entity": ent, "label": label_of.get(ent, "other"),
                         "role": role_of.get(ent, "other")}})
        if docs:
            helpers.bulk(es, docs, raise_on_error=False)
        total[idx] = len(docs)
    return total


def _eve_epoch(ts_iso):
    try:
        return datetime.fromisoformat(ts_iso.replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError, AttributeError):
        return None


def ingest_suricata(es, lab_dir, spread):
    manifest = json.loads((lab_dir / "manifest.json").read_text())
    role_of = manifest.get("entities", {})
    recreate(es, "suricata-alerts", {"properties": {"@timestamp": {"type": "date"},
             "signature": {"type": "keyword"}, "src_ip": {"type": "keyword"},
             "entity": {"type": "keyword"}, "scenario": {"type": "keyword"},
             "dest_ip": {"type": "keyword"}, "category": {"type": "keyword"}}})
    docs = []
    eve = lab_dir / "eve.json"
    if eve.exists():
        for ev in suri_parser.read_eve(eve, "alert"):
            a = ev.get("alert", {})
            src = ev.get("src_ip")
            docs.append({"_index": "suricata-alerts", "_source": {
                "@timestamp": spread.iso(_eve_epoch(ev.get("timestamp"))),
                "signature": a.get("signature"), "category": a.get("category"),
                "src_ip": src, "entity": src, "scenario": role_of.get(src, "other"),
                "dest_ip": ev.get("dest_ip")}})
    if docs:
        helpers.bulk(es, docs, raise_on_error=False)
    return len(docs)


def ingest_eval(es, results):
    """A/B/C comparison metrics as one doc per (config, metric) for a grouped bar chart."""
    recreate(es, "c2-eval", {"properties": {
        "@timestamp": {"type": "date"}, "config": {"type": "keyword"},
        "config_label": {"type": "keyword"}, "metric": {"type": "keyword"},
        "value": {"type": "float"}}})
    now = datetime.now(timezone.utc).isoformat()
    rows = {
        "A · signature-only": results["config_A_signature"],
        f"B · best single ({results['config_B_best']['indicator']})": results["config_B_best"],
        "C · multi-indicator + UEBA": results["config_C_multi_ueba"],
    }
    docs = []
    for label, m in rows.items():
        cfg_key = label.split(" ")[0]
        for metric in ("precision", "recall", "f1", "fpr"):
            docs.append({"_index": "c2-eval", "_source": {
                "@timestamp": now, "config": cfg_key, "config_label": label,
                "metric": metric, "value": m[metric]}})
    helpers.bulk(es, docs)
    return len(docs)


def ingest_indicator_scores(es, lab_dir, cfg, spread):
    """One doc per (host, indicator) sub-score — powers the entity×indicator heatmap."""
    from c2detect import pipeline
    manifest = json.loads((lab_dir / "manifest.json").read_text())
    ent_map = manifest["entities"]
    ccfg = Config(raw={**cfg.raw, "paths": {"zeek_log_dir": str(lab_dir),
                 "ja3_baseline": str(lab_dir / "ja3_baseline.txt")}})
    feats = pipeline.build_feature_vectors(ccfg)
    last = _host_last_ts(lab_dir)
    recreate(es, "c2-indicator-scores", {"properties": {
        "@timestamp": {"type": "date"}, "entity": {"type": "keyword"},
        "label": {"type": "keyword"}, "indicator": {"type": "keyword"},
        "subscore": {"type": "float"}}})
    docs = []
    for e, fv in feats.items():
        if e not in ent_map:
            continue
        lbl = "attack" if ent_map[e] != "benign" else "benign"
        for ind, val in fv.items():
            docs.append({"_index": "c2-indicator-scores", "_source": {
                "@timestamp": spread.iso(last.get(e)), "entity": e, "label": lbl,
                "indicator": ind, "subscore": round(val, 3)}})
    helpers.bulk(es, docs)
    return len(docs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", default="data/captures/lab")
    ap.add_argument("--config", default="config/config.lab.yaml")
    ap.add_argument("--es", default="https://localhost:9200")
    args = ap.parse_args()

    es = make_es(args.es)
    cfg = Config.load(args.config)
    lab = Path(args.lab)
    spread = TimeSpread(lab)

    n_scores, results = ingest_entity_scores(es, lab, cfg, spread)
    z = ingest_zeek(es, lab, spread)
    n_suri = ingest_suricata(es, lab, spread)
    n_eval = ingest_eval(es, results)
    n_ind = ingest_indicator_scores(es, lab, cfg, spread)
    es.indices.refresh(index="_all")
    print(f"c2-entity-scores: {n_scores} real hosts")
    for k, v in z.items():
        print(f"{k}: {v} records")
    print(f"suricata-alerts: {n_suri} alerts")
    print(f"c2-eval: {n_eval} metric points")
    print(f"c2-indicator-scores: {n_ind} (host x indicator)")


if __name__ == "__main__":
    main()
