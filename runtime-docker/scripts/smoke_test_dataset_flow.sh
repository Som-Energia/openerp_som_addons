#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

HARBOR_DOMAIN="${HARBOR_DOMAIN:-}"
HARBOR_USERNAME="${HARBOR_USERNAME:-}"
HARBOR_PASSWORD="${HARBOR_PASSWORD:-}"
HARBOR_DATASET_REPOSITORY="${HARBOR_DATASET_REPOSITORY:-}"

DATASET_TAG="${DATASET_TAG:-latest}"
COMPOSE_FILE="${COMPOSE_FILE:-}"
DB_SERVICE="${DB_SERVICE:-}"
POSTGRES_DB="${POSTGRES_DB:-${ERP_DATABASE:-}}"
POSTGRES_USER="${POSTGRES_USER:-erp}"

log() {
  printf '[dataset_smoke] %s\n' "$*"
}

fail() {
  printf '[dataset_smoke] ERROR: %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Falta l'eina requerida: $1"
}

validate_inputs() {
  [ -n "${HARBOR_DOMAIN}" ] || fail "Cal HARBOR_DOMAIN"
  [ -n "${HARBOR_USERNAME}" ] || fail "Cal HARBOR_USERNAME"
  [ -n "${HARBOR_PASSWORD}" ] || fail "Cal HARBOR_PASSWORD"

  if [ -z "${HARBOR_DATASET_REPOSITORY}" ]; then
    HARBOR_DATASET_REPOSITORY="${HARBOR_DOMAIN}/openerp/datasets"
  fi

  case "${HARBOR_DATASET_REPOSITORY}" in
    */*) ;;
    *) fail "HARBOR_DATASET_REPOSITORY invàlid: ${HARBOR_DATASET_REPOSITORY}. Exemple vàlid: ${HARBOR_DOMAIN}/openerp/datasets" ;;
  esac
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

compose_has_service() {
  local service="$1"
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose -f "${COMPOSE_FILE}" config --services | grep -Fxq "${service}"
    return
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f "${COMPOSE_FILE}" config --services | grep -Fxq "${service}"
    return
  fi
  fail "No s'ha trobat docker compose ni docker-compose"
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
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
      psql -U "${POSTGRES_USER}" -d postgres -tAc \
      "SELECT 1 FROM pg_database WHERE datname='${db_name}';" | grep -Fxq '1'
    return
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f "${COMPOSE_FILE}" exec -T "${DB_SERVICE}" \
      psql -U "${POSTGRES_USER}" -d postgres -tAc \
      "SELECT 1 FROM pg_database WHERE datname='${db_name}';" | grep -Fxq '1'
    return
  fi
  fail "No s'ha trobat docker compose ni docker-compose"
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

main() {
  require_cmd docker
  require_cmd oras
  require_cmd make

  validate_inputs
  resolve_compose_file
  resolve_db_service
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose -f "${COMPOSE_FILE}" up -d "${DB_SERVICE}" >/dev/null
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f "${COMPOSE_FILE}" up -d "${DB_SERVICE}" >/dev/null
  fi
  resolve_postgres_db

  log "Repository OCI: ${HARBOR_DATASET_REPOSITORY}"

  log "Login a Harbor (${HARBOR_DOMAIN})"
  printf '%s' "${HARBOR_PASSWORD}" | docker login "${HARBOR_DOMAIN}" -u "${HARBOR_USERNAME}" --password-stdin

  log "1/4 Crear dataset"
  COMPOSE_FILE="${COMPOSE_FILE}" DB_SERVICE="${DB_SERVICE}" POSTGRES_DB="${POSTGRES_DB}" POSTGRES_USER="${POSTGRES_USER}" \
    make -C "${ROOT_DIR}" dataset-producer-create

  log "2/4 Publicar dataset"
  HARBOR_DATASET_REPOSITORY="${HARBOR_DATASET_REPOSITORY}" \
    make -C "${ROOT_DIR}" dataset-producer-publish

  log "3/4 Descarregar dataset"
  HARBOR_DATASET_REPOSITORY="${HARBOR_DATASET_REPOSITORY}" DATASET_TAG="${DATASET_TAG}" \
    make -C "${ROOT_DIR}" dataset-consumer-pull

  log "4/4 Restaurar dataset"
  COMPOSE_FILE="${COMPOSE_FILE}" DB_SERVICE="${DB_SERVICE}" POSTGRES_DB="${POSTGRES_DB}" POSTGRES_USER="${POSTGRES_USER}" DATASET_TAG="${DATASET_TAG}" \
    make -C "${ROOT_DIR}" dataset-consumer-restore

  log "Smoke test completat correctament"
}

main "$@"
