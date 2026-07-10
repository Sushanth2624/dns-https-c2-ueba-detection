#!/usr/bin/env bash
# Bring up the container-based multi-host lab (real inline-gateway architecture):
#   - lab bridge labbr0 (10.50.0.0/24), this Analysis VM is gateway 10.50.0.1
#   - dnsmasq on 10.50.0.1 = the endpoints' DNS resolver (DNS traverses the bridge, captured inline)
#   - a local TLS "C2" on 10.50.0.1:8443 (LAN beacon target)
#   - one persistent container per line in scripts/lab_endpoints.txt (distinct host + IP + JA3)
# Idempotent: safe to re-run.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
MANIFEST="$ROOT/scripts/lab_endpoints.txt"

echo "== network =="
docker network inspect labnet >/dev/null 2>&1 || \
  docker network create --subnet 10.50.0.0/24 --gateway 10.50.0.1 \
    -o com.docker.network.bridge.name=labbr0 labnet >/dev/null
ip link set labbr0 up 2>/dev/null
echo "  labnet / labbr0 ready ($(ip -br addr show labbr0 | awk '{print $3}'))"

echo "== dnsmasq (endpoint resolver on 10.50.0.1) =="
if ! ss -lunp 2>/dev/null | grep -q '10.50.0.1:53'; then
  setsid dnsmasq --listen-address=10.50.0.1 --bind-interfaces --no-resolv --no-hosts \
    --server=8.8.8.8 --server=1.1.1.1 --cache-size=0 </dev/null >/dev/null 2>&1 &
  disown 2>/dev/null || true; sleep 1
fi
ss -lunp 2>/dev/null | grep -q '10.50.0.1:53' && echo "  dnsmasq up" || echo "  dnsmasq DOWN"

echo "== local C2 listener (10.50.0.1:8443) =="
C2DIR="$ROOT/data/tmp/c2srv"; mkdir -p "$C2DIR"
[ -f "$C2DIR/cert.pem" ] || openssl req -x509 -newkey rsa:2048 -keyout "$C2DIR/key.pem" \
  -out "$C2DIR/cert.pem" -days 3 -nodes -subj "/CN=c2.internal.lab" >/dev/null 2>&1
if ! ss -ltn 2>/dev/null | grep -q ':8443'; then
  ( cd "$C2DIR" && setsid openssl s_server -quiet -accept 8443 -cert cert.pem -key key.pem \
      -naccept 1000000 </dev/null >/dev/null 2>&1 ) & disown 2>/dev/null || true; sleep 1
fi
ss -ltn 2>/dev/null | grep -q ':8443' && echo "  C2 up" || echo "  C2 DOWN"

echo "== endpoint containers =="
docker image inspect c2lab-endpoint >/dev/null 2>&1 || \
  docker build -t c2lab-endpoint "$ROOT/data/tmp/labimg" >/dev/null
n=0
while IFS='|' read -r name ip role cmd; do
  [ -z "$name" ] && continue; case "$name" in \#*) continue;; esac
  docker rm -f "$name" >/dev/null 2>&1
  docker run -d --name "$name" --hostname "$name" --network labnet --ip "$ip" \
    --dns 10.50.0.1 --label c2lab.role="$role" c2lab-endpoint sleep infinity >/dev/null
  n=$((n+1)); printf "  %-16s %-12s %s\n" "$name" "$ip" "role=$role"
done < "$MANIFEST"
echo "lab is up: $n endpoint hosts. run: bash scripts/lab_capture.sh"
