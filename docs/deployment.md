# Single-host deployment (Analysis VM)

This is the as-built deployment on one Ubuntu 24.04 VM. It adapts the multi-VM inline-gateway
design (RESEARCH_AND_PLAN.md §5) to a single host: **this VM is both endpoint and sensor.** Traffic
generators run locally, are captured with `tcpdump`, and Zeek + Suricata process the pcaps offline.
Everything downstream (indicators → UEBA → correlation → explainable alerts → Elasticsearch →
Kibana) is unchanged, so the contribution and evaluation are identical to the multi-VM plan.

## Installed stack (versions as built)

| Component | Version | Notes |
|---|---|---|
| Ubuntu | 24.04.4 LTS | Analysis VM |
| Python | 3.12 | venv at `.venv/` |
| Zeek | 8.2.1 | `/opt/zeek`; JA3 (`salesforce/ja3`) + JA4 (`foxio/ja4`) packages via `zkg` |
| Suricata | 8.0.5 | signature baseline (Config A) + TLS/JA3 |
| Elasticsearch | 8.19 | single-node, security disabled (lab), bound to `localhost` |
| Kibana | 8.19 | `localhost:5601` |
| scikit-learn | ≥1.4 | IsolationForest + z-score UEBA fallback |

## Install (reproduce)

```bash
# 1. Python
sudo apt-get install -y python3.12-venv
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt

# 2. Sensors
sudo add-apt-repository -y ppa:oisf/suricata-stable && sudo apt-get install -y suricata
echo 'deb http://download.opensuse.org/repositories/security:/zeek/xUbuntu_24.04/ /' \
  | sudo tee /etc/apt/sources.list.d/security:zeek.list
curl -fsSL https://download.opensuse.org/repositories/security:zeek/xUbuntu_24.04/Release.key \
  | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/security_zeek.gpg >/dev/null
sudo apt-get update && sudo apt-get install -y zeek
export PATH=/opt/zeek/bin:$PATH && zkg autoconfig
zkg install --force https://github.com/salesforce/ja3 zeek/foxio/ja4

# 3. Elasticsearch + Kibana
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch \
  | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] \
https://artifacts.elastic.co/packages/8.x/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo apt-get update && sudo apt-get install -y elasticsearch kibana
```

**Elasticsearch config** (`/etc/elasticsearch/elasticsearch.yml`): `discovery.type: single-node`,
`http.host: 0.0.0.0` (reachable on the VM's LAN IP), heap capped at 2 GB.

### Security (authentication + TLS)

Elasticsearch runs with `xpack.security.enabled: true` and TLS on both the HTTP and transport
layers (auto-generated CA + node certs under `/etc/elasticsearch/certs/`). So:

- ES is **HTTPS-only** and rejects unauthenticated requests.
- The `elastic` and `kibana_system` passwords are set with `elasticsearch-reset-password` and stored
  in **`config/secrets.env`** (gitignored — never committed).
- Kibana connects to ES over TLS as `kibana_system` (`/etc/kibana/kibana.yml`) and now shows a
  **login page**; sign in as `elastic`.
- Every tool reads the ES password from the `ELASTIC_PASSWORD` env var or `config/secrets.env`:
  the pipeline (`c2detect.cli run`), `scripts/ingest_es.py`, and `scripts/build_dashboards.py`
  (which authenticates to the Kibana API). Committed configs contain **no passwords**.

```bash
source config/secrets.env          # exports ELASTIC_PASSWORD etc.
curl -k -u elastic:$ELASTIC_PASSWORD https://localhost:9200/_cluster/health
```

To rotate a password: `sudo /usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic -b
--url https://localhost:9200`, then update `config/secrets.env`.

## Key single-host adaptations (and why they are faithful)

- **Offline pcap capture, not port-mirror.** `scripts/run_capture.sh <label> <bpf> -- <generator>`
  runs a generator, captures with `tcpdump`, then runs Zeek (`-C`, JSON logs, JA3/JA4) and Suricata
  (`-k none`) over the pcap. `-C` / `-k none` are required because NIC checksum offload marks
  captured packets with invalid checksums, which Suricata would otherwise drop before TLS parsing.
- **tcpdump writes only under `/home`.** Ubuntu's AppArmor profile for `tcpdump` blocks `/root`;
  all capture output lives under the project's `data/`.
- **Local "C2" for the beacon.** A real LAN C2 has sub-ms latency, giving a tight beacon interval.
  Over the internet, TLS handshake jitter inflates the timing CV (~0.36) and hides the beacon. So
  the beacon target is a local `openssl s_server` on `127.0.0.1:8443` (SNI `c2.internal.lab`),
  captured on `lo` — CV drops to ~0.02, matching a real LAN implant. Start it before capturing:
  ```bash
  cd data/tmp/c2srv && openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem \
    -days 2 -nodes -subj "/CN=c2.internal.lab"
  openssl s_server -quiet -accept 8443 -cert cert.pem -key key.pem -naccept 999 &
  ```
- **Distinct client fingerprints fall out naturally.** Benign traffic uses `curl` (one JA3); the
  Python attack sims use their own TLS stacks (different JA3s), so `ja3_rarity` measures the
  implant fingerprint against a frozen benign baseline — no hand-tuning.
- **Multi-entity corpus.** Because every packet has this host's source IP, `eval/corpus.py`
  relabels each capture onto a synthetic entity IP (benign `10.10.20.x`, attacks `10.10.10.1x`) and
  blends benign background into each attack entity so detection is non-trivial. Features are still
  computed from **real** Zeek output — only the entity label is synthetic.

## Real multi-host lab (container endpoints, inline capture)

This VM has no nested virtualization (`vmx`/`svm` not exposed, no `/dev/kvm`), so hardware VMs can't
run here. Instead the endpoints are **Docker containers** on a lab bridge, which realizes the plan's
inline-gateway architecture faithfully — each endpoint is a distinct host with its own IP and TLS
fingerprint, and this VM is their gateway + DNS resolver, so Zeek/Suricata capture **100% inline**
with **real per-host source IPs (no relabeling)**.

```
 ┌──────────── Analysis VM (gateway 10.50.0.1, dnsmasq resolver, local C2 :8443) ───────────┐
 │  labbr0 bridge ── tcpdump (inline) ── Zeek + Suricata ── indicators ── UEBA ── correlate  │
 └───────┬───────┬───────┬───────┬───────┬───────┬───────┬──────────────────────────────────┘
   ep-benign1  benign2  benign3  ep-dga  ep-tunnel ep-beacon ep-doh     (7 container endpoints)
   10.50.0.11   .12      .13     .21      .22       .23       .24
```

```bash
make lab-up        # create bridge + dnsmasq + local C2 + 7 endpoint containers
make lab-capture   # run all endpoints' traffic, capture inline, build Zeek+Suricata logs
make evaluate-lab  # A/B/C on the real capture (distinct source IPs)
make lab-demo      # all of the above -> alerts + telemetry to ES -> Kibana dashboards
make lab-down      # tear down containers + helpers
```

Result on real inline data (7 hosts: 3 benign, 4 attack): **F1 C=1.00 > A/B=0.67, FPR C=0.00**.
`docker ps` shows the live endpoint hosts; `data/captures/lab/` holds their real Zeek/Suricata logs.

## Single-host demo (no Docker)

```bash
make demo          # capture on the host NIC -> A/B/C evaluation -> alerts to ES -> Kibana dashboard
make health        # stack health check
```
Then open Kibana → Dashboards → **"DNS/HTTPS C2 — Behavioral Detection"**.

Results land in `data/eval/` (`report.md`, `results.json`, `charts/`). Dashboards are exported to
`dashboards/kibana/c2-dashboards.ndjson` (importable into any Kibana).
