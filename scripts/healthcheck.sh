#!/usr/bin/env bash
# Health check for the single-host Analysis VM stack.
set -u
echo "== tool versions =="
echo -n "zeek:     "; /opt/zeek/bin/zeek --version 2>/dev/null | head -1 || echo MISSING
echo -n "suricata: "; suricata -V 2>/dev/null || echo MISSING
echo "== services =="
for svc in elasticsearch kibana; do
  printf "%s: %s\n" "$svc" "$(systemctl is-active "$svc" 2>/dev/null)"
done
echo "== elasticsearch (TLS + auth) =="
[ -f config/secrets.env ] && . config/secrets.env
ESP="${ELASTIC_PASSWORD:-}"
curl -s -k -u "elastic:$ESP" https://localhost:9200/_cluster/health?pretty 2>/dev/null \
  | grep -E '"status"|"number_of_nodes"' || echo "ES not reachable (check config/secrets.env)"
echo -n "c2-alerts docs: "; curl -s -k -u "elastic:$ESP" "https://localhost:9200/c2-alerts/_count" 2>/dev/null | jq -r '.count' 2>/dev/null || echo "n/a"
echo "== kibana =="
curl -s -o /dev/null -w 'kibana http=%{http_code}\n' http://localhost:5601/api/status 2>/dev/null || echo "Kibana not reachable"
echo "== captures =="
ls -1 data/captures 2>/dev/null | sed 's/^/  scenario: /' || echo "  (none yet — run: make dataset)"
echo "== local C2 test listener (beacon target) =="
ss -ltn 2>/dev/null | grep -q ':8443' && echo "  127.0.0.1:8443 up" || echo "  127.0.0.1:8443 down (start before capturing beacon)"
echo "== resources =="
free -h | head -2; df -h / | tail -1
