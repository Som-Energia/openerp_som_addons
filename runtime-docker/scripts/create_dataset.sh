#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${ROOT_DIR}/.." && pwd)"

DATASET_NAME="${DATASET_NAME:-openerp-demo}"
OUTPUT_DIR="${OUTPUT_DIR:-${ROOT_DIR}/build/datasets}"
COMPOSE_FILE="${COMPOSE_FILE:-}"
DB_SERVICE="${DB_SERVICE:-}"
POSTGRES_DB="${POSTGRES_DB:-${ERP_DATABASE:-}}"
POSTGRES_USER="${POSTGRES_USER:-erp}"
EXPECTED_POSTGRES_MAJOR="${EXPECTED_POSTGRES_MAJOR:-13}"
ODOO_VERSION="${ODOO_VERSION:-OpenERP 5}"
GIT_COMMIT="${GIT_COMMIT:-$(git -C "${REPO_ROOT}" rev-parse --short HEAD 2>/dev/null || printf 'unknown')}"
DATASET_DATE="${DATASET_DATE:-$(date -u +%Y%m%d)}"
DATASET_VERSION="${DATASET_VERSION:-${DATASET_DATE}}"
EXCLUDE_TIMESCALE_INTERNALS="${EXCLUDE_TIMESCALE_INTERNALS:-1}"
PG_DUMP_EXTRA_ARGS="${PG_DUMP_EXTRA_ARGS:-}"

log() {
  printf '[create_dataset] %s\n' "$*"
}

fail() {
  printf '[create_dataset] ERROR: %s\n' "$*" >&2
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

database_exists() {
  local db_name="$1"
  run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
    psql -U "${POSTGRES_USER}" -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='${db_name}';" | grep -Fxq '1'
}

resolve_postgres_db() {
  if [ -n "${POSTGRES_DB}" ]; then
    return
  fi

  if database_exists erp_runtime; then
    POSTGRES_DB="erp_runtime"
    return
  fi

  if database_exists erp; then
    POSTGRES_DB="erp"
    return
  fi

  fail "No s'ha pogut detectar la base de dades (esperat: erp_runtime o erp). Defineix POSTGRES_DB."
}

checksum_file() {
  local file="$1"
  if have_cmd sha256sum; then
    sha256sum "${file}" | cut -d' ' -f1
    return
  fi
  if have_cmd shasum; then
    shasum -a 256 "${file}" | cut -d' ' -f1
    return
  fi
  fail "No s'ha trobat sha256sum ni shasum"
}

require_tools() {
  local tools=(docker zstd date git)
  local tool
  for tool in "${tools[@]}"; do
    have_cmd "${tool}" || fail "Falta l'eina requerida: ${tool}"
  done
  if [ -z "${COMPOSE_FILE}" ]; then
    # Producer flow usually runs against root compose (host-accessible services).
    if [ -f "${REPO_ROOT}/docker-compose.yaml" ]; then
      COMPOSE_FILE="${REPO_ROOT}/docker-compose.yaml"
    elif [ -f "${REPO_ROOT}/docker-compose.yml" ]; then
      COMPOSE_FILE="${REPO_ROOT}/docker-compose.yml"
    elif [ -f "${ROOT_DIR}/docker-compose.yml" ]; then
      COMPOSE_FILE="${ROOT_DIR}/docker-compose.yml"
    fi
  fi

  [ -n "${COMPOSE_FILE}" ] || fail "No s'ha pogut resoldre COMPOSE_FILE"
  [ -f "${COMPOSE_FILE}" ] || fail "No existeix el fitxer compose: ${COMPOSE_FILE}"
  have_cmd sha256sum || have_cmd shasum || fail "No s'ha trobat sha256sum ni shasum"
  resolve_db_service
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

get_postgres_version() {
  run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
    psql -U "${POSTGRES_USER}" -d postgres -tAc 'SHOW server_version;' | tr -d '[:space:]'
}

assert_postgres_major() {
  local version major
  version="$(get_postgres_version)"
  major="${version%%.*}"
  [ -n "${major}" ] || fail "No s'ha pogut determinar la versió de PostgreSQL"
  if [ "${major}" != "${EXPECTED_POSTGRES_MAJOR}" ]; then
    fail "Versió PostgreSQL detectada ${version} (major ${major}) però s'esperava major ${EXPECTED_POSTGRES_MAJOR}"
  fi
}

main() {
  require_tools

  mkdir -p "${OUTPUT_DIR}"
  run_compose -f "${COMPOSE_FILE}" up -d "${DB_SERVICE}" >/dev/null
  wait_for_db
  resolve_postgres_db
  assert_postgres_major

  local dump_base dump_file compressed_file metadata_file checksum
  local -a dump_args
  dump_base="${DATASET_NAME}-${DATASET_DATE}"
  dump_file="${OUTPUT_DIR}/${dump_base}.dump"
  compressed_file="${dump_file}.zst"
  metadata_file="${OUTPUT_DIR}/${dump_base}.metadata.json"

  dump_args=( -Fc )
  if [ "${EXCLUDE_TIMESCALE_INTERNALS}" = "1" ]; then
    dump_args+=(
      --exclude-schema=_timescaledb_cache
      --exclude-schema=_timescaledb_catalog
      --exclude-schema=_timescaledb_config
      --exclude-schema=_timescaledb_functions
      --exclude-schema=_timescaledb_internal
    )
  fi
  if [ -n "${PG_DUMP_EXTRA_ARGS}" ]; then
    # shellcheck disable=SC2206
    dump_args+=( ${PG_DUMP_EXTRA_ARGS} )
  fi

  log "Generant dump PostgreSQL de ${POSTGRES_DB}"
  run_compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
    pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" "${dump_args[@]}" >"${dump_file}"

  log "Comprimint dump amb zstd"
  zstd -f --rm "${dump_file}" -o "${compressed_file}"

  checksum="$(checksum_file "${compressed_file}")"

  log "Escrivint metadata"
  cat >"${metadata_file}" <<EOF
{
  "dataset_version": "${DATASET_VERSION}",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "git_commit": "${GIT_COMMIT}",
  "postgres_version": "$(get_postgres_version)",
  "odoo_version": "${ODOO_VERSION}",
  "checksum_sha256": "${checksum}",
  "compressed_file": "$(basename "${compressed_file}")"
}
EOF

  log "Dataset creat correctament"
  log "Dump: ${compressed_file}"
  log "Metadata: ${metadata_file}"
}

main "$@"
