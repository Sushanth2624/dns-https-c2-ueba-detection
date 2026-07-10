#!/usr/bin/env python3
"""Build rich Kibana data views + three dashboards via the saved-objects API, then export the
canonical NDJSON to dashboards/kibana/c2-dashboards.ndjson.

Dashboards:
  "C2 — Executive Overview"   CISO view: KPI tiles, detections over time, attack mix, MITRE, A/B/C
  "C2 — Threat Detail"        SOC view: per-host scores, indicator heatmap, confidence, alerts
  "C2 — Network Telemetry"    raw Zeek/Suricata: DNS/NXDOMAIN over time, SNI, JA3, signatures

Charts use the vislib (SVG) library so they render in the browser and in headless exports.
Usage: build_dashboards.py [kibana_url]
"""
import base64
import json
import os
import ssl
import sys
import urllib.request
from pathlib import Path

KBN = sys.argv[1] if len(sys.argv) > 1 else "https://localhost:5601"
_SSL = ssl._create_unverified_context()
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dashboards" / "kibana" / "c2-dashboards.ndjson"


def _pw():
    pw = os.environ.get("ELASTIC_PASSWORD")
    if not pw:
        sec = ROOT / "config" / "secrets.env"
        if sec.exists():
            for line in sec.read_text().splitlines():
                if line.startswith("ELASTIC_PASSWORD="):
                    pw = line.split("=", 1)[1].strip()
    return pw


AUTH = {}
_p = _pw()
if _p:
    AUTH = {"Authorization": "Basic " + base64.b64encode(f"elastic:{_p}".encode()).decode()}

DATA_VIEWS = {
    "c2-alerts-view": ("c2-alerts", "@timestamp"),
    "c2-scores-view": ("c2-entity-scores", "@timestamp"),
    "c2-ind-view": ("c2-indicator-scores", "@timestamp"),
    "c2-eval-view": ("c2-eval", "@timestamp"),
    "zeek-dns-view": ("zeek-dns", "@timestamp"),
    "zeek-ssl-view": ("zeek-ssl", "@timestamp"),
    "zeek-conn-view": ("zeek-conn", "@timestamp"),
    "suricata-view": ("suricata-alerts", "@timestamp"),
}

COUNT = {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}}


def api(method, path, body=None):
    req = urllib.request.Request(
        f"{KBN}{path}", data=(json.dumps(body).encode() if body is not None else None),
        headers={"kbn-xsrf": "true", "Content-Type": "application/json", **AUTH}, method=method)
    with urllib.request.urlopen(req, timeout=60, context=_SSL) as r:
        return r.status, r.read().decode()


def vis(vid, title, vis_state, dv):
    ss = {"query": {"query": "", "language": "kuery"}, "filter": [],
          "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index"}
    return {"id": vid, "type": "visualization",
            "attributes": {"title": title, "visState": json.dumps(vis_state), "uiStateJSON": "{}",
                           "description": "",
                           "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(ss)}},
            "references": [{"name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                           "type": "index-pattern", "id": dv}]}


def with_query(obj, kql):
    """Bake a KQL filter into a visualization's search source (keeps the data-view ref)."""
    ss = {"query": {"query": kql, "language": "kuery"}, "filter": [],
          "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index"}
    obj["attributes"]["kibanaSavedObjectMeta"]["searchSourceJSON"] = json.dumps(ss)
    return obj


def terms(field, size, schema, order_by="1", order="desc"):
    return {"id": "2", "enabled": True, "type": "terms", "schema": schema,
            "params": {"field": field, "size": size, "order": order, "orderBy": order_by,
                       "otherBucket": False, "missingBucket": False}}


def _axes(cat_pos="bottom"):
    val_pos = "left"
    return {
        "categoryAxes": [{"id": "CategoryAxis-1", "type": "category", "position": cat_pos,
                          "show": True, "scale": {"type": "linear"}, "labels": {"show": True,
                          "truncate": 100, "rotate": 0}, "title": {}}],
        "valueAxes": [{"id": "ValueAxis-1", "name": "LeftAxis-1", "type": "value",
                       "position": val_pos, "show": True, "scale": {"type": "linear", "mode": "normal"},
                       "labels": {"show": True}, "title": {"text": ""}}],
    }


def metric_tile(vid, title, dv, agg=None, fmt=None, color=None):
    a = agg or COUNT
    m = {"metricColorMode": "None", "labels": {"show": True}, "invertColors": False,
         "style": {"bgColor": False, "labelColor": False, "fontSize": 48}}
    return vis(vid, title, {"title": title, "type": "metric", "aggs": [a],
               "params": {"addTooltip": True, "addLegend": False, "type": "metric", "metric": m}}, dv)


ES = "https://localhost:9200"


def es_count(index, query=None):
    body = {"query": {"query_string": {"query": query}}} if query else {"query": {"match_all": {}}}
    req = urllib.request.Request(f"{ES}/{index}/_count", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Basic " + base64.b64encode(f"elastic:{_p}".encode()).decode()},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30, context=_SSL) as r:
            return json.load(r).get("count", 0)
    except Exception:
        return 0


def markdown_tile(vid, title, value, sub, color="#2dd4bf"):
    # Kibana markdown escapes raw HTML, so use pure markdown: bold label, big H1 number, italic sub.
    md = f"**{title.upper()}**\n\n# {value}\n\n_{sub}_"
    return {"id": vid, "type": "visualization",
            "attributes": {"title": title,
                "visState": json.dumps({"title": title, "type": "markdown",
                    "params": {"fontSize": 12, "openLinksInNewTab": False, "markdown": md},
                    "aggs": []}),
                "uiStateJSON": "{}", "description": "",
                "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(
                    {"query": {"query": "", "language": "kuery"}, "filter": []})}},
            "references": []}


def tsvb_metric(vid, title, index, metric_type, field=None, query=None, color="#2dd4bf"):
    """A KPI 'big number' tile as a TSVB metric (renders reliably, unlike the agg-based metric)."""
    metric = {"id": "m1", "type": metric_type}
    if field:
        metric["field"] = field
    series = {"id": "s1", "color": color, "metrics": [metric], "separate_axis": 0,
              "axis_position": "right", "formatter": "number", "chart_type": "line",
              "line_width": 1, "point_size": 1, "fill": 0.5, "stacked": "none", "label": title,
              "value_template": "{{value}}"}
    if query:
        series["filter"] = {"language": "kuery", "query": query}
    params = {"time_range_mode": "entire_time_range", "id": vid, "type": "metric",
              "series": [series], "index_pattern": index, "use_kibana_indexes": False,
              "time_field": "@timestamp", "interval": "", "axis_position": "left",
              "background_color_rules": [{"id": "bcr"}], "bar_color_rules": [{"id": "bar"}],
              "tooltip_mode": "show_all", "drop_last_bucket": 0}
    return {"id": vid, "type": "visualization",
            "attributes": {"title": title, "visState": json.dumps(
                {"title": title, "type": "metrics", "aggs": [], "params": params}),
                "uiStateJSON": "{}", "description": "",
                "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(
                    {"query": {"query": "", "language": "kuery"}, "filter": []})}},
            "references": []}


def timeseries(vid, title, dv, ctype="area", split=None, interval="h", metric=None):
    agg = metric or COUNT
    aggs = [agg, {"id": "2", "enabled": True, "type": "date_histogram", "schema": "segment",
                  "params": {"field": "@timestamp", "useNormalizedEsInterval": True,
                             "interval": interval, "drop_partials": False, "min_doc_count": 1}}]
    if split:
        aggs.append(terms(split, 5, "group"))
    p = {"type": ctype, "grid": {"categoryLines": False}, "addTooltip": True, "addLegend": bool(split),
         "legendPosition": "bottom", "times": [], "addTimeMarker": False, "labels": {},
         "thresholdLine": {"show": False},
         "seriesParams": [{"show": True, "type": ctype, "mode": "stacked" if ctype == "area" else "normal",
                           "data": {"label": "Count", "id": agg["id"]}, "drawLinesBetweenPoints": True,
                           "lineWidth": 2, "showCircles": True, "interpolate": "linear",
                           "valueAxis": "ValueAxis-1"}]}
    p.update(_axes())
    return vis(vid, title, {"title": title, "type": ctype, "aggs": aggs, "params": p}, dv)


def bars(vid, title, dv, field, size=10, horizontal=False, metric=None, split=None):
    ctype = "horizontal_bar" if horizontal else "histogram"
    agg = metric or COUNT
    aggs = [agg, terms(field, size, "segment", order_by=agg["id"])]
    if split:
        aggs.append(terms(split, 5, "group"))
    p = {"type": "histogram", "grid": {"categoryLines": False}, "addTooltip": True,
         "addLegend": bool(split), "legendPosition": "right", "labels": {"show": False},
         "seriesParams": [{"show": True, "type": "histogram",
                           "mode": "stacked" if split else "normal",
                           "data": {"label": "value", "id": agg["id"]}, "valueAxis": "ValueAxis-1",
                           "drawLinesBetweenPoints": False, "showCircles": True}]}
    p.update(_axes(cat_pos="left" if horizontal else "bottom"))
    if horizontal:
        p["categoryAxes"][0]["position"] = "left"
        p["valueAxes"][0]["position"] = "bottom"
    return vis(vid, title, {"title": title, "type": ctype, "aggs": aggs, "params": p}, dv)


def donut(vid, title, dv, field, size=6):
    return vis(vid, title, {"title": title, "type": "pie",
               "aggs": [COUNT, terms(field, size, "segment")],
               "params": {"type": "pie", "addTooltip": True, "addLegend": True,
                          "legendPosition": "right", "isDonut": True, "labels": {"show": True,
                          "values": True, "last_level": True, "truncate": 100}}}, dv)


def heatmap(vid, title, dv, x_field, y_field, metric):
    return vis(vid, title, {"title": title, "type": "heatmap",
               "aggs": [metric, terms(x_field, 12, "group", order="asc"),
                        terms(y_field, 20, "segment", order="asc")],
               "params": {"type": "heatmap", "addTooltip": True, "addLegend": True,
                          "enableHover": True, "legendPosition": "right", "colorsNumber": 5,
                          "colorSchema": "Yellow to Red", "setColorRange": False,
                          "valueAxes": [{"show": False, "id": "ValueAxis-1", "type": "value",
                                         "scale": {"type": "linear"}, "labels": {"show": False}}]}}, dv)


def table(vid, title, dv, aggs, per_page=15):
    return vis(vid, title, {"title": title, "type": "table", "aggs": aggs,
               "params": {"perPage": per_page, "showTotal": False, "showToolbar": True}}, dv)


MAX = lambda f: {"id": "1", "enabled": True, "type": "max", "schema": "metric", "params": {"field": f}}
AVG = lambda f: {"id": "1", "enabled": True, "type": "avg", "schema": "metric", "params": {"field": f}}
UNIQ = lambda f: {"id": "1", "enabled": True, "type": "cardinality", "schema": "metric",
                  "params": {"field": f}}

objects = []
for dv_id, (title, tf) in DATA_VIEWS.items():
    objects.append({"id": dv_id, "type": "index-pattern",
                    "attributes": {"title": title, "timeFieldName": tf}, "references": []})

# ===== Dashboard 1: Executive Overview =====
objects += [
    markdown_tile("kpi-hosts", "Hosts monitored", es_count("c2-entity-scores"),
                  "endpoints on the lab network", "#3b82f6"),
    markdown_tile("kpi-threats", "Threats detected",
                  es_count("c2-entity-scores", "verdict:flagged"), "flagged as C2", "#ef4444"),
    markdown_tile("kpi-fp", "False positives",
                  es_count("c2-entity-scores", "label:benign AND verdict:flagged"),
                  "benign hosts flagged", "#22c55e"),
    markdown_tile("kpi-alerts", "Explainable alerts", es_count("c2-alerts"),
                  "with MITRE + evidence", "#f59e0b"),
    donut("exec-mix", "Benign vs attack hosts", "c2-scores-view", "label", 3),
    bars("exec-attacktype", "Attack techniques observed", "c2-scores-view", "attack_type", 6),
    timeseries("exec-timeline", "Network activity over 24h (benign vs attack)", "zeek-dns-view",
               "area", split="label", interval="h"),
    bars("exec-mitre", "MITRE ATT&CK techniques", "c2-alerts-view", "mitre", 12, horizontal=True),
    with_query(bars("exec-abc", "Detection quality — F1 score (A vs B vs C, higher = better)",
                    "c2-eval-view", "config_label", 3, metric=AVG("value")), "metric : f1"),
    table("exec-top", "Highest-risk hosts", "c2-scores-view",
          [MAX("confidence"),
           {"id": "2", "type": "terms", "schema": "bucket", "enabled": True,
            "params": {"field": "entity", "size": 15, "order": "desc", "orderBy": "1"}},
           {"id": "3", "type": "terms", "schema": "bucket", "enabled": True,
            "params": {"field": "attack_type", "size": 1, "order": "desc", "orderBy": "1"}}]),
]
# ===== Dashboard 2: Threat Detail =====
objects += [
    heatmap("td-heatmap", "Indicator sub-scores per host (hot = fired)", "c2-ind-view",
            "indicator", "entity", AVG("subscore")),
    bars("td-conf", "Confidence by host", "c2-scores-view", "entity", 15, horizontal=True,
         metric=MAX("confidence")),
    table("td-scores", "Per-host scores (verdict / confidence / UEBA)", "c2-scores-view",
          [MAX("confidence"), AVG("ueba_anomaly"),
           {"id": "2", "type": "terms", "schema": "bucket", "enabled": True,
            "params": {"field": "entity", "size": 20, "order": "desc", "orderBy": "1"}},
           {"id": "4", "type": "terms", "schema": "bucket", "enabled": True,
            "params": {"field": "label", "size": 3, "order": "desc", "orderBy": "1"}},
           {"id": "5", "type": "terms", "schema": "bucket", "enabled": True,
            "params": {"field": "verdict", "size": 3, "order": "desc", "orderBy": "1"}}]),
    donut("td-severity", "Alerts by severity", "c2-alerts-view", "severity", 4),
    bars("td-verdict", "Alerts by verdict", "c2-alerts-view", "verdict", 4),
]

# ===== Dashboard 3: Network Telemetry =====
objects += [
    timeseries("nt-dns", "DNS queries over 24h (benign vs attack)", "zeek-dns-view", "area",
               split="label", interval="h"),
    donut("nt-rcode", "DNS response codes (NXDOMAIN = DGA/tunnel)", "zeek-dns-view", "rcode_name", 6),
    bars("nt-nx", "NXDOMAIN volume by host", "zeek-dns-view", "entity", 12, horizontal=True),
    bars("nt-sni", "Top TLS SNI (server names)", "zeek-ssl-view", "server_name", 12, horizontal=True),
    bars("nt-ja3", "TLS client fingerprints (JA3)", "zeek-ssl-view", "ja3", 10, horizontal=True),
    bars("nt-suri-sig", "Suricata signature hits (Config A)", "suricata-view", "signature", 8,
         horizontal=True),
    timeseries("nt-suri-time", "Suricata alerts over 24h", "suricata-view", "line", interval="h"),
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
                           "version": 1, "timeRestore": True, "timeFrom": "now-30h",
                           "timeTo": "now+1h",
                           "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(
                               {"query": {"query": "", "language": "kuery"}, "filter": []})}},
            "references": refs}


objects.append(dashboard("c2-exec", "C2 — Executive Overview",
    "CISO view: coverage, threats, attack mix, MITRE ATT&CK, and A/B/C detection quality.", [
        ("kpi-hosts", 0, 0, 8, 7), ("kpi-threats", 8, 0, 8, 7),
        ("kpi-fp", 16, 0, 8, 7), ("kpi-alerts", 24, 0, 8, 7),
        ("exec-mix", 32, 0, 16, 14),
        ("exec-timeline", 0, 7, 32, 13),
        ("exec-attacktype", 0, 20, 16, 13), ("exec-mitre", 16, 20, 16, 13),
        ("exec-abc", 32, 14, 16, 12),
        ("exec-top", 0, 33, 48, 12)]))

objects.append(dashboard("c2-threat", "C2 — Threat Detail",
    "SOC view: which indicators fired per host, confidence, and explainable alerts.", [
        ("td-heatmap", 0, 0, 32, 16), ("td-conf", 32, 0, 16, 16),
        ("td-scores", 0, 16, 48, 14),
        ("td-severity", 0, 30, 16, 12), ("td-verdict", 16, 30, 16, 12)]))

objects.append(dashboard("c2-telemetry", "C2 — Network Telemetry",
    "Raw Zeek + Suricata: DNS/NXDOMAIN over time, SNI, JA3 fingerprints, signature hits.", [
        ("nt-dns", 0, 0, 32, 13), ("nt-rcode", 32, 0, 16, 13),
        ("nt-nx", 0, 13, 24, 14), ("nt-sni", 24, 13, 24, 14),
        ("nt-ja3", 0, 27, 24, 13), ("nt-suri-sig", 24, 27, 24, 13),
        ("nt-suri-time", 0, 40, 48, 12)]))

ndjson = "\n".join(json.dumps(o) for o in objects) + "\n"


def import_ndjson(text):
    b = "----c2labBOUNDARY7e3f"
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"c2.ndjson\"\r\n"
            f"Content-Type: application/x-ndjson\r\n\r\n{text}\r\n--{b}--\r\n").encode()
    req = urllib.request.Request(f"{KBN}/api/saved_objects/_import?overwrite=true", data=body,
        headers={"kbn-xsrf": "true", "Content-Type": f"multipart/form-data; boundary={b}", **AUTH},
        method="POST")
    with urllib.request.urlopen(req, timeout=120, context=_SSL) as r:
        return r.status, r.read().decode()


def export_dashboards():
    _, resp = api("POST", "/api/saved_objects/_export",
                  body={"objects": [{"type": "dashboard", "id": d} for d in
                                    ("c2-exec", "c2-threat", "c2-telemetry")],
                        "includeReferencesDeep": True})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [l for l in resp.splitlines() if l.strip() and '"exportedCount"' not in l]
    OUT.write_text("\n".join(lines) + "\n")
    return len(lines)


status, resp = import_ndjson(ndjson)
summary = json.loads(resp)
print("import status", status, "success", summary.get("success"), "count", summary.get("successCount"))
if summary.get("errors"):
    print("errors:", json.dumps(summary["errors"], indent=2)[:2500])
n = export_dashboards()
print(f"exported {n} objects to {OUT}")
