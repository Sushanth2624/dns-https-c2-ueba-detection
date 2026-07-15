# Demo Runbook — how to run and check everything by hand

This is the operator's guide for demonstrating the project live. Every command is copy-paste ready.
Run them from the project directory on the analysis machine:

```bash
cd /home/analysis/dns-https-c2-ueba-detection
source config/secrets.env        # loads ELASTIC_PASSWORD into your shell — do this first, every session
```

---

## 0. What exists and where (the honest map)

**There is ONE machine.** Everything below runs on it.

| Thing | What it is | Where |
|---|---|---|
| **Analysis VM** | The one real machine. Ubuntu 24.04, you are `root`. | IP `172.16.242.14` |
| **14 "endpoint hosts"** | **Docker containers** on the machine (NOT separate VMs). Distinct IPs `10.50.0.11–.28`. | `docker ps` |
| **Zeek 8.2.1** | Network sensor → structured logs | on the machine |
| **Suricata 8.0.5** | Signature engine (Config A baseline) | on the machine |
| **Elasticsearch 8.19** | Database (stores alerts, scores, telemetry) | `https://172.16.242.14:9200` |
| **Kibana 8.19** | Dashboards UI | `https://172.16.242.14:5601` |

> **Why containers, not VMs?** This machine has no nested virtualization, so it can't run full VMs
> inside itself. Containers give the same thing that matters for detection: separate hosts, distinct
> IPs, and real per-host traffic captured inline.

---

## 1. Credentials — who logs into what

| System | How you access it | Username | Password |
|---|---|---|---|
| **Analysis VM** | However you already log into it (console / SSH) | your normal login | your normal login |
| **The 14 containers** | `docker exec` — **no password** (you're root on the host) | — | — |
| **Kibana (dashboards)** | Browser → the URL, log in | `elastic` | in `config/secrets.env` |
| **Elasticsearch (API)** | `curl -u elastic:PASSWORD` | `elastic` | in `config/secrets.env` |

Show the passwords on the machine any time with:
```bash
cat config/secrets.env
```
(The `kibana_system` account is internal only — never log in with it.)

---

## 2. Check the whole stack is healthy (do this before the demo)

```bash
make health
```
Or check each piece by hand:
```bash
systemctl is-active elasticsearch kibana docker      # all should say 'active'
docker ps --format '{{.Names}}  {{.Label "c2lab.role"}}  {{.Status}}'   # 14 hosts, all 'Up'
curl -s -k -u elastic:$ELASTIC_PASSWORD https://localhost:9200/_cluster/health?pretty | grep status
curl -s -k -o /dev/null -w 'kibana http=%{http_code}\n' https://localhost:5601/api/status
```

---

## 3. See the "hosts" and get inside one

```bash
# list the 14 endpoint hosts (containers)
docker ps --format '{{.Names}}\t{{.Label "c2lab.role"}}'

# get a shell INSIDE a host (no password — docker exec)
docker exec -it ep-dga-alpha sh
#   inside: run `hostname -i` to see its IP (10.50.0.21), then `exit`

# see a host's identity in one line
docker exec ep-dga-alpha sh -c 'echo "I am $(hostname) at $(hostname -i)"'
```

Map of the hosts:

| Container | IP | Role |
|---|---|---|
| ep-benign1 … 6 | 10.50.0.11–.16 | normal traffic |
| ep-dga-alpha / beta | 10.50.0.21 / .22 | DGA |
| ep-tunnel-sm / lg | 10.50.0.23 / .24 | DNS tunneling |
| ep-beacon-fast / slow | 10.50.0.25 / .26 | beaconing |
| ep-doh-cf / quad9 | 10.50.0.27 / .28 | DNS-over-HTTPS |

---

## 4. How logs come in — watch it happen live

The flow is: **container makes traffic → tcpdump captures on the bridge → Zeek/Suricata write logs →
Python scores them → results pushed to Elasticsearch → Kibana shows them.**

### 4a. Make a host generate attack traffic on demand
```bash
# DGA host resolves 20 random domains (they fail = NXDOMAIN)
docker exec ep-dga-alpha python3 /opt/traffic/malicious/dga_sim.py 20

# beacon host calls home 6 times, 2s apart
docker exec ep-beacon-fast python3 /opt/traffic/malicious/beacon_sim.py 10.50.0.1 2 0.03 6 c2.internal.lab 8443
```

### 4b. Re-capture and re-process everything (the full pipeline)
```bash
make lab-demo
```
This runs, in order: create/refresh hosts → capture inline → Zeek+Suricata → score (A/B/C) →
push alerts + telemetry to Elasticsearch → rebuild dashboards. Takes a few minutes.

### 4c. Look at the raw logs on disk (proof the sensors work)
```bash
# a DGA record Zeek wrote (host, the random name, and NXDOMAIN)
head -1 data/captures/lab/dns.log | python3 -m json.tool

# a beacon's TLS record (its JA3 fingerprint and the C2 domain it contacted)
grep '10.50.0.25' data/captures/lab/ssl.log | head -1 | python3 -m json.tool

# a Suricata signature alert
grep '"event_type":"alert"' data/captures/lab/eve.json | head -1 | python3 -m json.tool
```

---

## 5. Check the data IN Elasticsearch by hand

```bash
# how many of each thing is stored
for i in c2-alerts c2-entity-scores zeek-dns zeek-ssl zeek-conn suricata-alerts; do
  echo -n "$i: "; curl -s -k -u elastic:$ELASTIC_PASSWORD https://localhost:9200/$i/_count | python3 -c "import sys,json;print(json.load(sys.stdin)['count'])"
done

# the alerts, most-suspicious first
curl -s -k -u elastic:$ELASTIC_PASSWORD "https://localhost:9200/c2-alerts/_search?size=20&sort=confidence:desc" \
  | python3 -c "import sys,json;[print(h['_source']['entity'],h['_source']['verdict'],h['_source']['confidence']) for h in json.load(sys.stdin)['hits']['hits']]"

# ONE full alert document (verdict, why, MITRE, actions) — great to show
curl -s -k -u elastic:$ELASTIC_PASSWORD "https://localhost:9200/c2-alerts/_search" \
  -H 'Content-Type: application/json' -d '{"size":1,"query":{"term":{"entity":"10.50.0.21"}}}' | python3 -m json.tool
```

---

## 6. Show the dashboards (the main visual demo)

Open a browser **on the machine** (or from your laptop if it can reach `172.16.242.14`):

- Kibana: **https://172.16.242.14:5601** → accept the certificate warning → log in `elastic` / (your password)
- Executive overview: `…/app/dashboards#/view/c2-exec`
- Threat detail (the heatmap): `…/app/dashboards#/view/c2-threat`
- Network telemetry: `…/app/dashboards#/view/c2-telemetry`

> **In Kibana, set the time picker (top-right) to "Last 24 hours"** or the panels look empty.
> The certificate warning is expected (self-signed lab cert) — click *Advanced → Proceed*.

If you are demoing from your **laptop** and can't reach the IP, run this on the laptop instead to
tunnel the ports over SSH, then use `https://localhost:5601`:
```bash
ssh -L 5601:localhost:5601 -L 9200:localhost:9200 <your-login>@172.16.242.14
```

---

## 7. Show the A/B/C result (the research payoff)

```bash
make evaluate-lab          # prints F1 for A (signatures), B (best single), C (this project)
cat data/eval/lab/report.md
```
Expected: **F1  A ≈ 0.55   B ≈ 0.67   C = 1.00**, false positives = 0 for C.

---

## 8. A clean 5-minute demo script (what to click/type on the day)

1. `make health` — "the stack is up: 14 hosts, Zeek, Suricata, Elasticsearch, Kibana."
2. `docker ps` — "here are the 14 endpoint hosts, each with its own IP."
3. `docker exec ep-dga-alpha python3 /opt/traffic/malicious/dga_sim.py 20` — "this host now behaves like DGA malware."
4. `make lab-demo` — "capture → sensors → detection → Elasticsearch → dashboards." (or say it's pre-run)
5. Open **c2-exec** dashboard — "14 hosts, 8 threats, 0 false positives, and A vs B vs C: our system scores 1.0."
6. Open **c2-threat** — "the heatmap shows exactly which behaviour fired for each host."
7. Show one alert JSON (section 5) — "every verdict is explained: why, MITRE, and what to do."
8. `cat data/eval/lab/report.md` — "measured head-to-head, behaviour + UEBA beats signatures."

---

## 9. If something looks wrong

| Symptom | Fix |
|---|---|
| Dashboards empty | Set Kibana time to **Last 24 hours**; or re-run `make lab-demo` |
| `curl` says "unauthorized" | You forgot `source config/secrets.env` |
| ES not responding | `sudo systemctl restart elasticsearch` (it also auto-restarts on failure) |
| A container is down | `make lab-up` recreates all 14 |
| Browser blocks the page | It's the self-signed cert — click *Advanced → Proceed to 172.16.242.14* |

---

**Repository:** github.com/Sushanth2624/dns-https-c2-ueba-detection
**Other docs:** `docs/full-report.html` (whitepaper), `docs/architecture.html`,
`docs/pin-to-pin-walkthrough.html` (the exact mechanics).
