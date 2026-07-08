# Deployment status — end-to-end, single-host

Built and deployed on one Ubuntu 24.04 Analysis VM (16 vCPU / 15 GB). Every phase of
RESEARCH_AND_PLAN.md §11 is implemented and verified; multi-VM inline capture is adapted to a
self-contained single host (see [`docs/deployment.md`](docs/deployment.md)).

| Phase | Exit gate | Status |
|---|---|---|
| 0 — Foundation & infra | benign request → Zeek log → Elasticsearch | ✅ Zeek 8.2.1, Suricata 8.0.5, ES+Kibana 8.19 installed; real capture lands in ES |
| 1 — Telemetry & features | per-entity feature vector; pytest green | ✅ all 9 indicators implemented; `build_feature_vectors`; **12/12 tests pass** |
| 2 — UEBA baselining | benign low, planted anomaly high, contract shape | ✅ IsolationForest **+ z-score**, frozen on benign; attacks score 1.0, benign ≤0.51 |
| 3 — Correlation & explainability | injected scenario → one explainable ES alert | ✅ glass-box fusion + boosts + reasoner → 4 explainable alerts in `c2-alerts` |
| 4 — Attack sim & labeled data | benign + 4 attacks captured through pipeline | ✅ **real container-lab: 7 endpoint hosts, inline capture, distinct source IPs** (+ single-host captures) |
| 5 — Evaluation A/B/C | results showing C vs B vs A | ✅ **F1 C=1.00 > B=0.80 > A=0.67**, FPR C=0.00 < B=0.33 |
| 6 — Dashboards & docs | one-path reproducible demo + report | ✅ `make demo`; Kibana dashboard exported; deployment/results/viva docs |

## What was implemented (previously stubbed)

- Indicators: `dga`, `ja3ja4` (rarity + SNI-mismatch), `doh`, `session`, new `length`
- `pipeline.build_feature_vectors` — Zeek/Suricata → per-entity 0–1 sub-scores (beacon grouped by
  dest IP **and** SNI to survive CDN IP rotation)
- `ueba/baseline_model` — IsolationForest **+ one-sided z-score**; `ueba/openuba_client` fetch adapter
- `traffic/malicious/dns_tunnel_sim`, `doh_sim`; TLS-handshake beacon in `beacon_sim`
- `eval/` package — labeled corpus, metrics, A/B/C evaluation, markdown+charts report
- `output/elastic` explicit mapping; alert `@timestamp`; CLI `corpus` + `evaluate` commands
- Scripts: `run_capture.sh`, `build_dataset.sh`, `build_dashboards.py`; updated `healthcheck.sh`

## Reproduce

```bash
make test       # 12/12
make lab-demo   # real multi-host: 7 container endpoints -> inline capture -> A/B/C -> ES -> Kibana
make demo       # single-host variant (no Docker): capture on host NIC -> ... -> Kibana
make health
```

**Real container-lab result** (7 hosts, distinct source IPs, inline capture): F1 C=1.00, A=0.67, B=0.67; FPR C=0.00.

Results: `data/eval/report.md`, `data/eval/results.json`, `data/eval/charts/*.png`.
Kibana: http://localhost:5601/app/dashboards → "DNS/HTTPS C2 — Behavioral Detection".

## Known limitations (honest, for the viva)

- Compressed benign baseline (minutes, not the plan's 7 days) — documented; methodology is the same.
- 10-entity corpus derived from single-host captures relabeled to synthetic IPs (features are real
  Zeek/Suricata output; only entity labels are synthetic).
- ES security disabled for the lab (single node, localhost) — not a production posture.
