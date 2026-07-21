#!/usr/bin/env bash
# End-to-end demo readiness check + recovery for the viva.
#
# Philosophy: verify first, only touch what's actually broken or stale. If everything is already
# up and the dashboard data is fresh, this is a no-op read-only health check (~5s). If something
# is down or the data is stale/missing, it brings the whole pipeline back up from scratch and
# regenerates real data end-to-end (containers -> capture -> evaluate -> Elasticsearch -> Kibana).
#
# Usage:
#   bash scripts/demo_recover.sh          # check + fix only what's needed
#   bash scripts/demo_recover.sh --force  # always regenerate fresh capture data, even if healthy
#
# Exit 0 = demo-ready. Exit 1 = something couldn't be recovered; read the FAIL lines above.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

PASS=0; FAIL=0
ok()   { printf "  [OK]   %s\n" "$1"; PASS=$((PASS+1)); }
bad()  { printf "  [FAIL] %s\n" "$1"; FAIL=$((FAIL+1)); }
info() { printf "  [..]   %s\n" "$1"; }

echo "== $(date -u +%FT%TZ) — demo recovery check =="

# ---- 1. Core systemd services: only start what's not already active ----
echo; echo "-- core services --"
for svc in elasticsearch kibana openuba-backend; do
  if systemctl is-active --quiet "$svc"; then
    ok "$svc already active"
  else
    info "$svc inactive — starting"
    sudo systemctl start "$svc"
    sleep 3
    if systemctl is-active --quiet "$svc"; then
      ok "$svc started"
    else
      bad "$svc failed to start — check: journalctl -u $svc -n 40 --no-pager"
      journalctl -u "$svc" -n 15 --no-pager | sed 's/^/         /'
    fi
  fi
done

# suricata.service is intentionally disabled: this pipeline runs Suricata offline per-capture
# (suricata -r capture.pcap), not as a live af-packet daemon. Don't "recover" it — just confirm
# the binary + rules are usable so the offline pass in lab_capture.sh works.
if command -v suricata >/dev/null 2>&1 && [ -f rules/suricata/local.rules ]; then
  ok "suricata binary + rules present (runs offline per-capture by design, no daemon expected)"
else
  bad "suricata binary or rules/suricata/local.rules missing"
fi

if systemctl is-active --quiet docker; then
  ok "docker daemon active"
else
  info "docker inactive — starting"
  sudo systemctl start docker; sleep 2
  systemctl is-active --quiet docker && ok "docker started" || bad "docker failed to start"
fi

# ---- 2. Elasticsearch / Kibana reachability (only meaningful once services are up) ----
echo; echo "-- API reachability --"
. config/secrets.env
if curl -s -k -u "elastic:$ELASTIC_PASSWORD" https://localhost:9200/_cluster/health 2>/dev/null | grep -q '"status"'; then
  ok "Elasticsearch API reachable"
else
  bad "Elasticsearch API not reachable (https://localhost:9200)"
fi
KIBANA_HTTP=$(curl -s -o /dev/null -k -w '%{http_code}' https://localhost:5601/api/status 2>/dev/null)
if [ "$KIBANA_HTTP" = "200" ]; then
  ok "Kibana API reachable"
else
  bad "Kibana API returned http=$KIBANA_HTTP (expected 200)"
fi

# ---- 3. Lab containers: bring up only if not all 14 are running ----
echo; echo "-- 14-host lab --"
RUNNING=$(docker ps --filter "label=c2lab.role" --filter "status=running" -q 2>/dev/null | wc -l | tr -d ' ')
if [ "$RUNNING" = "14" ]; then
  ok "all 14 lab containers already running"
else
  info "only $RUNNING/14 lab containers running — bringing lab up (idempotent)"
  bash scripts/lab_up.sh
  RUNNING=$(docker ps --filter "label=c2lab.role" --filter "status=running" -q 2>/dev/null | wc -l | tr -d ' ')
  [ "$RUNNING" = "14" ] && ok "all 14 lab containers now running" || bad "only $RUNNING/14 lab containers running after lab-up"
fi

# ---- 4. Dashboard data: only regenerate if missing, stale, or --force ----
echo; echo "-- dashboard data freshness --"
ALERT_COUNT=$(curl -s -k -u "elastic:$ELASTIC_PASSWORD" "https://localhost:9200/c2-alerts/_count" 2>/dev/null | python3 -c "import json,sys;print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo 0)
LATEST_TS=$(curl -s -k -u "elastic:$ELASTIC_PASSWORD" "https://localhost:9200/c2-alerts/_search?size=1&sort=@timestamp:desc" -H 'Content-Type: application/json' 2>/dev/null \
  | python3 -c "import json,sys
d=json.load(sys.stdin)
h=d.get('hits',{}).get('hits',[])
print(h[0]['_source']['@timestamp'] if h else '')" 2>/dev/null || echo "")

STALE=1
if [ -n "$LATEST_TS" ]; then
  NOW_EPOCH=$(date -u +%s)
  TS_EPOCH=$(date -u -d "$LATEST_TS" +%s 2>/dev/null || echo 0)
  AGE_H=$(( (NOW_EPOCH - TS_EPOCH) / 3600 ))
  if [ "$AGE_H" -lt 6 ]; then STALE=0; fi
  info "latest alert timestamp: $LATEST_TS (${AGE_H}h old)"
fi

if [ "$FORCE" = "1" ]; then
  info "--force passed: regenerating fresh capture + eval + dashboard data regardless of freshness"
  NEED_REGEN=1
elif [ "$ALERT_COUNT" != "8" ] || [ "$STALE" = "1" ]; then
  info "alert data missing/stale (count=$ALERT_COUNT, stale=$STALE) — regenerating"
  NEED_REGEN=1
else
  ok "alert data present and fresh (count=$ALERT_COUNT, <6h old) — leaving as-is"
  NEED_REGEN=0
fi

if [ "$NEED_REGEN" = "1" ]; then
  info "running full pipeline: lab-capture -> evaluate-lab -> alerts+telemetry -> dashboards"
  bash scripts/lab_capture.sh
  PYTHONPATH=src ./.venv/bin/python -m c2detect.cli evaluate-lab --config config/config.lab.yaml --out data/eval/lab
  curl -s -k -u "elastic:$ELASTIC_PASSWORD" -X DELETE "https://localhost:9200/c2-alerts" >/dev/null
  PYTHONPATH=src ./.venv/bin/python -m c2detect.cli run --config config/config.lab.yaml
  PYTHONPATH=src ./.venv/bin/python scripts/ingest_es.py --lab data/captures/lab --config config/config.lab.yaml
  ./.venv/bin/python scripts/build_dashboards.py

  ALERT_COUNT=$(curl -s -k -u "elastic:$ELASTIC_PASSWORD" "https://localhost:9200/c2-alerts/_count" 2>/dev/null | python3 -c "import json,sys;print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo 0)
  if [ "$ALERT_COUNT" = "8" ]; then
    ok "regenerated: 8 alerts written, dashboards rebuilt"
  else
    bad "regeneration finished but alert count=$ALERT_COUNT (expected 8) — check make lab-demo output manually"
  fi
fi

# ---- 5. F1/FPR sanity (headline number for the panel) ----
echo; echo "-- headline result --"
if [ -f data/eval/lab/report.md ] || [ -d data/eval/lab ]; then
  grep -m1 -E "F1|FPR" data/eval/lab/*.md 2>/dev/null | sed 's/^/  /' || info "eval report not in markdown form, re-check with: make evaluate-lab"
fi

# ---- summary ----
echo
echo "== summary: $PASS OK, $FAIL FAIL =="
if [ "$FAIL" = "0" ]; then
  echo "  DEMO-READY."
  echo "  Kibana:  https://localhost:5601/app/dashboards  (elastic / see config/secrets.env)"
  echo "  Dashboards: 'C2 — Executive Overview', 'C2 — Threat Detail', 'C2 — Network Telemetry'"
  echo "  Show services live:  systemctl status elasticsearch kibana openuba-backend"
  echo "  Show lab hosts live: docker ps --filter label=c2lab.role"
  exit 0
else
  echo "  NOT demo-ready — fix the FAIL lines above."
  exit 1
fi
