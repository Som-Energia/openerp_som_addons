#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${ROOT_DIR}/.." && pwd)"

COMPOSE_FILE="${COMPOSE_FILE:-}"
DB_SERVICE="${DB_SERVICE:-}"
POSTGRES_DB="${POSTGRES_DB:-${ERP_DATABASE:-erp}}"
POSTGRES_USER="${POSTGRES_USER:-erp}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-erp}"
USE_PREWARMED_DB="${USE_PREWARMED_DB:-1}"
PREWARMED_DB_DUMP_PATH="${PREWARMED_DB_DUMP_PATH:-${ROOT_DIR}/build/prewarmed/prewarmed-db.dump.zst}"

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

start_required_services() {
  local services
  services=("${DB_SERVICE}")

  if compose_has_service redis; then
    services+=(redis)
  fi

  if compose_has_service mongo; then
    services+=(mongo)
  fi

  run_compose -f "${COMPOSE_FILE}" up -d "${services[@]}" >/dev/null
}

resolve_compose_file() {
  if [ -n "${COMPOSE_FILE}" ]; then
    [ -f "${COMPOSE_FILE}" ] || fail "No existeix COMPOSE_FILE: ${COMPOSE_FILE}"
    return
  fi

  # Producer flow runs destral from host, so prefer compose files that usually
  # expose DB/Redis/Mongo ports on localhost.
  if [ -f "${REPO_ROOT}/docker-compose.yaml" ]; then
    COMPOSE_FILE="${REPO_ROOT}/docker-compose.yaml"
    return
  fi
  if [ -f "${REPO_ROOT}/docker-compose.yml" ]; then
    COMPOSE_FILE="${REPO_ROOT}/docker-compose.yml"
    return
  fi
  if [ -f "${ROOT_DIR}/docker-compose.yml" ]; then
    COMPOSE_FILE="${ROOT_DIR}/docker-compose.yml"
    return
  fi
  fail "No s'ha pogut resoldre COMPOSE_FILE"
}

service_port_published() {
  local service="$1"
  local port="$2"
  run_compose -f "${COMPOSE_FILE}" port "${service}" "${port}" >/dev/null 2>&1
}

service_port_published_in_compose() {
  local compose_file="$1"
  local service="$2"
  local port="$3"
  run_compose -f "${compose_file}" port "${service}" "${port}" >/dev/null 2>&1
}

compose_has_service_in_file() {
  local compose_file="$1"
  local service="$2"
  run_compose -f "${compose_file}" config --services | grep -Fxq "${service}"
}

fallback_to_host_compose_if_needed() {
  local root_compose

  if service_port_published "${DB_SERVICE}" 5432; then
    return
  fi

  root_compose=""
  if [ -f "${REPO_ROOT}/docker-compose.yaml" ]; then
    root_compose="${REPO_ROOT}/docker-compose.yaml"
  elif [ -f "${REPO_ROOT}/docker-compose.yml" ]; then
    root_compose="${REPO_ROOT}/docker-compose.yml"
  fi

  if [ -z "${root_compose}" ]; then
    return
  fi

  if compose_has_service_in_file "${root_compose}" db && service_port_published_in_compose "${root_compose}" db 5432; then
    log "El compose actual no publica 5432; faig fallback automàtic a ${root_compose} (servei db)"
    COMPOSE_FILE="${root_compose}"
    DB_SERVICE="db"
    return
  fi
}

assert_host_accessible_services() {
  service_port_published "${DB_SERVICE}" 5432 || \
    fail "El servei ${DB_SERVICE} no publica port 5432 a host. Usa COMPOSE_FILE amb ports exposats (p.ex. docker-compose.yaml arrel)."

  if compose_has_service redis; then
    service_port_published redis 6379 || \
      fail "El servei redis no publica port 6379 a host. Destral necessita redis accessible a localhost:6379."
  fi

  if compose_has_service mongo; then
    service_port_published mongo 27017 || \
      fail "El servei mongo no publica port 27017 a host."
  fi
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

wait_for_db() {
  local tries=30
  local i
  for ((i = 1; i <= tries; i++)); do
    if run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
      pg_isready -U "${POSTGRES_USER}" -d postgres >/dev/null 2>&1; then
      return
    fi
    sleep 2
  done
  fail "PostgreSQL no està llest després d'esperar"
}

force_admin_credentials() {
  log "Forçant credencials admin/admin"
  run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
    psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
    -v login="admin" -v password="admin" \
    -c "UPDATE res_users SET password = :'password' WHERE login = :'login';"
}

restore_prewarmed_db_if_available() {
  local app_tables

  if [ "${USE_PREWARMED_DB}" != "1" ]; then
    return 1
  fi
  if [ ! -f "${PREWARMED_DB_DUMP_PATH}" ]; then
    log "No s'ha trobat dump prewarmed a ${PREWARMED_DB_DUMP_PATH}; es farà inicialització amb destral"
    return 1
  fi

  have_cmd zstd || fail "Falta zstd per restaurar ${PREWARMED_DB_DUMP_PATH}"

  log "Restaurar BD des de dump prewarmed: ${PREWARMED_DB_DUMP_PATH}"
  run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
    dropdb -U "${POSTGRES_USER}" --if-exists "${POSTGRES_DB}" >/dev/null
  run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
    createdb -U "${POSTGRES_USER}" "${POSTGRES_DB}" >/dev/null

  zstd -dc "${PREWARMED_DB_DUMP_PATH}" | run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
    pg_restore -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --clean --if-exists --no-owner --no-privileges

  app_tables="$(count_app_tables)"
  if [ -z "${app_tables}" ] || [ "${app_tables}" -eq 0 ]; then
    fail "La restauració des de ${PREWARMED_DB_DUMP_PATH} ha deixat la BD buida"
  fi

  log "BD restaurada des de prewarmed dump (${app_tables} taules d'aplicació)"
  return 0
}

main() {
  local builder_script
  local app_tables
  builder_script="${REPO_ROOT}/scripts/build-openerp-server.sh"

  have_cmd bash || fail "Falta bash"

  resolve_compose_file
  resolve_db_service
  fallback_to_host_compose_if_needed

  log "Assegurant dependències disponibles (db/redis/mongo)"
  start_required_services
  wait_for_db
  assert_host_accessible_services

  if restore_prewarmed_db_if_available; then
    force_admin_credentials
    return
  fi

  if [ ! -f "${builder_script}" ]; then
    app_tables="$(count_app_tables)"
    if [ -n "${app_tables}" ] && [ "${app_tables}" -gt 0 ]; then
      log "No s'ha trobat ${builder_script}, però la BD ${POSTGRES_DB} ja té ${app_tables} taules d'aplicació. Continuem."
      force_admin_credentials
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

  force_admin_credentials

  log "Inicialització completada per BD ${POSTGRES_DB}"
}

main "$@"
