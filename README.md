# Behavioral Detection of Hidden DNS/HTTPS C2 Using UEBA and Multi-Indicator Analysis

Capstone 2 — Sushanth Sridhar (R24TF007), MTech Cyber Security, RACE.

Detects command-and-control hidden in DNS / HTTPS / DoH traffic by fusing **multiple behavioral
indicators** (JA3/JA4, NXDOMAIN behaviour, domain entropy, beacon regularity, communication
frequency, session shape) with a **UEBA** anomaly layer, then generating **explainable alerts**
through an original Python correlation + explainability engine. Results land in Elasticsearch and
Kibana.

> Read **[`RESEARCH_AND_PLAN.md`](RESEARCH_AND_PLAN.md)** first — it is the full research background,
> the list of everything needed, the architecture, and the sprint/phase plan.

## Pipeline

```
endpoints ──(inline)──► Analysis VM ─► Zeek + Suricata ─► indicators ─► UEBA ─► correlation ─► explainable alerts ─► Elasticsearch ─► Kibana
```

The UEBA layer is pluggable behind a fixed contract: **OpenUBA** or the built-in
**IsolationForest fallback** (`src/c2detect/ueba/`), so OpenUBA can never become a single point of
failure. See RESEARCH_AND_PLAN.md §6.

## Quickstart (Analysis VM)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config/config.example.yaml config/config.yaml   # then edit paths + ES

# run the pipeline over captured Zeek/Suricata logs
python -m c2detect.cli run --config config/config.yaml

# unit tests
pytest -q
```

Set `PYTHONPATH=src` or `pip install -e .` so `c2detect` is importable.

## Layout
See RESEARCH_AND_PLAN.md §10 for the annotated tree.

## Status
Scaffold. Implemented as reference: entropy, beaconing, nxdomain indicators; IsolationForest
baseline; correlation engine; explainable reasoner; ES writer. Remaining modules are stubs with
defined interfaces — filled in per the sprint plan.

## Ethics
All attack simulation runs inside an isolated lab against the author's own hosts. No live C2, no
external targets.
