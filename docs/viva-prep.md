# Viva prep — likely questions and where each is answered

See RESEARCH_AND_PLAN.md section 13 for the master checklist. Keep concise, defensible answers ready:

- **Novelty?** Multi-indicator fusion + UEBA + explainability + head-to-head vs signature-only. Not any single indicator (those exist in the literature).
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
- **Is the anomaly model really UEBA?** IsolationForest + one-sided z-score over per-entity behavior
  baselined on benign — the same class of model OpenUBA ships. The contribution is the correlation +
  explainability + A/B/C evaluation, not the anomaly model. (§6.)
- **Single-host vs the multi-VM plan?** Same pipeline; only capture is offline-pcap instead of inline
  gateway, and entities are relabeled onto synthetic IPs. Features come from real Zeek/Suricata
  output. (`docs/deployment.md`.)
