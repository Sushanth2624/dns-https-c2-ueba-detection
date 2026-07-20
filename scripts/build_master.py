#!/usr/bin/env python3
"""Build the MASTER REFERENCE — one exhaustive pin-to-pin document covering everything:
what exists and where, how to access the hosts, how to check logs, how to verify each stage,
how correlation works, and the honest UEBA/OpenUBA status."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/tmp/master-reference.html"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def code(text, lang=""):
    tag = f'<span class="lang">{lang}</span>' if lang else ""
    return f'<pre class="code">{tag}<code>{esc(text)}</code></pre>'


def check(text):
    return f'<div class="check"><span class="ct">✔ HOW TO CHECK</span>{text}</div>'


def note(kind, title, body):
    return f'<div class="note {kind}"><b>{title}</b><br>{body}</div>'


ARCH = """<svg viewBox="0 0 1000 340" class="svg"><defs><marker id="m1" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0L9,4.5L0,9z" fill="var(--edge)"/></marker><style>.lyr{fill:var(--card);stroke:var(--line);stroke-width:1.5}.nd{fill:var(--chip);stroke:var(--line)}.t{fill:var(--ink);font:600 14px system-ui}.s{fill:var(--mut);font:11px system-ui}.lb{fill:var(--acc);font:700 12px ui-monospace;letter-spacing:.06em;text-transform:uppercase}.f{stroke:var(--edge);stroke-width:2.2;fill:none;marker-end:url(#m1)}</style></defs>
<rect class="lyr" x="10" y="46" width="215" height="278" rx="12"/><rect class="lyr" x="255" y="46" width="230" height="278" rx="12"/><rect class="lyr" x="515" y="46" width="230" height="278" rx="12"/><rect class="lyr" x="775" y="46" width="215" height="278" rx="12"/>
<text class="lb" x="117" y="32" text-anchor="middle">Hosts (containers)</text><text class="lb" x="370" y="32" text-anchor="middle">Sensors</text><text class="lb" x="630" y="32" text-anchor="middle">Detection engine</text><text class="lb" x="882" y="32" text-anchor="middle">Store + view</text>
<rect class="nd" x="30" y="70" width="175" height="42" rx="8"/><text class="t" x="117" y="90" text-anchor="middle">6 benign .11–.16</text><text class="s" x="117" y="106" text-anchor="middle">curl browsing</text>
<rect class="nd" x="30" y="128" width="175" height="42" rx="8" style="stroke:var(--red)"/><text class="t" x="117" y="148" text-anchor="middle">8 attackers .21–.28</text><text class="s" x="117" y="164" text-anchor="middle">DGA·tunnel·beacon·DoH</text>
<rect class="nd" x="30" y="200" width="175" height="42" rx="8" style="stroke:var(--acc)"/><text class="t" x="117" y="220" text-anchor="middle">bridge labbr0</text><text class="s" x="117" y="236" text-anchor="middle">10.50.0.0/24</text>
<rect class="nd" x="275" y="70" width="190" height="42" rx="8" style="stroke:var(--acc)"/><text class="t" x="370" y="90" text-anchor="middle">gateway + dnsmasq</text><text class="s" x="370" y="106" text-anchor="middle">tcpdump 100% inline</text>
<rect class="nd" x="275" y="130" width="90" height="54" rx="8"/><text class="t" x="320" y="155" text-anchor="middle">Zeek</text><text class="s" x="320" y="172" text-anchor="middle">dns/ssl/conn</text>
<rect class="nd" x="375" y="130" width="90" height="54" rx="8"/><text class="t" x="420" y="155" text-anchor="middle">Suricata</text><text class="s" x="420" y="172" text-anchor="middle">eve.json</text>
<rect class="nd" x="275" y="240" width="190" height="42" rx="8" style="stroke:var(--red)"/><text class="t" x="370" y="266" text-anchor="middle">local C2 :8443</text>
<rect class="nd" x="535" y="66" width="190" height="46" rx="8"/><text class="t" x="630" y="94" text-anchor="middle">8 indicators</text>
<rect class="nd" x="535" y="120" width="190" height="46" rx="8" style="stroke:var(--acc)"/><text class="t" x="630" y="141" text-anchor="middle">UEBA anomaly</text><text class="s" x="630" y="158" text-anchor="middle">OpenUBA (fallback: IsoForest+z)</text>
<rect class="nd" x="535" y="174" width="190" height="46" rx="8" style="stroke:var(--acc)"/><text class="t" x="630" y="202" text-anchor="middle">correlation (glass-box)</text>
<rect class="nd" x="535" y="228" width="190" height="46" rx="8" style="stroke:var(--acc)"/><text class="t" x="630" y="256" text-anchor="middle">explainable alert</text>
<rect class="nd" x="795" y="100" width="175" height="46" rx="8"/><text class="t" x="882" y="128" text-anchor="middle">Elasticsearch</text>
<rect class="nd" x="795" y="200" width="175" height="46" rx="8" style="stroke:var(--acc)"/><text class="t" x="882" y="228" text-anchor="middle">Kibana</text>
<path class="f" d="M225,160 L251,160"/><path class="f" d="M485,160 L511,160"/><path class="f" d="M745,175 L793,135 L793,124"/><path class="f" d="M882,146 L882,196"/></svg>"""

# helper diagrams filled in content sections

CSS = r"""
:root{--bg:#0e1117;--card:#161b22;--chip:#1c2230;--ink:#e6edf3;--mut:#8b98a9;--acc:#38b6c4;
 --acc2:#7ee0ea;--green:#57d38c;--red:#ff7b72;--amber:#e3b341;--purple:#c8a2ff;--line:#28303c;--edge:#5a6b86;
 --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;--mono:ui-monospace,Menlo,Consolas,monospace}
:root[data-theme="light"]{--bg:#f7f9fb;--card:#fff;--chip:#eef2f6;--ink:#141b24;--mut:#5a6b7b;--acc:#0a7d8c;
 --acc2:#0a6f7c;--green:#1a7f4b;--red:#c0392b;--amber:#9a6a12;--purple:#6b46c1;--line:#dde3ea;--edge:#9aa6b2}
@media(prefers-color-scheme:light){:root{--bg:#f7f9fb;--card:#fff;--chip:#eef2f6;--ink:#141b24;--mut:#5a6b7b;
 --acc:#0a7d8c;--acc2:#0a6f7c;--green:#1a7f4b;--red:#c0392b;--amber:#9a6a12;--purple:#6b46c1;--line:#dde3ea;--edge:#9aa6b2}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15.5px;line-height:1.62}
.doc{max-width:920px;margin:0 auto;padding:clamp(18px,4vw,40px)}
h1{font-size:clamp(1.7rem,4vw,2.5rem);letter-spacing:-.02em;margin:.1em 0 .2em;line-height:1.1}
h2{font-size:1.55rem;margin:0 0 .1em;letter-spacing:-.015em}
h3{font-size:1.2rem;margin:1.5em 0 .3em}
h4{font-size:1.02rem;margin:1.2em 0 .2em;font-weight:700}
p{margin:0 0 .9em}b{font-weight:650}
.eyebrow{font-family:var(--mono);font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--acc)}
.deck{color:var(--mut);font-size:1.08rem;max-width:74ch}
.toc{position:sticky;top:0;z-index:10;background:color-mix(in srgb,var(--bg) 90%,transparent);
 backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:10px 0;margin:14px 0 8px;
 display:flex;flex-wrap:wrap;gap:3px}
.toc a{font-family:var(--mono);font-size:.72rem;color:var(--mut);text-decoration:none;padding:4px 9px;border-radius:6px}
.toc a:hover{color:var(--acc);background:var(--chip)}
.part{border-top:1px solid var(--line);padding-top:30px;margin-top:38px}
.pn{font-family:var(--mono);font-size:.75rem;letter-spacing:.14em;text-transform:uppercase;color:var(--acc)}
.pintro{color:var(--mut);max-width:70ch;margin-top:.2em}
.code{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:13px 15px;overflow-x:auto;position:relative;margin:12px 0}
.code code{font-family:var(--mono);font-size:.8rem;line-height:1.55;white-space:pre;color:var(--ink)}
.lang{position:absolute;top:7px;right:11px;font-family:var(--mono);font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;color:var(--mut)}
.check{background:color-mix(in srgb,var(--green) 12%,transparent);border:1px solid var(--green);border-radius:9px;padding:12px 15px;margin:12px 0;font-size:.95rem}
.check .ct{display:block;font-family:var(--mono);font-size:.7rem;letter-spacing:.08em;color:var(--green);font-weight:700;margin-bottom:5px}
.check .m{white-space:pre-wrap;display:block;line-height:1.55}
.note{border-radius:9px;padding:12px 15px;margin:14px 0;font-size:.94rem}
.note.key{background:color-mix(in srgb,var(--acc) 12%,transparent);border:1px solid var(--acc)}
.note.warn{background:color-mix(in srgb,var(--red) 13%,transparent);border:1px solid var(--red)}
.note.info{background:var(--chip);border:1px solid var(--line)}
.note.open{background:color-mix(in srgb,var(--purple) 14%,transparent);border:1px solid var(--purple)}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:9px;margin:14px 0}
table{border-collapse:collapse;width:100%;font-size:.86rem}
th,td{padding:9px 13px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--card);font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}
tr:last-child td{border-bottom:none}
td.m,.m{font-family:var(--mono);font-size:.8rem}
.svg{width:100%;height:auto;background:var(--card);border:1px solid var(--line);border-radius:11px;padding:14px;margin:14px 0}
ul,ol{padding-left:1.35em;margin:.2em 0 1em}li{margin:.28em 0}
.k{color:var(--acc)}.mono{font-family:var(--mono)}
.q{font-weight:700;color:var(--ink);margin-top:1.1em}
.big-idea{background:var(--card);border:1px solid var(--acc);border-left:5px solid var(--acc);border-radius:11px;padding:16px 20px;margin:16px 0;font-size:1.05rem}
a{color:var(--acc)}
@media print{.toc{display:none}.part{page-break-before:always}}
"""

def part(pid, num, title, intro):
    return f'<section class="part" id="{pid}"><div class="pn">Part {num}</div><h2>{title}</h2><p class="pintro">{intro}</p>'

TOC = ('<nav class="toc">'
 '<a href="#p1">1 Inventory &amp; access</a><a href="#p2">2 Architecture</a>'
 '<a href="#p3">3 Pin-to-pin stages</a><a href="#p4">4 The 8 indicators</a>'
 '<a href="#p5">5 UEBA &amp; OpenUBA</a><a href="#p6">6 Correlation</a>'
 '<a href="#p7">7 Where everything lives</a><a href="#p8">8 Verify everything</a>'
 '<a href="#p9">9 Evaluation A/B/C</a><a href="#p10">10 Commands</a>'
 '<a href="#p11">11 FAQ / doubts</a><a href="#p12">12 Glossary</a></nav>')

HEADER = """<div class="eyebrow">Master reference · pin to pin · for your understanding</div>
<h1>The complete guide to how this project works</h1>
<p class="deck">Everything, in one place: what exists and where, how to get into the hosts, how to read
the logs, how to verify every stage yourself, exactly how the correlation happens, and the honest
status of UEBA and OpenUBA. Every command is copy-paste ready. Run them from the project folder:</p>
""" + code("cd /home/analysis/dns-https-c2-ueba-detection\nsource config/secrets.env   # loads ELASTIC_PASSWORD — do this first, every session", "run first")

P1 = part("p1", 1, "Inventory & access — what exists and where",
  "The single most important section for your viva. Read this and you can answer 'where is everything and how do I get to it.'") + """
<h3>1.1 &nbsp;The golden rule: there is ONE machine</h3>
""" + note("warn", "Say this correctly in the viva",
  "There are <b>no separate VMs</b>. There is <b>one Analysis VM</b> (the machine you log into). "
  "The 14 'endpoint hosts' are <b>Docker containers</b> running on that one machine — because the "
  "machine has no nested virtualization (it can't run full VMs inside itself). Containers give the "
  "same thing that matters: separate hosts, distinct IPs, real per-host traffic captured inline.") + """
<h3>1.2 &nbsp;The Analysis VM (the one real machine)</h3>
<div class="scroll"><table><tbody>
<tr><td>What</td><td>The single Ubuntu 24.04 machine that runs everything</td></tr>
<tr><td>IP</td><td class="m">172.16.242.14</td></tr>
<tr><td>You are</td><td class="m">root</td></tr>
<tr><td>How you access it</td><td>However you already do — the college console, or SSH: <span class="m">ssh &lt;login&gt;@172.16.242.14</span></td></tr>
<tr><td>Project folder</td><td class="m">/home/analysis/dns-https-c2-ueba-detection</td></tr>
</tbody></table></div>
""" + check("<div class='m'>hostname -I        # shows 172.16.242.14<br>whoami            # root<br>uname -a          # Ubuntu 24.04</div>") + """
<h3>1.3 &nbsp;The 14 'hosts' (Docker containers) — and how to get inside them</h3>
<p>Each is a real host with its own IP on the lab network <span class="m">10.50.0.0/24</span>. They have
<b>no username or password</b> — you enter them with <span class="m">docker exec</span> because you are
root on the machine.</p>
<div class="scroll"><table><thead><tr><th>Container name</th><th>IP</th><th>Role</th><th>What it does</th></tr></thead><tbody>
<tr><td class="m">ep-benign1 … 6</td><td class="m">10.50.0.11–.16</td><td>benign</td><td>browse real sites with curl</td></tr>
<tr><td class="m">ep-dga-alpha / beta</td><td class="m">10.50.0.21 / .22</td><td>dga</td><td>resolve random domains → NXDOMAIN</td></tr>
<tr><td class="m">ep-tunnel-sm / lg</td><td class="m">10.50.0.23 / .24</td><td>dns_tunnel</td><td>encode data into long DNS names</td></tr>
<tr><td class="m">ep-beacon-fast / slow</td><td class="m">10.50.0.25 / .26</td><td>beacon</td><td>regular TLS call-home to the local C2</td></tr>
<tr><td class="m">ep-doh-cf / quad9</td><td class="m">10.50.0.27 / .28</td><td>doh</td><td>DNS-over-HTTPS to public resolvers</td></tr>
</tbody></table></div>
""" + check("<div class='m'># list all 14 hosts with their role\ndocker ps --format '{{.Names}}  {{.Label \"c2lab.role\"}}'\n\n# get a shell INSIDE a host (no password)\ndocker exec -it ep-dga-alpha sh\n#   then inside:  hostname -i   → 10.50.0.21 ;   exit\n\n# one-liner: a host's identity\ndocker exec ep-dga-alpha sh -c 'echo I am $(hostname) at $(hostname -i)'") + """
<h3>1.4 &nbsp;The software running on the machine</h3>
<div class="scroll"><table><thead><tr><th>Software</th><th>Version</th><th>Role</th><th>Where / port</th></tr></thead><tbody>
<tr><td>Zeek</td><td class="m">8.2.1</td><td>network sensor → logs</td><td class="m">/opt/zeek</td></tr>
<tr><td>Suricata</td><td class="m">8.0.5</td><td>signature engine (baseline)</td><td>system service</td></tr>
<tr><td>Elasticsearch</td><td class="m">8.19</td><td>database (stores results)</td><td class="m">https://172.16.242.14:9200</td></tr>
<tr><td>Kibana</td><td class="m">8.19</td><td>dashboards</td><td class="m">https://172.16.242.14:5601</td></tr>
<tr><td>Docker</td><td class="m">29.x</td><td>runs the 14 host containers</td><td>system service</td></tr>
<tr><td>Python + c2detect</td><td class="m">3.12</td><td>the detection engine (this project's code)</td><td class="m">src/c2detect/</td></tr>
</tbody></table></div>
""" + check("<div class='m'>systemctl is-active elasticsearch kibana docker   # all 'active'\n/opt/zeek/bin/zeek --version ; suricata -V</div>") + """
<h3>1.5 &nbsp;Credentials — the complete list</h3>
<div class="scroll"><table><thead><tr><th>To access…</th><th>Username</th><th>Password</th></tr></thead><tbody>
<tr><td>The Analysis VM</td><td>your normal login</td><td>your normal login</td></tr>
<tr><td>The 14 containers</td><td colspan="2">none — use <span class="m">docker exec</span> (you're root)</td></tr>
<tr><td>Kibana (dashboards)</td><td class="m">elastic</td><td>in <span class="m">config/secrets.env</span></td></tr>
<tr><td>Elasticsearch (API)</td><td class="m">elastic</td><td>in <span class="m">config/secrets.env</span></td></tr>
</tbody></table></div>
""" + check("<div class='m'>cat config/secrets.env      # shows the elastic + kibana_system passwords</div>") + note("info",
  "Note", "The <span class='m'>kibana_system</span> account is internal only (Kibana↔Elasticsearch). "
  "You log in as <span class='m'>elastic</span>.") + "</section>"

P2 = part("p2", 2, "Architecture & data flow",
  "How the pieces connect, and the one-line path a packet takes to become an alert.") + f"""
<h3>2.1 &nbsp;The map</h3>{ARCH}
<p>Four layers: the 14 host containers generate traffic; the machine is their gateway and captures
everything inline; the detection engine (this project) scores it; results go to Elasticsearch and
Kibana.</p>
<h3>2.2 &nbsp;The data flow in one line</h3>
""" + code("container traffic → tcpdump (labbr0) → Zeek + Suricata → 8 indicators → UEBA → correlation → explainable alert → Elasticsearch → Kibana") + note("key",
  "One command runs all of it", "<span class='m'>make lab-demo</span> — creates hosts, captures inline, "
  "runs Zeek/Suricata, scores, pushes to Elasticsearch, rebuilds dashboards.") + "</section>"

P3 = part("p3", 3, "Pin-to-pin: every stage, and how to check it yourself",
  "For each stage: what runs, where its output lives, and the exact command to prove it works. We follow the DGA host 10.50.0.21.") + """
<h3>Stage 1 — a host generates traffic</h3>
<p>Container <span class="m">ep-dga-alpha</span> resolves random domains. They don't exist → NXDOMAIN.</p>
""" + code("docker exec ep-dga-alpha python3 /opt/traffic/malicious/dga_sim.py 20", "run") + check(
  "You'll see the command return. Traffic left the host on the bridge.") + """
<h3>Stage 2 — inline capture (tcpdump)</h3>
<p>All host traffic crosses the bridge <span class="m">labbr0</span>; tcpdump records it to a pcap.</p>
""" + code("# this runs inside scripts/lab_capture.sh:\ntcpdump -i labbr0 -n -w data/captures/lab/capture.pcap 'port 53 or port 443 or port 8443'") + check(
  "<div class='m'>ls -lh data/captures/lab/capture.pcap    # the raw packet file exists</div>") + """
<h3>Stage 3 — Zeek &amp; Suricata write logs</h3>
""" + code("/opt/zeek/bin/zeek -C -r capture.pcap policy/tuning/json-logs.zeek packages   # -> dns.log ssl.log conn.log\nsuricata -k none -r capture.pcap -S rules/suricata/local.rules -l data/captures/lab   # -> eve.json") + check(
  "<div class='m'># the DGA record Zeek wrote:\nhead -1 data/captures/lab/dns.log | python3 -m json.tool\n#   → id.orig_h 10.50.0.21, query 'fktqbkqrsqn4920v.com', rcode_name NXDOMAIN\n\n# a Suricata signature hit:\ngrep '\"event_type\":\"alert\"' data/captures/lab/eve.json | head -1 | python3 -m json.tool</div>") + """
<h3>Stage 4 — the 8 indicators score the host</h3>
<p><span class="m">pipeline.build_feature_vectors()</span> groups logs by host and runs the 8 indicators.</p>
""" + check("<div class='m'>PYTHONPATH=src ./.venv/bin/python -c \"\nfrom c2detect.config import Config; from c2detect import pipeline\ncfg=Config(raw={'paths':{'zeek_log_dir':'data/captures/lab','ja3_baseline':'data/captures/lab/ja3_baseline.txt'},'thresholds':{'entropy_high':3.5,'nxdomain_ratio_high':0.2,'beacon_cv_low':0.10}})\nf=pipeline.build_feature_vectors(cfg)\nprint(f['10.50.0.21'])\"\n#  → {'dns_entropy':0.76,'dga':0.91,'nxdomain_rate':1.0, ...}</div>") + """
<h3>Stage 5 — UEBA scores how abnormal the host is</h3>
<p><b>OpenUBA</b> (the integrated UEBA engine) scores the host vs the benign baseline; its risk is
calibrated to an anomaly of ~1.0. A built-in IsolationForest+z-score is the drop-in fallback. Full
detail — the integration, the adapter, and how to verify it — is in <a href="#p5">Part 5</a>.</p>
<h3>Stage 6 — correlation fuses it into one confidence</h3>
<p>The glass-box engine (Part 6) blends UEBA + indicators + boosts → confidence 0.898. Full math in
<a href="#p6">Part 6</a>.</p>
<h3>Stage 7 — the explainable alert is built</h3>
<p><span class="m">explain/reasoner.py</span> builds the alert: verdict, confidence, contributing
indicators + reasons, MITRE, actions.</p>
<h3>Stage 8 — the alert is pushed to Elasticsearch</h3>
<p>Two writers push to ES over HTTPS+password (Part 7 lists all indices).</p>
""" + code("# AlertWriter (src/c2detect/output/elastic.py) pushes ONE alert:\nself.es.index(index='c2-alerts', id=alert['alert_id'], document=alert)\n\n# ingest_es.py pushes MANY telemetry docs at once:\nfrom elasticsearch import helpers\nhelpers.bulk(es, docs)   # docs = [{'_index':'zeek-dns','_source':{...}}, ...]") + check(
  "<div class='m'># the alert is now a real document — fetch it:\ncurl -s -k -u elastic:$ELASTIC_PASSWORD \"https://localhost:9200/c2-alerts/_search\" \\\n  -H 'Content-Type: application/json' -d '{\"query\":{\"term\":{\"entity\":\"10.50.0.21\"}}}' | python3 -m json.tool</div>") + """
<h3>Stage 9 — Kibana reads the indices</h3>
<p>Each dashboard panel is an Elasticsearch aggregation query; Kibana runs it and draws the result.</p>
""" + check("Open <span class='m'>https://172.16.242.14:5601</span> → dashboards <span class='m'>c2-exec / c2-threat / c2-telemetry</span> (set time = Last 24 hours).") + "</section>"

P4 = part("p4", 4, "The 8 indicators in detail",
  "Each is a small function returning a 0–1 sub-score for a host. Higher = more suspicious.") + """
<div class="scroll"><table><thead><tr><th>#</th><th>Indicator (file)</th><th>What it detects</th><th>How it's computed</th><th>MITRE</th></tr></thead><tbody>
<tr><td>1</td><td class="m">entropy.py</td><td>random-looking domains (DGA/tunnel)</td><td>Shannon entropy of the highest-entropy label ÷ threshold</td><td class="m">T1568.002</td></tr>
<tr><td>2</td><td class="m">dga.py</td><td>machine-generated names</td><td>blend of entropy + length + digit-ratio + (low) vowel-ratio</td><td class="m">T1568.002</td></tr>
<tr><td>3</td><td class="m">nxdomain.py</td><td>failed-lookup bursts</td><td>fraction of the host's DNS answers = NXDOMAIN ÷ threshold</td><td class="m">T1568.002</td></tr>
<tr><td>4</td><td class="m">length.py</td><td>long/deep names (tunneling)</td><td>longest label length &amp; subdomain depth, normalised</td><td class="m">T1071.004</td></tr>
<tr><td>5</td><td class="m">beaconing.py</td><td>robotic call-home timing</td><td>gap-robust dispersion (median/MAD) of inter-arrival times, grouped by dest IP &amp; SNI</td><td class="m">T1071.001·T1571</td></tr>
<tr><td>6</td><td class="m">ja3ja4.py</td><td>unusual TLS fingerprint</td><td>rarity of the JA3 hash vs the frozen benign baseline</td><td class="m">T1573</td></tr>
<tr><td>7</td><td class="m">doh.py</td><td>DNS hidden in HTTPS</td><td>SNI/host matches a known DoH resolver or /dns-query</td><td class="m">T1071.004·T1572</td></tr>
<tr><td>8</td><td class="m">session.py</td><td>small, steady, long-lived flows</td><td>duration, throughput and up/down byte balance from conn.log</td><td class="m">T1071.001</td></tr>
</tbody></table></div>
""" + note("info", "Why every host has 8 numbers even if some are 0",
  "A DGA host makes no TLS, so its <span class='m'>ja3_rarity</span> and <span class='m'>doh_endpoint</span> "
  "are 0 — that's correct. The correlation only rewards the behaviours that actually fired.") + check(
  "<div class='m'># see all 8 sub-scores for every host at once:\ncurl -s -k -u elastic:$ELASTIC_PASSWORD \"https://localhost:9200/c2-indicator-scores/_search?size=200\" \\\n  -H 'Content-Type: application/json' -d '{\"query\":{\"term\":{\"entity\":\"10.50.0.21\"}}}' | python3 -m json.tool</div>") + "</section>"

P5 = part("p5", 5, "UEBA &amp; OpenUBA — the honest, complete picture",
  "Read this carefully — it's the question examiners most often ask.") + note("open",
  "The direct answer",
  "<b>OpenUBA IS integrated, running, and connected — it is the UEBA engine.</b> Parsed feature "
  "vectors go into OpenUBA, which returns per-entity anomaly/risk; the correlation engine consumes "
  "those scores. A built-in <b>IsolationForest + z-score</b> in <span class='m'>baseline_model.py</span> "
  "remains as a drop-in fallback, selectable with <span class='m'>ueba.source</span>. A/B/C was "
  "re-verified with OpenUBA in the loop: <b>F1 C=1.00 &gt; B=0.67 &gt; A=0.55</b>, FPR 0.00.") + """
<h3>5.1 &nbsp;What UEBA is, and why it's here</h3>
<p>UEBA (User &amp; Entity Behaviour Analytics) means: learn what "normal" looks like for each entity
(here, each host), then score how far a host deviates. In this project the UEBA layer takes each
host's 8-number feature vector and returns an <b>anomaly score</b> (0 = normal, 1 = extreme outlier)
plus a risk score and severity.</p>
<h3>5.2 &nbsp;OpenUBA as the engine — running on one VM, no Kubernetes</h3>
<p>OpenUBA (GACWR/OpenUBA v0.0.2) is an open-source UEBA platform. Its newest release is
Kubernetes-native, but it is deployed here on the <b>single Analysis VM with no Kubernetes and no
Spark</b>:</p>
<ul>
<li><b>Backend</b> — runs on the host as a systemd service <span class="m">openuba-backend</span>
(uvicorn on <span class="m">:8000</span>, <span class="m">EXECUTION_MODE=docker</span>). On the host,
not in a container, so the <span class="m">docker run</span> it issues for each job uses host paths.</li>
<li><b>Postgres</b> — in Docker Compose (<span class="m">openuba-src-postgres-1</span>), OpenUBA's state store.</li>
<li><b>Model-runner</b> — each job spawns a container (<span class="m">openuba-model-runner:sklearn</span>)
that runs the IsolationForest and reports results back.</li>
</ul>
<p>The repo lives at <span class="m">/home/analysis/openuba-src</span>.</p>
<h3>5.3 &nbsp;How our features flow into OpenUBA and scores come back</h3>
<p>The adapter <span class="m">src/c2detect/ueba/openuba_client.py</span> (<span class="m">class OpenUBAClient</span>)
drives OpenUBA and maps its output onto the UEBA contract. One batch call, <span class="m">prime()</span>:</p>
""" + code("src/c2detect/ueba/openuba_client.py  →  class OpenUBAClient\n  .prime(features, benign_entities)   # 1 write per-host feature CSV into OpenUBA's runner volume\n                                      # 2 train the model on the BENIGN hosts (learn 'normal')\n                                      # 3 run inference on all hosts (model-runner container)\n                                      # 4 read per-host risk back, CALIBRATE -> 0..1 anomaly\n  .score(entity, vec)                 # -> UebaRecord(anomaly_score, risk_score, severity)", "file") + note("key",
  "Why calibrate OpenUBA's risk?",
  "OpenUBA's native <span class='m'>risk/100</span> compresses every host into ~0.16–0.51, so the "
  "0.40 UEBA weight can't lift subtle beacon-only / DoH-only attackers over threshold. The adapter "
  "normalises OpenUBA's risk against the <b>benign peer cohort</b> (one-sided z, 6σ saturation — the "
  "same step the fallback uses). OpenUBA still produces the anomaly signal; the adapter only maps it "
  "onto the contract's scale. Result: benign ≤ 0.28, attackers ≥ 0.80.") + """
<p>The config selects OpenUBA:</p>
""" + code("# config/config.openuba.yaml\nueba:\n  source: openuba         # <-- OpenUBA is the engine\n  openuba: {api_url: http://localhost:8000, username: openuba, password: password,\n            model_id: ffa8ddb1-a6b3-41af-8354-422609c37fb7, train_on_benign: true}\n# config/config.lab.yaml still has source: baseline (fast, no external deps) as the fallback profile", "config") + """
<h3>5.4 &nbsp;The pluggable contract — and two SDK bugs we worked around</h3>
""" + note("info", "The contract that keeps this safe",
  "Both producers implement the same interface (<span class='m'>.score(entity, features) → UebaRecord</span>), "
  "so the correlation/explainability/alerting code never knows which engine ran. Switch with "
  "<span class='m'>ueba.source: openuba|baseline</span> — nothing else changes. OpenUBA is the engine; "
  "the fallback means it can never become a single point of failure.") + """
<p>Two real bugs in OpenUBA's Python SDK were handled inside the adapter (worth mentioning — it shows
the integration is genuine):</p>
<ul>
<li>The SDK's <span class="m">wait_for_job()</span> treats only <span class="m">completed/failed/error</span>
as terminal, but the backend reports success as <span class="m">succeeded</span> → <span class="m">wait=True</span>
hangs forever. The adapter submits <span class="m">wait=False</span> and polls the job itself.</li>
<li>A <i>trained</i> run persists anomalies to the store (not inline in the job), and the SDK's
<span class="m">query_anomalies</span> hardcodes <span class="m">limit=5000</span> which the API rejects
(422, cap 1000). The adapter reads <span class="m">/api/v1/anomalies</span> directly.</li>
</ul>
<h3>5.5 &nbsp;How to prove all of this yourself</h3>
""" + check("<div class='m'># 1. OpenUBA backend is running and healthy:\nsystemctl status openuba-backend --no-pager | head -3\ncurl -s http://localhost:8000/health        # 200 OK\n\n# 2. its Postgres + a model-runner image exist:\ndocker ps --format '{{.Names}}' | grep -i openuba     # openuba-src-postgres-1\ndocker images | grep openuba-model-runner\n\n# 3. the SDK is installed and the config points at OpenUBA:\n.venv/bin/pip list | grep -i openuba\ngrep -A1 '^ueba:' config/config.openuba.yaml           # source: openuba\n\n# 4. run A/B/C with OpenUBA in the loop and watch C=1.00:\nPYTHONPATH=src ./.venv/bin/python -m c2detect.cli evaluate-lab \\\n  --config config/config.openuba.yaml --lab data/captures/lab --out data/eval/lab-openuba</div>") + note("info",
  "If asked \"did you really integrate OpenUBA, or just use its model?\"",
  "\"OpenUBA runs as the UEBA engine — the backend, its Postgres, and a model-runner container are up "
  "on this VM; my adapter pushes the parsed features in, trains on benign, runs inference, and reads "
  "per-host risk back, which I calibrate onto the 0–1 contract. I re-ran the A/B/C benchmark with "
  "OpenUBA driving the anomaly scores and C&gt;B&gt;A still holds (F1 C=1.00). A built-in IsolationForest "
  "stays as a selectable fallback so OpenUBA is never a single point of failure. My contribution is "
  "the correlation and explainability layer on top.\"") + "</section>"

P6 = part("p6", 6, "Correlation — exactly how the verdict is calculated",
  "This is the project's core contribution and it is a glass box: every number is inspectable. Worked with real values for host 10.50.0.21.") + """
<h3>6.1 &nbsp;The formula</h3>
""" + code("# src/c2detect/correlation/engine.py\nindicator_component = Σ (weightᵢ × sub_scoreᵢ) / Σ weightᵢ\nueba_component      = ueba_weight × ueba_anomaly\nbase                = ueba_component + (1 − ueba_weight) × indicator_component\nboost               = Σ boosts for high-signal combinations that fired\nCONFIDENCE          = clip(base + boost, 0, 1)", "formula") + """
<h3>6.2 &nbsp;The weights (from config, fully reported)</h3>
<div class="scroll"><table><thead><tr><th>Indicator</th><th>weight</th><th>Indicator</th><th>weight</th></tr></thead><tbody>
<tr><td>beacon_cv</td><td class="m">0.25</td><td>dns_entropy</td><td class="m">0.15</td></tr>
<tr><td>nxdomain_rate</td><td class="m">0.15</td><td>dga</td><td class="m">0.10</td></tr>
<tr><td>ja3_rarity</td><td class="m">0.10</td><td>doh_endpoint</td><td class="m">0.10</td></tr>
<tr><td>session_shape</td><td class="m">0.10</td><td>query_len</td><td class="m">0.05</td></tr>
</tbody></table></div>
<p><span class="m">ueba_weight = 0.40</span> · alert threshold <span class="m">confidence ≥ 0.60</span>.</p>
<h3>6.3 &nbsp;The boost rules (src/c2detect/correlation/rules.py)</h3>
<p>When two or more high-signal behaviours fire <b>together</b> (each ≥ 0.6), an extra confidence is
added — because a combination is far stronger evidence than either alone:</p>
<ul>
<li><b>dns_entropy + nxdomain_rate</b> → +0.10 (classic DGA)</li>
<li><b>dga + nxdomain_rate</b> → +0.10</li>
<li><b>query_len + dns_entropy</b> → +0.10 (tunneling)</li>
<li><b>beacon_cv + session_shape</b> → +0.10 (encrypted beacon)</li>
<li><b>beacon_cv + ja3_rarity</b> → +0.12 (regular call-home + odd TLS)</li>
<li><b>dns_entropy + beacon_cv + ja3_rarity</b> → +0.15</li>
<li><b>doh_endpoint + beacon_cv</b> → +0.10 (DoH beacon)</li>
</ul>
<h3>6.4 &nbsp;Worked example — host 10.50.0.21 (DGA)</h3>
""" + code("sub-scores:  dns_entropy 0.762 · dga 0.907 · nxdomain_rate 1.0 · query_len 0.533 · others ~0\n\nindicator_component = 0.497            (weighted average of the sub-scores)\nueba_component      = 0.40 × 1.0 = 0.400\nbase                = 0.400 + 0.60 × 0.497 = 0.698\nboost               = +0.10 (dga & nxdomain) + 0.10 (entropy & nxdomain) = 0.200\nCONFIDENCE          = 0.698 + 0.200 = 0.898   →  verdict 'likely_c2' (≥ 0.60)", "worked") + check(
  "<div class='m'># the ES alert shows the exact breakdown (ueba_component, indicator_component, boost):\ncurl -s -k -u elastic:$ELASTIC_PASSWORD \"https://localhost:9200/c2-alerts/_search\" \\\n  -H 'Content-Type: application/json' -d '{\"query\":{\"term\":{\"entity\":\"10.50.0.21\"}}}' \\\n  | python3 -c \"import sys,json;print(json.load(sys.stdin)['hits']['hits'][0]['_source']['score_breakdown'])\"</div>") + note("key",
  "Why this beats a black box", "Because every term is a named, reported number, you can defend any "
  "verdict line-by-line — impossible with a neural-net classifier. That auditability is the point.") + "</section>"

P7 = part("p7", 7, "Where everything lives — the master map",
  "One table each for: the logs, the code, the data on disk, and the Elasticsearch indices.") + """
<h3>7.1 &nbsp;Logs — where every log is</h3>
<div class="scroll"><table><thead><tr><th>Log</th><th>Location</th><th>Read it with</th></tr></thead><tbody>
<tr><td>Zeek DNS/TLS/conn</td><td class="m">data/captures/lab/{dns,ssl,conn}.log</td><td class="m">python3 -m json.tool</td></tr>
<tr><td>Suricata events</td><td class="m">data/captures/lab/eve.json</td><td class="m">grep '"alert"' | json.tool</td></tr>
<tr><td>Raw packets</td><td class="m">data/captures/lab/capture.pcap</td><td class="m">tcpdump -r</td></tr>
<tr><td>Elasticsearch service log</td><td class="m">journalctl -u elasticsearch</td><td>systemd journal</td></tr>
<tr><td>Kibana service log</td><td class="m">journalctl -u kibana</td><td>systemd journal</td></tr>
<tr><td>A container's stdout</td><td class="m">docker logs ep-dga-alpha</td><td>docker</td></tr>
</tbody></table></div>
<h3>7.2 &nbsp;Code — the src/c2detect package</h3>
""" + code("src/c2detect/\n  pipeline.py            group logs by host, run the 8 indicators (build_feature_vectors)\n  cli.py                 command entrypoints (run, evaluate-lab, corpus)\n  config.py              load YAML config\n  parsers/zeek.py        read Zeek logs (JSON/TSV)\n  parsers/suricata.py    read Suricata eve.json\n  indicators/            the 8 behaviours (entropy, dga, nxdomain, length, beaconing, ja3ja4, doh, session)\n  ueba/openuba_client.py OpenUBA integration adapter (ACTIVE — ueba.source: openuba)\n  ueba/baseline_model.py IsolationForest + z-score   (fallback — ueba.source: baseline)\n  correlation/engine.py  the fusion formula\n  correlation/rules.py   weights + boost rules\n  explain/reasoner.py    build the explainable alert\n  output/elastic.py      push alerts to Elasticsearch (AlertWriter)\n  eval/                  A/B/C evaluation (lab.py, evaluate.py, metrics.py, report.py)", "tree") + """
<h3>7.3 &nbsp;Data &amp; config on disk</h3>
<div class="scroll"><table><tbody>
<tr><td class="m">config/config.lab.yaml</td><td>weights, thresholds, UEBA source, MITRE map, ES settings (baseline profile)</td></tr>
<tr><td class="m">config/config.openuba.yaml</td><td>same, but <span class="m">ueba.source: openuba</span> — runs on the OpenUBA engine</td></tr>
<tr><td class="m">config/secrets.env</td><td>the elastic/kibana passwords (git-ignored)</td></tr>
<tr><td class="m">scripts/lab_endpoints.txt</td><td>the 14 hosts (name, IP, role, command)</td></tr>
<tr><td class="m">models/isoforest.joblib</td><td>the trained UEBA model</td></tr>
<tr><td class="m">data/captures/lab/</td><td>the current capture + Zeek/Suricata logs</td></tr>
<tr><td class="m">data/eval/lab/</td><td>the A/B/C results (report.md, results.json, charts)</td></tr>
</tbody></table></div>
<h3>7.4 &nbsp;Elasticsearch indices — what's stored where</h3>
<div class="scroll"><table><thead><tr><th>Index</th><th>Holds</th><th>Written by</th></tr></thead><tbody>
<tr><td class="m">c2-alerts</td><td>explainable alerts</td><td>AlertWriter</td></tr>
<tr><td class="m">c2-entity-scores</td><td>per-host verdict/confidence/UEBA (all 14)</td><td>ingest_es.py</td></tr>
<tr><td class="m">c2-indicator-scores</td><td>each host × each indicator (heatmap)</td><td>ingest_es.py</td></tr>
<tr><td class="m">c2-eval</td><td>A/B/C metrics</td><td>ingest_es.py</td></tr>
<tr><td class="m">zeek-dns / zeek-ssl / zeek-conn</td><td>raw telemetry</td><td>ingest_es.py</td></tr>
<tr><td class="m">suricata-alerts</td><td>signature hits</td><td>ingest_es.py</td></tr>
</tbody></table></div>
""" + check("<div class='m'>curl -s -k -u elastic:$ELASTIC_PASSWORD 'https://localhost:9200/_cat/indices/c2-*,zeek-*,suricata-*?v&h=index,docs.count'</div>") + "</section>"

P8 = part("p8", 8, "Verify EVERYTHING — a one-shot checklist",
  "Run these top to bottom; each line proves one part of the system is real and working.") + code(
  "cd /home/analysis/dns-https-c2-ueba-detection && source config/secrets.env\n\n"
  "# services up\nsystemctl is-active elasticsearch kibana docker\n"
  "/opt/zeek/bin/zeek --version ; suricata -V\n\n"
  "# 14 hosts up\ndocker ps --format '{{.Names}} {{.Label \"c2lab.role\"}}' | sort\n\n"
  "# get inside a host\ndocker exec ep-dga-alpha sh -c 'echo $(hostname) $(hostname -i)'\n\n"
  "# raw logs exist and are real\nwc -l data/captures/lab/*.log\nhead -1 data/captures/lab/dns.log | python3 -m json.tool\n\n"
  "# UEBA engine: OpenUBA integrated (backend up) with a selectable baseline fallback\nsystemctl is-active openuba-backend ; grep -A1 '^ueba:' config/config.openuba.yaml\n\n"
  "# data is in Elasticsearch\ncurl -s -k -u elastic:$ELASTIC_PASSWORD 'https://localhost:9200/_cat/indices/c2-*?v&h=index,docs.count'\n\n"
  "# the alerts, ranked\ncurl -s -k -u elastic:$ELASTIC_PASSWORD 'https://localhost:9200/c2-alerts/_search?sort=confidence:desc' \\\n"
  "  | python3 -c \"import sys,json;[print(h['_source']['entity'],h['_source']['confidence']) for h in json.load(sys.stdin)['hits']['hits']]\"\n\n"
  "# the A/B/C result\nmake evaluate-lab\n\n"
  "# unit tests\nmake test\n\n"
  "# Kibana up\ncurl -s -k -o /dev/null -w 'kibana %{http_code}\\n' https://localhost:5601/api/status", "checklist") + "</section>"

P9 = part("p9", 9, "The evaluation (A vs B vs C)",
  "How the head-to-head result is computed, and how to reproduce it.") + """
<p>The same real capture is scored three ways against ground truth (we know which hosts are attackers,
from <span class="m">scripts/lab_endpoints.txt</span>):</p>
<ul>
<li><b>A — signatures only:</b> a host is flagged if Suricata raised any alert for it.</li>
<li><b>B — best single indicator:</b> each indicator alone, thresholded; report the best.</li>
<li><b>C — this project:</b> the full correlation + UEBA verdict.</li>
</ul>
<p>For each we compute precision, recall, F1 and false-positive rate. Code:
<span class="m">src/c2detect/eval/lab.py</span>.</p>
<div class="scroll"><table><thead><tr><th>Config</th><th>Precision</th><th>Recall</th><th>F1</th><th>FP rate</th></tr></thead><tbody>
<tr><td>A — signatures</td><td>1.00</td><td>0.38</td><td>0.55</td><td>0.00</td></tr>
<tr><td>B — best single</td><td>1.00</td><td>0.50</td><td>0.67</td><td>0.00</td></tr>
<tr><td><b>C — multi + UEBA</b></td><td><b>1.00</b></td><td><b>1.00</b></td><td><b>1.00</b></td><td><b>0.00</b></td></tr>
</tbody></table></div>
""" + note("key", "Verified with OpenUBA as the UEBA engine, too",
  "The table above is the 14-host lab. Re-running it with OpenUBA driving the anomaly scores "
  "(<span class='m'>config/config.openuba.yaml</span>) gives the <b>same ordering — F1 C=1.00 &gt; B=0.67 "
  "&gt; A=0.55, FPR 0.00</b>. C&gt;B&gt;A does not depend on which UEBA engine runs.") + check("<div class='m'># baseline engine:\nmake evaluate-lab        # prints the three F1 scores\ncat data/eval/lab/report.md\n\n# OpenUBA engine (same result):\nPYTHONPATH=src ./.venv/bin/python -m c2detect.cli evaluate-lab \\\n  --config config/config.openuba.yaml --lab data/captures/lab --out data/eval/lab-openuba</div>") + "</section>"

P10 = part("p10", 10, "Command reference",
  "Every make target and script, one line each.") + """
<div class="scroll"><table><thead><tr><th>Command</th><th>What it does</th></tr></thead><tbody>
<tr><td class="m">make health</td><td>check the whole stack</td></tr>
<tr><td class="m">make lab-up</td><td>create the bridge, resolver, C2, and 14 host containers</td></tr>
<tr><td class="m">make lab-capture</td><td>run all hosts' traffic, capture inline, run Zeek+Suricata</td></tr>
<tr><td class="m">make evaluate-lab</td><td>score A/B/C and write the report</td></tr>
<tr><td class="m">make lab-demo</td><td>everything: hosts → capture → score → push to ES → dashboards</td></tr>
<tr><td class="m">make lab-down</td><td>tear down the containers + helpers</td></tr>
<tr><td class="m">make test</td><td>run the 12 unit tests</td></tr>
<tr><td class="m">python -m c2detect.cli run --config config/config.lab.yaml</td><td>build alerts and push to Elasticsearch</td></tr>
<tr><td class="m">python scripts/ingest_es.py …</td><td>push telemetry + scores to Elasticsearch</td></tr>
<tr><td class="m">python scripts/build_dashboards.py</td><td>(re)create the Kibana dashboards</td></tr>
</tbody></table></div>""" + "</section>"

P11 = part("p11", 11, "FAQ — the doubts you (or examiners) will have",
  "Straight answers to the questions this project attracts.") + """
<p class="q">Q. How many VMs did you host?</p>
<p>One — the Analysis VM. The 14 endpoint hosts are Docker containers on it (no nested virtualization
to run full VMs). Same real per-host traffic and inline capture.</p>
<p class="q">Q. Where is UEBA? Is OpenUBA connected?</p>
<p><b>Yes — OpenUBA is the UEBA engine.</b> Its backend, Postgres and a model-runner container run on
this VM (no Kubernetes/Spark); the adapter <span class="m">openuba_client.py</span> pushes the parsed
features in, trains on benign, runs inference, and reads per-host risk back (calibrated to a 0–1
anomaly). A built-in IsolationForest + z-score stays as a selectable fallback
(<span class="m">ueba.source</span>). A/B/C was re-verified with OpenUBA: F1 C=1.00 &gt; B=0.67 &gt; A=0.55. (Part 5.)</p>
<p class="q">Q. How does the correlation actually happen?</p>
<p>A transparent weighted blend of the UEBA anomaly and the 8 indicator sub-scores, plus additive
boosts for high-signal combinations, giving a 0–1 confidence. Fully worked in Part 6.</p>
<p class="q">Q. How do logs get into Elasticsearch?</p>
<p>Two ways: <span class="m">AlertWriter.index()</span> pushes each alert; <span class="m">ingest_es.py</span>
uses <span class="m">helpers.bulk()</span> for telemetry — both over HTTPS with the elastic password. (Parts 3 &amp; 7.)</p>
<p class="q">Q. Is this real malware?</p>
<p>No — safe simulators that reproduce the behaviours (DGA, tunneling, beaconing, DoH) in an isolated
lab. No real C2, no external targets.</p>
<p class="q">Q. Why do the beacons show "suspicious" not "likely_c2"?</p>
<p>They're still correctly flagged; a pure beacon has fewer corroborating behaviours than a DGA host,
so its confidence (~0.73) is a bit lower than the DGA hosts (~0.90). Honest and correct.</p>
<p class="q">Q. Could a benign host be flagged?</p>
<p>Not in our run — FP rate 0. Correlation needs several behaviours to agree, so one odd behaviour
never crosses the 0.60 threshold. Benign hosts peaked at ~0.41.</p>""" + "</section>"

def g(t, d): return f'<p><b>{t}</b> — {d}</p>'
P12 = part("p12", 12, "Glossary", "Every term, in one line.") + \
  g("C2","the secret channel malware uses to talk to its operator") + \
  g("DNS","the internet's phone book — names → numeric addresses") + \
  g("NXDOMAIN","the DNS answer 'no such name'; bursts hint at DGA") + \
  g("HTTPS/TLS","encrypted web traffic; contents unreadable in transit") + \
  g("SNI","the server name revealed during a TLS handshake") + \
  g("JA3/JA4","a fingerprint of how a client set up its encryption") + \
  g("DoH","DNS-over-HTTPS — DNS lookups hidden inside HTTPS") + \
  g("DGA","malware + controller share a formula producing new domains daily") + \
  g("Beaconing","regular, robotic call-home timing") + \
  g("DNS tunneling","smuggling data inside DNS query names") + \
  g("Indicator","one behaviour reduced to a 0–1 suspicion score") + \
  g("UEBA","learns 'normal' per entity and flags deviations") + \
  g("IsolationForest","an ML method that finds outliers by how easily they separate") + \
  g("z-score","how many standard deviations a value is from the mean") + \
  g("Correlation engine","the glass-box logic that fuses everything into one verdict") + \
  g("Boost","extra confidence when high-signal behaviours co-occur") + \
  g("Signature","a fixed known-bad pattern — the traditional method modern C2 evades") + \
  g("MITRE ATT&CK","a catalogue of attacker techniques; each alert cites its matches") + \
  g("Zeek","turns packets into structured logs") + \
  g("Suricata","signature-based detection engine (our baseline)") + \
  g("Elasticsearch","the database storing alerts, scores, telemetry") + \
  g("Kibana","the dashboard UI over Elasticsearch") + \
  g("Inline capture","watching traffic on its path, so 100% is seen with real host identity") + \
  g("F1 / precision / recall","standard accuracy measures") + "</section>"

HTML = ('<div class="doc">' + HEADER + TOC + P1 + P2 + P3 + P4 + P5 + P6 + P7 + P8 + P9 + P10 + P11 + P12
        + '<footer style="border-top:1px solid var(--line);margin-top:34px;padding-top:18px;color:var(--mut);'
          'font-family:var(--mono);font-size:.8rem">Master reference · github.com/Sushanth2624/dns-https-c2-ueba-detection'
          ' · reproduce: make lab-demo</footer></div>')
OUT.write_text(f"<style>{CSS}</style>\n{HTML}")
print("wrote", OUT, round(len(OUT.read_text())/1024), "KB")
