#!/usr/bin/env python3
"""Assemble the professional architecture & data-flow document (self-contained HTML artifact)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
shots = json.load(open(ROOT / "data/tmp/doc_shots.json"))


def fig(name, cap):
    return (f'<figure class="shot"><img alt="{cap}" src="data:image/png;base64,{shots[name]}">'
            f'<figcaption>{cap}</figcaption></figure>')


# ---------- inline SVG: architecture ----------
ARCH_SVG = """
<svg viewBox="0 0 1000 430" role="img" aria-label="System architecture" class="diagram">
  <defs>
    <marker id="ah" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="var(--edge)"/></marker>
    <style>
      .lyr{fill:var(--card);stroke:var(--line);stroke-width:1.5;rx:12}
      .lbl{fill:var(--muted);font:600 12px var(--mono);letter-spacing:.06em;text-transform:uppercase}
      .node{fill:var(--chip);stroke:var(--line);stroke-width:1}
      .nt{fill:var(--ink);font:600 13px var(--sans)}
      .ns{fill:var(--muted);font:11px var(--sans)}
      .flow{stroke:var(--edge);stroke-width:2;fill:none;marker-end:url(#ah)}
    </style>
  </defs>
  <!-- layer frames -->
  <rect class="lyr" x="12" y="60" width="188" height="340" rx="12"/>
  <rect class="lyr" x="236" y="60" width="230" height="340" rx="12"/>
  <rect class="lyr" x="502" y="60" width="230" height="340" rx="12"/>
  <rect class="lyr" x="768" y="60" width="220" height="340" rx="12"/>
  <text class="lbl" x="106" y="44" text-anchor="middle">Endpoints</text>
  <text class="lbl" x="351" y="44" text-anchor="middle">Capture &amp; Sensors</text>
  <text class="lbl" x="617" y="30" text-anchor="middle">Detection engine</text>
  <text class="lbl" x="617" y="48" text-anchor="middle">(the contribution)</text>
  <text class="lbl" x="878" y="44" text-anchor="middle">Store &amp; Visualize</text>

  <!-- endpoints -->
  <rect class="node" x="34" y="86"  width="144" height="42" rx="8"/>
  <text class="nt" x="106" y="104" text-anchor="middle">6 benign hosts</text>
  <text class="ns" x="106" y="120" text-anchor="middle">normal DNS / HTTPS</text>
  <rect class="node" x="34" y="150" width="144" height="42" rx="8" style="stroke:var(--red)"/>
  <text class="nt" x="106" y="168" text-anchor="middle">2 DGA · 2 tunnel</text>
  <text class="ns" x="106" y="184" text-anchor="middle">random / long names</text>
  <rect class="node" x="34" y="214" width="144" height="42" rx="8" style="stroke:var(--red)"/>
  <text class="nt" x="106" y="232" text-anchor="middle">2 beacon</text>
  <text class="ns" x="106" y="248" text-anchor="middle">regular TLS call-home</text>
  <rect class="node" x="34" y="278" width="144" height="42" rx="8" style="stroke:var(--red)"/>
  <text class="nt" x="106" y="296" text-anchor="middle">2 DoH</text>
  <text class="ns" x="106" y="312" text-anchor="middle">DNS over HTTPS</text>
  <text class="ns" x="106" y="354" text-anchor="middle">each a real host,</text>
  <text class="ns" x="106" y="370" text-anchor="middle">own IP + fingerprint</text>

  <!-- sensors (Analysis VM) -->
  <rect class="node" x="258" y="86"  width="186" height="40" rx="8" style="stroke:var(--accent)"/>
  <text class="nt" x="351" y="103" text-anchor="middle">Inline gateway + resolver</text>
  <text class="ns" x="351" y="118" text-anchor="middle">this VM routes all traffic</text>
  <rect class="node" x="258" y="140" width="186" height="36" rx="8"/>
  <text class="nt" x="351" y="163" text-anchor="middle">tcpdump — 100% inline</text>
  <rect class="node" x="258" y="192" width="88" height="52" rx="8"/>
  <text class="nt" x="302" y="214" text-anchor="middle">Zeek</text>
  <text class="ns" x="302" y="230" text-anchor="middle">dns/ssl/conn</text>
  <rect class="node" x="356" y="192" width="88" height="52" rx="8"/>
  <text class="nt" x="400" y="214" text-anchor="middle">Suricata</text>
  <text class="ns" x="400" y="230" text-anchor="middle">signatures</text>
  <rect class="node" x="258" y="300" width="186" height="40" rx="8" style="stroke:var(--red)"/>
  <text class="nt" x="351" y="317" text-anchor="middle">local C2 (beacon target)</text>
  <text class="ns" x="351" y="332" text-anchor="middle">openssl TLS :8443</text>

  <!-- detection engine -->
  <rect class="node" x="524" y="86"  width="186" height="52" rx="8"/>
  <text class="nt" x="617" y="108" text-anchor="middle">8 behavioral indicators</text>
  <text class="ns" x="617" y="124" text-anchor="middle">entropy · DGA · NXDOMAIN · beacon</text>
  <rect class="node" x="524" y="152" width="186" height="52" rx="8"/>
  <text class="nt" x="617" y="174" text-anchor="middle">UEBA anomaly</text>
  <text class="ns" x="617" y="190" text-anchor="middle">IsolationForest + z-score</text>
  <rect class="node" x="524" y="218" width="186" height="52" rx="8" style="stroke:var(--accent)"/>
  <text class="nt" x="617" y="240" text-anchor="middle">Correlation (glass-box)</text>
  <text class="ns" x="617" y="256" text-anchor="middle">weighted fusion + boosts</text>
  <rect class="node" x="524" y="284" width="186" height="52" rx="8" style="stroke:var(--accent)"/>
  <text class="nt" x="617" y="306" text-anchor="middle">Explainable alert</text>
  <text class="ns" x="617" y="322" text-anchor="middle">verdict · MITRE · actions</text>

  <!-- store/viz -->
  <rect class="node" x="790" y="120" width="176" height="52" rx="8"/>
  <text class="nt" x="878" y="142" text-anchor="middle">Elasticsearch</text>
  <text class="ns" x="878" y="158" text-anchor="middle">alerts · scores · telemetry</text>
  <rect class="node" x="790" y="230" width="176" height="52" rx="8" style="stroke:var(--accent)"/>
  <text class="nt" x="878" y="252" text-anchor="middle">Kibana</text>
  <text class="ns" x="878" y="268" text-anchor="middle">3 dashboards</text>

  <!-- flows -->
  <path class="flow" d="M200,235 L232,235"/>
  <path class="flow" d="M466,235 L498,235"/>
  <path class="flow" d="M710,240 L788,180 L788,160"/>
  <path class="flow" d="M878,172 L878,226"/>
</svg>
"""

# ---------- inline SVG: data flow ----------
FLOW_SVG = """
<svg viewBox="0 0 1000 190" role="img" aria-label="Data flow" class="diagram">
  <defs>
    <marker id="ah2" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="var(--edge)"/></marker>
    <style>
      .st{fill:var(--card);stroke:var(--line);stroke-width:1.5}
      .stt{fill:var(--ink);font:600 13px var(--sans)}
      .sts{fill:var(--muted);font:11px var(--mono)}
      .fl{stroke:var(--edge);stroke-width:2;fill:none;marker-end:url(#ah2)}
    </style>
  </defs>
""" + "".join(
    f'<rect class="st" x="{x}" y="60" width="150" height="66" rx="10" '
    f'style="stroke:{clr}"/><text class="stt" x="{x+75}" y="88" text-anchor="middle">{t}</text>'
    f'<text class="sts" x="{x+75}" y="108" text-anchor="middle">{s}</text>'
    for (x, t, s, clr) in [
        (16,  "Packets", "tcpdump", "var(--line)"),
        (183, "Telemetry", "Zeek + Suricata", "var(--line)"),
        (350, "Features", "8 sub-scores / host", "var(--line)"),
        (517, "Anomaly", "UEBA score", "var(--line)"),
        (684, "Verdict", "correlation", "var(--accent)"),
        (851, "Alert", "→ ES → Kibana", "var(--accent)"),
    ]
) + "".join(
    f'<path class="fl" d="M{x},93 L{x+17},93"/>' for x in (166, 333, 500, 667, 834)
) + "</svg>"

# ---------- results chart (single-series bars, winner emphasized, direct-labeled) ----------
RESULTS = [("A — signature only", 0.55, "var(--muted)"),
           ("B — best single indicator", 0.67, "var(--muted)"),
           ("C — multi-indicator + UEBA", 1.00, "var(--accent)")]
bars = ""
for i, (label, f1, clr) in enumerate(RESULTS):
    y = 20 + i * 62
    w = f1 * 620
    bars += (f'<text x="0" y="{y+20}" class="rlabel">{label}</text>'
             f'<rect x="300" y="{y}" width="620" height="34" rx="6" fill="var(--track)"/>'
             f'<rect x="300" y="{y}" width="{w:.0f}" height="34" rx="6" fill="{clr}"/>'
             f'<text x="{300+w-10:.0f}" y="{y+23}" class="rval">{f1:.2f}</text>')
RESULTS_SVG = (f'<svg viewBox="0 0 940 210" role="img" aria-label="F1 score by configuration" '
              f'class="diagram"><style>.rlabel{{fill:var(--ink);font:600 13px var(--sans)}}'
              f'.rval{{fill:#fff;font:700 13px var(--mono);text-anchor:end}}</style>{bars}'
              f'<text x="300" y="205" class="sts" style="fill:var(--muted);font:11px var(--mono)">'
              f'F1 score (0–1) · higher is better · zero false positives for C</text></svg>')

INDICATORS = [
    ("Domain entropy", "Random-looking domains → DGA / tunneling", "T1568.002"),
    ("DGA structure", "Length + digits + few vowels", "T1568.002"),
    ("NXDOMAIN rate", "Bursts of failed lookups", "T1568.002"),
    ("Query length", "Long / deep names carry data", "T1071.004"),
    ("Beacon regularity", "Low-jitter call-home timing (gap-robust)", "T1071.001 · T1571"),
    ("JA3/JA4 rarity", "TLS fingerprint unseen in baseline", "T1573"),
    ("DoH endpoint", "DNS hidden inside HTTPS", "T1071.004 · T1572"),
    ("Session shape", "Small, steady, long-lived flows", "T1071.001"),
]
ind_rows = "".join(
    f"<tr><td><b>{n}</b></td><td>{d}</td><td class='mono'>{m}</td></tr>" for n, d, m in INDICATORS)

HTML = f"""<main>
<header class="hero">
  <div class="eyebrow">Capstone 2 · Behavioral C2 detection · architecture &amp; data flow</div>
  <h1>Catching command-and-control that hides inside normal DNS &amp; HTTPS</h1>
  <p class="deck">Modern malware talks to its operators through the same DNS and encrypted web
  traffic your business depends on. Signatures can't see it. This system detects it by
  <b>behaviour</b> — fusing many weak signals with user-and-entity behaviour analytics (UEBA) into a
  single, explainable verdict — and proves the approach beats signatures head-to-head.</p>
  <div class="hero-stats">
    <div><span class="hs-num" style="color:var(--accent)">100%</span><span class="hs-l">of attacks caught (F1 = 1.00)</span></div>
    <div><span class="hs-num" style="color:var(--good)">0</span><span class="hs-l">false positives</span></div>
    <div><span class="hs-num">14</span><span class="hs-l">real hosts, live capture</span></div>
    <div><span class="hs-num">8</span><span class="hs-l">behavioral indicators + UEBA</span></div>
  </div>
</header>

<nav class="toc">
  <a href="#problem">The problem</a><a href="#idea">The idea</a><a href="#arch">Architecture</a>
  <a href="#flow">Data flow</a><a href="#method">How detection works</a>
  <a href="#results">Results</a><a href="#dash">Dashboards</a>
</nav>

<section id="problem">
  <div class="eyebrow">01 — The core problem</div>
  <h2>Why command-and-control is so hard to see</h2>
  <p>After malware lands on a machine, it needs to phone home — to receive commands and exfiltrate
  data. That channel is called <b>command-and-control (C2)</b>. Attackers deliberately hide it inside
  traffic every network already allows:</p>
  <ul class="cards">
    <li><h3>Encrypted web (HTTPS)</h3>The payload is inside TLS, so the packet contents are invisible.
      A firewall sees "a host visited a website," nothing more.</li>
    <li><h3>DNS &amp; DNS-over-HTTPS</h3>DNS is required for everything, so it's rarely blocked. Malware
      tunnels data through it — or hides it in DoH, where even the resolver can't inspect it.</li>
    <li><h3>Looks legitimate</h3>Low-and-slow beacons, domains that rotate every day (DGA), traffic
      shaped to resemble a browser. There is no fixed "bad string" to match.</li>
  </ul>
  <p class="pull">Signature and IOC matching answer "have I seen this exact bad thing before?"
  Against traffic that is encrypted, ever-changing, and disguised as normal, the answer is almost
  always no — so the attack sails straight through.</p>
  <p>The defensive shift the security industry has made is from <i>signatures</i> to <i>behaviour</i>:
  not "is this a known-bad string" but <b>"does this host behave like it is talking to a
  controller?"</b> A single behaviour (say, one odd DNS lookup) is noisy and easy to dismiss. The
  insight of this project is that <b>several weak behavioural signals, correlated together and
  baselined against normal, become a strong and defensible one.</b></p>
</section>

<section id="idea">
  <div class="eyebrow">02 — The idea</div>
  <h2>Many weak signals → one explainable verdict</h2>
  <p>The system watches every host for eight independent behaviours, asks a UEBA model how abnormal
  each host is versus a learned baseline of "normal," then a <b>glass-box correlation engine</b>
  fuses everything into a confidence score. Crucially, every verdict is <b>explainable</b>: it names
  which behaviours fired, why, the matching MITRE ATT&amp;CK techniques, and what the analyst should
  do next — no black box.</p>
  <div class="idea-grid">
    <div><span class="ig-n">1</span><b>Observe behaviour</b><p>8 indicators per host from real network telemetry.</p></div>
    <div><span class="ig-n">2</span><b>Baseline with UEBA</b><p>How far is this host from normal?</p></div>
    <div><span class="ig-n">3</span><b>Correlate</b><p>Weighted fusion + rules; needs corroboration.</p></div>
    <div><span class="ig-n">4</span><b>Explain</b><p>Verdict, evidence, MITRE, next steps.</p></div>
  </div>
</section>

<section id="arch">
  <div class="eyebrow">03 — Architecture &amp; infrastructure</div>
  <h2>How the lab is built</h2>
  <p>The environment mirrors a real enterprise segment on a single analysis machine. Endpoints are
  isolated hosts on a lab network; the analysis VM is their <b>gateway and DNS resolver</b>, so all
  their traffic passes through it and is captured <b>100% inline</b> — every host keeps its own real
  IP address and TLS fingerprint. Sensors turn packets into structured telemetry; the detection
  engine scores it; results land in Elasticsearch and are shown in Kibana.</p>
  {ARCH_SVG}
  <p class="note">Because there is no nested virtualization on the host, the endpoints are lightweight
  containers rather than full VMs — but the network path (endpoint → inline gateway → sensors) and the
  per-host telemetry are exactly as a multi-VM lab would produce.</p>
</section>

<section id="flow">
  <div class="eyebrow">04 — Data flow</div>
  <h2>From packet to explained alert</h2>
  <p>One continuous path carries a packet all the way to a ranked, explained alert on a dashboard.</p>
  {FLOW_SVG}
  <ol class="flowlist">
    <li><b>Capture.</b> tcpdump records every packet crossing the lab bridge.</li>
    <li><b>Sensors.</b> Zeek writes structured logs (DNS queries, TLS SNI + JA3, connections);
      Suricata runs the signature baseline.</li>
    <li><b>Features.</b> For each host, the eight indicators are computed as 0–1 sub-scores.</li>
    <li><b>UEBA.</b> An IsolationForest + z-score model scores how anomalous the host is vs. benign.</li>
    <li><b>Correlate &amp; explain.</b> Weighted fusion + boost rules produce a confidence; if it
      crosses the threshold, an explainable alert is built (verdict, contributing indicators, MITRE,
      recommended actions).</li>
    <li><b>Store &amp; visualize.</b> Alerts, per-host scores, and raw telemetry go to Elasticsearch,
      rendered in three Kibana dashboards.</li>
  </ol>
</section>

<section id="method">
  <div class="eyebrow">05 — How detection works</div>
  <h2>The eight behaviours it watches</h2>
  <p>Each maps to real attacker tradecraft and to MITRE ATT&amp;CK. No single row is conclusive —
  <b>the correlation across rows is the detector.</b></p>
  <div class="scroll"><table class="ind">
    <thead><tr><th>Indicator</th><th>What it catches</th><th>MITRE ATT&amp;CK</th></tr></thead>
    <tbody>{ind_rows}</tbody>
  </table></div>
  <p><b>Why false positives stay near zero:</b> a benign host with, say, high-entropy CDN hostnames
  trips one indicator — but correlation requires corroboration and a high UEBA anomaly, so it never
  reaches the alert threshold. Attack hosts trip several indicators at once and are baselined as
  clearly abnormal.</p>
</section>

<section id="results">
  <div class="eyebrow">06 — Results</div>
  <h2>Behaviour + UEBA beats signatures, head-to-head</h2>
  <p>The same real capture (14 hosts, 6 benign + 8 attack) was scored three ways: <b>A</b> signatures
  only (Suricata), <b>B</b> the best single behavioral indicator, and <b>C</b> the full
  multi-indicator + UEBA system. Higher F1 = better overall accuracy.</p>
  {RESULTS_SVG}
  <p class="pull">C detects <b>all four</b> techniques (DGA, tunneling, beaconing, DoH) with
  <b>zero false positives</b>. Signatures structurally miss DGA and beaconing — there is no static
  string to match — so they top out at F1 0.55. Every single indicator alone misses at least one
  technique. Only the correlation catches everything.</p>
</section>

<section id="dash">
  <div class="eyebrow">07 — The dashboards</div>
  <h2>What the analyst and the CISO see</h2>
  <p>Three Kibana dashboards read the live indices. Every panel below is a real screenshot of the
  running system.</p>
  <h3>Executive overview</h3>
  <p class="cap">Coverage, threats, attack mix, MITRE techniques, and the A/B/C detection-quality
  comparison — the one-screen view for leadership.</p>
  {fig('exec','Executive overview dashboard')}
  <h3>Threat detail</h3>
  <p class="cap">The indicator heatmap shows exactly <i>which</i> behaviours fired for each host —
  attack hosts light up red on the relevant indicators, benign hosts stay cool.</p>
  {fig('threat','Threat detail dashboard with indicator heatmap')}
  <h3>Network telemetry</h3>
  <p class="cap">Raw evidence: DNS and NXDOMAIN over time, the C2 server names, TLS client
  fingerprints, and signature hits.</p>
  {fig('telemetry','Network telemetry dashboard')}
</section>

<footer>
  <div><b>Reproduce</b> · <span class="mono">make lab-demo</span> — build the 14 hosts, capture
  inline, score A/B/C, load Elasticsearch, publish dashboards.</div>
  <div>github.com/Sushanth2624/dns-https-c2-ueba-detection · Kibana https://172.16.242.14:5601</div>
</footer>
</main>"""

CSS = """
:root{
  --bg:#f6f8fc; --card:#ffffff; --chip:#f1f5f9; --ink:#0c1526; --muted:#5a6b82; --line:#dbe3ef;
  --accent:#0e8fa8; --good:#16a34a; --red:#dc2626; --amber:#b45309; --edge:#94a6bd;
  --track:#e6edf6;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#0a0f1a; --card:#0f1626; --chip:#141d30; --ink:#e7eef8; --muted:#8598b2; --line:#213048;
  --accent:#2dd4bf; --good:#3fd07a; --red:#f26d6d; --amber:#e0a44a; --edge:#4a5d78; --track:#1a2740;
}}
:root[data-theme="dark"]{
  --bg:#0a0f1a; --card:#0f1626; --chip:#141d30; --ink:#e7eef8; --muted:#8598b2; --line:#213048;
  --accent:#2dd4bf; --good:#3fd07a; --red:#f26d6d; --amber:#e0a44a; --edge:#4a5d78; --track:#1a2740;
}
:root[data-theme="light"]{
  --bg:#f6f8fc; --card:#ffffff; --chip:#f1f5f9; --ink:#0c1526; --muted:#5a6b82; --line:#dbe3ef;
  --accent:#0e8fa8; --good:#16a34a; --red:#dc2626; --amber:#b45309; --edge:#94a6bd; --track:#e6edf6;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.62;
  -webkit-font-smoothing:antialiased}
main{max-width:960px;margin:0 auto;padding:clamp(22px,4vw,60px)}
.mono{font-family:var(--mono)}
.eyebrow{font-family:var(--mono);font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;
  color:var(--accent);margin-bottom:12px}
h1{font-size:clamp(1.9rem,5vw,3.1rem);line-height:1.04;letter-spacing:-.025em;margin:0 0 18px;
  text-wrap:balance}
h2{font-size:clamp(1.4rem,3vw,1.9rem);letter-spacing:-.02em;margin:.2em 0 .5em;text-wrap:balance}
h3{font-size:1.08rem;margin:1.6em 0 .3em;letter-spacing:-.01em}
p{margin:0 0 1em;max-width:72ch}
b{color:var(--ink);font-weight:650}
.hero{border-bottom:1px solid var(--line);padding-bottom:34px;margin-bottom:8px}
.deck{font-size:1.12rem;color:var(--muted);max-width:70ch}
.deck b{color:var(--ink)}
.hero-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:26px}
.hero-stats>div{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.hs-num{display:block;font:700 2rem/1 var(--mono)}
.hs-l{display:block;font-size:.8rem;color:var(--muted);margin-top:6px}
.toc{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;gap:4px;padding:12px 0;margin:8px 0 10px;
  background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line)}
.toc a{font-family:var(--mono);font-size:.76rem;color:var(--muted);text-decoration:none;
  padding:5px 10px;border-radius:7px}
.toc a:hover{color:var(--accent);background:var(--chip)}
section{padding:34px 0;border-bottom:1px solid var(--line)}
.diagram{width:100%;height:auto;display:block;margin:18px 0;background:var(--card);
  border:1px solid var(--line);border-radius:14px;padding:14px}
.cards{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  gap:14px;margin:18px 0}
.cards li{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;
  color:var(--muted);font-size:.94rem}
.cards h3{margin:0 0 6px;color:var(--ink);font-size:1rem}
.pull{border-left:3px solid var(--accent);padding:2px 0 2px 18px;font-size:1.08rem;color:var(--ink);
  margin:18px 0}
.idea-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-top:18px}
.idea-grid>div{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.ig-n{display:inline-flex;width:26px;height:26px;align-items:center;justify-content:center;
  border-radius:50%;background:var(--accent);color:#fff;font:700 13px var(--mono);margin-bottom:8px}
.idea-grid b{display:block;margin-bottom:4px}
.idea-grid p{font-size:.88rem;color:var(--muted);margin:0}
.flowlist,.cards{margin-top:16px}
.flowlist{padding-left:20px;color:var(--muted)}
.flowlist li{margin:.4em 0}
.flowlist b{color:var(--ink)}
.note{font-size:.9rem;color:var(--muted);background:var(--chip);border-radius:10px;padding:12px 16px}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--card);margin:16px 0}
table.ind{border-collapse:collapse;width:100%;font-size:.92rem}
table.ind th,table.ind td{padding:11px 16px;text-align:left;border-bottom:1px solid var(--line);
  vertical-align:top}
table.ind thead th{font:600 .72rem var(--mono);text-transform:uppercase;letter-spacing:.06em;
  color:var(--muted)}
table.ind td.mono{font-family:var(--mono);font-size:.82rem;color:var(--accent);white-space:nowrap}
table.ind tbody tr:last-child td{border-bottom:none}
.cap{font-size:.9rem;color:var(--muted);margin-bottom:10px}
.shot{margin:10px 0 8px;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--card)}
.shot img{display:block;width:100%;height:auto}
.shot figcaption{font-size:.8rem;color:var(--muted);padding:10px 14px;border-top:1px solid var(--line);
  font-family:var(--mono)}
footer{padding-top:26px;display:flex;flex-direction:column;gap:8px;font-size:.85rem;color:var(--muted)}
footer .mono{color:var(--accent)}
@media(max-width:620px){.hero-stats{grid-template-columns:repeat(2,1fr)}}
"""

out = ROOT / "data/tmp/architecture-doc.html"
out.write_text(f"<style>{CSS}</style>\n{HTML}")
print("wrote", out, len(out.read_text()), "bytes")
