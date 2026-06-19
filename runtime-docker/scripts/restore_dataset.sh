#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

COMPOSE_FILE="${COMPOSE_FILE:-}"
DB_SERVICE="${DB_SERVICE:-}"
POSTGRES_HOST="${POSTGRES_HOST:-}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-erp}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-erp}"
POSTGRES_DB="${POSTGRES_DB:-${ERP_DATABASE:-}}"
EXPECTED_POSTGRES_MAJOR="${EXPECTED_POSTGRES_MAJOR:-13}"
RESET_ADMIN_LOGIN="${RESET_ADMIN_LOGIN:-admin}"
RESET_ADMIN_PASSWORD="${RESET_ADMIN_PASSWORD:-}"
CACHE_DIR="${CACHE_DIR:-${ROOT_DIR}/.cache/datasets}"
DATASET_TAG="${DATASET_TAG:-latest}"
DATASET_PATH="${DATASET_PATH:-}"
TMP_DUMP=""

log() {
  printf '[restore_dataset] %s\n' "$*"
}

fail() {
  printf '[restore_dataset] ERROR: %s\n' "$*" >&2
  exit 1
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

filter_toc() {
  local toc_file="$1"
  local filtered_toc="$2"

  awk '!($0 ~ / EXTENSION - timescaledb( |$)/ || $0 ~ / COMMENT - EXTENSION timescaledb( |$)/ || $0 ~ /^[0-9]+; .* (_timescaledb_cache|_timescaledb_catalog|_timescaledb_config|_timescaledb_functions|_timescaledb_internal|timescaledb_information)( |$)/ || $0 ~ / TRIGGER .* ts_insert_blocker( |$)/)' "${toc_file}" >"${filtered_toc}"
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

resolve_db_service() {
  if [ -n "${DB_SERVICE}" ]; then
    compose_has_service "${DB_SERVICE}" || fail "El servei DB_SERVICE=${DB_SERVICE} no existeix a ${COMPOSE_FILE}"
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

  fail "No s'ha pogut detectar cap servei PostgreSQL (esperat: postgres o db)"
}

resolve_postgres_db() {
  if [ -n "${POSTGRES_DB}" ]; then
    return
  fi

  POSTGRES_DB="erp_runtime"
  if run_compose -f "${COMPOSE_FILE}" config --services | grep -Fxq 'db'; then
    POSTGRES_DB="erp"
  fi
}

get_compose_postgres_version() {
  run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
    psql -U "${POSTGRES_USER}" -d postgres -tAc 'SHOW server_version;' | tr -d '[:space:]'
}

assert_compose_postgres_major() {
  local version major
  version="$(get_compose_postgres_version)"
  major="${version%%.*}"
  [ -n "${major}" ] || fail "No s'ha pogut determinar la versió de PostgreSQL"
  if [ "${major}" != "${EXPECTED_POSTGRES_MAJOR}" ]; then
    fail "Versió PostgreSQL detectada ${version} (major ${major}) però s'esperava major ${EXPECTED_POSTGRES_MAJOR}"
  fi
}

reset_admin_external() {
  if [ -z "${RESET_ADMIN_PASSWORD}" ]; then
    return
  fi

  log "Aplicant credencials després del restore per ${RESET_ADMIN_LOGIN}"
  PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
    -v login="${RESET_ADMIN_LOGIN}" -v password="${RESET_ADMIN_PASSWORD}" \
    -c "UPDATE res_users SET password = :'password' WHERE login = :'login';"
}

reset_admin_compose() {
  if [ -z "${RESET_ADMIN_PASSWORD}" ]; then
    return
  fi

  log "Aplicant credencials després del restore per ${RESET_ADMIN_LOGIN}"
  run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
    psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
    -v login="${RESET_ADMIN_LOGIN}" -v password="${RESET_ADMIN_PASSWORD}" \
    -c "UPDATE res_users SET password = :'password' WHERE login = :'login';"
}

resolve_compose_file() {
  if [ -n "${COMPOSE_FILE}" ]; then
    [ -f "${COMPOSE_FILE}" ] || fail "No existeix el fitxer compose: ${COMPOSE_FILE}"
    return
  fi

  if [ -f "${ROOT_DIR}/docker-compose.yml" ]; then
    COMPOSE_FILE="${ROOT_DIR}/docker-compose.yml"
    return
  fi

  if [ -f "${ROOT_DIR}/../docker-compose.yaml" ]; then
    COMPOSE_FILE="${ROOT_DIR}/../docker-compose.yaml"
    return
  fi

  if [ -f "${ROOT_DIR}/../docker-compose.yml" ]; then
    COMPOSE_FILE="${ROOT_DIR}/../docker-compose.yml"
    return
  fi

  fail "No s'ha pogut resoldre COMPOSE_FILE"
}

resolve_dataset_path() {
  if [ -n "${DATASET_PATH}" ]; then
    [ -f "${DATASET_PATH}" ] || fail "DATASET_PATH no existeix: ${DATASET_PATH}"
    return
  fi

  local candidate f
  candidate="${CACHE_DIR}/${DATASET_TAG}"
  [ -d "${candidate}" ] || fail "No s'ha trobat el directori descarregat: ${candidate}"

  shopt -s nullglob
  for f in "${candidate}"/*.dump.zst; do
    DATASET_PATH="${f}"
    break
  done
  shopt -u nullglob

  [ -n "${DATASET_PATH}" ] || fail "No s'ha trobat cap .dump.zst a ${candidate}"
}

wait_for_external_db() {
  local tries=30
  local i
  for ((i = 1; i <= tries; i++)); do
    if PGPASSWORD="${POSTGRES_PASSWORD}" psql \
      -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
      -d postgres -c 'SELECT 1;' >/dev/null 2>&1; then
      return
    fi
    sleep 2
  done
  fail "PostgreSQL extern no està llest després d'esperar"
}

wait_for_compose_db() {
  local tries=30
  local i
  for ((i = 1; i <= tries; i++)); do
    if run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
      pg_isready -U "${POSTGRES_USER}" -d postgres >/dev/null 2>&1; then
      return
    fi
    sleep 2
  done
  fail "PostgreSQL del compose no està llest després d'esperar"
}

wait_for_compose_db_stable() {
  local required_successes=3
  local successes=0
  local tries=30
  local i

  for ((i = 1; i <= tries; i++)); do
    if run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
      psql -h 127.0.0.1 -U "${POSTGRES_USER}" -d postgres -tAc 'SELECT 1;' \
      | grep -Fxq '1'; then
      successes=$((successes + 1))
      if [ "${successes}" -ge "${required_successes}" ]; then
        return
      fi
    else
      successes=0
    fi
    sleep 1
  done

  fail "PostgreSQL del compose no s'ha mantingut estable després d'esperar"
}

restore_external() {
  local dump_file="$1"
  local toc_file filtered_toc

  have_cmd psql || fail "Falta l'eina requerida: psql"
  have_cmd dropdb || fail "Falta l'eina requerida: dropdb"
  have_cmd createdb || fail "Falta l'eina requerida: createdb"
  have_cmd pg_restore || fail "Falta l'eina requerida: pg_restore"

  toc_file="$(mktemp -t runtime-dataset-toc.XXXXXX.list)"
  filtered_toc="$(mktemp -t runtime-dataset-toc-filtered.XXXXXX.list)"
  trap 'rm -f "${TMP_DUMP}" "${toc_file}" "${filtered_toc}"' EXIT

  pg_restore -l "${dump_file}" >"${toc_file}"
  filter_toc "${toc_file}" "${filtered_toc}"

  log "Esperant disponibilitat de PostgreSQL extern"
  wait_for_external_db

  log "Recreant base de dades ${POSTGRES_DB}"
  PGPASSWORD="${POSTGRES_PASSWORD}" dropdb --if-exists \
    -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" "${POSTGRES_DB}"
  PGPASSWORD="${POSTGRES_PASSWORD}" createdb \
    -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" "${POSTGRES_DB}"

  log "Restaurant dump en host extern"
  PGPASSWORD="${POSTGRES_PASSWORD}" pg_restore \
    -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" --clean --if-exists -L "${filtered_toc}" "${dump_file}"

  reset_admin_external
}

restore_compose() {
  local dump_file="$1"
  local remote_dump="/tmp/runtime-dataset-restore.dump"
  local toc_file filtered_toc remote_toc remote_filtered_toc

  have_cmd docker || fail "Falta l'eina requerida: docker"

  toc_file="$(mktemp -t runtime-dataset-toc.XXXXXX.list)"
  filtered_toc="$(mktemp -t runtime-dataset-toc-filtered.XXXXXX.list)"
  remote_toc="/tmp/runtime-dataset-restore.toc.list"
  remote_filtered_toc="/tmp/runtime-dataset-restore.filtered.toc.list"

  pg_restore -l "${dump_file}" >"${toc_file}"
  filter_toc "${toc_file}" "${filtered_toc}"

  log "Assegurant que el servei PostgreSQL està actiu"
  run_compose -f "${COMPOSE_FILE}" up -d "${DB_SERVICE}" >/dev/null
  wait_for_compose_db
  assert_compose_postgres_major
  wait_for_compose_db_stable

  log "Copiant dump dins del contenidor"
  run_compose -f "${COMPOSE_FILE}" cp "${dump_file}" "${DB_SERVICE}:${remote_dump}"
  run_compose -f "${COMPOSE_FILE}" cp "${filtered_toc}" "${DB_SERVICE}:${remote_filtered_toc}"

  log "Recreant base de dades ${POSTGRES_DB} dins del compose"
  run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
    dropdb --if-exists -h 127.0.0.1 -U "${POSTGRES_USER}" "${POSTGRES_DB}"
  run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
    createdb -h 127.0.0.1 -U "${POSTGRES_USER}" "${POSTGRES_DB}"

  log "Restaurant dump dins del compose"
  run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
    pg_restore -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --clean --if-exists -L "${remote_filtered_toc}" "${remote_dump}"

  reset_admin_compose

  run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" rm -f "${remote_dump}"
  run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" rm -f "${remote_filtered_toc}"
  rm -f "${toc_file}" "${filtered_toc}"
}

main() {
  have_cmd zstd || fail "Falta l'eina requerida: zstd"
  resolve_compose_file
  resolve_db_service
  resolve_postgres_db
  resolve_dataset_path

  TMP_DUMP="$(mktemp -t runtime-dataset-restore.XXXXXX.dump)"
  trap 'rm -f "${TMP_DUMP}"' EXIT

  log "Descomprimint ${DATASET_PATH}"
  zstd -d -f "${DATASET_PATH}" -o "${TMP_DUMP}"

  if [ -n "${POSTGRES_HOST}" ]; then
    restore_external "${TMP_DUMP}"
  else
    restore_compose "${TMP_DUMP}"
  fi

  log "Restore completat"
}

main "$@"
