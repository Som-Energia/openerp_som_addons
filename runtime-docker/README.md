# Local ERP runtime with Docker Compose

This setup provides a local ERP runtime with low-friction startup using Docker only.

## Prerequisites

- Docker and Docker Compose plugin
- `GITHUB_TOKEN` with read access to private Som Energia repositories

## Start runtime

```bash
export GITHUB_TOKEN=<token>
docker compose -f runtime-docker/docker-compose.yml up --build
```

First startup bootstraps ERP dependencies and can take several minutes.

Runtime startup uses `runtime-docker/erp.conf` with container-friendly defaults
(`db_host=postgres`, `redis://redis:6379/0`, `mongodb://mongo:27017/...`,
`stop_after_init=False`).

## Ready signal

- ERP XML-RPC is exposed on `http://localhost:8069` by default.
- Container health indicates readiness:

```bash
docker compose -f runtime-docker/docker-compose.yml ps
```

- Runtime logs are available with:

```bash
docker compose -f runtime-docker/docker-compose.yml logs -f erp-runtime
```

## Optional variables

- `ERP_XMLRPC_PORT` (default `8069`)
- `ERP_DATABASE` (default `erp_runtime`)
- `ERP_BRANCH` (default `rolling_erp01`)

## Stop runtime

```bash
docker compose -f runtime-docker/docker-compose.yml down
```
