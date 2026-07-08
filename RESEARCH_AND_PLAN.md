# Behavioral Detection of Hidden DNS/HTTPS Command-and-Control Communication Using UEBA and Multi-Indicator Analysis

**Research & Implementation Plan — single source of truth**

| | |
|---|---|
| Author | Sushanth Sridhar |
| SRN | R24TF007 |
| Program | MTech in Cyber Security, REVA Academy for Corporate Excellence (RACE) |
| Batch | CS14 |
| Artefact | Capstone 2 — implementation |
| Repo | `dns-https-c2-ueba-detection` |

> This one file is the research background, the full list of what we need, the architecture, and the sprint/phase plan. Everything else in the repo implements what is described here.

---

## 0. One-paragraph summary

Modern C2 hides inside legitimate DNS, HTTPS, and DNS-over-HTTPS (DoH) traffic, defeating signature-only detection. This project builds an isolated lab that generates both benign and hidden-C2 traffic, captures it with Zeek and Suricata, extracts a **set** of behavioral indicators (JA3/JA4, NXDOMAIN behaviour, domain entropy, beacon-interval regularity, communication frequency, session shape), feeds entity behaviour to a **UEBA** layer for baselining and anomaly scoring, and then runs a **Python correlation + explainability layer** — the actual contribution — that fuses the UEBA score with the indicators into an explainable alert (verdict, confidence, contributing evidence, MITRE mapping, next investigation steps). Results are stored in Elasticsearch and shown in Kibana. The research question is whether combining **multiple** behavioral indicators with UEBA beats using indicators in isolation and beats signature-only detection.

---

## 1. Problem & research motivation

Signature and IOC matching fail against C2 that: rides encrypted TLS (payload invisible), looks like ordinary web/DNS traffic, uses low-and-slow beacons, rotates domains via DGA, or tunnels through DoH so the resolver can't be inspected. Defenders are pushed toward **behaviour**: not "is this a known-bad string" but "does this entity behave like it is talking to a controller."

The literature (Section 2) shows individual behavioral signals work, but each in isolation is noisy and evadable. **The gap:** few studies evaluate *multiple* behavioral indicators *together*, combined with UEBA baselining, with *explainable* output, and compared head-to-head against signature-only detection.

### Research question
Does fusing multiple behavioral indicators with UEBA-based anomaly detection improve detection of hidden DNS/HTTPS C2 (higher recall, lower false positives, explainable verdicts) compared with (a) single indicators used alone and (b) signature-only detection?

### Hypothesis
A weighted correlation of UEBA anomaly score + independent behavioral indicators yields higher F1 and fewer false positives than any single indicator or signature ruleset, while producing analyst-usable explanations.

### Contribution (what is genuinely yours)
The lab, the sensors, and OpenUBA are integration. **Your original contribution is the correlation + explainability layer**: the logic that turns "an anomaly score plus a bag of indicators" into a defensible, ranked, explained alert with investigation guidance and MITRE mapping — plus the comparative evaluation that answers the research question.

---

## 2. Literature grounding (from proposal, carried forward)

| # | Work | Year | Takeaway | Gap it leaves |
|---|------|------|----------|----------------|
| 1 | Marchal et al. — Behavioral detection of HTTPS-based malware C2 | 2020 | Beacon timing / repetitive patterns expose C2 even when encrypted | Encrypted payload still opaque; few indicators combined |
| 2 | Jerabek et al. — Measurement & characterization of DoH traffic | 2022 | Resolver behaviour + HTTPS frequency help flag suspicious DoH | DoH-only; no UEBA, no correlation |
| 3 | Singh & Roy — Malicious DoH detection via ensemble ML | 2022 | ML lifts accuracy on encrypted DNS | Dataset-bound; no explainable reasoning |
| 4 | Dawood et al. — Impact of DoH on cyber security | 2024 | Encrypted DNS misuse rising; monitoring must improve | Per-technique focus; false-positive prone |
| 5 | Thomson et al. — TLS fingerprinting via feature expansion + similarity | 2024 | JA3/JA4-style fingerprinting is discriminative | Fingerprint in isolation; evadable alone |

**Consolidated gap:** JA3, DoH, and beaconing are each studied alone. Little work fuses them with UEBA and outputs explainable alerts, or benchmarks behavioral-multi-indicator vs signature-only. This project fills that.

---

## 3. Threat model — what we detect and how it shows up

| Stealth technique | Observable behaviour | Primary indicator(s) | MITRE ATT&CK |
|---|---|---|---|
| DNS tunneling | Long/high-entropy labels, TXT/NULL/CNAME heavy, high query volume to one zone | entropy, query length, qtype mix, frequency | T1071.004, T1048.003 |
| Beaconing / periodic C2 | Regular call-home interval, low jitter, small consistent payloads | beacon regularity, session shape | T1071.001, T1571 |
| DNS-over-HTTPS (DoH) C2 | TLS to known//dns-query DoH endpoints, DNS "disappears" from port 53 | DoH endpoint match, TLS SNI/JA3, freq | T1071.004, T1572 |
| Domain Generation Algorithm | Bursts of NXDOMAIN, high-entropy random domains, short TTLs | NXDOMAIN rate, entropy, domain age/rarity | T1568.002 |
| JA3/JA4 evasion | Rare or known-bad TLS client fingerprint, JA3↔SNI mismatch | JA3/JA4 rarity + mismatch | T1573, T1071.001 |
| NXDOMAIN abuse | Elevated failed lookups per host | NXDOMAIN ratio | T1568 |
| Encrypted HTTPS C2 | Periodic small POSTs, steady up/down byte ratio, long-lived low-volume flows | session shape, beacon regularity, JA3 | T1071.001, T1573 |

The point: no single row is conclusive. **Correlation across rows is the detector.**

---

## 4. Behavioral indicators — definitions and how each is computed

Each indicator is a function `features(entity, window) -> value`, computed from Zeek/Suricata logs. All are implemented under `src/c2detect/indicators/`.

1. **Domain entropy** (`entropy.py`) — Shannon entropy of the queried domain / longest label. High entropy → DGA or tunneling. Data: Zeek `dns.log` (`query`).
2. **NXDOMAIN rate & ratio** (`nxdomain.py`) — count and fraction of `rcode == NXDOMAIN` per host per window. Bursts → DGA. Data: Zeek `dns.log` (`rcode_name`).
3. **Query/label length & subdomain depth** — mean/max label length and label count; long, deep names → tunneling. Data: `dns.log`.
4. **Query-type mix** — fraction of TXT/NULL/CNAME/A; TXT/NULL-heavy → tunneling. Data: `dns.log` (`qtype_name`).
5. **Beacon-interval regularity** (`beaconing.py`) — for each (src→dst) pair, inter-arrival times → coefficient of variation, and/or FFT/autocorrelation peak. Low jitter + strong periodicity → beacon. Data: Zeek `conn.log` / `ssl.log` timestamps.
6. **Communication frequency & fan-out** — connections per dest, unique dests per host, bytes/flow. Steady low-volume repeat contact is suspicious. Data: `conn.log`.
7. **JA3 / JA4 fingerprint** (`ja3ja4.py`) — TLS client fingerprint; flag rare fingerprints, known-bad lists, and JA3↔SNI mismatch. Data: Zeek `ssl.log` (JA3 plugin) / Suricata `eve.json` TLS.
8. **DoH detection** (`doh.py`) — match SNI/IP against known DoH providers, and HTTPS requests to `/dns-query`; flag DNS traffic that vanished from port 53 while DoH rose. Data: `ssl.log`, `http.log`, resolver lists.
9. **Session shape** (`session.py`) — duration, up/down byte ratio, packet-size consistency; small, steady, long-lived flows → encrypted C2. Data: `conn.log`.

Each indicator outputs both a **raw value** and a **normalized 0–1 sub-score** with a documented threshold, so the correlation layer can weight them.

---

## 5. Architecture (corrected for the real lab)

```
 ESXi:  [Windows VM]   [Ubuntu VM]        Proxmox: [Linux Mint VM]
             \             |                          /
              \            |                         /
               \      LAB NETWORK (endpoints route through Analysis VM)
                \          |                       /
                 v         v                      v
        ┌───────────────────────────────────────────────────┐
        │  ANALYSIS VM (Ubuntu 24.04, 8 vCPU / 16 GB / 300GB) │
        │  NIC1 = mgmt   NIC2 = lab gateway (inline capture)  │
        │                                                     │
        │  Zeek ─┐   Suricata ─┐   (see ALL endpoint traffic  │
        │        │             │    because it is inline)     │
        │        v             v                              │
        │   parsers  →  behavioral indicators (Section 4)     │
        │        │                                            │
        │        v                                            │
        │   UEBA layer  =  OpenUBA  OR  baseline_model.py      │
        │   (anomaly_score, risk_score, severity per entity)  │
        │        │   << decoupling contract, Section 6 >>     │
        │        v                                            │
        │   CORRELATION ENGINE  +  EXPLAINABILITY  (Sec 7)     │  <-- your contribution
        │        │                                            │
        │        v                                            │
        │   Elasticsearch  ───────────────►  Kibana dashboards│
        └───────────────────────────────────────────────────┘
```

**Two corrections baked in versus the proposal diagram:**

- **Inline capture, not port-mirror.** The endpoints live on ESXi *and* Proxmox; you cannot SPAN/mirror a vSwitch on one physical host into a VM on another. So the Analysis VM is the **gateway + DNS resolver** for the endpoints (second NIC). All endpoint DNS/HTTPS flows through it, so Zeek/Suricata see 100% inline. Prerequisite: a routable lab network shared between the two hosts. **Prove this in Sprint 0 before anything else.**
- **UEBA is pluggable.** The pipeline talks to a UEBA *contract* (Section 6), not to OpenUBA directly, so OpenUBA cannot become a single point of failure.

---

## 6. The UEBA layer and the decoupling contract (critical de-risk)

**OpenUBA status (verify at install):** OpenUBA is open-source but is flagged in current references as possibly unmaintained and validate-before-use; UEBA historically needs *weeks* of activity before baselines are useful. Its newest release is Kubernetes-native (Next.js + FastAPI + PostGraphile + a K8s operator + Spark + Elasticsearch) — heavy for one 16 GB VM. Treat OpenUBA as a **spike with a go/no-go gate**, not a certainty.

**Contract (what the rest of the system depends on).** Whatever produces the UEBA scores must emit, per entity per window:

```json
{
  "entity": "10.10.10.15",
  "window_start": "2026-07-06T10:00:00Z",
  "window_end":   "2026-07-06T10:05:00Z",
  "anomaly_score": 0.87,
  "risk_score": 74,
  "severity": "high",
  "features": { "dns_entropy": 4.2, "nxdomain_rate": 0.31, "beacon_cv": 0.04 }
}
```

Two interchangeable producers implement this contract:

- `ueba/openuba_client.py` — reads OpenUBA's outputs (its Elasticsearch index or export) and maps them onto the contract.
- `ueba/baseline_model.py` — a self-contained fallback: an sklearn **IsolationForest** (plus z-score) over the same feature vectors. This is exactly the model OpenUBA ships as its own default, so using it is *still* legitimately "UEBA-based anomaly detection" — defensible in the viva.

**Decision rule:** if the OpenUBA spike (Sprint 0) doesn't produce the contract cleanly within its time-box, switch to `baseline_model.py` and keep OpenUBA as "evaluated, deprioritized for stability" in the report. Nothing downstream changes.

---

## 7. Correlation & explainability layer — your contribution

Input: the UEBA contract record + the per-entity indicator sub-scores. Output: an explainable alert.

**Scoring.** `confidence = f(anomaly_score, Σ wᵢ·indicatorᵢ)` — a transparent weighted model (weights in `correlation/rules.py`, tunable and reported). Rules add hard boosts for high-signal combinations (e.g. high entropy + NXDOMAIN burst + rare JA3). Everything is glass-box so you can *explain* every verdict — that is the whole point versus black-box ML.

**Explainable alert schema** (written to Elasticsearch, rendered in Kibana):

```json
{
  "alert_id": "…",
  "entity": "10.10.10.15",
  "verdict": "likely_c2",
  "confidence": 0.91,
  "severity": "high",
  "ueba": { "anomaly_score": 0.87, "risk_score": 74 },
  "contributing_indicators": [
    { "name": "dns_entropy",   "value": 4.2,  "weight": 0.25, "why": "domains near-random, consistent with DGA/tunneling" },
    { "name": "nxdomain_rate", "value": 0.31, "weight": 0.20, "why": "31% failed lookups — DGA hallmark" },
    { "name": "beacon_cv",     "value": 0.04, "weight": 0.30, "why": "call-home every ~60s, jitter <5% — automated beacon" },
    { "name": "ja3_rarity",    "value": 0.98, "weight": 0.15, "why": "TLS fingerprint unseen in baseline" }
  ],
  "mitre": ["T1071.004", "T1568.002", "T1571"],
  "recommended_actions": [
    "Isolate host 10.10.10.15 and capture full pcap",
    "Pull process→network mapping on the host for the beaconing process",
    "Block the destination and resolver; hunt the domain across other hosts"
  ]
}
```

The reasoner (`explain/reasoner.py`) generates the `why` strings and `recommended_actions` from templates keyed to which indicators fired — deterministic, auditable, no LLM required.

---

## 8. Evaluation methodology (the research payoff)

**Baseline establishment.** Run only benign generators for a defined window (target: a continuous benign period long enough to populate baselines — in the compressed lab, generate benign DNS/HTTPS continuously for the agreed duration and document it; be ready to justify it in the viva). Baseline is frozen before attacks are injected.

**Labeled scenarios.** Benign, plus one run per attack type (beacon, DNS tunnel, DoH C2, DGA), each with known ground truth (source host, start/stop time) so every alert can be scored TP/FP/FN.

**Metrics.** Precision, recall, F1, false-positive rate, and detection latency (time from attack start to first correct alert).

**Core comparison — this answers the research question:**

| Configuration | What it is |
|---|---|
| A. Signature-only | Suricata rules alone |
| B. Single indicator | each indicator alone (entropy-only, beacon-only, JA3-only, …) |
| C. Multi-indicator + UEBA | the full correlation layer (this project) |

Hypothesis holds if **C** > **B** > **A** on F1 and false-positive rate. Present as tables + bar/ROC-style plots. This comparison, plus explainability, *is* your novelty.

---

## 9. Everything we need (tooling, data, environment)

### 9.1 Virtualization & VMs (as built)
- **Proxmox:** Linux Mint endpoint; Ubuntu 24.04 Analysis VM (8 vCPU / 16 GB / 300 GB, CPU type = host, QEMU guest agent).
- **ESXi:** Windows endpoint; Ubuntu endpoint.
- Shared **lab network** so endpoints can route through the Analysis VM (inline capture).

### 9.2 Software (pin latest stable at install; confirm versions in Sprint 0)
| Component | Target | Role |
|---|---|---|
| Ubuntu | 24.04.2 LTS | Analysis VM OS |
| Python | 3.12 | correlation engine, sims |
| Zeek | 7.x stable | DNS/SSL/HTTP/conn telemetry + JA3 plugin |
| Suricata | 7.x stable | signature baseline + TLS/JA3, eve.json |
| Elasticsearch | 8.15+ (or 9.x — pin one) | storage/search |
| Kibana | match ES | dashboards |
| OpenUBA | pinned release/commit after spike | UEBA (with fallback) |
| scikit-learn | 1.4+ | fallback IsolationForest baseline |
| pandas / numpy / scipy | current | feature engineering, FFT/autocorr |
| elasticsearch-py | match ES major | write alerts |

### 9.3 Attack/traffic tooling (lab-only, isolated)
- **Benign generators:** scripted normal DNS lookups + HTTPS browsing patterns (`traffic/benign/`).
- **Beaconing:** simple scripted call-home at fixed interval + jitter (`beacon_sim.py`).
- **DNS tunneling:** `iodine` or `dnscat2`, or a scripted TXT-exfil simulator (`dns_tunnel_sim.py`).
- **DoH C2:** requests to a public DoH resolver `/dns-query`, or a scripted DoH channel (`doh_sim.py`).
- **DGA:** scripted pseudo-random domain generator producing NXDOMAINs (`dga_sim.py`).
- Optional public reference datasets for cross-checking indicators: CIRA-CIC-DoHBrw-2020 (DoH), CIC-Bell-DNS, and DGA domain lists. Use only to validate feature logic, not as the primary result.

> **Ethics/safety:** every attack tool runs inside the isolated lab against your own hosts. No real C2, no external targets.

---

## 10. Repository layout

```
dns-https-c2-ueba-detection/
├── README.md                     project overview + quickstart
├── RESEARCH_AND_PLAN.md          <-- this file
├── requirements.txt
├── Makefile                      convenience targets
├── .gitignore
├── config/
│   └── config.example.yaml       paths, thresholds, ES, UEBA source, weights
├── docs/
│   └── viva-prep.md              likely questions → where answered
├── src/c2detect/
│   ├── config.py                 load config
│   ├── pipeline.py               orchestrates parse→indicators→ueba→correlate→explain→store
│   ├── cli.py                    entrypoint
│   ├── parsers/{zeek.py,suricata.py}
│   ├── indicators/{entropy,beaconing,nxdomain,dga,ja3ja4,doh,session}.py
│   ├── ueba/{openuba_client.py,baseline_model.py}   contract + fallback
│   ├── correlation/{engine.py,rules.py}             your scoring
│   ├── explain/reasoner.py                          explainable alerts
│   └── output/elastic.py                            write to ES
├── rules/
│   ├── suricata/local.rules      signature baseline (config A)
│   └── zeek/c2-indicators.zeek   Zeek-side helpers/JA3
├── traffic/
│   ├── benign/generate_benign.py
│   └── malicious/{beacon_sim,dns_tunnel_sim,doh_sim,dga_sim}.py
├── dashboards/kibana/            saved objects (.ndjson) — added in Phase 6
├── scripts/healthcheck.sh
└── tests/test_indicators.py
```

---

## 11. Sprint & phase plan

Sprints are ~1–2 weeks; adjust to your calendar. Each has an **exit gate** — don't advance until it's met — and a **viva artefact** you can show.

### Phase 0 — Foundation & de-risk  ·  **Sprint 0**
- **Goal:** repo live; capture path proven; UEBA go/no-go decided.
- **Tasks:** push repo to GitHub (private); create Python venv, `pip install -r requirements.txt`; make Analysis VM the inline gateway/resolver for one endpoint; install Zeek + Suricata; stand up Elasticsearch + Kibana; run the OpenUBA spike time-boxed; wire `baseline_model.py` as fallback.
- **Exit gate:** a single benign DNS + HTTPS request from an endpoint appears in Zeek `dns.log`/`ssl.log` on the Analysis VM **and** lands in Elasticsearch. OpenUBA decision recorded.
- **Artefact:** screenshot of endpoint traffic captured inline + ES doc.

### Phase 1 — Telemetry & feature extraction  ·  **Sprints 1–2**
- **Goal:** logs → per-entity feature vectors.
- **Tasks:** tune Zeek (DNS/SSL/HTTP/conn) + enable JA3/JA4; tune Suricata TLS + eve.json; implement `parsers/`; implement all `indicators/` with normalized sub-scores + unit tests; build benign generators (needed for baseline next).
- **Exit gate:** given a captured log/pcap, the pipeline emits a complete feature vector per entity; `pytest` green on indicators.
- **Artefact:** feature table for a benign sample + passing tests.

### Phase 2 — UEBA baselining & anomaly scoring  ·  **Sprint 3**
- **Goal:** produce the UEBA contract per entity.
- **Tasks:** run benign period; produce baselines; emit `anomaly_score`/`risk_score`/`severity` via chosen producer (OpenUBA or fallback); validate contract shape.
- **Exit gate:** benign entities score low; a manually planted anomaly scores high; records match the contract.
- **Artefact:** scored entity list showing separation.

### Phase 3 — Correlation & explainability  ·  **Sprints 4–5**  *(core contribution)*
- **Goal:** explainable alerts end-to-end.
- **Tasks:** implement `correlation/engine.py` + `rules.py` (weights) and `explain/reasoner.py`; write alerts to ES via `output/elastic.py`; map indicators→MITRE + investigation steps.
- **Exit gate:** an injected beacon scenario produces one explainable alert in ES with correct contributing indicators, confidence, MITRE, and actions.
- **Artefact:** the alert JSON + a Kibana view of it.

### Phase 4 — Attack simulation & labeled data  ·  **Sprint 6**
- **Goal:** labeled runs for evaluation.
- **Tasks:** finalize `beacon_sim`, `dns_tunnel_sim`, `doh_sim`, `dga_sim`; run each with recorded ground truth (host, start/stop); capture benign + each attack end-to-end.
- **Exit gate:** labeled dataset covering benign + all four attack types captured through the full pipeline.
- **Artefact:** run log / label manifest.

### Phase 5 — Evaluation & comparison  ·  **Sprint 7**
- **Goal:** answer the research question.
- **Tasks:** compute precision/recall/F1/FP-rate/latency for configs A (signature-only), B (single-indicator), C (multi+UEBA); produce tables + plots.
- **Exit gate:** results showing C vs B vs A; hypothesis supported or honestly refuted.
- **Artefact:** results tables + comparison chart.

### Phase 6 — Dashboards, hardening, report & viva  ·  **Sprint 8**
- **Goal:** demo-ready + defensible.
- **Tasks:** Kibana dashboards (export to `dashboards/kibana/`); stabilize; write thesis chapters; rehearse a fixed demo path; complete `docs/viva-prep.md`.
- **Exit gate:** one-command/one-path reproducible demo + written report + every design decision defended.
- **Artefact:** the demo + report.

**Cross-cutting:** benign traffic generation starts in Phase 1 (baseline needs it); documentation and git-commit-per-sprint run throughout.

---

## 12. Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| OpenUBA unmaintained / too heavy for 16 GB | Could sink the project | Time-boxed spike + `baseline_model.py` fallback behind the UEBA contract |
| Cross-hypervisor capture doesn't work | No data at all | Inline gateway (not port-mirror); prove in Sprint 0 before building |
| UEBA baseline too short to be meaningful | Weak/indefensible results | Defined continuous benign window; document methodology; frozen baseline |
| Analysis VM resource exhaustion | Instability during demo | Watch ES heap; keep OpenUBA off the box if using fallback; `scripts/healthcheck.sh` |
| JA4 tooling immature vs JA3 | Missing indicator | JA3 is first-class in Zeek/Suricata; treat JA4 as best-effort add-on |
| Scope creep (more indicators/features) | Miss deadline | Freeze indicator set after Phase 1; stability > features |
| Attack sims too "clean" (trivially detected) | Inflated results | Add jitter/noise; mix with heavy benign so detection is non-trivial |

---

## 13. Viva readiness checklist

- **Why behavioral, not signatures?** → §1, §3, §8 comparison.
- **What exactly is your contribution?** → §1 contribution, §7 correlation/explainability.
- **How did you establish the baseline?** → §8 baseline establishment.
- **Why is a verdict trustworthy / not a black box?** → §7 glass-box weighting + `why` strings.
- **What if OpenUBA is just an IsolationForest?** → §6: yes, and that's a legitimate UEBA model; the novelty is the correlation + explainability + evaluation, not the anomaly model.
- **How do you know it's better than single indicators?** → §8 A/B/C comparison with metrics.
- **How does your sensor see ESXi traffic from Proxmox?** → §5 inline gateway.
- **MITRE mapping?** → §3 table + per-alert `mitre` field.

---

## 14. References
1. S. Marchal et al., "Behavioral detection of HTTPS-based malware command and control traffic," ACM Computing Surveys, 2020.
2. K. Jerabek, O. Rysavy, I. Burgetova, "Measurement and characterization of DNS over HTTPS traffic," arXiv, 2022.
3. S. K. Singh, P. K. Roy, "Malicious traffic detection of DNS over HTTPS using ensemble machine learning," IJCDS, 2022.
4. M. Dawood et al., "The impact of DNS over HTTPS on cyber security: limitations, challenges and detection techniques," CMC, 2024.
5. A. Thomson, L. Maglaras, H. Janicke, "A novel TLS-based fingerprinting approach combining feature expansion and similarity mapping," Future Internet, 2024.
6. GACWR/OpenUBA — open-source UEBA framework (validate maintenance status before relying on it).
