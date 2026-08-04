#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MODULES="${MODULES:-${MODULE:-}}"
CONSUMER_LOCAL_MODE="${CONSUMER_LOCAL_MODE:-0}"
COMPOSE_ENV_FILE="${COMPOSE_ENV_FILE:-${ROOT_DIR}/.env.consumer}"
POSTGRES_USER="${POSTGRES_USER:-erp}"
COMPOSE_FILE_ARGS=(-f "${ROOT_DIR}/docker-compose.consumer.yml")

log() {
  printf '[update_runtime_module] %s\n' "$*"
}

fail() {
  printf '[update_runtime_module] ERROR: %s\n' "$*" >&2
  exit 1
}

run_compose() {
  docker compose --env-file "${COMPOSE_ENV_FILE}" "${COMPOSE_FILE_ARGS[@]}" "$@"
}

wait_for_postgres() {
  local tries=30
  local i
  for ((i = 1; i <= tries; i++)); do
    if run_compose exec -T postgres pg_isready -U "${POSTGRES_USER}" -d postgres >/dev/null 2>&1; then
      return
    fi
    sleep 2
  done
  fail "PostgreSQL del consumer no està llest després d'esperar"
}

main() {
  local was_running=0

  command -v docker >/dev/null 2>&1 || fail "Falta l'eina requerida: docker"
  [ -n "${MODULES}" ] || fail "Cal informar MODULE=<modul> o MODULES=<m1,m2>"
  [ -f "${COMPOSE_ENV_FILE}" ] || fail "No existeix ${COMPOSE_ENV_FILE}"

  if [ "${CONSUMER_LOCAL_MODE}" = "1" ]; then
    [ -f "${ROOT_DIR}/docker-compose.consumer.override.yml" ] || fail "Cal docker-compose.consumer.override.yml per al mode local"
    COMPOSE_FILE_ARGS+=(-f "${ROOT_DIR}/docker-compose.consumer.override.yml")
  fi

  log "Assegurant dependències del consumer"
  run_compose up -d postgres mongo redis >/dev/null
  wait_for_postgres

  if run_compose ps --status running --services | grep -Fxq 'erp-runtime'; then
    was_running=1
    log "Aturant temporalment erp-runtime per actualitzar mòduls"
    run_compose stop erp-runtime >/dev/null
  fi

  log "Actualitzant mòduls: ${MODULES}"
  run_compose run --rm --no-deps -e MODULES="${MODULES}" --entrypoint /bin/bash erp-runtime -lc '
    set -euo pipefail
    export ERP_SERVER="/opt/somenergia/src/erp/server/bin/openerp-server.py"
    export OPENERP_CONFIG="/opt/somenergia/src/openerp_som_addons/runtime-docker/erp.conf"
    export OPENERP_DB_HOST="postgres"
    export OPENERP_MONGODB_HOST="mongo"
    export OPENERP_REDIS_URL="redis://redis:6379/0"
    export PYTHONPATH="/opt/somenergia/src/erp/server/bin:/opt/somenergia/src/erp/server/bin/addons:/opt/somenergia/src/erp/server/sitecustomize:${PYTHONPATH:-}"
    export ERP_FOREGROUND=1
    export OPENERP_EXTRA_ARGS="--update=${MODULES} --stop-after-init"
    exec bash /opt/somenergia/src/openerp_som_addons/scripts/start-openerp-server.sh
  '

  if [ "${was_running}" = "1" ]; then
    log "Tornant a arrencar erp-runtime"
    run_compose up -d erp-runtime >/dev/null
  fi

  log "Actualització completada"
}

main "$@"
