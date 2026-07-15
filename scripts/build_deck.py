#!/usr/bin/env python3
"""Build a self-contained, keyboard-navigable slide deck for the demo/viva."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
shots = json.load(open(ROOT / "data/tmp/doc_shots.json"))
OUT = ROOT / "data/tmp/deck.html"


def img(name):
    return f'data:image/png;base64,{shots[name]}'


ARCH = """<svg viewBox="0 0 1000 340" class="dsvg"><defs><marker id="m1" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0L9,4.5L0,9z" fill="var(--edge)"/></marker><style>.lyr{fill:var(--card);stroke:var(--line);stroke-width:1.5}.nd{fill:var(--chip);stroke:var(--line)}.t{fill:var(--ink);font:600 16px system-ui}.s{fill:var(--mut);font:12px system-ui}.lb{fill:var(--acc);font:700 13px ui-monospace;letter-spacing:.06em;text-transform:uppercase}.f{stroke:var(--edge);stroke-width:2.5;fill:none;marker-end:url(#m1)}</style></defs>
<rect class="lyr" x="10" y="50" width="215" height="270" rx="12"/><rect class="lyr" x="255" y="50" width="230" height="270" rx="12"/><rect class="lyr" x="515" y="50" width="230" height="270" rx="12"/><rect class="lyr" x="775" y="50" width="215" height="270" rx="12"/>
<text class="lb" x="117" y="35" text-anchor="middle">Hosts</text><text class="lb" x="370" y="35" text-anchor="middle">Sensors</text><text class="lb" x="630" y="35" text-anchor="middle">Detection engine</text><text class="lb" x="882" y="35" text-anchor="middle">Store + view</text>
<rect class="nd" x="30" y="80" width="175" height="46" rx="8"/><text class="t" x="117" y="102" text-anchor="middle">6 benign</text><text class="s" x="117" y="119" text-anchor="middle">normal traffic</text>
<rect class="nd" x="30" y="150" width="175" height="46" rx="8" style="stroke:var(--red)"/><text class="t" x="117" y="172" text-anchor="middle">8 attackers</text><text class="s" x="117" y="189" text-anchor="middle">DGA·tunnel·beacon·DoH</text>
<rect class="nd" x="30" y="220" width="175" height="80" rx="8" style="stroke:var(--acc)"/><text class="t" x="117" y="250" text-anchor="middle">14 real hosts</text><text class="s" x="117" y="270" text-anchor="middle">own IP each</text>
<rect class="nd" x="275" y="90" width="190" height="46" rx="8" style="stroke:var(--acc)"/><text class="t" x="370" y="112" text-anchor="middle">inline gateway</text><text class="s" x="370" y="129" text-anchor="middle">tcpdump — 100%</text>
<rect class="nd" x="275" y="160" width="90" height="60" rx="8"/><text class="t" x="320" y="188" text-anchor="middle">Zeek</text><text class="s" x="320" y="206" text-anchor="middle">logs</text>
<rect class="nd" x="375" y="160" width="90" height="60" rx="8"/><text class="t" x="420" y="188" text-anchor="middle">Suricata</text><text class="s" x="420" y="206" text-anchor="middle">signatures</text>
<rect class="nd" x="535" y="72" width="190" height="52" rx="8"/><text class="t" x="630" y="103" text-anchor="middle">8 indicators</text>
<rect class="nd" x="535" y="132" width="190" height="52" rx="8"/><text class="t" x="630" y="163" text-anchor="middle">UEBA anomaly</text>
<rect class="nd" x="535" y="192" width="190" height="52" rx="8" style="stroke:var(--acc)"/><text class="t" x="630" y="223" text-anchor="middle">correlation</text>
<rect class="nd" x="535" y="252" width="190" height="52" rx="8" style="stroke:var(--acc)"/><text class="t" x="630" y="283" text-anchor="middle">explainable alert</text>
<rect class="nd" x="795" y="110" width="175" height="52" rx="8"/><text class="t" x="882" y="141" text-anchor="middle">Elasticsearch</text>
<rect class="nd" x="795" y="210" width="175" height="52" rx="8" style="stroke:var(--acc)"/><text class="t" x="882" y="241" text-anchor="middle">Kibana</text>
<path class="f" d="M225,185 L251,185"/><path class="f" d="M485,185 L511,185"/><path class="f" d="M745,180 L793,150 L793,136"/><path class="f" d="M882,162 L882,206"/></svg>"""

FLOW = """<svg viewBox="0 0 1000 120" class="dsvg"><defs><marker id="m2" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0L9,4.5L0,9z" fill="var(--edge)"/></marker><style>.b{fill:var(--card);stroke:var(--line);stroke-width:1.5}.t{fill:var(--ink);font:600 15px system-ui}.s{fill:var(--mut);font:11px ui-monospace}.f{stroke:var(--edge);stroke-width:2.5;fill:none;marker-end:url(#m2)}</style></defs>""" + "".join(f'<rect class="b" x="{x}" y="30" width="150" height="58" rx="10" style="stroke:{c}"/><text class="t" x="{x+75}" y="58" text-anchor="middle">{t}</text><text class="s" x="{x+75}" y="76" text-anchor="middle">{s}</text>' for x,t,s,c in [(15,"Packets","tcpdump","var(--line)"),(182,"Telemetry","Zeek/Suricata","var(--line)"),(349,"Features","8 scores","var(--line)"),(516,"Anomaly","UEBA","var(--line)"),(683,"Verdict","correlate","var(--acc)"),(850,"Alert","→ ES → Kibana","var(--acc)")]) + "".join(f'<path class="f" d="M{x},59 L{x+17},59"/>' for x in (165,332,499,666,833)) + "</svg>"

# results big bars
_R=[("A · signatures",0.55,"var(--mut2)"),("B · best single",0.67,"var(--mut2)"),("C · multi + UEBA",1.00,"var(--acc)")]
_rb=""
for i,(l,f,c) in enumerate(_R):
    y=10+i*70; w=f*680
    _rb+=f'<text x="0" y="{y+30}" style="fill:var(--ink);font:700 22px system-ui">{l}</text><rect x="300" y="{y}" width="680" height="46" rx="8" fill="var(--track)"/><rect x="300" y="{y}" width="{w:.0f}" height="46" rx="8" fill="{c}"/><text x="{300+w-14:.0f}" y="{y+32}" style="fill:#fff;font:800 24px ui-monospace;text-anchor:end">{f:.2f}</text>'
RESULTS=f'<svg viewBox="0 0 1000 230" class="dsvg">{_rb}</svg>'

SLIDES = []
def s(cls, body): SLIDES.append(f'<section class="slide {cls}">{body}</section>')

# 1 title
s("center title", """<div class="kick">Capstone 2 · MTech Cyber Security · REVA (RACE)</div>
<h1>Behavioral Detection of Hidden<br>DNS/HTTPS Command-and-Control</h1>
<p class="lead">Catching malware that hides its secret communications inside ordinary web &amp; DNS traffic —
using multi-indicator correlation and UEBA.</p>
<div class="by">Sushanth Sridhar · R24TF007</div>""")

# 2 problem
s("", """<h2>The problem</h2>
<p class="big">Malware must secretly <b>phone home</b> to its operator — <span class="hl">command-and-control (C2)</span>.
Attackers hide it inside the traffic every network allows.</p>
<div class="cols3">
<div class="c"><div class="ci">🔒</div><b>Encrypted HTTPS</b><p>payload invisible</p></div>
<div class="c"><div class="ci">📖</div><b>DNS &amp; DoH</b><p>never blocked</p></div>
<div class="c"><div class="ci">🎭</div><b>Looks normal</b><p>no fixed bad string</p></div>
</div>""")

# 3 why signatures fail
s("", """<h2>Why signatures fail</h2>
<p class="big">Traditional detection matches <b>known-bad patterns</b>. Modern C2 defeats it by design:</p>
<ul class="checks bad">
<li>rides encrypted TLS — payload unreadable</li>
<li>rotates domains daily (DGA) — blocklists useless</li>
<li>low-and-slow beacons — blends into noise</li>
<li>tunnels through DoH — resolver can't inspect</li>
</ul>
<p class="pull">The shift: from "is this a known-bad string?" to <span class="hl">"does this host behave like it's talking to a controller?"</span></p>""")

# 4 the idea
s("", """<h2>The idea</h2>
<p class="big">Many weak behavioural signals → one <b>explainable</b> verdict.</p>
<div class="cols4">
<div class="c"><div class="n">1</div><b>Observe</b><p>8 behaviours per host</p></div>
<div class="c"><div class="n">2</div><b>Baseline</b><p>UEBA: how abnormal?</p></div>
<div class="c"><div class="n">3</div><b>Correlate</b><p>glass-box fusion</p></div>
<div class="c"><div class="n">4</div><b>Explain</b><p>verdict · MITRE · actions</p></div>
</div>
<p class="pull">No single clue is enough — <span class="hl">several suspicious behaviours together</span> is the detector.</p>""")

# 5 attacks
s("", """<h2>Four hidden C2 techniques we detect</h2>
<div class="cols4 tall">
<div class="c"><b class="r">DGA</b><p>daily-changing random domains → bursts of failed lookups</p></div>
<div class="c"><b class="r">DNS tunneling</b><p>stolen data smuggled inside long DNS names</p></div>
<div class="c"><b class="r">Beaconing</b><p>robotic, clockwork call-home timing</p></div>
<div class="c"><b class="r">DoH C2</b><p>DNS lookups hidden inside HTTPS</p></div>
</div>""")

# 6 architecture
s("", f"""<h2>Architecture</h2>{ARCH}
<p class="cap">One machine. 14 host containers route through it, so sensors see 100% inline with real per-host identity.</p>""")

# 7 dataflow
s("", f"""<h2>Data flow — packet to explained alert</h2>{FLOW}
<p class="cap">One continuous path: raw packets → structured logs → behaviour scores → UEBA → correlation → alert → dashboards.</p>""")

# 8 indicators
s("", """<h2>The eight behaviours</h2>
<div class="grid8">
<div class="g">Domain entropy</div><div class="g">DGA structure</div><div class="g">NXDOMAIN rate</div><div class="g">Query length</div>
<div class="g">Beacon regularity</div><div class="g">JA3 rarity</div><div class="g">DoH endpoint</div><div class="g">Session shape</div>
</div>
<p class="pull">Each is a 0–1 score mapped to <span class="hl">MITRE ATT&amp;CK</span>. The correlation across them is the contribution.</p>""")

# 9 correlation
s("", """<h2>Glass-box correlation — the contribution</h2>
<div class="formula">
confidence = <span class="hl">ueba_weight · anomaly</span> + (1−w) · Σ wᵢ·behaviourᵢ + <span class="acc">boosts</span>
</div>
<ul class="checks">
<li><b>Transparent:</b> every weight is inspectable and reported — no black box</li>
<li><b>Boosts:</b> extra confidence when high-signal behaviours co-occur (e.g. beacon + rare TLS)</li>
<li><b>Explainable:</b> we can say exactly <i>why</i> any host scored what it did</li>
</ul>""")

# 10 alert
s("", """<h2>Every verdict is explained</h2>
<div class="alert">
<div class="ah"><span class="verdict">likely_c2</span><span class="conf">confidence 0.90</span><span class="ent">10.50.0.21</span></div>
<div class="ab"><b>Why:</b> domains near-random (DGA) · elevated failed lookups (NXDOMAIN) · generated structure</div>
<div class="ab"><b>MITRE:</b> <span class="mono">T1568.002 · T1071.004</span></div>
<div class="ab"><b>Do:</b> hunt the domain across hosts · pre-block predicted domains · block the seed zone</div>
</div>
<p class="cap">Auditable, analyst-ready — not a black-box score.</p>""")

# 11 lab
s("", """<h2>The lab — real, separate hosts</h2>
<div class="cols3">
<div class="c"><div class="stat">14</div><b>hosts</b><p>6 benign · 8 attack</p></div>
<div class="c"><div class="stat">100%</div><b>inline capture</b><p>real per-host IP</p></div>
<div class="c"><div class="stat">4</div><b>techniques</b><p>DGA·tunnel·beacon·DoH</p></div>
</div>
<p class="pull">Containers stand in for endpoint VMs (no nested virtualization) — <span class="hl">same real per-host telemetry.</span></p>""")

# 12 RESULTS
s("center", f"""<h2>The result — A vs B vs C</h2>
<p class="big" style="margin-bottom:10px">Same real traffic, scored three ways. F1 = overall accuracy.</p>
{RESULTS}
<p class="pull">C caught <b>all four techniques</b> with <span class="hl">zero false positives</span> — beating signatures and any single behaviour. <b>C &gt; B &gt; A.</b></p>""")

# 13 dashboard exec
s("shot", f"""<h2>Executive dashboard</h2><img src="{img('exec')}" alt="executive dashboard"/>""")
# 14 dashboard threat
s("shot", f"""<h2>Threat detail — which behaviour fired per host</h2><img src="{img('threat')}" alt="threat heatmap"/>""")

# 15 contribution
s("", """<h2>Contribution &amp; novelty</h2>
<ul class="checks">
<li>Fuses <b>multiple</b> behavioural indicators — not one in isolation</li>
<li>Adds a <b>UEBA</b> baseline of normal per host</li>
<li>Produces <b>explainable</b>, MITRE-mapped, actionable alerts (glass-box)</li>
<li>Benchmarks <b>head-to-head vs signatures</b> — and wins</li>
</ul>
<p class="pull">The lab and tools are integration. The <span class="hl">correlation + explainability engine and the evaluation</span> are the original work.</p>""")

# 16 limitations & future work
s("", """<h2>Limitations &amp; future work</h2>
<div class="two">
<div>
<div class="colh red">Limitations — honestly</div>
<ul class="checks bad sm">
<li>Compressed benign baseline (minutes, not a 7-day window)</li>
<li>Container endpoints, not full VMs; lab traffic, not live enterprise scale</li>
<li>Scripted attack simulators — cleaner than real, evasive C2</li>
<li>Batch (not real-time); single-node ES; JA4 best-effort</li>
</ul>
</div>
<div>
<div class="colh acc">Future work</div>
<ul class="checks sm">
<li>Real-time streaming detection on a live network tap</li>
<li>Longer, real benign baseline; more entity diversity</li>
<li>Learned / adaptive indicator weights</li>
<li>Evaluate against real C2 frameworks (Sliver, Cobalt Strike)</li>
<li>Automated response via SOAR integration</li>
</ul>
</div>
</div>""")

# 17 thanks
s("center title", """<h1>Thank you</h1>
<p class="lead">Behavioral Detection of Hidden DNS/HTTPS C2 — a working system, deployed end-to-end,
that beats signatures with explainable verdicts.</p>
<div class="by">github.com/Sushanth2624/dns-https-c2-ueba-detection · Questions?</div>""")

CSS = r"""
:root{--bg:#0b1220;--card:#141d2e;--chip:#1b2740;--ink:#eaf1fb;--mut:#93a3bd;--mut2:#5a6b86;
 --acc:#33d6cf;--red:#ff7b72;--edge:#4a5d78;--track:#22304a;--line:#2a3a55;
 --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;--mono:ui-monospace,Menlo,Consolas,monospace}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);font-family:var(--sans);overflow:hidden}
.deck{height:100vh;width:100vw;position:relative}
.slide{position:absolute;inset:0;display:none;flex-direction:column;justify-content:center;
 padding:6vh 8vw;opacity:0;transition:opacity .25s}
.slide.on{display:flex;opacity:1}
.slide.center{align-items:center;text-align:center}
h1{font-size:clamp(2rem,5vw,4rem);line-height:1.05;letter-spacing:-.025em;margin:.1em 0}
h2{font-size:clamp(1.5rem,3.4vw,2.6rem);letter-spacing:-.02em;margin:0 0 .6em;color:var(--ink)}
.kick{font-family:var(--mono);font-size:clamp(.7rem,1.4vw,1rem);letter-spacing:.18em;text-transform:uppercase;color:var(--acc);margin-bottom:20px}
.lead{font-size:clamp(1rem,2.1vw,1.5rem);color:var(--mut);max-width:60ch;margin:18px auto}
.by{font-family:var(--mono);color:var(--mut);margin-top:30px;font-size:clamp(.8rem,1.5vw,1.05rem)}
.big{font-size:clamp(1.1rem,2.3vw,1.7rem);max-width:60ch;line-height:1.4}
b{color:#fff;font-weight:700}.hl{color:var(--acc);font-weight:700}.acc{color:var(--acc)}.r,.c b.r{color:var(--red)}
.pull{font-size:clamp(1.1rem,2.3vw,1.7rem);border-left:4px solid var(--acc);padding-left:22px;margin-top:34px;max-width:66ch}
.cap{color:var(--mut);font-size:clamp(.85rem,1.5vw,1.1rem);margin-top:20px}
.cols3,.cols4{display:grid;gap:20px;margin-top:30px;width:100%}
.cols3{grid-template-columns:repeat(3,1fr)}.cols4{grid-template-columns:repeat(4,1fr)}
.c{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:24px;text-align:center}
.c p{color:var(--mut);margin:.3em 0 0;font-size:clamp(.8rem,1.4vw,1.05rem)}
.c b{font-size:clamp(1rem,1.8vw,1.35rem);display:block}
.ci{font-size:2.4rem;margin-bottom:8px}
.n{width:40px;height:40px;border-radius:50%;background:var(--acc);color:#04222a;font-weight:800;font-family:var(--mono);
 display:flex;align-items:center;justify-content:center;margin:0 auto 12px;font-size:1.2rem}
.tall .c{padding:30px 22px}.tall b{margin-bottom:10px}
.stat{font:800 clamp(2rem,4vw,3.4rem)/1 var(--mono);color:var(--acc)}
.checks{list-style:none;padding:0;font-size:clamp(1rem,2vw,1.5rem);max-width:64ch}
.checks li{padding:10px 0 10px 42px;position:relative}
.checks li::before{content:"✓";position:absolute;left:0;color:var(--acc);font-weight:800}
.checks.bad li::before{content:"✗";color:var(--red)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:44px;width:100%;margin-top:8px}
.colh{font-family:var(--mono);font-size:clamp(.9rem,1.5vw,1.15rem);letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px;font-weight:700}
.colh.red{color:var(--red)}.colh.acc{color:var(--acc)}
.checks.sm{font-size:clamp(.85rem,1.45vw,1.15rem);max-width:none}
.checks.sm li{padding:7px 0 7px 32px}
.grid8{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:24px;width:100%}
.g{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:22px;text-align:center;
 font-weight:600;font-size:clamp(.95rem,1.6vw,1.3rem)}
.formula{background:var(--card);border:1px solid var(--acc);border-radius:14px;padding:26px;font-family:var(--mono);
 font-size:clamp(.9rem,1.9vw,1.4rem);text-align:center;margin:10px 0 30px}
.dsvg{width:100%;height:auto;max-height:52vh;display:block;margin:6px 0}
.slide.shot{padding:4vh 4vw}
.slide.shot img{max-width:100%;max-height:80vh;border:1px solid var(--line);border-radius:12px;object-fit:contain;margin-top:10px}
.alert{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--red);border-radius:14px;
 padding:26px;max-width:70ch;font-size:clamp(.95rem,1.7vw,1.25rem)}
.ah{display:flex;gap:18px;align-items:center;margin-bottom:14px;flex-wrap:wrap}
.verdict{background:var(--red);color:#fff;font-weight:800;font-family:var(--mono);padding:4px 12px;border-radius:8px}
.conf{color:var(--acc);font-family:var(--mono);font-weight:700}.ent{color:var(--mut);font-family:var(--mono)}
.ab{margin:8px 0;color:var(--mut)}.ab b{color:var(--ink)}.mono{font-family:var(--mono);color:var(--acc)}
.bar{position:absolute;top:0;left:0;height:4px;background:var(--acc);transition:width .25s;z-index:5}
.pg{position:absolute;bottom:20px;right:28px;font-family:var(--mono);color:var(--mut);font-size:.9rem;z-index:5}
.hint{position:absolute;bottom:20px;left:28px;font-family:var(--mono);color:var(--mut2);font-size:.8rem;z-index:5}
@media(max-width:700px){.cols3,.cols4,.grid8,.two{grid-template-columns:1fr 1fr}}
"""

JS = """
const slides=[...document.querySelectorAll('.slide')];let i=0;
const bar=document.querySelector('.bar'),pg=document.querySelector('.pg');
function show(n){i=Math.max(0,Math.min(slides.length-1,n));
 slides.forEach((s,k)=>s.classList.toggle('on',k===i));
 bar.style.width=((i+1)/slides.length*100)+'%';pg.textContent=(i+1)+' / '+slides.length;
 location.hash=i+1;}
function next(){show(i+1)}function prev(){show(i-1)}
document.addEventListener('keydown',e=>{
 if(['ArrowRight','ArrowDown',' ','PageDown'].includes(e.key)){e.preventDefault();next()}
 else if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){e.preventDefault();prev()}
 else if(e.key==='Home')show(0);else if(e.key==='End')show(slides.length-1);});
document.querySelector('.deck').addEventListener('click',e=>{if(e.clientX<window.innerWidth*0.25)prev();else next();});
show((parseInt(location.hash.slice(1))||1)-1);
"""

html = (f"<style>{CSS}</style><div class='deck'><div class='bar'></div>"
        + "".join(SLIDES)
        + "<div class='pg'></div><div class='hint'>→ / space: next · ← back · click</div></div>"
        + f"<script>{JS}</script>")
OUT.write_text(html)
print("wrote", OUT, round(len(html)/1024), "KB,", len(SLIDES), "slides")
