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
