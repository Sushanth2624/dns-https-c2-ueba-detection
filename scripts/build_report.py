#!/usr/bin/env python3
"""Assemble the full whitepaper (self-contained, print-to-PDF friendly HTML).

A complete, cover-to-cover explanation of the DNS/HTTPS C2 behavioral-detection project for a
non-technical reader: plain-language analogy, every diagram and flow, the method, the
infrastructure, how it was tested, the results, the dashboards, a glossary, and appendices.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
shots = json.load(open(ROOT / "data/tmp/doc_shots.json"))


def fig(name, cap, num):
    return (f'<figure class="shot"><img alt="{cap}" src="data:image/png;base64,{shots[name]}">'
            f'<figcaption><b>Figure {num}.</b> {cap}</figcaption></figure>')


def svgfig(svg, cap, num):
    return f'<figure class="dia">{svg}<figcaption><b>Figure {num}.</b> {cap}</figcaption></figure>'


def callout(kind, title, body):
    return f'<div class="callout {kind}"><div class="co-t">{title}</div><div>{body}</div></div>'


# ============================ DIAGRAMS (inline SVG) ============================

OFFICE = """
<svg viewBox="0 0 1000 560" class="svg" role="img" aria-label="The office-building analogy">
 <defs><marker id="a1" markerWidth="10" markerHeight="10" refX="7.5" refY="4.5" orient="auto">
   <path d="M0,0L9,4.5L0,9z" fill="var(--edge)"/></marker>
 <style>.t{fill:var(--ink);font:600 14px var(--sans)} .s{fill:var(--muted);font:12px var(--sans)}
   .lbl{fill:var(--muted);font:700 11px var(--mono);letter-spacing:.08em;text-transform:uppercase}
   .fl{stroke:var(--edge);stroke-width:2.5;fill:none;marker-end:url(#a1)}</style></defs>

 <!-- building -->
 <rect x="24" y="70" width="470" height="440" rx="16" fill="var(--card)" stroke="var(--line)" stroke-width="1.5"/>
 <text class="lbl" x="40" y="100">The network — an office building</text>
 <text class="s" x="40" y="120">each desk = one computer</text>
 <!-- normal desks -->
 """ + "".join(
    f'<g><rect x="{40+ (i%4)*108}" y="{140+(i//4)*72}" width="92" height="52" rx="9" '
    f'fill="var(--good-bg)" stroke="var(--good)" stroke-width="1.3"/>'
    f'<circle cx="{40+(i%4)*108+18}" cy="{140+(i//4)*72+18}" r="8" fill="var(--good)"/>'
    f'<text class="s" x="{40+(i%4)*108+34}" y="{140+(i//4)*72+22}">worker</text>'
    f'<text class="s" x="{40+(i%4)*108+10}" y="{140+(i//4)*72+44}" style="font-size:10px">normal</text></g>'
    for i in range(8)
 ) + """
 <!-- spy desk -->
 <g><rect x="40" y="428" width="200" height="62" rx="9" fill="var(--red-bg)" stroke="var(--red)" stroke-width="2"/>
   <circle cx="66" cy="452" r="9" fill="var(--red)"/>
   <text class="t" x="84" y="450" style="fill:var(--red)">infected desk</text>
   <text class="s" x="84" y="470">a hidden "spy" (malware)</text>
   <text class="s" x="52" y="484" style="font-size:10px">secretly phoning its boss outside</text></g>

 <!-- hallway / guard -->
 <rect x="524" y="70" width="210" height="440" rx="16" fill="var(--chip)" stroke="var(--line)" stroke-width="1.5"/>
 <text class="lbl" x="540" y="100">The one hallway</text>
 <text class="s" x="540" y="120">all mail &amp; calls exit here</text>
 <g><rect x="548" y="150" width="162" height="70" rx="10" fill="var(--accent-bg)" stroke="var(--accent)" stroke-width="1.6"/>
   <text class="t" x="629" y="180" text-anchor="middle" style="fill:var(--accent)">The smart guard</text>
   <text class="s" x="629" y="200" text-anchor="middle">watches behaviour,</text>
   <text class="s" x="629" y="214" text-anchor="middle">not faces</text></g>
 <rect x="548" y="250" width="76" height="60" rx="9" fill="var(--card)" stroke="var(--line)"/>
 <text class="s" x="586" y="276" text-anchor="middle">note-taker</text>
 <text class="s" x="586" y="292" text-anchor="middle" style="font-size:10px">"Zeek"</text>
 <rect x="634" y="250" width="76" height="60" rx="9" fill="var(--card)" stroke="var(--line)"/>
 <text class="s" x="672" y="276" text-anchor="middle">note-taker</text>
 <text class="s" x="672" y="292" text-anchor="middle" style="font-size:10px">"Suricata"</text>
 <g><rect x="548" y="336" width="162" height="150" rx="10" fill="var(--card)" stroke="var(--line)"/>
   <text class="lbl" x="560" y="360">8 behaviour clues</text>
   <text class="s" x="560" y="384">• calls home like clockwork</text>
   <text class="s" x="560" y="404">• dials dead numbers</text>
   <text class="s" x="560" y="424">• gibberish addresses</text>
   <text class="s" x="560" y="444">• unseen disguise</text>
   <text class="s" x="560" y="464">• hides in locked mail…</text></g>

 <!-- verdict board -->
 <rect x="764" y="150" width="212" height="230" rx="16" fill="var(--card)" stroke="var(--accent)" stroke-width="1.6"/>
 <text class="lbl" x="780" y="180">The verdict board</text>
 <text class="t" x="780" y="212" style="fill:var(--red)">Desk 27 — likely spy</text>
 <text class="s" x="780" y="234">confidence: high</text>
 <text class="s" x="780" y="258">why:</text>
 <text class="s" x="780" y="278">✓ regular call-home</text>
 <text class="s" x="780" y="298">✓ hides DNS in HTTPS</text>
 <text class="s" x="780" y="318">✓ unseen fingerprint</text>
 <text class="s" x="780" y="346">what to do: isolate &amp;</text>
 <text class="s" x="780" y="364">block the destination</text>

 <path class="fl" d="M496,300 L520,300"/>
 <path class="fl" d="M712,240 L760,220"/>
</svg>
"""

DNS_SVG = """
<svg viewBox="0 0 900 210" class="svg" role="img" aria-label="How DNS works">
 <defs><marker id="a2" markerWidth="10" markerHeight="10" refX="7.5" refY="4.5" orient="auto">
   <path d="M0,0L9,4.5L0,9z" fill="var(--edge)"/></marker>
 <style>.t{fill:var(--ink);font:600 13px var(--sans)}.s{fill:var(--muted);font:11px var(--sans)}
   .fl{stroke:var(--edge);stroke-width:2;fill:none;marker-end:url(#a2)}</style></defs>
 <rect x="20" y="70" width="180" height="70" rx="12" fill="var(--card)" stroke="var(--line)"/>
 <text class="t" x="110" y="100" text-anchor="middle">Your computer</text>
 <text class="s" x="110" y="120" text-anchor="middle">wants to reach google.com</text>
 <rect x="360" y="70" width="200" height="70" rx="12" fill="var(--accent-bg)" stroke="var(--accent)"/>
 <text class="t" x="460" y="100" text-anchor="middle">The "phone book"</text>
 <text class="s" x="460" y="120" text-anchor="middle">DNS resolver</text>
 <rect x="720" y="70" width="160" height="70" rx="12" fill="var(--card)" stroke="var(--line)"/>
 <text class="t" x="800" y="100" text-anchor="middle">google.com</text>
 <text class="s" x="800" y="120" text-anchor="middle">at 142.250.x.x</text>
 <path class="fl" d="M202,95 L356,95"/><text class="s" x="278" y="86" text-anchor="middle">"what's the address?"</text>
 <path class="fl" d="M356,120 L204,120"/><text class="s" x="278" y="138" text-anchor="middle">"it's 142.250.x.x"</text>
 <path class="fl" d="M562,105 L716,105"/><text class="s" x="640" y="96" text-anchor="middle">now connect</text>
</svg>
"""


def arch_svg():
    return ARCH


ARCH = """
<svg viewBox="0 0 1000 430" class="svg" role="img" aria-label="System architecture">
  <defs><marker id="ah" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="var(--edge)"/></marker>
    <style>.lyr{fill:var(--card);stroke:var(--line);stroke-width:1.5}
      .lbl{fill:var(--muted);font:700 11px var(--mono);letter-spacing:.06em;text-transform:uppercase}
      .node{fill:var(--chip);stroke:var(--line);stroke-width:1}
      .nt{fill:var(--ink);font:600 12px var(--sans)}.ns{fill:var(--muted);font:10px var(--sans)}
      .flow{stroke:var(--edge);stroke-width:2;fill:none;marker-end:url(#ah)}</style></defs>
  <rect class="lyr" x="12" y="60" width="188" height="340" rx="12"/>
  <rect class="lyr" x="236" y="60" width="230" height="340" rx="12"/>
  <rect class="lyr" x="502" y="60" width="230" height="340" rx="12"/>
  <rect class="lyr" x="768" y="60" width="220" height="340" rx="12"/>
  <text class="lbl" x="106" y="44" text-anchor="middle">Endpoints</text>
  <text class="lbl" x="351" y="44" text-anchor="middle">Capture &amp; Sensors</text>
  <text class="lbl" x="617" y="34" text-anchor="middle">Detection engine</text>
  <text class="lbl" x="878" y="44" text-anchor="middle">Store &amp; Visualize</text>
  <rect class="node" x="34" y="86"  width="144" height="42" rx="8"/>
  <text class="nt" x="106" y="104" text-anchor="middle">6 benign hosts</text><text class="ns" x="106" y="120" text-anchor="middle">normal DNS / HTTPS</text>
  <rect class="node" x="34" y="150" width="144" height="42" rx="8" style="stroke:var(--red)"/>
  <text class="nt" x="106" y="168" text-anchor="middle">2 DGA · 2 tunnel</text><text class="ns" x="106" y="184" text-anchor="middle">random / long names</text>
  <rect class="node" x="34" y="214" width="144" height="42" rx="8" style="stroke:var(--red)"/>
  <text class="nt" x="106" y="232" text-anchor="middle">2 beacon</text><text class="ns" x="106" y="248" text-anchor="middle">regular call-home</text>
  <rect class="node" x="34" y="278" width="144" height="42" rx="8" style="stroke:var(--red)"/>
  <text class="nt" x="106" y="296" text-anchor="middle">2 DoH</text><text class="ns" x="106" y="312" text-anchor="middle">DNS over HTTPS</text>
  <text class="ns" x="106" y="356" text-anchor="middle">real host · own IP</text>
  <rect class="node" x="258" y="86" width="186" height="40" rx="8" style="stroke:var(--accent)"/>
  <text class="nt" x="351" y="103" text-anchor="middle">Inline gateway + resolver</text><text class="ns" x="351" y="118" text-anchor="middle">this VM routes all traffic</text>
  <rect class="node" x="258" y="140" width="186" height="34" rx="8"/><text class="nt" x="351" y="162" text-anchor="middle">tcpdump — 100% inline</text>
  <rect class="node" x="258" y="190" width="88" height="50" rx="8"/><text class="nt" x="302" y="212" text-anchor="middle">Zeek</text><text class="ns" x="302" y="228" text-anchor="middle">dns/ssl/conn</text>
  <rect class="node" x="356" y="190" width="88" height="50" rx="8"/><text class="nt" x="400" y="212" text-anchor="middle">Suricata</text><text class="ns" x="400" y="228" text-anchor="middle">signatures</text>
  <rect class="node" x="258" y="300" width="186" height="38" rx="8" style="stroke:var(--red)"/><text class="nt" x="351" y="316" text-anchor="middle">local C2 (beacon target)</text><text class="ns" x="351" y="330" text-anchor="middle">TLS :8443</text>
  <rect class="node" x="524" y="86" width="186" height="48" rx="8"/><text class="nt" x="617" y="106" text-anchor="middle">8 behavioral indicators</text><text class="ns" x="617" y="122" text-anchor="middle">entropy·DGA·NXDOMAIN·beacon…</text>
  <rect class="node" x="524" y="148" width="186" height="48" rx="8"/><text class="nt" x="617" y="168" text-anchor="middle">UEBA anomaly</text><text class="ns" x="617" y="184" text-anchor="middle">OpenUBA (fallback: IsoForest+z)</text>
  <rect class="node" x="524" y="210" width="186" height="48" rx="8" style="stroke:var(--accent)"/><text class="nt" x="617" y="230" text-anchor="middle">Correlation (glass-box)</text><text class="ns" x="617" y="246" text-anchor="middle">weighted fusion + boosts</text>
  <rect class="node" x="524" y="272" width="186" height="48" rx="8" style="stroke:var(--accent)"/><text class="nt" x="617" y="292" text-anchor="middle">Explainable alert</text><text class="ns" x="617" y="308" text-anchor="middle">verdict · MITRE · actions</text>
  <rect class="node" x="790" y="120" width="176" height="50" rx="8"/><text class="nt" x="878" y="140" text-anchor="middle">Elasticsearch</text><text class="ns" x="878" y="156" text-anchor="middle">alerts·scores·telemetry</text>
  <rect class="node" x="790" y="230" width="176" height="50" rx="8" style="stroke:var(--accent)"/><text class="nt" x="878" y="250" text-anchor="middle">Kibana</text><text class="ns" x="878" y="266" text-anchor="middle">3 dashboards</text>
  <path class="flow" d="M200,235 L232,235"/><path class="flow" d="M466,235 L498,235"/>
  <path class="flow" d="M710,240 L788,180 L788,160"/><path class="flow" d="M878,170 L878,226"/>
</svg>"""

FLOW = """
<svg viewBox="0 0 1000 150" class="svg" role="img" aria-label="Data flow">
 <defs><marker id="ah2" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
   <path d="M0,0L9,4.5L0,9z" fill="var(--edge)"/></marker>
 <style>.st{fill:var(--card);stroke:var(--line);stroke-width:1.5}.stt{fill:var(--ink);font:600 12px var(--sans)}
  .sts{fill:var(--muted);font:10px var(--mono)}.fl{stroke:var(--edge);stroke-width:2;fill:none;marker-end:url(#ah2)}</style></defs>
""" + "".join(
    f'<rect class="st" x="{x}" y="45" width="150" height="60" rx="10" style="stroke:{c}"/>'
    f'<text class="stt" x="{x+75}" y="72" text-anchor="middle">{t}</text>'
    f'<text class="sts" x="{x+75}" y="90" text-anchor="middle">{s}</text>'
    for x, t, s, c in [(16,"Packets","tcpdump","var(--line)"),(183,"Telemetry","Zeek+Suricata","var(--line)"),
        (350,"Features","8 scores/host","var(--line)"),(517,"Anomaly","UEBA","var(--line)"),
        (684,"Verdict","correlation","var(--accent)"),(851,"Alert","→ES→Kibana","var(--accent)")]
) + "".join(f'<path class="fl" d="M{x},75 L{x+17},75"/>' for x in (166,333,500,667,834)) + "</svg>"

FUNNEL = """
<svg viewBox="0 0 900 330" class="svg" role="img" aria-label="Correlation funnel">
 <defs><marker id="a3" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">
   <path d="M0,0L9,4.5L0,9z" fill="var(--edge)"/></marker>
 <style>.t{fill:var(--ink);font:600 12px var(--sans)}.s{fill:var(--muted);font:10px var(--sans)}
   .fl{stroke:var(--edge);stroke-width:2;fill:none;marker-end:url(#a3)}</style></defs>
""" + "".join(
    f'<rect x="20" y="{18+i*35}" width="200" height="28" rx="6" fill="var(--chip)" stroke="var(--line)"/>'
    f'<text class="t" x="30" y="{37+i*35}" style="font-size:11px">{n}</text>'
    f'<path class="fl" d="M222,{32+i*35} L300,155"/>'
    for i, n in enumerate(["domain entropy","DGA structure","NXDOMAIN rate","query length",
        "beacon regularity","JA3 rarity","DoH endpoint","session shape"])
) + """
 <rect x="300" y="120" width="180" height="70" rx="10" fill="var(--accent-bg)" stroke="var(--accent)" stroke-width="1.6"/>
 <text class="t" x="390" y="150" text-anchor="middle" style="fill:var(--accent)">Weighted fusion</text>
 <text class="s" x="390" y="168" text-anchor="middle">+ boost rules</text>
 <text class="s" x="390" y="182" text-anchor="middle">+ UEBA anomaly</text>
 <path class="fl" d="M482,155 L560,155"/>
 <rect x="560" y="120" width="150" height="70" rx="10" fill="var(--card)" stroke="var(--line)"/>
 <text class="t" x="635" y="150" text-anchor="middle">Confidence</text>
 <text class="s" x="635" y="168" text-anchor="middle">0.00 – 1.00</text>
 <path class="fl" d="M712,155 L760,155"/>
 <rect x="760" y="120" width="130" height="70" rx="10" fill="var(--card)" stroke="var(--red)"/>
 <text class="t" x="825" y="150" text-anchor="middle" style="fill:var(--red)">Verdict</text>
 <text class="s" x="825" y="168" text-anchor="middle">+ explanation</text>
 <text class="s" x="300" y="230">UEBA anomaly ─────────────────────┘ feeds the fusion</text>
</svg>"""

# results chart
_R = [("A — signature only", 0.55, "var(--muted)"), ("B — best single indicator", 0.67, "var(--muted)"),
      ("C — multi-indicator + UEBA", 1.00, "var(--accent)")]
_bars = ""
for i, (l, f, c) in enumerate(_R):
    y = 16 + i * 58; w = f * 560
    _bars += (f'<text x="0" y="{y+21}" style="fill:var(--ink);font:600 13px var(--sans)">{l}</text>'
              f'<rect x="330" y="{y}" width="560" height="34" rx="6" fill="var(--track)"/>'
              f'<rect x="330" y="{y}" width="{w:.0f}" height="34" rx="6" fill="{c}"/>'
              f'<text x="{330+w-10:.0f}" y="{y+23}" style="fill:#fff;font:700 13px var(--mono);text-anchor:end">{f:.2f}</text>')
RESULTS = f'<svg viewBox="0 0 900 190" class="svg" role="img" aria-label="F1 by config">{_bars}</svg>'


def attack_svg(title, steps, color):
    boxes = ""
    for i, s in enumerate(steps):
        x = 20 + i * 220
        boxes += (f'<rect x="{x}" y="40" width="190" height="70" rx="10" fill="var(--card)" '
                  f'stroke="{color}" stroke-width="1.4"/>'
                  f'<text x="{x+95}" y="70" text-anchor="middle" style="fill:var(--ink);font:600 12px var(--sans)">'
                  f'{s[0]}</text><text x="{x+95}" y="90" text-anchor="middle" '
                  f'style="fill:var(--muted);font:10px var(--sans)">{s[1]}</text>')
        if i < len(steps) - 1:
            boxes += (f'<path d="M{x+192},75 L{x+218},75" stroke="var(--edge)" stroke-width="2" '
                      f'fill="none" marker-end="url(#a4)"/>')
    return (f'<svg viewBox="0 0 {20+len(steps)*220} 130" class="svg" role="img" aria-label="{title}">'
            f'<defs><marker id="a4" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto">'
            f'<path d="M0,0L9,4.5L0,9z" fill="var(--edge)"/></marker></defs>{boxes}</svg>')


# ============================ CONTENT ============================
# (long-form prose lives here; helpers above render the visuals)

CSS = r"""
:root{
  --paper:#fbfaf7; --card:#ffffff; --chip:#f1efe9; --ink:#1a1c1e; --muted:#5f6b78; --line:#e2ddd3;
  --accent:#0e7c8b; --accent-bg:#e2f2f4; --good:#1f8a4c; --good-bg:#e4f3ea; --red:#c0392b;
  --red-bg:#fbe9e7; --amber:#a86b12; --edge:#9aa6b2; --track:#e9e5dd;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --serif:Georgia,"Times New Roman",'Iowan Old Style',serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root{
  --paper:#12140f; --card:#1a1d17; --chip:#20241c; --ink:#ece7db; --muted:#9aa392; --line:#2c3126;
  --accent:#4bc4cf; --accent-bg:#123034; --good:#5cc483; --good-bg:#14301f; --red:#e8776a;
  --red-bg:#301613; --amber:#d3a24a; --edge:#586152; --track:#242820;
}}
:root[data-theme="dark"]{
  --paper:#12140f;--card:#1a1d17;--chip:#20241c;--ink:#ece7db;--muted:#9aa392;--line:#2c3126;
  --accent:#4bc4cf;--accent-bg:#123034;--good:#5cc483;--good-bg:#14301f;--red:#e8776a;--red-bg:#301613;--amber:#d3a24a;--edge:#586152;--track:#242820;}
:root[data-theme="light"]{
  --paper:#fbfaf7;--card:#ffffff;--chip:#f1efe9;--ink:#1a1c1e;--muted:#5f6b78;--line:#e2ddd3;
  --accent:#0e7c8b;--accent-bg:#e2f2f4;--good:#1f8a4c;--good-bg:#e4f3ea;--red:#c0392b;--red-bg:#fbe9e7;--amber:#a86b12;--edge:#9aa6b2;--track:#e9e5dd;}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:17px;
  line-height:1.7;-webkit-font-smoothing:antialiased}
.doc{max-width:820px;margin:0 auto;padding:clamp(20px,4vw,40px)}
h1,h2,h3,h4{font-family:var(--serif);letter-spacing:-.01em;line-height:1.2}
p{margin:0 0 1.05em}
b,strong{font-weight:700}
.sans{font-family:var(--sans)}.mono{font-family:var(--mono)}
.eyebrow{font-family:var(--mono);font-size:.72rem;letter-spacing:.18em;text-transform:uppercase;
  color:var(--accent);margin-bottom:10px}
/* cover */
.cover{min-height:92vh;display:flex;flex-direction:column;justify-content:center;
  border-bottom:2px solid var(--ink);padding-bottom:40px}
.cover h1{font-size:clamp(2.1rem,5.5vw,3.5rem);margin:.2em 0 .3em;text-wrap:balance}
.cover .sub{font-size:1.25rem;color:var(--muted);max-width:60ch}
.cover .meta{margin-top:auto;padding-top:34px;font-family:var(--sans);font-size:.9rem;color:var(--muted)}
.cover .meta b{color:var(--ink)}
.cover .badge{display:inline-block;font-family:var(--mono);font-size:.8rem;color:var(--accent);
  border:1px solid var(--accent);border-radius:20px;padding:4px 12px;margin-bottom:18px}
/* part dividers */
.part{margin:0;padding:70px 0 20px;border-top:1px solid var(--line)}
.part .pnum{font-family:var(--mono);font-size:.8rem;letter-spacing:.14em;color:var(--accent);text-transform:uppercase}
.part h2{font-size:clamp(1.7rem,4vw,2.4rem);margin:.15em 0 .1em}
.part .pintro{color:var(--muted);font-size:1.12rem;max-width:64ch}
h3{font-size:1.35rem;margin:1.8em 0 .4em}
h4{font-size:1.08rem;margin:1.4em 0 .3em;font-family:var(--sans);font-weight:700}
/* toc */
.toc{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:24px 28px;margin:30px 0}
.toc h2{font-size:1.1rem;font-family:var(--sans);margin:0 0 14px}
.toc ol{margin:0;padding-left:22px;columns:2;column-gap:34px;font-family:var(--sans);font-size:.95rem}
.toc li{margin:.28em 0;break-inside:avoid}
.toc a{color:var(--ink);text-decoration:none}.toc a:hover{color:var(--accent)}
/* figures */
figure{margin:24px 0}
.svg{width:100%;height:auto;display:block;background:var(--card);border:1px solid var(--line);
  border-radius:12px;padding:16px}
.shot img{width:100%;height:auto;display:block;border:1px solid var(--line);border-radius:12px}
figcaption{font-family:var(--sans);font-size:.85rem;color:var(--muted);margin-top:8px;text-align:center}
.dia figcaption,.shot figcaption{margin-top:10px}
/* callouts */
.callout{border-radius:12px;padding:16px 20px;margin:20px 0;font-family:var(--sans);font-size:.95rem}
.callout .co-t{font-weight:700;margin-bottom:5px}
.callout.key{background:var(--accent-bg);border:1px solid var(--accent)}
.callout.plain{background:var(--chip);border:1px solid var(--line)}
.callout.warn{background:var(--red-bg);border:1px solid var(--red)}
.callout.good{background:var(--good-bg);border:1px solid var(--good)}
/* tables */
.scroll{overflow-x:auto;margin:20px 0;border:1px solid var(--line);border-radius:12px}
table{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:.9rem}
th,td{padding:10px 14px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
thead th{background:var(--chip);font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
tbody tr:last-child td{border-bottom:none}
td.mono,.tcode{font-family:var(--mono);font-size:.82rem}
/* lists */
ul,ol{margin:0 0 1.05em;padding-left:1.4em}
li{margin:.3em 0}
.lead{font-size:1.15rem;color:var(--muted)}
.pull{border-left:4px solid var(--accent);padding:4px 0 4px 20px;font-size:1.18rem;margin:24px 0;
  font-style:italic}
code,.kbd{font-family:var(--mono);font-size:.86em;background:var(--chip);padding:1px 6px;border-radius:5px}
pre{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;overflow-x:auto;
  font-family:var(--mono);font-size:.82rem;line-height:1.5}
.glo{border-bottom:1px solid var(--line);padding:12px 0}
.glo b{font-family:var(--sans)}
.stat-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:22px 0;font-family:var(--sans)}
.stat-row>div{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;text-align:center}
.stat-row .n{font:700 1.9rem/1 var(--mono);display:block}
.stat-row .l{font-size:.78rem;color:var(--muted);margin-top:6px;display:block}
@media(max-width:600px){.toc ol{columns:1}.stat-row{grid-template-columns:repeat(2,1fr)}}
@media print{
  body{font-size:11pt} .doc{max-width:none;padding:0}
  .part{page-break-before:always;border-top:none} .cover{page-break-after:always;min-height:auto}
  figure,.callout,.scroll,pre{page-break-inside:avoid} a{color:inherit;text-decoration:none}
}
"""

COVER = f"""
<section class="cover">
  <span class="badge">Capstone 2 · Complete technical &amp; plain-language report</span>
  <h1>Behavioral Detection of Hidden DNS/HTTPS Command-and-Control</h1>
  <p class="sub">How to catch malware that hides its secret communications inside ordinary web and
  DNS traffic — explained from the ground up, with every diagram, decision, and result.</p>
  <div class="stat-row">
    <div><span class="n" style="color:var(--accent)">1.00</span><span class="l">F1 score (our system)</span></div>
    <div><span class="n" style="color:var(--good)">0</span><span class="l">false positives</span></div>
    <div><span class="n">14</span><span class="l">real hosts, live capture</span></div>
    <div><span class="n">8</span><span class="l">behaviors + UEBA</span></div>
  </div>
  <div class="meta">
    <b>Author</b> Sushanth Sridhar (R24TF007) &nbsp;·&nbsp; MTech Cyber Security, REVA Academy (RACE)<br>
    <b>Artefact</b> Working system deployed end-to-end &nbsp;·&nbsp;
    <b>Repository</b> github.com/Sushanth2624/dns-https-c2-ueba-detection<br>
    <b>How to read this</b> Parts 1–3 need no technical background. Parts 4–12 go progressively deeper;
    a plain-language glossary (Part 11) defines every term.
  </div>
</section>
"""

def part(num, pid, title, intro):
    return f'<section class="part" id="{pid}"><div class="pnum">Part {num}</div><h2>{title}</h2><p class="pintro">{intro}</p>'

TOC = """
<div class="toc"><h2>Contents</h2><ol>
<li><a href="#p1">Executive summary</a></li>
<li><a href="#p2">The big picture, in plain language</a></li>
<li><a href="#p3">The problem, in depth</a></li>
<li><a href="#p4">The research question</a></li>
<li><a href="#p5">How the system works</a></li>
<li><a href="#p6">The infrastructure we built</a></li>
<li><a href="#p7">How we tested it</a></li>
<li><a href="#p8">Results</a></li>
<li><a href="#p9">The dashboards</a></li>
<li><a href="#p10">Operating &amp; reproducing it</a></li>
<li><a href="#p11">Glossary — every term in plain words</a></li>
<li><a href="#p12">Appendices</a></li>
</ol></div>
"""

P1 = part(1, "p1", "Executive summary",
  "The whole project in one page — what problem it solves, how, and how well.") + """
<p>When a computer is compromised by malware, the malware must secretly <b>communicate</b> with the
criminals who control it — to receive commands and to steal data. Security professionals call this
channel <b>command-and-control</b>, or <b>C2</b>. Modern attackers hide this channel inside the two
kinds of internet traffic that every organization must allow: <b>DNS</b> (the internet's address
lookup system) and <b>HTTPS</b> (encrypted web traffic). Because the traffic is encrypted and looks
ordinary, traditional defences — which work by matching known "bad" patterns — miss it.</p>
<p>This project builds a detector that works differently. Instead of looking for known-bad patterns,
it watches <b>how each computer behaves</b> and asks: <i>does this machine act like it is secretly
talking to a controller?</i> It measures eight independent behaviours, compares each machine to a
learned picture of "normal" using <b>UEBA</b> (User &amp; Entity Behaviour Analytics), and then a
transparent <b>correlation engine</b> combines everything into a single, <b>explainable</b> verdict:
who is suspicious, how confident we are, exactly which behaviours triggered, the matching
<b>MITRE ATT&amp;CK</b> techniques, and what the analyst should do next.</p>
<p>We built and deployed the entire system on one machine, generated realistic traffic from
<b>14 separate hosts</b> (6 normal, 8 running different attack techniques), captured it with real
network sensors, and measured detection accuracy three ways:</p>
""" + svgfig(RESULTS, "F1 score (overall accuracy, 0–1) for three approaches on the same real traffic. "
  "A = traditional signatures, B = the best single behaviour, C = our full multi-behaviour + UEBA system.", 1) + """
<p>The result is decisive: our system (C) caught <b>every one</b> of the four attack techniques —
DGA, DNS tunneling, beaconing, and DNS-over-HTTPS — with <b>zero false alarms</b>. Traditional
signatures (A) caught barely half, because there is no fixed "bad string" for a beacon or a
daily-changing domain. Any single behaviour on its own (B) also missed at least one technique. Only
by <b>correlating several behaviours together and baselining against normal</b> do we catch
everything without crying wolf.</p>
""" + callout("key", "The one idea to remember",
  "No single clue proves anything — plenty of honest computers occasionally do one odd thing. But "
  "several suspicious behaviours in the <i>same</i> machine, at the <i>same</i> time, is strong, "
  "defensible evidence of C2. That correlation, plus a plain-English explanation of every verdict, "
  "is the contribution of this work.") + "</section>"

P2 = part(2, "p2", "The big picture, in plain language",
  "No technical background needed. One analogy carries the whole idea.") + """
<h3>2.1 &nbsp;A company, a spy, and a smart guard</h3>
<p>Imagine a large <b>office building</b> full of employees. Each employee is a <b>computer</b> on the
network. Now imagine a <b>spy</b> has secretly taken a job inside. The spy needs to send stolen
information <i>out</i> to their boss and receive instructions back <i>in</i> — but without being
noticed. That secret channel is exactly what malware's "command-and-control" is.</p>
<p>The spy is clever. They don't climb out a window — that gets caught. Instead they <b>hide their
secret messages inside the normal mail and phone calls the company already allows.</b> That is
precisely how modern malware behaves: it hides inside ordinary internet traffic.</p>
""" + svgfig(OFFICE, "The whole system as an office building. Traffic from every desk passes through "
  "one hallway, where a behaviour-watching guard and two note-takers observe everything and post a "
  "clear verdict.", 2) + """
<h3>2.2 &nbsp;Two kinds of "normal traffic" the spy hides in</h3>
<p>Two things every computer does constantly:</p>
<p><b>DNS is the internet's phone book.</b> Before your computer visits <span class="mono">google.com</span>,
it quietly asks "what is the numeric address for google.com?" and gets an answer. This happens
thousands of times a day.</p>
""" + svgfig(DNS_SVG, "DNS in one picture: look up the address, then connect. Attackers abuse the "
  "lookup step because DNS is never blocked.", 3) + """
<p><b>HTTPS is a sealed, locked envelope.</b> When you visit a secure website, the contents are locked
so nobody in between can read them. Attackers love these two because <b>DNS is used by everyone so
it is never blocked</b>, and <b>HTTPS hides what is inside</b>. Perfect cover.</p>
<h3>2.3 &nbsp;Why the old way of catching spies fails</h3>
<p>The traditional guard is a <b>bouncer with a list of known troublemakers' faces</b>. If your face
is on the list, you're stopped. But this spy wears a <i>disguise that changes every day</i> and hides
messages inside <i>sealed envelopes the guard can't open</i>. The known-faces list is useless.</p>
<p><b>Our guard is different.</b> Instead of checking faces, it <b>watches how people behave</b> — and
a spy behaves differently from a normal employee, even in disguise.</p>
<h3>2.4 &nbsp;What our guard actually watches</h3>
<ul>
<li><b>Calls home like clockwork.</b> A machine that contacts the same outside address at a perfectly
regular rhythm (say every two minutes) is behaving like a robot, not a person. (This is
<b>beaconing</b>.)</li>
<li><b>Dials dead numbers.</b> A spy whose boss changes their address every day has to try many
made-up addresses to find the working one, producing lots of "no such address" answers. (This is a
<b>domain-generation algorithm</b>, or DGA.)</li>
<li><b>Asks for gibberish addresses.</b> Absurdly long, random-looking address requests are secretly
<i>carrying stolen data</i> inside the request itself. (This is <b>DNS tunneling</b>.)</li>
<li><b>Hides the phone-book lookups inside locked envelopes</b> so even the phone-book operator can't
see them. (This is <b>DNS-over-HTTPS</b>, or DoH.)</li>
<li><b>Wears a disguise nobody has seen before</b> — an unusual "fingerprint" on its encrypted
connections. (This is <b>JA3/JA4 rarity</b>.)</li>
</ul>
<h3>2.5 &nbsp;How the guard reaches a verdict</h3>
<p>The guard compares each employee to what <b>normal</b> looks like in this building (that is the
UEBA part), then combines all the clues. It does <b>not</b> raise the alarm on one odd behaviour —
that would falsely accuse honest employees. It raises the alarm only when <b>several</b> suspicious
behaviours appear in the <b>same</b> employee at once, and it writes a clear note explaining exactly
why. That note goes on a <b>verdict board</b> — the dashboards your security team watches.</p>
""" + callout("plain", "In one sentence",
  "We cannot read the spy's messages (locked) and cannot recognise their face (it changes daily) — so "
  "we catch them by how they behave, and only sound the alarm when several suspicious behaviours "
  "appear together.") + "</section>"

P3 = part(3, "p3", "The problem, in depth",
  "The same story again, now with the real technical detail behind each piece.") + """
<h3>3.1 &nbsp;What command-and-control really is</h3>
<p>After an initial compromise (a phishing click, a vulnerable server), malware rarely acts entirely
on its own. It needs to reach a <b>controller</b> operated by the attacker to fetch commands, receive
new modules, and exfiltrate data. This ongoing channel is <b>command-and-control (C2)</b>. Detecting
C2 is high-value because it catches an intrusion during the window <i>after</i> the foothold but
<i>before</i> major damage, and a single C2 detection can unravel an entire campaign.</p>
<h3>3.2 &nbsp;Why signatures and IOCs fail against modern C2</h3>
<p>Classic detection matches <b>signatures</b> (byte patterns) and <b>indicators of compromise</b>
(known-bad domains/IPs/hashes). Modern C2 defeats this by design. It:</p>
<ul>
<li>rides <b>encrypted TLS</b>, so the payload is invisible to inspection;</li>
<li>looks like ordinary web or DNS traffic, so there is nothing categorically "bad" to flag;</li>
<li>uses <b>low-and-slow</b> beacons that blend into background noise;</li>
<li>rotates domains via a <b>DGA</b>, so yesterday's blocklist is worthless today;</li>
<li>tunnels through <b>DoH</b>, so even the resolver cannot inspect the DNS.</li>
</ul>
<p>The defensive answer is a shift from <i>signatures</i> to <i>behaviour</i>: not "is this a known-bad
string" but "does this entity <b>behave</b> like it is talking to a controller." The literature shows
individual behavioural signals work but are each noisy and evadable in isolation. <b>The gap this
project fills:</b> few studies fuse <i>multiple</i> behavioural indicators with UEBA baselining, output
<i>explainable</i> verdicts, and benchmark that head-to-head against signature-only detection.</p>
<h3>3.3 &nbsp;DNS and HTTPS: the two channels, precisely</h3>
<p><b>DNS</b> translates human names to numeric IP addresses. A client sends a query for a name; a
resolver answers with an address (or <span class="mono">NXDOMAIN</span> — "no such domain" — if it
doesn't exist). DNS is UDP port 53, tiny, and universally allowed. <b>HTTPS</b> wraps web traffic in
<b>TLS</b> encryption. During the TLS handshake, before encryption fully engages, the client reveals
the <b>SNI</b> (the server name it wants) and a <b>JA3/JA4 fingerprint</b> (a hash of how the client
proposed to encrypt — effectively the client software's signature). These two observable fields are
exactly what our TLS-based indicators use, since the payload itself is unreadable.</p>
<h3>3.4 &nbsp;The four attack techniques we detect</h3>
<h4>Domain Generation Algorithm (DGA)</h4>
<p>The controller and malware share a secret algorithm that produces a fresh batch of random-looking
domains every day. The malware tries them until one resolves; defenders cannot pre-block domains that
don't exist yet. The tell-tale behaviour: <b>bursts of NXDOMAIN</b> and <b>high-entropy (random)
domain names</b>.</p>
""" + svgfig(attack_svg("DGA", [("Secret algorithm","both sides share it"),
  ("Generate domains","random, daily"),("Try each","many fail → NXDOMAIN"),
  ("One resolves","C2 found")], "var(--red)"),
  "DGA: a rotating, un-blockable address that produces a burst of failed lookups.", 4) + """
<h4>DNS tunneling</h4>
<p>Data is encoded <i>into the DNS query names themselves</i> — long, high-entropy labels sent to a
domain the attacker controls, whose "answers" carry data back. It abuses DNS as a covert transport.
The tell-tale behaviour: <b>very long/deep names</b> and <b>high query volume to one zone</b>.</p>
""" + svgfig(attack_svg("DNS tunneling", [("Take secret data","a file to steal"),
  ("Encode into names","<data>.tunnel.lab"),("Send as DNS","looks like lookups"),
  ("Attacker decodes","data exfiltrated")], "var(--red)"),
  "DNS tunneling: stolen data smuggled inside the address requests.", 5) + """
<h4>Beaconing</h4>
<p>The implant "phones home" at a regular interval to poll for commands — often small, consistent
payloads with low timing jitter. The tell-tale behaviour: <b>regular call-home timing</b> to the same
destination.</p>
""" + svgfig(attack_svg("Beaconing", [("Implant sleeps","fixed interval"),
  ("Wakes, calls home","every ~2 min"),("Polls for orders","tiny message"),
  ("Repeats forever","clockwork rhythm")], "var(--red)"),
  "Beaconing: a robotic, regular heartbeat no human produces.", 6) + """
<h4>DNS-over-HTTPS (DoH) C2</h4>
<p>DNS lookups are performed over an encrypted HTTPS connection to a DoH provider, so the queries
"disappear" from port 53 and cannot be inspected by the network resolver. The tell-tale behaviour:
<b>TLS to a known DoH endpoint</b> and DNS traffic vanishing from port 53 while DoH rises.</p>
""" + svgfig(attack_svg("DoH C2", [("Normal DNS stops","port 53 goes quiet"),
  ("Lookups move to HTTPS","to a DoH provider"),("Encrypted & hidden","resolver can't see"),
  ("C2 rides along","inside the tunnel")], "var(--red)"),
  "DoH C2: the phone-book lookups hidden inside a locked envelope.", 7) + """
""" + callout("plain", "Why one clue is never enough",
  "Each technique above also occurs, faintly, in benign traffic: a CDN hostname can look random; a "
  "browser can make repeated requests; DoH is a legitimate privacy feature. That is exactly why a "
  "single indicator is noisy — and why correlation across several is the real detector.") + "</section>"

P4 = part(4, "p4", "The research question",
  "What we set out to prove, and why the answer matters.") + """
<h3>4.1 &nbsp;The question and hypothesis</h3>
<p><b>Research question.</b> Does fusing <i>multiple</i> behavioural indicators with UEBA-based anomaly
detection improve detection of hidden DNS/HTTPS C2 — higher recall, lower false positives, explainable
verdicts — compared with (a) single indicators used alone and (b) signature-only detection?</p>
<p><b>Hypothesis.</b> A weighted correlation of a UEBA anomaly score plus independent behavioural
indicators yields higher F1 and fewer false positives than any single indicator or signature ruleset,
while producing analyst-usable explanations.</p>
<h3>4.2 &nbsp;Where it sits in the literature</h3>
<div class="scroll"><table>
<thead><tr><th>Prior work</th><th>Takeaway</th><th>Gap it leaves</th></tr></thead>
<tbody>
<tr><td>Marchal et al. — behavioural HTTPS C2 (2020)</td><td>Beacon timing exposes C2 even when encrypted</td><td>Payload opaque; few indicators combined</td></tr>
<tr><td>Jerabek et al. — DoH measurement (2022)</td><td>Resolver behaviour flags suspicious DoH</td><td>DoH-only; no UEBA, no correlation</td></tr>
<tr><td>Singh &amp; Roy — malicious DoH via ML (2022)</td><td>ML lifts accuracy on encrypted DNS</td><td>Dataset-bound; not explainable</td></tr>
<tr><td>Dawood et al. — impact of DoH (2024)</td><td>Encrypted-DNS misuse is rising</td><td>Per-technique; false-positive prone</td></tr>
<tr><td>Thomson et al. — TLS fingerprinting (2024)</td><td>JA3/JA4 is discriminative</td><td>Fingerprint alone is evadable</td></tr>
</tbody></table></div>
<p><b>Consolidated gap.</b> JA3, DoH, and beaconing are each studied alone. Little work fuses them
with UEBA, outputs explainable alerts, and benchmarks behavioural-multi-indicator vs signature-only.
This project does exactly that.</p>
<h3>4.3 &nbsp;What is genuinely the contribution</h3>
<p>The lab, the sensors (Zeek, Suricata), and the anomaly model are integration of existing tools.
The <b>original contribution is the correlation + explainability layer</b>: the logic that turns "an
anomaly score plus a bag of indicators" into a defensible, ranked, explained alert with investigation
guidance and MITRE mapping — plus the comparative A/B/C evaluation that answers the research
question.</p></section>"""

P5 = part(5, "p5", "How the system works",
  "The full pipeline, component by component, from packet to explained alert.") + """
<h3>5.1 &nbsp;Architecture at a glance</h3>
<p>Four stages: real hosts generate traffic; the analysis machine captures and sensors it; a detection
engine scores it; results are stored and visualised.</p>
""" + svgfig(ARCH, "System architecture. Every host routes through the analysis VM (the inline "
  "gateway), so the sensors see 100% of traffic with real per-host identity. The detection engine — "
  "the project's contribution — is the third column.", 8) + """
<h3>5.2 &nbsp;The data flow, end to end</h3>
""" + svgfig(FLOW, "One continuous path: packets → structured telemetry → per-host behaviour scores → "
  "UEBA anomaly → correlation verdict → explainable alert in Elasticsearch and Kibana.", 9) + """
<ol>
<li><b>Capture.</b> <span class="mono">tcpdump</span> records every packet crossing the lab bridge.</li>
<li><b>Sensors.</b> <b>Zeek</b> turns packets into structured logs — <span class="mono">dns.log</span>
(queries, response codes), <span class="mono">ssl.log</span> (SNI, JA3/JA4), <span class="mono">conn.log</span>
(timing, byte counts). <b>Suricata</b> runs the signature baseline (Config A).</li>
<li><b>Features.</b> For each host, the eight indicators are computed as normalised 0–1 sub-scores.</li>
<li><b>UEBA.</b> <b>OpenUBA</b> (the integrated UEBA engine) scores how anomalous the host is versus a
benign baseline; a built-in IsolationForest + z-score is the drop-in fallback.</li>
<li><b>Correlate &amp; explain.</b> A weighted fusion plus boost rules produces a confidence; if it
crosses the threshold, an explainable alert is built.</li>
<li><b>Store &amp; visualise.</b> Alerts, per-host scores, and raw telemetry go to Elasticsearch and
three Kibana dashboards.</li>
</ol>
<h3>5.3 &nbsp;The eight behavioural indicators</h3>
<p>Each indicator is a small function that reduces a host's traffic to a single 0–1 sub-score, where
higher means more suspicious. Each maps to real attacker tradecraft and to MITRE ATT&amp;CK.</p>
<div class="scroll"><table>
<thead><tr><th>Indicator</th><th>What it measures (plain)</th><th>How it's computed (technical)</th><th>MITRE</th></tr></thead>
<tbody>
<tr><td><b>Domain entropy</b></td><td>How random the domain name looks</td><td>Shannon entropy of the highest-entropy label; normalised against a threshold</td><td class="mono">T1568.002</td></tr>
<tr><td><b>DGA structure</b></td><td>Does the name look machine-generated?</td><td>Blend of entropy, length, digit-ratio and (low) vowel-ratio of the longest label</td><td class="mono">T1568.002</td></tr>
<tr><td><b>NXDOMAIN rate</b></td><td>How many lookups fail</td><td>Fraction of the host's DNS answers that are NXDOMAIN, vs a threshold</td><td class="mono">T1568.002</td></tr>
<tr><td><b>Query length</b></td><td>Unusually long/deep names</td><td>Longest label length and subdomain depth, normalised</td><td class="mono">T1071.004</td></tr>
<tr><td><b>Beacon regularity</b></td><td>Robotic, clockwork timing</td><td>Gap-robust dispersion (median/MAD) of inter-arrival times, grouped by destination IP <i>and</i> domain</td><td class="mono">T1071.001 · T1571</td></tr>
<tr><td><b>JA3/JA4 rarity</b></td><td>An unusual TLS "fingerprint"</td><td>Rarity of the client's JA3 hash vs a frozen benign baseline</td><td class="mono">T1573</td></tr>
<tr><td><b>DoH endpoint</b></td><td>DNS hidden inside HTTPS</td><td>SNI/host matches a known DoH resolver, or a <span class="mono">/dns-query</span> request</td><td class="mono">T1071.004 · T1572</td></tr>
<tr><td><b>Session shape</b></td><td>Small, steady, long-lived flows</td><td>Duration, throughput and up/down byte balance from conn.log</td><td class="mono">T1071.001</td></tr>
</tbody></table></div>
""" + callout("plain", "A real engineering fix worth noting",
  "The beacon indicator originally used the standard coefficient-of-variation of timing. When a "
  "beacon pauses and resumes (as real low-and-slow implants do), that big gap wrecked the measure. "
  "We switched to a <b>gap-robust</b> version based on the median and median-absolute-deviation, so a "
  "minority of large gaps no longer hides the periodicity. This is more faithful to real beacons, and "
  "it fixed detection of both our fast and slow beacons.") + """
<h3>5.4 &nbsp;The UEBA layer — a sense of "normal"</h3>
<p>UEBA (User &amp; Entity Behaviour Analytics) learns what normal looks like and flags deviations. The
UEBA engine here is <b>OpenUBA</b> (an open-source UEBA platform), integrated and running on the single
Analysis VM — no Kubernetes, no Spark: its backend, a Postgres store, and a model-runner container
are all on the host. The parsed per-host feature vectors are pushed to OpenUBA, which trains on the
benign hosts and returns a per-host <b>risk</b>; the adapter calibrates that risk into a 0–1 anomaly
against the benign peer cohort. A built-in <b>IsolationForest + one-sided z-score</b> stays as a
drop-in fallback behind the same interface (selectable with <span class="mono">ueba.source</span>), so
OpenUBA can never become a single point of failure. Either way, the anomaly model is deliberately the
same class a commercial UEBA ships — the novelty is not the anomaly model but what happens next.</p>
<p>The A/B/C benchmark was re-run with OpenUBA driving the anomaly scores and the result is unchanged:
<b>F1 C = 1.00 &gt; B = 0.67 &gt; A = 0.55</b>, with zero false positives. The ordering does not depend
on which UEBA engine runs.</p>
<h3>5.5 &nbsp;The correlation engine — the contribution</h3>
<p>This is the heart of the project, and it is deliberately a <b>glass box</b> — every number is
inspectable and reported, unlike a black-box classifier.</p>
""" + svgfig(FUNNEL, "The correlation funnel. Eight indicator sub-scores plus the UEBA anomaly are "
  "fused by a transparent weighted model with boost rules for high-signal combinations, producing a "
  "confidence and an explained verdict.", 10) + """
<p>The confidence is a weighted blend of the UEBA anomaly and the indicator bundle, plus additive
<b>boosts</b> for high-signal combinations (for example: a regular beacon <i>and</i> a rare TLS
fingerprint; or high entropy <i>and</i> an NXDOMAIN burst). Every weight lives in configuration and is
reported. Because it is transparent, we can explain <i>why</i> any host scored what it did.</p>
<h3>5.6 &nbsp;Explainability — verdicts a human can act on</h3>
<p>If confidence crosses the alert threshold, the system builds an alert containing: the
<b>verdict</b> (benign / suspicious / likely-C2), the <b>confidence</b>, the <b>contributing
indicators</b> each with a plain-English reason, the score breakdown, the matching <b>MITRE ATT&amp;CK
techniques</b>, and <b>recommended actions</b> (isolate the host, capture a full packet trace, block
the destination, hunt the domain across the fleet). No machine learning "black box" is involved in the
explanation — it is deterministic and auditable, which is exactly what an analyst and an auditor
need.</p></section>"""

P6 = part(6, "p6", "The infrastructure we built",
  "Everything that runs, why it's there, and the honest engineering trade-offs.") + """
<h3>6.1 &nbsp;The analysis machine and the software stack</h3>
<p>The system runs on a single Ubuntu 24.04 machine (16 CPU / 15 GB RAM). On it we deployed:</p>
<div class="scroll"><table>
<thead><tr><th>Component</th><th>Version</th><th>What it does, in plain terms</th></tr></thead>
<tbody>
<tr><td><b>Zeek</b></td><td>8.2.1</td><td>The primary "note-taker" — turns raw packets into readable logs of DNS, TLS and connections (plus JA3/JA4 fingerprints)</td></tr>
<tr><td><b>Suricata</b></td><td>8.0.5</td><td>The traditional signature engine — our Config-A baseline to beat</td></tr>
<tr><td><b>Elasticsearch</b></td><td>8.19</td><td>The database — stores alerts, scores and telemetry so they can be searched</td></tr>
<tr><td><b>Kibana</b></td><td>8.19</td><td>The screens — turns the stored data into dashboards</td></tr>
<tr><td><b>Python</b></td><td>3.12</td><td>The detection engine itself (the <span class="mono">c2detect</span> package)</td></tr>
</tbody></table></div>
<h3>6.2 &nbsp;The multi-host lab — real, separate hosts</h3>
<p>The original plan called for endpoints on separate physical hypervisors routing through the
analysis machine. This machine has <b>no nested virtualization</b> (it cannot run full VMs inside
itself), so we used the faithful equivalent: <b>14 lightweight containers</b>, each a real host with
its own IP address and its own TLS fingerprint, on a private lab network
(<span class="mono">10.50.0.0/24</span>).</p>
<div class="scroll"><table>
<thead><tr><th>Hosts</th><th>Role</th><th>What they do</th></tr></thead>
<tbody>
<tr><td><span class="mono">.11–.16</span></td><td>6 benign</td><td>Browse real websites with a normal tool (curl), at human-like irregular intervals</td></tr>
<tr><td><span class="mono">.21, .22</span></td><td>2 DGA</td><td>Resolve random domains → NXDOMAIN bursts</td></tr>
<tr><td><span class="mono">.23, .24</span></td><td>2 tunnel</td><td>Encode data into long DNS names</td></tr>
<tr><td><span class="mono">.25, .26</span></td><td>2 beacon</td><td>Regular TLS call-home to a local C2 (fast and slow)</td></tr>
<tr><td><span class="mono">.27, .28</span></td><td>2 DoH</td><td>DNS-over-HTTPS to real public resolvers</td></tr>
</tbody></table></div>
<h3>6.3 &nbsp;Inline capture — why per-host identity is real</h3>
<p>The analysis machine is the endpoints' <b>gateway and DNS resolver</b>, so all their traffic
physically crosses one bridge and is captured <b>100% inline</b>. Crucially, on that bridge each
packet still carries its <b>real source host IP</b> (address translation happens later, on the way
out) — so the detector sees genuine per-host behaviour with no relabeling. A local TLS server acts as
the beacon's "controller" so beacon timing reflects a real LAN implant rather than internet jitter.</p>
""" + callout("plain", "An honest note on VMs vs containers",
  "Containers are not full virtual machines. But for this project's purpose — separate hosts with "
  "distinct IPs whose real traffic is captured inline — they are equivalent, and every feature is "
  "computed from genuine Zeek/Suricata sensor output, not synthesised.") + """
<h3>6.4 &nbsp;Security hardening</h3>
<p>Elasticsearch runs with authentication and <b>TLS</b> on both its HTTP and internal layers; it
rejects unauthenticated and plain-HTTP requests. Kibana connects over TLS with a dedicated service
account and its <b>own HTTPS</b> UI with a login page. Passwords live only in a git-ignored secrets
file; committed configuration contains none. Elasticsearch and Kibana are set to auto-restart on
failure so the stack self-heals.</p></section>"""

P7 = part(7, "p7", "How we tested it",
  "The traffic we generated, how we captured it, and the fair three-way comparison.") + """
<h3>7.1 &nbsp;Generating realistic traffic</h3>
<p>Small, lab-only generators produce each behaviour: a benign generator browses real sites with curl
at irregular intervals; a DGA generator resolves random domains; a DNS-tunnel generator encodes random
data into long labels; a beacon generator makes a real TLS handshake to the local C2 at a fixed
interval with slight jitter; a DoH generator sends DNS-over-HTTPS requests to public resolvers. Each
runs inside its own container, so its traffic carries that host's real identity.</p>
<h3>7.2 &nbsp;Capturing it into telemetry</h3>
<p>While all 14 hosts generate traffic (over two rounds, for volume and a realistic time-spread),
<span class="mono">tcpdump</span> records the bridge; then Zeek and Suricata process the capture into
structured telemetry. This yielded, for this report's run, <b>3,162 DNS records, 606 TLS records,
3,795 connection records, and 328 Suricata signature hits</b> across the 14 hosts.</p>
<h3>7.3 &nbsp;The fair comparison — A vs B vs C</h3>
<p>The same real capture is scored three ways against ground truth (we know which hosts are attackers),
so every alert can be counted as a true or false positive/negative:</p>
<div class="scroll"><table>
<thead><tr><th>Config</th><th>What it is</th><th>What it represents</th></tr></thead>
<tbody>
<tr><td><b>A</b></td><td>Signature-only (Suricata rules)</td><td>The traditional approach</td></tr>
<tr><td><b>B</b></td><td>Each single behavioural indicator, alone</td><td>"Is one good behaviour enough?"</td></tr>
<tr><td><b>C</b></td><td>Multi-indicator + UEBA correlation</td><td>This project</td></tr>
</tbody></table></div>
<p>The hypothesis holds if <b>C &gt; B &gt; A</b> on F1 and false-positive rate. We measure precision,
recall, F1, false-positive rate, and detection latency (time from attack start to first correct
alert).</p>
""" + callout("plain", "What the metrics mean",
  "<b>Precision</b> = of the hosts we flagged, how many were truly attackers (few false alarms). "
  "<b>Recall</b> = of the real attackers, how many we caught (few misses). <b>F1</b> = a single score "
  "balancing both. <b>False-positive rate</b> = how often we wrongly flagged a benign host.") + "</section>"

P8 = part(8, "p8", "Results",
  "The evidence that behaviour + UEBA beats single indicators and signatures.") + """
<h3>8.1 &nbsp;Headline comparison</h3>
<div class="scroll"><table>
<thead><tr><th>Configuration</th><th>Precision</th><th>Recall</th><th>F1</th><th>False-positive rate</th></tr></thead>
<tbody>
<tr><td>A — signature-only (Suricata)</td><td>1.00</td><td>0.38</td><td>0.55</td><td>0.00</td></tr>
<tr><td>B — best single indicator</td><td>1.00</td><td>0.50</td><td>0.67</td><td>0.00</td></tr>
<tr><td><b>C — multi-indicator + UEBA</b></td><td><b>1.00</b></td><td><b>1.00</b></td><td><b>1.00</b></td><td><b>0.00</b></td></tr>
</tbody></table></div>
""" + svgfig(RESULTS, "F1 by configuration. C beats B beats A — exactly the hypothesis.", 11) + """
<p><b>C detects all four techniques with zero false positives.</b> Signatures (A) structurally miss
DGA and beaconing — there is no static string to match — so recall is only 0.38. Every single
indicator (B) misses at least one technique. Only the correlation catches everything.</p>
<h3>8.2 &nbsp;Per-host outcome</h3>
<p>All eight attack hosts were correctly flagged with high confidence; all six benign hosts stayed
well below the alert threshold — no false alarms.</p>
<div class="scroll"><table>
<thead><tr><th>Host</th><th>Type</th><th>UEBA anomaly</th><th>Confidence</th><th>Verdict</th></tr></thead>
<tbody>
<tr><td class="mono">10.50.0.27</td><td>DoH</td><td>1.00</td><td>1.00</td><td>flagged</td></tr>
<tr><td class="mono">10.50.0.24</td><td>tunnel</td><td>1.00</td><td>0.96</td><td>flagged</td></tr>
<tr><td class="mono">10.50.0.21</td><td>DGA</td><td>1.00</td><td>0.90</td><td>flagged</td></tr>
<tr><td class="mono">10.50.0.25</td><td>beacon</td><td>1.00</td><td>0.73</td><td>flagged</td></tr>
<tr><td class="mono">10.50.0.12</td><td>benign</td><td>0.51</td><td>0.32</td><td>clear</td></tr>
<tr><td class="mono">10.50.0.16</td><td>benign</td><td>0.26</td><td>0.23</td><td>clear</td></tr>
</tbody></table></div>
<h3>8.3 &nbsp;Detection latency</h3>
<p>DGA and tunneling are flagged almost immediately (the first burst of NXDOMAIN / long names is
enough); DoH within a couple of seconds; beaconing after roughly ten seconds, because the detector
must observe several intervals before it can establish a regular rhythm. This is inherent to
timing-based detection, and still fast enough for practical response.</p>
""" + callout("good", "Answering the research question",
  "Yes: fusing multiple behavioural indicators with UEBA improves detection over both single "
  "indicators and signatures — higher recall, zero false positives, and every verdict explained. "
  "C &gt; B &gt; A holds.") + "</section>"

P9 = part(9, "p9", "The dashboards",
  "What the CISO and the analyst actually see, panel by panel. Live screenshots of the running system.") + """
<h3>9.1 &nbsp;Executive overview (for leadership)</h3>
<p>One screen: how many hosts are monitored, how many threats were detected, how many false positives
(zero), the benign-vs-attack split, network activity over 24 hours, the MITRE techniques observed, the
highest-risk hosts, and the A-vs-B-vs-C detection-quality comparison.</p>
""" + fig("exec", "Executive Overview dashboard — the leadership view.", 12) + """
<h3>9.2 &nbsp;Threat detail (for the analyst)</h3>
<p>The centrepiece is the <b>indicator heatmap</b>: rows are behaviours, columns are hosts, red means
"this behaviour fired for this host." Attack hosts light up red on their relevant behaviours; benign
hosts stay cool. Beside it: confidence per host, a full scores table, and alert breakdowns.</p>
""" + fig("threat", "Threat Detail dashboard — which behaviours fired for each host.", 13) + """
<h3>9.3 &nbsp;Network telemetry (the raw evidence)</h3>
<p>DNS and NXDOMAIN over time, the top TLS server names (including the C2 domains
<span class="mono">c2.internal.lab</span> and the DoH resolvers), the TLS client fingerprints, and the
Suricata signature hits — the ground-truth evidence behind every verdict.</p>
""" + fig("telemetry", "Network Telemetry dashboard — the raw supporting evidence.", 14) + "</section>"

P10 = part(10, "p10", "Operating & reproducing it",
  "How to run, view, and re-run the whole system.") + """
<h3>10.1 &nbsp;One-command reproduction</h3>
<pre>source config/secrets.env        # load credentials
make lab-demo                    # 14 hosts -&gt; inline capture -&gt; A/B/C -&gt; Elasticsearch -&gt; dashboards
make health                      # check the whole stack
make test                        # 12 unit tests</pre>
<h3>10.2 &nbsp;Where to look</h3>
<div class="scroll"><table>
<thead><tr><th>Thing</th><th>Where</th></tr></thead>
<tbody>
<tr><td>Kibana (dashboards, login as <span class="mono">elastic</span>)</td><td class="mono">https://172.16.242.14:5601</td></tr>
<tr><td>Elasticsearch (data/API)</td><td class="mono">https://172.16.242.14:9200</td></tr>
<tr><td>Executive dashboard</td><td class="mono">…/app/dashboards#/view/c2-exec</td></tr>
<tr><td>Threat detail</td><td class="mono">…/app/dashboards#/view/c2-threat</td></tr>
<tr><td>Network telemetry</td><td class="mono">…/app/dashboards#/view/c2-telemetry</td></tr>
<tr><td>Results, report, charts</td><td class="mono">data/eval/lab/</td></tr>
</tbody></table></div>
""" + callout("plain", "Viewing tips",
  "Use <b>https://</b> (plain http is refused). The browser will warn about the self-signed lab "
  "certificate — that is expected; click through. Set the Kibana time picker to <b>Last 24 hours</b> "
  "so the time-spread data is in view.") + "</section>"

def glo(t, d): return f'<div class="glo"><b>{t}</b> — {d}</div>'
P11 = part(11, "p11", "Glossary — every term in plain words",
  "If a word in this report was unfamiliar, it is defined here.") + \
  glo("C2 (command-and-control)","The secret channel malware uses to talk to the attacker who controls it.") + \
  glo("DNS","The internet's phone book: it turns names like google.com into numeric addresses.") + \
  glo("NXDOMAIN","The phone-book answer meaning \"no such name.\" Bursts of these hint at a DGA.") + \
  glo("HTTPS / TLS","Encrypted web traffic. TLS is the lock; the contents are unreadable in transit.") + \
  glo("SNI","The one part of an encrypted connection that reveals which website is being contacted.") + \
  glo("JA3 / JA4","A fingerprint of how a program set up its encryption — effectively the software's signature.") + \
  glo("DoH (DNS-over-HTTPS)","Doing DNS lookups inside an HTTPS tunnel, hiding them from the network.") + \
  glo("DGA","A domain-generation algorithm: malware and its controller share a formula that produces new domains daily, defeating blocklists.") + \
  glo("Beaconing","Malware phoning home at a regular interval — a robotic rhythm no human produces.") + \
  glo("DNS tunneling","Smuggling data inside DNS query names, abusing DNS as a covert transport.") + \
  glo("Indicator","One measurable behaviour, reduced to a 0–1 suspicion score.") + \
  glo("UEBA","User &amp; Entity Behaviour Analytics: software that learns \"normal\" and flags deviations.") + \
  glo("IsolationForest","A machine-learning method that finds outliers by how easily they can be separated from the crowd.") + \
  glo("Correlation engine","Our transparent logic that fuses all indicators + the UEBA score into one confidence and verdict.") + \
  glo("Signature","A fixed pattern of known-bad content — the traditional detection method that modern C2 evades.") + \
  glo("MITRE ATT&amp;CK","An industry catalogue of attacker techniques; each alert cites the techniques it matches.") + \
  glo("Zeek","A network-monitoring tool that turns packets into structured logs.") + \
  glo("Suricata","A signature-based intrusion-detection engine — our traditional baseline.") + \
  glo("Elasticsearch / Kibana","A search database and its dashboard UI, where results are stored and shown.") + \
  glo("Inline capture","Watching traffic on the path it must travel, so 100% is seen with real host identity.") + \
  glo("F1 / precision / recall","Standard accuracy measures — see Part 7 for plain definitions.") + \
  glo("False positive","Wrongly flagging a benign host as malicious.") + "</section>"

P12 = part(12, "p12", "Appendices",
  "Reference material: indicator weights, MITRE mapping, and the project layout.") + """
<h3>A. Indicator weights (the correlation model)</h3>
<p>All weights live in configuration and are reported — the model is a glass box.</p>
<div class="scroll"><table>
<thead><tr><th>Indicator</th><th>Weight</th><th>Indicator</th><th>Weight</th></tr></thead>
<tbody>
<tr><td>beacon regularity</td><td class="mono">0.25</td><td>domain entropy</td><td class="mono">0.15</td></tr>
<tr><td>NXDOMAIN rate</td><td class="mono">0.15</td><td>DGA structure</td><td class="mono">0.10</td></tr>
<tr><td>JA3 rarity</td><td class="mono">0.10</td><td>DoH endpoint</td><td class="mono">0.10</td></tr>
<tr><td>session shape</td><td class="mono">0.10</td><td>query length</td><td class="mono">0.05</td></tr>
</tbody></table></div>
<p>The UEBA anomaly is blended in at weight <span class="mono">0.40</span> against the indicator
bundle, and boost rules add confidence for high-signal combinations (e.g. beacon + rare JA3; entropy
+ NXDOMAIN). Alert threshold: confidence ≥ <span class="mono">0.60</span>.</p>
<h3>B. MITRE ATT&amp;CK techniques detected</h3>
<div class="scroll"><table>
<thead><tr><th>Technique</th><th>ID</th><th>Seen in</th></tr></thead>
<tbody>
<tr><td>Application Layer Protocol: Web</td><td class="mono">T1071.001</td><td>beaconing, session shape</td></tr>
<tr><td>Application Layer Protocol: DNS</td><td class="mono">T1071.004</td><td>tunneling, DoH, entropy</td></tr>
<tr><td>Dynamic Resolution: DGA</td><td class="mono">T1568.002</td><td>DGA, entropy, NXDOMAIN</td></tr>
<tr><td>Non-Standard Port</td><td class="mono">T1571</td><td>beaconing</td></tr>
<tr><td>Encrypted Channel</td><td class="mono">T1573</td><td>JA3 rarity, session shape</td></tr>
<tr><td>Protocol Tunneling</td><td class="mono">T1572</td><td>DoH</td></tr>
<tr><td>Exfiltration Over Alternative Protocol</td><td class="mono">T1048.003</td><td>DNS tunneling</td></tr>
</tbody></table></div>
<h3>C. Project layout</h3>
<pre>src/c2detect/
  indicators/   the 8 behaviours (entropy, dga, nxdomain, beaconing, ja3ja4, doh, session, length)
  ueba/         OpenUBA integration adapter (openuba_client.py, active) + IsolationForest+z fallback (baseline_model.py)
  correlation/  the glass-box fusion engine + boost rules
  explain/      the explainable-alert builder
  parsers/      read Zeek and Suricata logs
  output/       write alerts to Elasticsearch
  eval/         the A/B/C evaluation harness
scripts/        lab_up, lab_capture, ingest_es, build_dashboards, build_doc/report
config/         weights, thresholds, MITRE map (secrets kept out of git)
dashboards/     exported Kibana dashboards
docs/           this report + architecture doc</pre>
<h3>D. Environment</h3>
<p>Ubuntu 24.04 · Python 3.12 · Zeek 8.2.1 · Suricata 8.0.5 · Elasticsearch &amp; Kibana 8.19 ·
scikit-learn 1.4+. Repository: <span class="mono">github.com/Sushanth2624/dns-https-c2-ueba-detection</span>.
Unit tests: 12/12 passing.</p>
</section>
<footer style="padding:40px 0;color:var(--muted);font-family:var(--sans);font-size:.85rem;border-top:1px solid var(--line)">
End of report · Behavioral Detection of Hidden DNS/HTTPS Command-and-Control · Sushanth Sridhar (R24TF007)
</footer>"""

HTML = ('<div class="doc">' + COVER + TOC + P1 + P2 + P3 + P4 + P5 + P6 + P7 + P8 + P9 + P10 + P11 + P12 + '</div>')
out = ROOT / "data/tmp/report.html"
out.write_text(f"<style>{CSS}</style>\n{HTML}")
print("wrote", out, round(len(out.read_text())/1024), "KB")
