#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${ROOT_DIR}/.." && pwd)"

COMPOSE_FILE="${COMPOSE_FILE:-}"
DB_SERVICE="${DB_SERVICE:-}"
POSTGRES_DB="${POSTGRES_DB:-${ERP_DATABASE:-erp}}"
POSTGRES_USER="${POSTGRES_USER:-erp}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-erp}"

log() {
  printf '[producer_create_db] %s\n' "$*"
}

fail() {
  printf '[producer_create_db] ERROR: %s\n' "$*" >&2
  exit 1
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

run_compose() {
  if have_cmd docker && docker compose version >/dev/null 2>&1; then
    docker compose "$@"
    return
  fi
  if have_cmd docker-compose; then
    docker-compose "$@"
    return
  fi
  fail "No s'ha trobat docker compose ni docker-compose"
}

compose_has_service() {
  local service="$1"
  run_compose -f "${COMPOSE_FILE}" config --services | grep -Fxq "${service}"
}

resolve_compose_file() {
  if [ -n "${COMPOSE_FILE}" ]; then
    [ -f "${COMPOSE_FILE}" ] || fail "No existeix COMPOSE_FILE: ${COMPOSE_FILE}"
    return
  fi
  if [ -f "${ROOT_DIR}/docker-compose.yml" ]; then
    COMPOSE_FILE="${ROOT_DIR}/docker-compose.yml"
    return
  fi
  if [ -f "${REPO_ROOT}/docker-compose.yaml" ]; then
    COMPOSE_FILE="${REPO_ROOT}/docker-compose.yaml"
    return
  fi
  if [ -f "${REPO_ROOT}/docker-compose.yml" ]; then
    COMPOSE_FILE="${REPO_ROOT}/docker-compose.yml"
    return
  fi
  fail "No s'ha pogut resoldre COMPOSE_FILE"
}

resolve_db_service() {
  if [ -n "${DB_SERVICE}" ]; then
    compose_has_service "${DB_SERVICE}" || fail "DB_SERVICE=${DB_SERVICE} no existeix"
    return
  fi
  if compose_has_service postgres; then
    DB_SERVICE="postgres"
    return
  fi
  if compose_has_service db; then
    DB_SERVICE="db"
    return
  fi
  fail "No s'ha pogut detectar servei PostgreSQL (postgres o db)"
}

count_app_tables() {
  run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
    psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -tAc "
      SELECT count(*)
      FROM information_schema.tables
      WHERE table_type = 'BASE TABLE'
        AND table_schema NOT IN ('pg_catalog', 'information_schema')
        AND table_schema NOT LIKE '_timescaledb%'
        AND table_schema <> 'timescaledb_information';
    " | tr -d '[:space:]'
}

main() {
  local builder_script
  local app_tables
  builder_script="${REPO_ROOT}/scripts/build-openerp-server.sh"

  have_cmd bash || fail "Falta bash"

  resolve_compose_file
  resolve_db_service

  log "Assegurant PostgreSQL disponible"
  run_compose -f "${COMPOSE_FILE}" up -d "${DB_SERVICE}" >/dev/null

  if [ ! -f "${builder_script}" ]; then
    app_tables="$(count_app_tables)"
    if [ -n "${app_tables}" ] && [ "${app_tables}" -gt 0 ]; then
      log "No s'ha trobat ${builder_script}, però la BD ${POSTGRES_DB} ja té ${app_tables} taules d'aplicació. Continuem."
      return
    fi
    fail "No s'ha trobat ${builder_script} i la BD ${POSTGRES_DB} no té model de negoci. Inicialitza-la externament o restaura un dataset abans de fer dump."
  fi

  log "Executant inicialització de model/dades amb destral"
  ROOT_DIR_SRC="${REPO_ROOT}/.." \
  ERP_DATABASE="${POSTGRES_DB}" \
  OPENERP_DB_HOST="localhost" \
  OPENERP_DB_USER="${POSTGRES_USER}" \
  OPENERP_DB_PASSWORD="${POSTGRES_PASSWORD}" \
  ERP_IGNORE_DESTRAL_FAILURES=0 \
  bash "${builder_script}"

  log "Inicialització completada per BD ${POSTGRES_DB}"
}

main "$@"
