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

echo "############ BEACON (regular TLS call-home to local LAN C2) ############"
# Stand up a local TLS 'C2' listener so beacon timing reflects a LAN implant (sub-ms latency),
# not internet handshake jitter. Captured on loopback.
C2DIR="data/tmp/c2srv"; mkdir -p "$C2DIR"
[ -f "$C2DIR/cert.pem" ] || openssl req -x509 -newkey rsa:2048 -keyout "$C2DIR/key.pem" \
  -out "$C2DIR/cert.pem" -days 2 -nodes -subj "/CN=c2.internal.lab" >/dev/null 2>&1
if ! ss -ltn 2>/dev/null | grep -q ':8443'; then
  ( cd "$C2DIR" && setsid openssl s_server -quiet -accept 8443 -cert cert.pem -key key.pem \
      -naccept 999 </dev/null >/dev/null 2>&1 ) &
  disown 2>/dev/null || true
  sleep 1
fi
CAP_IFACE=lo $CAP beacon "tcp port 8443" -- \
  python3 traffic/malicious/beacon_sim.py 127.0.0.1 2 0.03 15 c2.internal.lab 8443

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
