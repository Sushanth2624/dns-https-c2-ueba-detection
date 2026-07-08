#!/usr/bin/env bash
# Capture real traffic from a lab traffic generator and turn it into Zeek + Suricata telemetry.
# Single-host adaptation of the inline-gateway design: this VM is both endpoint and sensor.
#
# Usage: run_capture.sh <label> <bpf_filter> -- <generator command ...>
# Example: run_capture.sh dga "udp port 53" -- python3 traffic/malicious/dga_sim.py 200
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ZEEK=/opt/zeek/bin/zeek
IFACE="${CAP_IFACE:-ens18}"

label="$1"; bpf="$2"; shift 2
[ "$1" = "--" ] && shift

outdir="$ROOT/data/captures/$label"
rm -rf "$outdir"; mkdir -p "$outdir"
pcap="$outdir/capture.pcap"

echo "[$label] starting capture on $IFACE (filter: $bpf)"
tcpdump -i "$IFACE" -n -w "$pcap" $bpf >/dev/null 2>&1 &
TCPDUMP_PID=$!
sleep 1

start=$(date -u +%FT%TZ)
echo "[$label] running generator: $*"
"$@"
rc=$?
end=$(date -u +%FT%TZ)

sleep 1
kill "$TCPDUMP_PID" 2>/dev/null; wait "$TCPDUMP_PID" 2>/dev/null
echo "[$label] captured $(stat -c%s "$pcap" 2>/dev/null || echo 0) bytes"

# Zeek: JSON logs + JA3/JA4 packages, ignore checksum offload errors (-C)
( cd "$outdir" && "$ZEEK" -C -r "$pcap" \
    policy/tuning/json-logs.zeek packages \
    "$ROOT/rules/zeek/c2-indicators.zeek" 2>zeek.err )
echo "[$label] zeek logs: $(ls "$outdir"/*.log 2>/dev/null | xargs -n1 basename 2>/dev/null | tr '\n' ' ')"

# Suricata: eve.json (signature baseline = Config A + TLS/JA3)
if command -v suricata >/dev/null 2>&1; then
  suricata -k none -r "$pcap" -S "$ROOT/rules/suricata/local.rules" -l "$outdir" \
    --set default-log-dir="$outdir" >/dev/null 2>&1
  echo "[$label] suricata eve: $([ -f "$outdir/eve.json" ] && wc -l < "$outdir/eve.json" || echo 0) events"
fi

# ground-truth manifest
cat > "$outdir/manifest.json" <<EOF
{"label": "$label", "start": "$start", "end": "$end", "generator": "$*", "rc": $rc}
EOF
echo "[$label] done -> $outdir"
