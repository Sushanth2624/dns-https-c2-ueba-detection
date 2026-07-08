# Kibana saved objects

`c2-dashboards.ndjson` is the exported, importable dashboard (built by
`scripts/build_dashboards.py`). Rebuild + re-export any time with `make dashboards`.

Import into a fresh Kibana:
```bash
python3 scripts/build_dashboards.py            # builds + imports + re-exports
# or manually: Stack Management > Saved Objects > Import > c2-dashboards.ndjson
```

Dashboard **"DNS/HTTPS C2 — Behavioral Detection"** (data view `c2-alerts`, time field `@timestamp`):
- Total alerts (metric)
- Alerts by severity (donut)
- Alerts by verdict (bar)
- MITRE ATT&CK techniques (horizontal bar)
- Top entities by confidence (data table)

Populate the `c2-alerts` index first: `make demo`, or
`python -m c2detect.cli run --config config/config.demo.yaml`.
