#!/usr/bin/env bash
# Build the full labeled capture dataset: benign + four attack scenarios, each captured from real
# traffic and turned into Zeek + Suricata telemetry with a ground-truth manifest.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
CAP="bash scripts/run_capture.sh"

echo "############ BENIGN ############"
$CAP benign "port 53 or port 443" -- \
  python3 traffic/benign/generate_benign.py --count 45 --min-sleep 0.2 --max-sleep 1.4

echo "############ DGA ############"
$CAP dga "udp port 53" -- python3 traffic/malicious/dga_sim.py 150

echo "############ DNS TUNNEL ############"
$CAP dns_tunnel "udp port 53" -- \
  python3 traffic/malicious/dns_tunnel_sim.py tunnel.lab "" 30 60

echo "############ BEACON (regular TLS call-home) ############"
$CAP beacon "port 443 or port 53" -- \
  python3 traffic/malicious/beacon_sim.py example.com 3 0.03 14 c2.internal.lab

echo "############ DOH (DNS over HTTPS beacon) ############"
$CAP doh "port 443 or port 53" -- \
  python3 traffic/malicious/doh_sim.py https://cloudflare-dns.com/dns-query 3 12 0.05

echo "############ SUMMARY ############"
for d in benign dga dns_tunnel beacon doh; do
  o="data/captures/$d"
  dns=$( [ -f "$o/dns.log" ] && wc -l < "$o/dns.log" || echo 0 )
  ssl=$( [ -f "$o/ssl.log" ] && wc -l < "$o/ssl.log" || echo 0 )
  conn=$( [ -f "$o/conn.log" ] && wc -l < "$o/conn.log" || echo 0 )
  eve=$( [ -f "$o/eve.json" ] && wc -l < "$o/eve.json" || echo 0 )
  echo "$d: dns=$dns ssl=$ssl conn=$conn eve=$eve"
done
echo "DATASET_BUILD_DONE"
