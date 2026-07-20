# Deploy — OpenUBA backend as a boot service

Runs the [OpenUBA](https://github.com/GACWR/OpenUBA) backend (the UEBA engine) as a
boot-persistent `systemd` service on the single Analysis VM — **no Kubernetes, no Spark**.

## Topology

- **Backend** — runs on the host (not in a container) so the `docker run` it issues for each
  model-runner job uses host paths. uvicorn on `:8000`, `EXECUTION_MODE=docker`.
- **Postgres** — OpenUBA's state store, in Docker Compose (`openuba-src-postgres-1`), reached by the
  backend at the bridge gateway `172.17.0.1:5432`.
- **Model-runner** — each job spawns an `openuba-model-runner:sklearn` container that runs the
  IsolationForest and reports results back.

The Python pipeline talks to this backend via `src/c2detect/ueba/openuba_client.py` when
`ueba.source: openuba` (see `config/config.openuba.yaml`).

## Files

| File | Purpose |
|---|---|
| `openuba-backend.service` | the systemd unit (installed to `/etc/systemd/system/`) |
| `install-openuba-backend.sh` | idempotent installer: installs the unit, enables it on boot, sets the Postgres container to restart on boot, and health-checks `:8000` |

## Install

Prereq: the OpenUBA repo + host venv must already exist at `/home/analysis/openuba-src`
(clone OpenUBA there, create `.ouba-venv`, install backend deps) and its compose Postgres must be up.

```bash
sudo deploy/install-openuba-backend.sh
```

## What it guarantees on boot

1. Docker starts → the `openuba-src-postgres-1` container comes back (`--restart unless-stopped`).
2. `openuba-backend` starts after `docker.service` and, via an `ExecStartPre` guard, **waits up to
   ~120s for Postgres `172.17.0.1:5432` to accept connections** before launching uvicorn — so it
   never crash-loops against a not-yet-ready DB. `Restart=on-failure` is the backstop.

## Verify

```bash
systemctl is-enabled openuba-backend      # enabled
systemctl is-active  openuba-backend      # active
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/health   # 200
docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' openuba-src-postgres-1   # unless-stopped
```

## Paths (edit the unit if your layout differs)

- OpenUBA repo: `/home/analysis/openuba-src`
- Host venv: `/home/analysis/openuba-src/.ouba-venv`
- `DATABASE_URL=postgresql://openuba:openuba@172.17.0.1:5432/openuba`
