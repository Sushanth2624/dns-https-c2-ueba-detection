#!/usr/bin/env bash
# Quick health check for the Analysis VM stack.
set -u
echo "== services =="
for svc in zeek suricata elasticsearch kibana; do
  systemctl is-active "$svc" 2>/dev/null | sed "s/^/$svc: /"
done
echo "== elasticsearch =="
curl -s http://localhost:9200/_cluster/health?pretty || echo "ES not reachable"
echo "== recent zeek logs =="
ls -1t /opt/zeek/logs/current/ 2>/dev/null | head
echo "== suricata eve =="
tail -n 1 /var/log/suricata/eve.json 2>/dev/null | cut -c1-120
echo "== resources =="
free -h; echo; df -h / | tail -1
