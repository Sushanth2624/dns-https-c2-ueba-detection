#!/usr/bin/env python3
"""Create the Kibana data view + C2 detection dashboard via the saved-objects API, then export
the canonical NDJSON to dashboards/kibana/c2-dashboards.ndjson (the committed deliverable).

Usage: build_dashboards.py [kibana_url]
"""
import json
import sys
import urllib.request
from pathlib import Path

KBN = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5601"
DV_ID = "c2-alerts-view"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dashboards" / "kibana" / "c2-dashboards.ndjson"


def api(method, path, body=None, ndjson=False):
    url = f"{KBN}{path}"
    headers = {"kbn-xsrf": "true"}
    data = None
    if ndjson:
        headers["Content-Type"] = "application/x-ndjson"
        data = body.encode()
    elif body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read().decode()


def vis(vid, title, vis_state):
    return {
        "id": vid, "type": "visualization",
        "attributes": {
            "title": title,
            "visState": json.dumps(vis_state),
            "uiStateJSON": "{}",
            "description": "",
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({"query": {"query": "", "language": "kuery"},
                                                "filter": []})},
        },
        "references": [{"name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                        "type": "index-pattern", "id": DV_ID}],
    }


def terms(field, size=10):
    return {"id": "2", "enabled": True, "type": "terms", "schema": "segment" if True else "bucket",
            "params": {"field": field, "size": size, "order": "desc", "orderBy": "1",
                       "otherBucket": False, "missingBucket": False}}


count_metric = {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}}

objects = []

# 1. data view
objects.append({
    "id": DV_ID, "type": "index-pattern",
    "attributes": {"title": "c2-alerts", "timeFieldName": "@timestamp"},
    "references": [],
})

# 2. metric — total alerts
objects.append(vis("c2-metric-total", "C2 — total alerts",
                   {"title": "C2 — total alerts", "type": "metric",
                    "aggs": [count_metric],
                    "params": {"metric": {"colorSchema": "Green to Red",
                                          "labels": {"show": True}}}}))

# 3. pie — by severity
objects.append(vis("c2-pie-severity", "C2 — alerts by severity",
                   {"title": "C2 — alerts by severity", "type": "pie",
                    "aggs": [count_metric,
                             {"id": "2", "enabled": True, "type": "terms", "schema": "segment",
                              "params": {"field": "severity", "size": 5, "order": "desc",
                                         "orderBy": "1"}}],
                    "params": {"isDonut": True, "legendPosition": "right"}}))

# 4. vertical bar — by verdict
objects.append(vis("c2-bar-verdict", "C2 — alerts by verdict",
                   {"title": "C2 — alerts by verdict", "type": "histogram",
                    "aggs": [count_metric,
                             {"id": "2", "enabled": True, "type": "terms", "schema": "segment",
                              "params": {"field": "verdict", "size": 5, "order": "desc",
                                         "orderBy": "1"}}],
                    "params": {"addLegend": True, "addTooltip": True,
                               "categoryAxes": [{"id": "CategoryAxis-1", "type": "category",
                                                 "position": "bottom", "show": True,
                                                 "scale": {"type": "linear"}}],
                               "valueAxes": [{"id": "ValueAxis-1", "position": "left",
                                              "show": True, "scale": {"type": "linear"},
                                              "type": "value"}],
                               "seriesParams": [{"data": {"id": "1", "label": "Count"},
                                                 "type": "histogram", "mode": "normal",
                                                 "valueAxis": "ValueAxis-1", "show": True}]}}))

# 5. horizontal bar — MITRE technique frequency
objects.append(vis("c2-bar-mitre", "C2 — MITRE ATT&CK techniques",
                   {"title": "C2 — MITRE ATT&CK techniques", "type": "horizontal_bar",
                    "aggs": [count_metric,
                             {"id": "2", "enabled": True, "type": "terms", "schema": "segment",
                              "params": {"field": "mitre", "size": 15, "order": "desc",
                                         "orderBy": "1"}}],
                    "params": {"addLegend": False, "addTooltip": True,
                               "categoryAxes": [{"id": "CategoryAxis-1", "type": "category",
                                                 "position": "left", "show": True,
                                                 "scale": {"type": "linear"}}],
                               "valueAxes": [{"id": "ValueAxis-1", "position": "bottom",
                                              "show": True, "scale": {"type": "linear"},
                                              "type": "value"}],
                               "seriesParams": [{"data": {"id": "1", "label": "Count"},
                                                 "type": "histogram", "mode": "normal",
                                                 "valueAxis": "ValueAxis-1", "show": True}]}}))

# 6. data table — entities by max confidence
objects.append(vis("c2-table-entities", "C2 — top entities by confidence",
                   {"title": "C2 — top entities by confidence", "type": "table",
                    "aggs": [{"id": "1", "enabled": True, "type": "max", "schema": "metric",
                              "params": {"field": "confidence"}},
                             {"id": "2", "enabled": True, "type": "terms", "schema": "bucket",
                              "params": {"field": "entity", "size": 20, "order": "desc",
                                         "orderBy": "1"}}],
                    "params": {"perPage": 10, "showTotal": False}}))

# 7. dashboard
panels = []
refs = []
layout = [
    ("c2-metric-total", 0, 0, 12, 8),
    ("c2-pie-severity", 12, 0, 12, 8),
    ("c2-bar-verdict", 24, 0, 24, 8),
    ("c2-bar-mitre", 0, 8, 24, 15),
    ("c2-table-entities", 24, 8, 24, 15),
]
for i, (vid, x, y, w, h) in enumerate(layout, start=1):
    pref = f"panel_{i}"
    panels.append({"version": "8.19.0", "type": "visualization",
                   "gridData": {"x": x, "y": y, "w": w, "h": h, "i": str(i)},
                   "panelIndex": str(i), "embeddableConfig": {}, "panelRefName": pref})
    refs.append({"name": pref, "type": "visualization", "id": vid})

objects.append({
    "id": "c2-dashboard", "type": "dashboard",
    "attributes": {
        "title": "DNS/HTTPS C2 — Behavioral Detection",
        "hits": 0, "description": "Explainable C2 alerts: severity, verdict, MITRE, top entities.",
        "panelsJSON": json.dumps(panels),
        "optionsJSON": json.dumps({"useMargins": True, "hidePanelTitles": False}),
        "version": 1,
        "timeRestore": True, "timeFrom": "now-7d", "timeTo": "now",
        "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps({"query": {"query": "",
                                  "language": "kuery"}, "filter": []})},
    },
    "references": refs,
})

ndjson = "\n".join(json.dumps(o) for o in objects) + "\n"


def import_ndjson(text):
    boundary = "----c2labBOUNDARY7e3f"
    body = (f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="c2.ndjson"\r\n'
            f"Content-Type: application/x-ndjson\r\n\r\n"
            f"{text}\r\n--{boundary}--\r\n").encode()
    req = urllib.request.Request(
        f"{KBN}/api/saved_objects/_import?overwrite=true", data=body,
        headers={"kbn-xsrf": "true",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read().decode()


def export_dashboard():
    status, resp = api("POST", "/api/saved_objects/_export",
                       body={"objects": [{"type": "dashboard", "id": "c2-dashboard"}],
                             "includeReferencesDeep": True})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # export returns NDJSON (last line is an export summary); keep object lines only
    lines = [l for l in resp.splitlines() if l.strip() and '"exportedCount"' not in l]
    OUT.write_text("\n".join(lines) + "\n")
    return status, len(lines)


status, resp = import_ndjson(ndjson)
summary = json.loads(resp)
print("import status", status, "success", summary.get("success"),
      "count", summary.get("successCount"))
if summary.get("errors"):
    print("errors:", json.dumps(summary["errors"], indent=2)[:1500])

est, n = export_dashboard()
print(f"export status {est}: wrote {n} objects to {OUT}")


if __name__ == "__main__":
    pass
