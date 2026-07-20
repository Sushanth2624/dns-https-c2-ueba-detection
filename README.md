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

The UEBA layer is pluggable behind a fixed contract: **OpenUBA** (the primary engine, now integrated
and verified end-to-end) or the built-in **IsolationForest fallback** (`src/c2detect/ueba/`), so
OpenUBA can never become a single point of failure. Switch with `ueba.source: openuba|baseline`. See
RESEARCH_AND_PLAN.md §6.

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

## Status — implemented & deployed end-to-end (single-host)

All phases built and running on one Ubuntu 24.04 Analysis VM. See
[`docs/deployment.md`](docs/deployment.md) for the single-host adaptation and
[`data/eval/report.md`](data/eval/report.md) for full results.

- **Indicators (all implemented):** entropy, DGA, query-length, NXDOMAIN, beaconing (grouped by
  dest IP *and* SNI), JA3/JA4 rarity, DoH, session-shape — each a normalized 0–1 sub-score.
- **UEBA:** **OpenUBA integrated as the primary engine** — parsed feature vectors are pushed to
  OpenUBA (GACWR v0.0.2, single-VM: host backend + Postgres + model-runner containers), which runs
  its IsolationForest and returns per-entity risk; the adapter calibrates that risk to the 0–1 UEBA
  contract against the benign peer cohort. The built-in IsolationForest **+ one-sided z-score** stays
  as a drop-in fallback (`ueba.source`). A/B/C re-verified with OpenUBA in the loop (below).
- **Correlation + explainability:** glass-box weighted fusion + boost rules → explainable alerts
  (verdict, confidence, contributing indicators with reasons, MITRE, actions) → Elasticsearch.
- **Sensors deployed:** Zeek 8.2.1 (+JA3/JA4), Suricata 8.0.5, Elasticsearch + Kibana 8.19.
- **Evaluation (A/B/C), real captured traffic, 10 entities:**

  | Config | F1 | FPR |
  |---|---|---|
  | A — signature-only (Suricata) | 0.67 | 0.00 |
  | B — best single indicator | 0.80 | 0.33 |
  | **C — multi-indicator + UEBA (this project)** | **1.00** | **0.00** |

  Hypothesis supported: **C > B > A** on F1, with C the only config at zero false positives.
- **Evaluation (A/B/C) re-verified with OpenUBA as the UEBA engine, 14-host inline lab:**

  | Config | F1 | FPR |
  |---|---|---|
  | A — signature-only (Suricata) | 0.55 | 0.00 |
  | B — best single indicator (dga) | 0.67 | 0.00 |
  | **C — multi-indicator + OpenUBA UEBA** | **1.00** | **0.00** |

  **C > B > A holds with OpenUBA driving the anomaly scores — identical to the fallback.** Calibrated
  separation is clean (benign ≤ 0.28, attackers ≥ 0.80). Results: [`data/eval/lab-openuba/`](data/eval/lab-openuba/).
  Reproduce: `PYTHONPATH=src python -m c2detect.cli evaluate-lab --config config/config.openuba.yaml --lab data/captures/lab --out data/eval/lab-openuba`.
- **Reproduce (fallback):** `make demo` (capture → evaluate → alerts to ES → Kibana dashboard).

## Ethics
All attack simulation runs inside an isolated lab against the author's own hosts. No live C2, no
external targets.
