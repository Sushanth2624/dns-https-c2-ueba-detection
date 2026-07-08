#!/usr/bin/env bash
# Run each endpoint's traffic concurrently while capturing 100% inline on the lab bridge, then
# turn the single mixed capture into Zeek + Suricata telemetry. Produces REAL per-host logs with
# genuine distinct source IPs (no relabeling) — the multi-VM inline-capture design, realized.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT="$ROOT/data/captures/lab"
rm -rf "$OUT"; mkdir -p "$OUT"
PCAP="$OUT/capture.pcap"
DUR="${LAB_DURATION:-70}"

echo "== starting inline capture on labbr0 (${DUR}s budget) =="
tcpdump -i labbr0 -n -w "$PCAP" 'port 53 or port 443 or port 8443' >/dev/null 2>&1 &
TP=$!
sleep 1
START=$(date -u +%FT%TZ)

echo "== launching endpoint traffic (real hosts, concurrent) =="
declare -a PIDS
run() { echo "  [$1] $2"; docker exec "$1" sh -c "$2" >/dev/null 2>&1 & PIDS+=($!); }

run ep-benign1 "python3 /opt/traffic/benign/generate_benign.py --count 30 --min-sleep 0.3 --max-sleep 1.6"
run ep-benign2 "python3 /opt/traffic/benign/generate_benign.py --count 30 --min-sleep 0.3 --max-sleep 1.6"
run ep-benign3 "python3 /opt/traffic/benign/generate_benign.py --count 25 --min-sleep 0.4 --max-sleep 1.8"
run ep-dga     "python3 /opt/traffic/malicious/dga_sim.py 150"
run ep-tunnel  "python3 /opt/traffic/malicious/dns_tunnel_sim.py tunnel.lab '' 30 60"
run ep-beacon  "python3 /opt/traffic/malicious/beacon_sim.py 10.50.0.1 2 0.03 20 c2.internal.lab 8443"
run ep-doh     "python3 /opt/traffic/malicious/doh_sim.py https://cloudflare-dns.com/dns-query 2 15 0.05"

echo "== waiting for endpoints to finish =="
for p in "${PIDS[@]}"; do wait "$p" 2>/dev/null; done
END=$(date -u +%FT%TZ)
sleep 2
kill "$TP" 2>/dev/null; wait "$TP" 2>/dev/null
echo "  captured $(stat -c%s "$PCAP" 2>/dev/null || echo 0) bytes"

echo "== Zeek (JSON + JA3/JA4) =="
( cd "$OUT" && /opt/zeek/bin/zeek -C -r "$PCAP" policy/tuning/json-logs.zeek packages \
    "$ROOT/rules/zeek/c2-indicators.zeek" 2>zeek.err )
echo "  logs: $(ls "$OUT"/*.log 2>/dev/null | xargs -n1 basename | tr '\n' ' ')"

echo "== Suricata (signatures = Config A) =="
suricata -k none -r "$PCAP" -S "$ROOT/rules/suricata/local.rules" -l "$OUT" \
  --set default-log-dir="$OUT" >/dev/null 2>&1
echo "  suricata alerts: $([ -f "$OUT/eve.json" ] && grep -c '"event_type":"alert"' "$OUT/eve.json" || echo 0)"

cat > "$OUT/manifest.json" <<EOF
{"lab":"container-inline","start":"$START","end":"$END",
 "entities":{"10.50.0.11":"benign","10.50.0.12":"benign","10.50.0.13":"benign",
 "10.50.0.21":"dga","10.50.0.22":"dns_tunnel","10.50.0.23":"beacon","10.50.0.24":"doh"}}
EOF

echo "== per-host telemetry (real source IPs) =="
python3 - "$OUT" <<'PY'
import json,sys,collections
o=sys.argv[1]
def load(n):
    try: return [json.loads(l) for l in open(f"{o}/{n}.log")]
    except FileNotFoundError: return []
dns=load("dns"); ssl=load("ssl"); conn=load("conn")
hosts=sorted(set([r.get("id.orig_h") for r in dns+ssl+conn if str(r.get("id.orig_h","")).startswith("10.50")]))
for h in hosts:
    d=sum(1 for r in dns if r.get("id.orig_h")==h)
    s=sum(1 for r in ssl if r.get("id.orig_h")==h)
    nx=sum(1 for r in dns if r.get("id.orig_h")==h and r.get("rcode_name")=="NXDOMAIN")
    snis=set(r.get("server_name") for r in ssl if r.get("id.orig_h")==h and r.get("server_name"))
    print(f"  {h:12s} dns={d:4d} nx={nx:4d} ssl={s:3d} sni={sorted(snis)[:3]}")
PY
echo "lab capture complete -> $OUT"
