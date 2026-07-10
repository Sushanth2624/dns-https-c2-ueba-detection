#!/usr/bin/env python3
"""Create Kibana data views + two dashboards via the saved-objects API, then export the canonical
NDJSON to dashboards/kibana/c2-dashboards.ndjson (the committed deliverable).

Dashboards:
  "DNS/HTTPS C2 — Behavioral Detection"  alerts: severity, verdict, MITRE, top entities
  "C2 — Telemetry & Scores"              entity scores (benign vs attack), Suricata, raw Zeek

Usage: build_dashboards.py [kibana_url]
"""
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

KBN = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5601"


def _kbn_auth_header():
    """Basic auth for Kibana when ES security is on (elastic:<ELASTIC_PASSWORD>)."""
    pw = os.environ.get("ELASTIC_PASSWORD")
    if not pw:
        sec = Path(__file__).resolve().parent.parent / "config" / "secrets.env"
        if sec.exists():
            for line in sec.read_text().splitlines():
                if line.startswith("ELASTIC_PASSWORD="):
                    pw = line.split("=", 1)[1].strip()
                    break
    if not pw:
        return {}
    tok = base64.b64encode(f"elastic:{pw}".encode()).decode()
    return {"Authorization": f"Basic {tok}"}


AUTH = _kbn_auth_header()
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dashboards" / "kibana" / "c2-dashboards.ndjson"

# data views: id -> (index title, time field)
DATA_VIEWS = {
    "c2-alerts-view": ("c2-alerts", "@timestamp"),
    "c2-scores-view": ("c2-entity-scores", "@timestamp"),
    "zeek-dns-view": ("zeek-dns", "@timestamp"),
    "zeek-ssl-view": ("zeek-ssl", "@timestamp"),
    "zeek-conn-view": ("zeek-conn", "@timestamp"),
    "suricata-view": ("suricata-alerts", "@timestamp"),
}

count_metric = {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}}


def api(method, path, body=None):
    req = urllib.request.Request(
        f"{KBN}{path}", data=(json.dumps(body).encode() if body is not None else None),
        headers={"kbn-xsrf": "true", "Content-Type": "application/json", **AUTH}, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read().decode()


def vis(vid, title, vis_state, dv):
    # NOTE: legacy visualizations link their data view via `indexRefName` inside searchSourceJSON,
    # which maps to the references[] entry of the same name. Without it Kibana can't load the index
    # pattern ("[esaggs] > [indexPatternLoad] requires the 'id' argument") and the panel is empty.
    search_source = {"query": {"query": "", "language": "kuery"}, "filter": [],
                     "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index"}
    return {"id": vid, "type": "visualization",
            "attributes": {"title": title, "visState": json.dumps(vis_state),
                           "uiStateJSON": "{}", "description": "",
                           "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(search_source)}},
            "references": [{"name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                           "type": "index-pattern", "id": dv}]}


def terms_agg(field, size=10, schema="segment"):
    return {"id": "2", "enabled": True, "type": "terms", "schema": schema,
            "params": {"field": field, "size": size, "order": "desc", "orderBy": "1"}}


def bar(vid, title, dv, field, size=10, horizontal=False, metric=None):
    # Rendered as a data table (DOM) rather than an elastic-charts bar (canvas) so it displays
    # reliably in every browser and in headless exports, and shows exact counts for the viva.
    m = metric or count_metric
    return vis(vid, title, {"title": title, "type": "table",
               "aggs": [m, {"id": "2", "enabled": True, "type": "terms", "schema": "bucket",
                            "params": {"field": field, "size": size,
                                       "order": "desc", "orderBy": m["id"]}}],
               "params": {"perPage": min(size, 12), "showTotal": True,
                          "showToolbar": True, "totalFunc": "sum"}}, dv)


def pie(vid, title, dv, field, size=6):
    return vis(vid, title, {"title": title, "type": "pie",
               "aggs": [count_metric, terms_agg(field, size)],
               "params": {"isDonut": True, "legendPosition": "right"}}, dv)


def metric_vis(vid, title, dv):
    # Total count as a 1-row data table (DOM) — renders reliably everywhere.
    return vis(vid, title, {"title": title, "type": "table", "aggs": [count_metric],
               "params": {"perPage": 5, "showTotal": False, "showToolbar": False}}, dv)


def table(vid, title, dv, aggs, per_page=10):
    return vis(vid, title, {"title": title, "type": "table", "aggs": aggs,
               "params": {"perPage": per_page, "showTotal": False}}, dv)


objects = []
for dv_id, (title, tf) in DATA_VIEWS.items():
    objects.append({"id": dv_id, "type": "index-pattern",
                    "attributes": {"title": title, "timeFieldName": tf}, "references": []})

# ---- Dashboard 1: alerts ----
objects += [
    metric_vis("c2-metric-total", "C2 — total alerts", "c2-alerts-view"),
    pie("c2-pie-severity", "C2 — alerts by severity", "c2-alerts-view", "severity", 5),
    bar("c2-bar-verdict", "C2 — alerts by verdict", "c2-alerts-view", "verdict", 5),
    bar("c2-bar-mitre", "C2 — MITRE ATT&CK techniques", "c2-alerts-view", "mitre", 15, horizontal=True),
    table("c2-table-entities", "C2 — top entities by confidence", "c2-alerts-view",
          [{"id": "1", "enabled": True, "type": "max", "schema": "metric",
            "params": {"field": "confidence"}},
           {"id": "2", "enabled": True, "type": "terms", "schema": "bucket",
            "params": {"field": "entity", "size": 20, "order": "desc", "orderBy": "1"}}]),
]

# ---- Dashboard 2: telemetry & scores ----
max_conf = {"id": "1", "enabled": True, "type": "max", "schema": "metric",
            "params": {"field": "confidence"}}
avg_ueba = {"id": "3", "enabled": True, "type": "avg", "schema": "metric",
            "params": {"field": "ueba_anomaly"}}
objects += [
    bar("sc-bar-conf", "Confidence by entity (benign vs attack)", "c2-scores-view",
        "entity", 20, metric=max_conf),
    pie("sc-pie-label", "Entities: benign vs attack", "c2-scores-view", "label", 3),
    table("sc-table", "Entity scores (verdict / confidence / UEBA)", "c2-scores-view",
          [max_conf, avg_ueba,
           {"id": "2", "enabled": True, "type": "terms", "schema": "bucket",
            "params": {"field": "entity", "size": 20, "order": "desc", "orderBy": "1"}},
           {"id": "4", "enabled": True, "type": "terms", "schema": "bucket",
            "params": {"field": "label", "size": 3, "order": "desc", "orderBy": "1"}},
           {"id": "5", "enabled": True, "type": "terms", "schema": "bucket",
            "params": {"field": "verdict", "size": 3, "order": "desc", "orderBy": "1"}}]),
    bar("suri-bar-sig", "Suricata alerts by signature (Config A)", "suricata-view",
        "signature", 10, horizontal=True),
    bar("suri-bar-scn", "Suricata alerts by scenario", "suricata-view", "scenario", 6),
    bar("zeek-dns-rcode", "Zeek DNS by response code", "zeek-dns-view", "rcode_name", 8),
    bar("zeek-ssl-sni", "Zeek TLS top SNI", "zeek-ssl-view", "server_name", 12, horizontal=True),
    bar("zeek-ssl-ja3", "Zeek TLS top JA3 fingerprints", "zeek-ssl-view", "ja3", 10, horizontal=True),
]


def dashboard(did, title, desc, layout):
    panels, refs = [], []
    for i, (vid, x, y, w, h) in enumerate(layout, start=1):
        pref = f"panel_{i}"
        panels.append({"version": "8.19.0", "type": "visualization",
                       "gridData": {"x": x, "y": y, "w": w, "h": h, "i": str(i)},
                       "panelIndex": str(i), "embeddableConfig": {}, "panelRefName": pref})
        refs.append({"name": pref, "type": "visualization", "id": vid})
    return {"id": did, "type": "dashboard",
            "attributes": {"title": title, "hits": 0, "description": desc,
                           "panelsJSON": json.dumps(panels),
                           "optionsJSON": json.dumps({"useMargins": True, "hidePanelTitles": False}),
                           "version": 1, "timeRestore": True,
                           "timeFrom": "now-1y", "timeTo": "now+1y",
                           "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(
                               {"query": {"query": "", "language": "kuery"}, "filter": []})}},
            "references": refs}


objects.append(dashboard("c2-dashboard", "DNS/HTTPS C2 — Behavioral Detection",
    "Explainable C2 alerts: severity, verdict, MITRE, top entities.", [
        ("c2-metric-total", 0, 0, 12, 8), ("c2-pie-severity", 12, 0, 12, 8),
        ("c2-bar-verdict", 24, 0, 24, 8), ("c2-bar-mitre", 0, 8, 24, 15),
        ("c2-table-entities", 24, 8, 24, 15)]))

objects.append(dashboard("c2-telemetry-dashboard", "C2 — Telemetry & Scores",
    "Per-entity scores (benign vs attack), Suricata signature hits, raw Zeek telemetry.", [
        ("sc-bar-conf", 0, 0, 32, 12), ("sc-pie-label", 32, 0, 16, 12),
        ("sc-table", 0, 12, 48, 12),
        ("suri-bar-sig", 0, 24, 24, 12), ("suri-bar-scn", 24, 24, 24, 12),
        ("zeek-dns-rcode", 0, 36, 16, 12), ("zeek-ssl-sni", 16, 36, 16, 12),
        ("zeek-ssl-ja3", 32, 36, 16, 12)]))

ndjson = "\n".join(json.dumps(o) for o in objects) + "\n"


def import_ndjson(text):
    boundary = "----c2labBOUNDARY7e3f"
    body = (f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="c2.ndjson"\r\n'
            f"Content-Type: application/x-ndjson\r\n\r\n{text}\r\n--{boundary}--\r\n").encode()
    req = urllib.request.Request(f"{KBN}/api/saved_objects/_import?overwrite=true", data=body,
        headers={"kbn-xsrf": "true",
                 "Content-Type": f"multipart/form-data; boundary={boundary}", **AUTH}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.status, r.read().decode()


def export_dashboards():
    status, resp = api("POST", "/api/saved_objects/_export",
                       body={"objects": [{"type": "dashboard", "id": "c2-dashboard"},
                                         {"type": "dashboard", "id": "c2-telemetry-dashboard"}],
                             "includeReferencesDeep": True})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [l for l in resp.splitlines() if l.strip() and '"exportedCount"' not in l]
    OUT.write_text("\n".join(lines) + "\n")
    return status, len(lines)


status, resp = import_ndjson(ndjson)
summary = json.loads(resp)
print("import status", status, "success", summary.get("success"), "count", summary.get("successCount"))
if summary.get("errors"):
    print("errors:", json.dumps(summary["errors"], indent=2)[:2000])
est, n = export_dashboards()
print(f"export status {est}: wrote {n} objects to {OUT}")
