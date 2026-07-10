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
from datetime import datetime, timezone
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


def _iso(ts):
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
    except (TypeError, ValueError):
        return datetime.now(timezone.utc).isoformat()


def ingest_entity_scores(es, lab_dir, cfg):
    results = evaluate_lab(lab_dir, cfg, model_path=cfg.get(
        "ueba", "baseline", "model_path", default="models/isoforest.joblib"))
    recreate(es, "c2-entity-scores", {"properties": {
        "@timestamp": {"type": "date"}, "entity": {"type": "keyword"},
        "label": {"type": "keyword"}, "attack_type": {"type": "keyword"},
        "verdict": {"type": "keyword"}, "confidence": {"type": "float"},
        "ueba_anomaly": {"type": "float"}}})
    now = datetime.now(timezone.utc).isoformat()
    docs = []
    gt = results["ground_truth"]
    for e in gt:
        docs.append({"_index": "c2-entity-scores", "_id": e, "_source": {
            "@timestamp": now, "entity": e,
            "label": "attack" if gt[e] == 1 else "benign",
            "attack_type": results["attack_type"].get(e),
            "verdict": "flagged" if results["C_predictions"][e] == 1 else "clear",
            "confidence": results["C_confidence"][e],
            "ueba_anomaly": results["ueba_anomaly"][e]}})
    helpers.bulk(es, docs)
    return len(docs), results


def ingest_zeek(es, lab_dir):
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
            docs.append({"_index": idx, "_source": {**r, "@timestamp": _iso(r.get("ts")),
                         "entity": ent, "label": label_of.get(ent, "other"),
                         "role": role_of.get(ent, "other")}})
        if docs:
            helpers.bulk(es, docs, raise_on_error=False)
        total[idx] = len(docs)
    return total


def ingest_suricata(es, lab_dir):
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
                "@timestamp": ev.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "signature": a.get("signature"), "category": a.get("category"),
                "src_ip": src, "entity": src, "scenario": role_of.get(src, "other"),
                "dest_ip": ev.get("dest_ip")}})
    if docs:
        helpers.bulk(es, docs, raise_on_error=False)
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

    n_scores, _ = ingest_entity_scores(es, lab, cfg)
    z = ingest_zeek(es, lab)
    n_suri = ingest_suricata(es, lab)
    es.indices.refresh(index="_all")
    print(f"c2-entity-scores: {n_scores} real hosts")
    for k, v in z.items():
        print(f"{k}: {v} records")
    print(f"suricata-alerts: {n_suri} alerts")


if __name__ == "__main__":
    main()
