#!/usr/bin/env python3
"""Ingest the full lab dataset into Elasticsearch so every stage is explorable in Kibana:

  c2-alerts         explainable alerts (written by the pipeline `run`)
  c2-entity-scores  per-entity scores for ALL entities (benign + attack) — shows the separation
  zeek-dns / zeek-ssl / zeek-conn   raw Zeek telemetry (tagged with entity + ground-truth label)
  suricata-alerts   Suricata rule hits per scenario (Config A signal)

Usage: ingest_es.py [--corpus data/eval/corpus] [--captures data/captures] [--es http://localhost:9200]
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from elasticsearch import Elasticsearch, helpers

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from c2detect.config import Config
from c2detect import pipeline
from c2detect.parsers import zeek as zeek_parser
from c2detect.parsers import suricata as suri_parser


def recreate(es, index, mapping):
    es.indices.delete(index=index, ignore_unavailable=True)
    es.indices.create(index=index, mappings=mapping)


def _iso(ts):
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
    except (TypeError, ValueError):
        return datetime.now(timezone.utc).isoformat()


def ingest_entity_scores(es, corpus_dir, cfg):
    gt = json.loads((corpus_dir / "ground_truth.json").read_text())
    ccfg = Config(raw={**cfg.raw, "paths": {"zeek_log_dir": str(corpus_dir),
                 "ja3_baseline": str(corpus_dir / "ja3_baseline.txt")}})
    feats = pipeline.build_feature_vectors(ccfg)
    from c2detect.eval.evaluate import _train_ueba
    from c2detect.correlation.engine import correlate
    weight_keys = list(cfg.weights.keys())
    ueba = _train_ueba(feats, gt, weight_keys, 0.05, None)
    min_conf = float(cfg.thresholds.get("alert_confidence_min", 0.6))

    recreate(es, "c2-entity-scores", {"properties": {
        "@timestamp": {"type": "date"}, "entity": {"type": "keyword"},
        "label": {"type": "keyword"}, "attack_type": {"type": "keyword"},
        "verdict": {"type": "keyword"}, "confidence": {"type": "float"},
        "ueba_anomaly": {"type": "float"}, "subscores": {"type": "object"}}})
    now = datetime.now(timezone.utc).isoformat()
    docs = []
    for e, fv in feats.items():
        rec = ueba.score(e, fv)
        corr = correlate(e, rec.anomaly_score, fv, cfg.weights, cfg.ueba_weight)
        g = gt.get(e, {})
        docs.append({"_index": "c2-entity-scores", "_id": e, "_source": {
            "@timestamp": now, "entity": e,
            "label": "attack" if g.get("label") == 1 else "benign",
            "attack_type": g.get("attack_type"),
            "verdict": "flagged" if corr.confidence >= min_conf else "clear",
            "confidence": round(corr.confidence, 3),
            "ueba_anomaly": round(rec.anomaly_score, 3),
            "subscores": {k: round(v, 3) for k, v in fv.items()}}})
    helpers.bulk(es, docs)
    return len(docs)


def ingest_zeek(es, corpus_dir):
    gt = json.loads((corpus_dir / "ground_truth.json").read_text())
    label_of = {e: ("attack" if g["label"] == 1 else "benign") for e, g in gt.items()}
    total = {}
    for kind in ("dns", "ssl", "conn"):
        idx = f"zeek-{kind}"
        recreate(es, idx, {"properties": {"@timestamp": {"type": "date"},
                 "entity": {"type": "keyword"}, "label": {"type": "keyword"},
                 "query": {"type": "keyword"}, "server_name": {"type": "keyword"},
                 "ja3": {"type": "keyword"}, "rcode_name": {"type": "keyword"},
                 "id.resp_h": {"type": "keyword"}}})
        p = corpus_dir / f"{kind}.log"
        if not p.exists():
            continue
        docs = []
        for r in zeek_parser.read_log(p):
            ent = r.get("id.orig_h")
            docs.append({"_index": idx, "_source": {**r, "@timestamp": _iso(r.get("ts")),
                         "entity": ent, "label": label_of.get(ent, "benign")}})
        if docs:
            helpers.bulk(es, docs, raise_on_error=False)
        total[idx] = len(docs)
    return total


def ingest_suricata(es, captures_dir):
    recreate(es, "suricata-alerts", {"properties": {"@timestamp": {"type": "date"},
             "scenario": {"type": "keyword"}, "signature": {"type": "keyword"},
             "src_ip": {"type": "keyword"}, "dest_ip": {"type": "keyword"},
             "category": {"type": "keyword"}}})
    docs = []
    for cap in sorted(captures_dir.glob("*/eve.json")):
        scenario = cap.parent.name
        for ev in suri_parser.read_eve(cap, "alert"):
            a = ev.get("alert", {})
            docs.append({"_index": "suricata-alerts", "_source": {
                "@timestamp": ev.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "scenario": scenario, "signature": a.get("signature"),
                "category": a.get("category"), "src_ip": ev.get("src_ip"),
                "dest_ip": ev.get("dest_ip")}})
    if docs:
        helpers.bulk(es, docs, raise_on_error=False)
    return len(docs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="data/eval/corpus")
    ap.add_argument("--captures", default="data/captures")
    ap.add_argument("--config", default="config/config.yaml")
    ap.add_argument("--es", default="http://localhost:9200")
    args = ap.parse_args()

    es = Elasticsearch(args.es)
    cfg = Config.load(args.config)
    corpus = Path(args.corpus)
    captures = Path(args.captures)

    n_scores = ingest_entity_scores(es, corpus, cfg)
    z = ingest_zeek(es, corpus)
    n_suri = ingest_suricata(es, captures)
    es.indices.refresh(index="_all")
    print(f"c2-entity-scores: {n_scores} entities")
    for k, v in z.items():
        print(f"{k}: {v} records")
    print(f"suricata-alerts: {n_suri} alerts")


if __name__ == "__main__":
    main()
