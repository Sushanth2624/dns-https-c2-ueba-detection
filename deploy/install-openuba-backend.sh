#!/usr/bin/env bash
# Install + enable the OpenUBA backend as a boot-persistent systemd service, and make its
# Postgres container come back on boot too. Idempotent — safe to re-run. Run as root.
#
#   sudo deploy/install-openuba-backend.sh
#
# Assumes the OpenUBA repo + host venv are already set up (see deploy/README.md).
set -euo pipefail

UNIT_SRC="$(cd "$(dirname "$0")" && pwd)/openuba-backend.service"
UNIT_DST="/etc/systemd/system/openuba-backend.service"
PG_CONTAINER="${PG_CONTAINER:-openuba-src-postgres-1}"

if [[ $EUID -ne 0 ]]; then
  echo "run as root (sudo $0)" >&2; exit 1
fi

echo "==> installing unit -> $UNIT_DST"
install -m 0644 "$UNIT_SRC" "$UNIT_DST"

echo "==> ensuring Postgres container '$PG_CONTAINER' restarts on boot"
if docker inspect "$PG_CONTAINER" >/dev/null 2>&1; then
  docker update --restart unless-stopped "$PG_CONTAINER" >/dev/null
  docker inspect -f '    restart policy = {{.HostConfig.RestartPolicy.Name}}' "$PG_CONTAINER"
else
  echo "    WARNING: container '$PG_CONTAINER' not found — bring OpenUBA's compose up first" >&2
fi

echo "==> enabling + (re)starting openuba-backend"
systemctl daemon-reload
systemctl enable openuba-backend
systemctl restart openuba-backend

echo "==> waiting for health on :8000"
for i in $(seq 1 30); do
  if [[ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health || true)" == "200" ]]; then
    echo "    backend healthy (200)"; break
  fi
  sleep 2
done

echo
echo "state:  enabled=$(systemctl is-enabled openuba-backend)  active=$(systemctl is-active openuba-backend)"
echo "done. openuba-backend will now start on boot."
