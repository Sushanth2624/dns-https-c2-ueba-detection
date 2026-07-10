#!/usr/bin/env bash
# Run every endpoint's traffic (LAB_ROUNDS times) while capturing 100% inline on the lab bridge,
# then turn the single mixed capture into Zeek + Suricata telemetry. Produces REAL per-host logs
# with genuine distinct source IPs (no relabeling) — the multi-VM inline-capture design, realized.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
MANIFEST="$ROOT/scripts/lab_endpoints.txt"
OUT="$ROOT/data/captures/lab"
rm -rf "$OUT"; mkdir -p "$OUT"
PCAP="$OUT/capture.pcap"
ROUNDS="${LAB_ROUNDS:-2}"

echo "== starting inline capture on labbr0 (${ROUNDS} rounds) =="
tcpdump -i labbr0 -n -w "$PCAP" 'port 53 or port 443 or port 8443' >/dev/null 2>&1 &
TP=$!
sleep 1
START=$(date -u +%FT%TZ)

for r in $(seq 1 "$ROUNDS"); do
  echo "== round $r/$ROUNDS =="
  declare -a PIDS=()
  while IFS='|' read -r name ip role cmd; do
    [ -z "$name" ] && continue; case "$name" in \#*) continue;; esac
    docker exec "$name" sh -c "$cmd" >/dev/null 2>&1 & PIDS+=($!)
  done < "$MANIFEST"
  for p in "${PIDS[@]}"; do wait "$p" 2>/dev/null; done
  [ "$r" -lt "$ROUNDS" ] && sleep 3
done

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

# ground-truth entity map from the manifest
python3 - "$MANIFEST" "$OUT" "$START" "$END" <<'PY'
import sys, json
manifest, out, start, end = sys.argv[1:5]
ents = {}
for line in open(manifest):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    name, ip, role, cmd = line.split("|", 3)
    ents[ip] = role
json.dump({"lab": "container-inline", "start": start, "end": end, "entities": ents},
          open(f"{out}/manifest.json", "w"))
print(f"  {len(ents)} entities in manifest")
PY

echo "== per-host telemetry (real source IPs) =="
python3 - "$OUT" <<'PY'
import json,sys
o=sys.argv[1]
def load(n):
    try: return [json.loads(l) for l in open(f"{o}/{n}.log")]
    except FileNotFoundError: return []
dns=load("dns"); ssl=load("ssl"); conn=load("conn")
hosts=sorted(set(r.get("id.orig_h") for r in dns+ssl+conn if str(r.get("id.orig_h","")).startswith("10.50")))
for h in hosts:
    d=sum(1 for r in dns if r.get("id.orig_h")==h)
    nx=sum(1 for r in dns if r.get("id.orig_h")==h and r.get("rcode_name")=="NXDOMAIN")
    s=sum(1 for r in ssl if r.get("id.orig_h")==h)
    print(f"  {h:12s} dns={d:4d} nx={nx:4d} ssl={s:3d}")
print(f"  TOTAL dns={len(dns)} ssl={len(ssl)} conn={len(conn)}")
PY
echo "lab capture complete -> $OUT"
