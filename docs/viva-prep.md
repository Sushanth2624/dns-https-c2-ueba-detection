# Viva prep — likely questions and where each is answered

See RESEARCH_AND_PLAN.md section 13 for the master checklist. Keep concise, defensible answers ready:

- **Novelty?** Multi-indicator fusion + UEBA + explainability + head-to-head vs signature-only. Not any single indicator (those exist in the literature).
- **Did you integrate OpenUBA, or just replace it?** Integrated. OpenUBA (GACWR v0.0.2) runs as the UEBA engine on this single VM (host backend + Postgres + model-runner containers, no k8s/Spark). The adapter (`ueba/openuba_client.py`) pushes the parsed feature vectors to OpenUBA, trains on benign, runs inference, and reads per-entity risk back. The correlation engine consumes those scores unchanged. Switch engines with `ueba.source: openuba|baseline`. See "OpenUBA integration" below.
- **Is OpenUBA just IsolationForest?** Its default model is — and that's fine. Novelty is the correlation/explainability/evaluation, not the anomaly model. (RESEARCH_AND_PLAN §6.)
- **Baseline methodology?** Defined continuous benign window, frozen before attacks. (§8.)
- **Explainability?** Glass-box weighted score + per-indicator reasons + MITRE + actions; auditable, no black box. (§7.)
- **Cross-hypervisor capture?** Inline gateway, not port-mirror. (§5.)
- **How do you prove it's better?** Configs A/B/C with precision/recall/F1/FP-rate/latency. (§8.)
- **False positives?** Correlation + boosts require multiple corroborating signals, cutting single-indicator noise.
- **Limitations / future work?** Compressed baseline window; JA4 immaturity; lab traffic vs real-world diversity.

## As-built results (defend with numbers)

- **Headline:** F1 **C=1.00 > B=0.80 > A=0.67**; FPR **C=0.00 < B=0.33**. C is the only config that
  catches all four attacks with zero false positives. (`data/eval/report.md`, charts in
  `data/eval/charts/`.)
- **Why does C beat B?** The best single indicator (`dns_entropy`, F1 0.80) fires on benign CDN
  hostnames → 2 false positives (FPR 0.33). Correlation requires corroboration + UEBA anomaly, so
  benign entities peak at confidence 0.41 (< 0.6 threshold) → 0 FPs.
- **Why does C beat A?** Signatures catch what they have rules for — long DNS names (tunneling) and
  DoH SNI — but structurally miss DGA and beaconing (no static string), so A recall = 0.50. The
  behavioral layer catches all four.
- **Detection latency (C):** DGA/tunnel ~0 s (first burst of NXDOMAIN/long names), DoH 1.4 s, beacon
  10.7 s (needs ≥6 intervals to establish regularity). Reported per attack in the results table.
- **What made the beacon detectable?** Beacon timing is grouped by destination **domain (SNI)** as
  well as IP, so anycast/CDN IP rotation doesn't scatter the samples; and the UEBA z-score term flags
  `beacon_cv≈0.95` as far above the benign mean (~0). Both are in the code, not hand-set verdicts.
- **Is the anomaly model really UEBA?** Per-entity behavior baselined on benign, scored by OpenUBA's
  IsolationForest (with the built-in IsolationForest + one-sided z-score as fallback). The
  contribution is the correlation + explainability + A/B/C evaluation, not the anomaly model. (§6.)
- **Single-host vs the multi-VM plan?** Same pipeline; only capture is offline-pcap instead of inline
  gateway, and entities are relabeled onto synthetic IPs. Features come from real Zeek/Suricata
  output. (`docs/deployment.md`.)

## OpenUBA integration (how it works, and what it took)

- **Topology (single VM, no Kubernetes/Spark):** OpenUBA backend runs on the host via systemd
  `openuba-backend` (uvicorn :8000, `EXECUTION_MODE=docker`); Postgres runs in Docker Compose; each
  job spawns a **model-runner container** that runs the sklearn IsolationForest. Repo at
  `/home/analysis/openuba-src`. Backend on the host (not in a container) so its `docker run` for the
  runner uses host paths — a container-in-container bind-mount mismatch was the reason.
- **Data flow:** `OpenUBAClient.prime()` writes the per-entity feature CSV into OpenUBA's shared
  model-runner volume → trains the model on the benign entities → runs inference on all entities →
  reads per-entity `risk_score` back → **calibrates it to the 0–1 UEBA `anomaly_score` against the
  benign peer cohort** (one-sided z, 6σ saturation — the same normalization the fallback uses).
  `.score(entity)` then serves the cached record. The correlation/explainability/alerting code is
  untouched and never knows which engine ran.
- **Why calibrate?** OpenUBA's native `risk/100` compresses every host into ~0.16–0.51, so the 0.40
  UEBA weight contributes too little to lift subtle beacon-only / DoH-only attackers over threshold.
  After benign-cohort calibration the separation is clean: **benign ≤ 0.28, attackers ≥ 0.80.**
  OpenUBA still computes the anomaly signal; the adapter only maps it onto the contract's scale.
- **Two OpenUBA SDK bugs I had to work around (defensible engineering):** (1) the SDK's
  `wait_for_job()` treats only `completed/failed/error` as terminal, but the backend reports success
  as `succeeded` → `wait=True` hangs; the adapter submits `wait=False` and polls the job itself.
  (2) a *trained* run persists anomalies to the store (not inline in `job.metrics`), and the SDK's
  `query_anomalies` hardcodes `limit=5000` which the API rejects (422, cap 1000); the adapter reads
  `/api/v1/anomalies` directly.
- **Verified result:** A/B/C re-run with OpenUBA driving the scores (`config/config.openuba.yaml`,
  14-host inline lab): **F1 C=1.00 > B=0.67 > A=0.55, FPR all 0.00** — C>B>A holds, identical to the
  fallback. Results in `data/eval/lab-openuba/`.
