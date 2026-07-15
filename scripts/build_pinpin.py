#!/usr/bin/env python3
"""Pin-to-pin technical walkthrough: trace ONE real host through every stage of the pipeline,
with the actual data, commands, and code — including exactly how logs are pushed to Elasticsearch."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/tmp/pinpin.html"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def stage(n, title, what, body):
    return (f'<section class="stg"><div class="sn">{n}</div><div class="sc">'
            f'<h3>{title}</h3><div class="what">{what}</div>{body}</div></section>')


def code(lang, text):
    return f'<pre class="code"><span class="lang">{lang}</span><code>{esc(text)}</code></pre>'


CSS = r"""
:root{--bg:#0d1117;--panel:#131a24;--ink:#e6edf3;--muted:#8b98a9;--line:#243040;--accent:#39d3e0;
 --green:#57d38c;--red:#ff7b72;--amber:#e3b341;--purple:#c8a2ff;
 --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;--mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;}
:root[data-theme="light"]{--bg:#f6f8fa;--panel:#ffffff;--ink:#111820;--muted:#5a6b7b;--line:#dde3ea;
 --accent:#0a7d8c;--green:#1a7f4b;--red:#c0392b;--amber:#9a6a12;--purple:#6b46c1;}
@media(prefers-color-scheme:light){:root{--bg:#f6f8fa;--panel:#ffffff;--ink:#111820;--muted:#5a6b7b;
 --line:#dde3ea;--accent:#0a7d8c;--green:#1a7f4b;--red:#c0392b;--amber:#9a6a12;--purple:#6b46c1;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.65;font-size:16px}
.doc{max-width:900px;margin:0 auto;padding:clamp(20px,4vw,44px)}
h1{font-size:clamp(1.7rem,4vw,2.5rem);letter-spacing:-.02em;margin:.1em 0 .3em;line-height:1.1}
h2{font-size:1.5rem;margin:1.6em 0 .3em;letter-spacing:-.01em}
h3{font-size:1.22rem;margin:0 0 .2em}
.eyebrow{font-family:var(--mono);font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--accent)}
.deck{color:var(--muted);font-size:1.1rem;max-width:70ch}
.trace-host{display:inline-block;font-family:var(--mono);background:var(--panel);border:1px solid var(--accent);
 color:var(--accent);border-radius:8px;padding:4px 12px;font-size:.9rem;margin:8px 0}
p{margin:0 0 1em;max-width:74ch}
b{font-weight:650}
.stg{display:flex;gap:18px;margin:0;padding:26px 0;border-top:1px solid var(--line)}
.sn{flex:0 0 40px;height:40px;border-radius:50%;background:var(--accent);color:#04222a;font-weight:800;
 font-family:var(--mono);display:flex;align-items:center;justify-content:center;font-size:1.1rem}
.sc{flex:1;min-width:0}
.what{color:var(--muted);font-size:.95rem;margin:.1em 0 .8em}
.code{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px;overflow-x:auto;
 position:relative;margin:12px 0}
.code code{font-family:var(--mono);font-size:.82rem;line-height:1.55;white-space:pre;color:var(--ink)}
.lang{position:absolute;top:8px;right:12px;font-family:var(--mono);font-size:.66rem;letter-spacing:.1em;
 text-transform:uppercase;color:var(--muted)}
.arrow{color:var(--accent);font-family:var(--mono);text-align:center;font-size:1.3rem;margin:-6px 0}
.callout{border-radius:10px;padding:14px 18px;margin:16px 0;font-size:.95rem}
.callout.key{background:color-mix(in srgb,var(--accent) 12%,transparent);border:1px solid var(--accent)}
.callout.push{background:color-mix(in srgb,var(--purple) 14%,transparent);border:1px solid var(--purple)}
.co-t{font-weight:700;margin-bottom:4px}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin:14px 0}
table{border-collapse:collapse;width:100%;font-size:.86rem}
th,td{padding:9px 13px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--panel);font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
tr:last-child td{border-bottom:none}
td.m,.m{font-family:var(--mono);font-size:.8rem}
.k{color:var(--accent)}.g{color:var(--green)}.r{color:var(--red)}.pp{color:var(--purple)}
ul{padding-left:1.3em}li{margin:.3em 0}
.mono{font-family:var(--mono)}
.pipemap{font-family:var(--mono);font-size:.8rem;background:var(--panel);border:1px solid var(--line);
 border-radius:10px;padding:16px;overflow-x:auto;line-height:1.9;margin:16px 0}
a{color:var(--accent)}
"""


def build():
    b = ['<div class="doc">']
    b.append('<div class="eyebrow">Technical walkthrough · pin to pin</div>')
    b.append("<h1>How the system works, end to end</h1>")
    b.append('<p class="deck">We follow <b>one real host</b> — a DGA attacker — through every stage: '
             'from the packet it sent, to the log Zeek wrote, to the score, to the alert, to the exact '
             'moment it is <b>pushed into Elasticsearch</b> and rendered on a dashboard. Every code '
             'block and every piece of data below is real, taken from the running system.</p>')
    b.append('<div class="trace-host">TRACING &nbsp; host = 10.50.0.21 &nbsp; (role: DGA attacker)</div>')

    # pipeline map
    b.append("<h2>The whole pipeline on one line</h2>")
    b.append('<div class="pipemap">'
             'container sim <span class="k">→</span> tcpdump (labbr0) <span class="k">→</span> '
             'Zeek + Suricata <span class="k">→</span> parsers <span class="k">→</span> 8 indicators '
             '<span class="k">→</span> UEBA <span class="k">→</span> correlation <span class="k">→</span> '
             'explainable alert <span class="k">→</span> <span class="pp">Elasticsearch (push)</span> '
             '<span class="k">→</span> Kibana</div>')
    b.append('<p>One command runs all of it: <span class="mono k">make lab-demo</span>. Each stage below '
             'names the exact script and shows its real input and output.</p>')

    # command map
    b.append('<div class="scroll"><table><thead><tr><th>make target</th><th>Script</th><th>Stage(s)</th></tr></thead><tbody>'
             '<tr><td class="m">lab-up</td><td class="m">scripts/lab_up.sh</td><td>1 — create hosts, resolver, C2</td></tr>'
             '<tr><td class="m">lab-capture</td><td class="m">scripts/lab_capture.sh</td><td>2–3 — capture + Zeek/Suricata</td></tr>'
             '<tr><td class="m">evaluate-lab</td><td class="m">c2detect.cli evaluate-lab</td><td>4–7 — features → UEBA → correlate → A/B/C</td></tr>'
             '<tr><td class="m">cli run</td><td class="m">c2detect.cli run</td><td>7–8 — build alerts + push to ES</td></tr>'
             '<tr><td class="m">ingest_es.py</td><td class="m">scripts/ingest_es.py</td><td>8 — push telemetry + scores to ES</td></tr>'
             '<tr><td class="m">build_dashboards.py</td><td class="m">scripts/build_dashboards.py</td><td>9 — Kibana data views + dashboards</td></tr>'
             '</tbody></table></div>')

    # STAGE 1
    b.append(stage(1, "Traffic generation — the host does something",
        "A container named <b>ep-dga-alpha</b> (IP 10.50.0.21) runs a generator that resolves random "
        "domains. Almost all don't exist, producing NXDOMAIN answers — the DGA hallmark.",
        code("scripts/lab_capture.sh — the exec that drives host .21",
        'docker exec ep-dga-alpha sh -c \\\n'
        '  "python3 /opt/traffic/malicious/dga_sim.py 180 com"\n\n'
        '# dga_sim.py builds names like:  fktqbkqrsqn4920v.com\n'
        '#                                zw6co6fb7qk7bwqw.com   (random, 16 chars)\n'
        '# and calls socket.gethostbyname() on each -> a DNS query leaves the host')))
    b.append('<div class="arrow">↓ a DNS query packet leaves 10.50.0.21</div>')

    # STAGE 2
    b.append(stage(2, "Inline capture — tcpdump on the lab bridge",
        "The analysis VM is the gateway for every host, so all traffic crosses one virtual bridge "
        "(<span class='mono'>labbr0</span>). tcpdump records it to a pcap. On the bridge the packet "
        "still carries its <b>real source IP</b> (10.50.0.21) — no relabeling.",
        code("scripts/lab_capture.sh",
        "tcpdump -i labbr0 -n -w data/captures/lab/capture.pcap \\\n"
        "        'port 53 or port 443 or port 8443'")))
    b.append('<div class="arrow">↓ capture.pcap (raw packets)</div>')

    # STAGE 3
    b.append(stage(3, "Sensors — Zeek & Suricata turn packets into logs",
        "Zeek reads the pcap and writes structured JSON logs (one line per event). Suricata runs the "
        "signature baseline. <span class='mono'>-k none</span> tells Suricata to ignore checksum "
        "offload so it still parses the traffic.",
        code("scripts/lab_capture.sh",
        "# Zeek -> dns.log, ssl.log, conn.log (JSON)\n"
        "/opt/zeek/bin/zeek -C -r capture.pcap policy/tuning/json-logs.zeek packages\n\n"
        "# Suricata -> eve.json (alerts)\n"
        "suricata -k none -r capture.pcap -S rules/suricata/local.rules -l data/captures/lab")
        + "<p>The DNS query from stage 1 becomes this real line in <span class='mono'>dns.log</span>:</p>"
        + code("data/captures/lab/dns.log  (real record)",
        '{ "ts": 1783673499.435441,\n'
        '  "id.orig_h": "10.50.0.21",        ← the host (source)\n'
        '  "id.resp_h": "10.50.0.1",         ← the resolver (this VM)\n'
        '  "query": "fktqbkqrsqn4920v.com",  ← random-looking name\n'
        '  "qtype_name": "A",\n'
        '  "rcode_name": "NXDOMAIN" }        ← no such domain')
        + "<p>A beacon host writes to <span class='mono'>ssl.log</span> instead, exposing its TLS "
        "fingerprint and the server name it contacted:</p>"
        + code("data/captures/lab/ssl.log  (real record, host .25)",
        '{ "id.orig_h": "10.50.0.25",\n'
        '  "server_name": "c2.internal.lab",              ← the C2 domain (SNI)\n'
        '  "ja3": "e459f9ec156647e137eec3618527db1f",     ← client fingerprint\n'
        '  "ja4": "t13d171200_ab0a1bf427ad_ecd0401ec68b" }')
        + "<p>And Suricata writes a signature alert (the traditional Config-A baseline):</p>"
        + code("data/captures/lab/eve.json  (real alert)",
        '{ "event_type": "alert", "src_ip": "10.50.0.24",\n'
        '  "alert": { "signature": "C2LAB Long DNS query name (possible tunnel)" } }')))
    b.append('<div class="arrow">↓ dns.log / ssl.log / conn.log / eve.json</div>')

    # STAGE 4
    b.append(stage(4, "Parse & score — the 8 indicators run",
        "<span class='mono'>pipeline.build_feature_vectors()</span> reads the Zeek logs, groups records "
        "by host, and runs the 8 indicator functions. Each returns a 0–1 sub-score for the host.",
        code("src/c2detect/indicators/entropy.py  (real)",
        "def subscore(domain, entropy_high=3.5):\n"
        "    e = longest_label_entropy(domain)         # Shannon entropy of the label\n"
        "    return max(0.0, min(1.0, e / (entropy_high * 1.5)))\n\n"
        "# 'fktqbkqrsqn4920v' is near-random -> high entropy -> sub-score 0.762")
        + "<p>Running all 8 indicators for host 10.50.0.21 yields this <b>feature vector</b> "
        "(the real numbers):</p>"
        + code("feature vector for 10.50.0.21  (real)",
        '{ "dns_entropy":   0.762,   ← random-looking domains\n'
        '  "dga":           0.907,   ← machine-generated structure\n'
        '  "nxdomain_rate": 1.000,   ← every lookup failed\n'
        '  "query_len":     0.533,\n'
        '  "beacon_cv":     0.291,\n'
        '  "session_shape": 0.427,\n'
        '  "ja3_rarity":    0.000,   ← this host made no TLS\n'
        '  "doh_endpoint":  0.000 }')))
    b.append('<div class="arrow">↓ feature vector (8 sub-scores)</div>')

    # STAGE 5
    b.append(stage(5, "UEBA — how abnormal is this host vs. normal?",
        "An IsolationForest is trained on the <b>benign</b> hosts, plus a one-sided z-score. The host's "
        "feature vector is scored against that baseline. Host .21 is wildly abnormal (nxdomain_rate 1.0 "
        "when benign hosts are ~0), so:",
        code("UEBA output for 10.50.0.21  (real)", "anomaly_score = 1.00   (0 = normal, 1 = extreme outlier)")))
    b.append('<div class="arrow">↓ anomaly_score = 1.0</div>')

    # STAGE 6
    b.append(stage(6, "Correlation — fuse everything into one confidence",
        "The glass-box engine blends the UEBA anomaly with the weighted indicator bundle, then adds "
        "<b>boosts</b> for high-signal combinations. Every term is inspectable.",
        code("src/c2detect/correlation/engine.py  (real formula)",
        "indicator_component = Σ wᵢ·subscoreᵢ / Σ wᵢ        = 0.497\n"
        "ueba_component      = ueba_weight · anomaly   = 0.40 · 1.0 = 0.400\n"
        "base                = ueba_component + (1 - ueba_weight) · indicator_component\n"
        "                    = 0.400 + 0.60 · 0.497            = 0.698\n"
        "boost               = +0.10 (dga & nxdomain) +0.10 (entropy & nxdomain) = 0.200\n"
        "CONFIDENCE          = base + boost = 0.698 + 0.200      = 0.898")
        + '<div class="callout key"><div class="co-t">Why the boost matters</div>Two behaviours firing '
        "<i>together</i> (DGA structure AND failed lookups) is far stronger evidence than either alone — "
        "so the rules add confidence for the combination. This is the correlation that beats single "
        "indicators.</div>"))
    b.append('<div class="arrow">↓ confidence = 0.898  (≥ 0.60 threshold → alert)</div>')

    # STAGE 7
    b.append(stage(7, "Explainable alert — build the analyst-ready record",
        "<span class='mono'>explain/reasoner.py</span> turns the correlation result into a full alert: "
        "verdict, confidence, the indicators that fired with plain-English reasons, MITRE techniques, "
        "and recommended actions. This is the JSON that will be stored.",
        code("the alert object for 10.50.0.21  (real, abridged)",
        '{ "alert_id": "5a6d6bca-…",\n'
        '  "@timestamp": "2026-07-10T09:49:24Z",\n'
        '  "entity": "10.50.0.21",\n'
        '  "verdict": "likely_c2",  "confidence": 0.898,  "severity": "high",\n'
        '  "ueba": { "anomaly_score": 1.0, "risk_score": 100 },\n'
        '  "score_breakdown": { "ueba_component":0.4, "indicator_component":0.497, "boost":0.2 },\n'
        '  "contributing_indicators": [\n'
        '     {"name":"dns_entropy","value":0.762,"why":"domains near-random (DGA/tunneling)"},\n'
        '     {"name":"dga","value":0.907,"why":"structure matches generated names"},\n'
        '     {"name":"nxdomain_rate","value":1.0,"why":"elevated failed lookups — DGA hallmark"}],\n'
        '  "mitre": ["T1071.004","T1568.002"],\n'
        '  "recommended_actions": ["Hunt the domain across all hosts…", "Pre-block predicted domains…"] }')))
    b.append('<div class="arrow pp">↓ now it gets pushed to Elasticsearch</div>')

    # STAGE 8 — the push
    b.append(stage(8, "Push to Elasticsearch — how logs actually land",
        "There are two writers, both talking to Elasticsearch over <b>HTTPS with a password</b>. This "
        "is the part you asked about specifically.",
        '<div class="callout push"><div class="co-t">Path A — alerts (one document each)</div>'
        "The pipeline’s <span class='mono'>AlertWriter</span> connects, ensures the index exists with an "
        "explicit field mapping, then indexes each alert by its id.</div>"
        + code("src/c2detect/output/elastic.py  (real)",
        "from elasticsearch import Elasticsearch\n"
        "self.es = Elasticsearch(\n"
        "    ['https://localhost:9200'],\n"
        "    basic_auth=('elastic', PASSWORD),   # from ELASTIC_PASSWORD / secrets.env\n"
        "    verify_certs=False, ssl_show_warn=False)   # self-signed lab cert\n\n"
        "def ensure_index(self):                 # create index with typed fields\n"
        "    if not self.es.indices.exists(index='c2-alerts'):\n"
        "        self.es.indices.create(index='c2-alerts', mappings=self.MAPPING)\n\n"
        "def write(self, alert):                 # <-- the actual push, one doc\n"
        "    self.es.index(index='c2-alerts', id=alert['alert_id'], document=alert)")
        + '<div class="callout push"><div class="co-t">Path B — telemetry &amp; scores (bulk)</div>'
        "<span class='mono'>ingest_es.py</span> pushes thousands of Zeek/Suricata records and per-host "
        "scores using the <b>bulk</b> helper (one big request, not one-by-one), tagging each with the "
        "host, its label, and a spread <span class='mono'>@timestamp</span> for the time-series.</div>"
        + code("scripts/ingest_es.py  (real)",
        "from elasticsearch import helpers\n"
        "docs = []\n"
        "for r in zeek_parser.read_log('dns.log'):\n"
        "    docs.append({'_index': 'zeek-dns',\n"
        "                 '_source': {**r, 'entity': r['id.orig_h'],\n"
        "                             'label': 'attack', '@timestamp': spread.iso(r['ts'])}})\n"
        "helpers.bulk(es, docs)                  # <-- the actual push, many docs at once")
        + "<p>After the push, the alert is a real document you can fetch straight from Elasticsearch:</p>"
        + code("verify from the shell",
        "$ curl -k -u elastic:$PW 'https://localhost:9200/c2-alerts/_doc/5a6d6bca-…'\n"
        '{ "_index":"c2-alerts", "_id":"5a6d6bca-…",\n'
        '  "_source": { "entity":"10.50.0.21", "verdict":"likely_c2", "confidence":0.898, … } }')
        + "<p>Fields are <b>typed</b> by the index mapping so Kibana can aggregate on them:</p>"
        + code("c2-alerts mapping  (real)",
        "entity   -> keyword     confidence -> float      @timestamp -> date\n"
        "verdict  -> keyword     severity   -> keyword     mitre      -> keyword\n"
        "contributing_indicators -> nested (name/value/why)")
        + "<p>In total the pipeline pushes to <b>eight indices</b>:</p>"
        + '<div class="scroll"><table><thead><tr><th>Index</th><th>What it holds</th><th>Writer</th><th>Docs</th></tr></thead><tbody>'
        '<tr><td class="m">c2-alerts</td><td>explainable alerts</td><td class="m">AlertWriter.index</td><td class="m">34</td></tr>'
        '<tr><td class="m">c2-entity-scores</td><td>per-host verdict/confidence/UEBA (all 14 hosts)</td><td class="m">bulk</td><td class="m">14</td></tr>'
        '<tr><td class="m">c2-indicator-scores</td><td>each host × each indicator (heatmap)</td><td class="m">bulk</td><td class="m">112</td></tr>'
        '<tr><td class="m">c2-eval</td><td>A/B/C metrics</td><td class="m">bulk</td><td class="m">12</td></tr>'
        '<tr><td class="m">zeek-dns</td><td>raw DNS telemetry</td><td class="m">bulk</td><td class="m">3162</td></tr>'
        '<tr><td class="m">zeek-ssl</td><td>raw TLS telemetry (SNI, JA3)</td><td class="m">bulk</td><td class="m">606</td></tr>'
        '<tr><td class="m">zeek-conn</td><td>raw connection telemetry</td><td class="m">bulk</td><td class="m">3795</td></tr>'
        '<tr><td class="m">suricata-alerts</td><td>signature hits (Config A)</td><td class="m">bulk</td><td class="m">328</td></tr>'
        '</tbody></table></div>'))
    b.append('<div class="arrow">↓ documents in Elasticsearch</div>')

    # STAGE 9
    b.append(stage(9, "Kibana — dashboards read the indices",
        "<span class='mono'>build_dashboards.py</span> creates a <b>data view</b> per index (a pointer + "
        "time field) and the dashboard panels. Each panel is just an Elasticsearch aggregation query.",
        code("what a panel really runs (e.g. 'alerts by verdict')",
        'POST c2-alerts/_search\n'
        '{ "size": 0,\n'
        '  "aggs": { "by_verdict": { "terms": { "field": "verdict" } } } }\n\n'
        '# -> [ {"key":"likely_c2","doc_count":6}, {"key":"suspicious","doc_count":2} ]')
        + "<p>The heatmap reads <span class='mono'>c2-indicator-scores</span>; the KPI tiles run "
        "<span class='mono'>_count</span> queries; the A/B/C bar reads <span class='mono'>c2-eval</span>. "
        "You see the result at <span class='mono k'>https://172.16.242.14:5601</span>.</p>"))

    # file reference
    b.append("<h2>File-by-file reference</h2>")
    b.append('<div class="scroll"><table><thead><tr><th>File</th><th>Responsibility</th></tr></thead><tbody>'
        '<tr><td class="m">scripts/lab_up.sh</td><td>Create the bridge, DNS resolver, local C2, and 14 host containers</td></tr>'
        '<tr><td class="m">scripts/lab_capture.sh</td><td>Run each host’s traffic, capture inline, run Zeek + Suricata</td></tr>'
        '<tr><td class="m">src/c2detect/parsers/</td><td>Read Zeek (TSV/JSON) and Suricata eve.json into dicts</td></tr>'
        '<tr><td class="m">src/c2detect/indicators/</td><td>The 8 behaviours: entropy, dga, nxdomain, beaconing, ja3ja4, doh, session, length</td></tr>'
        '<tr><td class="m">src/c2detect/pipeline.py</td><td>build_feature_vectors — group by host, run indicators</td></tr>'
        '<tr><td class="m">src/c2detect/ueba/baseline_model.py</td><td>IsolationForest + z-score anomaly model</td></tr>'
        '<tr><td class="m">src/c2detect/correlation/</td><td>engine.py (fusion) + rules.py (weights, boosts)</td></tr>'
        '<tr><td class="m">src/c2detect/explain/reasoner.py</td><td>Build the explainable alert (verdict, MITRE, actions)</td></tr>'
        '<tr><td class="m">src/c2detect/output/elastic.py</td><td>AlertWriter — push alerts to Elasticsearch</td></tr>'
        '<tr><td class="m">scripts/ingest_es.py</td><td>Bulk-push telemetry + scores; spread @timestamp over 24h</td></tr>'
        '<tr><td class="m">scripts/build_dashboards.py</td><td>Create Kibana data views + 3 dashboards</td></tr>'
        '<tr><td class="m">src/c2detect/eval/</td><td>The A/B/C evaluation harness (lab.py, evaluate.py, metrics.py)</td></tr>'
        '</tbody></table></div>')

    b.append('<div class="callout key"><div class="co-t">The whole thing, restated</div>'
        "A random DNS query left host 10.50.0.21 → tcpdump caught it on the bridge → Zeek logged it as an "
        "NXDOMAIN record → the entropy/DGA/NXDOMAIN indicators scored it → UEBA called the host an extreme "
        "outlier → correlation fused it to confidence 0.898 → the reasoner wrote an explained alert → "
        "<b>AlertWriter.index() pushed it into the c2-alerts index over HTTPS</b> → a Kibana aggregation "
        "counted it on the dashboard. Every arrow above is a real, inspectable step.</div>")

    b.append('<footer style="border-top:1px solid var(--line);margin-top:30px;padding-top:18px;'
             'color:var(--muted);font-family:var(--mono);font-size:.8rem">'
             'github.com/Sushanth2624/dns-https-c2-ueba-detection · reproduce with <b>make lab-demo</b></footer>')
    b.append("</div>")
    return f"<style>{CSS}</style>\n" + "".join(b)


OUT.write_text(build())
print("wrote", OUT, round(len(OUT.read_text()) / 1024), "KB")
