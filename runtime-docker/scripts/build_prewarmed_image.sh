#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

BASE_IMAGE="${BASE_IMAGE:-}"
TARGET_IMAGE="${TARGET_IMAGE:-}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
ERP_BRANCH="${ERP_BRANCH:-rolling_erp01}"
ERP_DATABASE="${ERP_DATABASE:-erp}"
POSTGRES_IMAGE="${POSTGRES_IMAGE:-timescale/timescaledb-postgis:latest-pg13}"
REDIS_IMAGE="${REDIS_IMAGE:-redis:5.0}"
MONGO_IMAGE="${MONGO_IMAGE:-mongo:3.0}"
WAIT_TIMEOUT_SECONDS="${WAIT_TIMEOUT_SECONDS:-900}"

WORK_ID="prewarm-$(date +%Y%m%d%H%M%S)-$$"
NETWORK_NAME="${NETWORK_NAME:-${WORK_ID}-net}"
PG_CONTAINER="${PG_CONTAINER:-${WORK_ID}-postgres}"
REDIS_CONTAINER="${REDIS_CONTAINER:-${WORK_ID}-redis}"
MONGO_CONTAINER="${MONGO_CONTAINER:-${WORK_ID}-mongo}"
RUNTIME_CONTAINER="${RUNTIME_CONTAINER:-${WORK_ID}-runtime}"

log() {
  printf '[prewarm_image] %s\n' "$*"
}

fail() {
  printf '[prewarm_image] ERROR: %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Falta l'eina requerida: $1"
}

cleanup() {
  set +e
  docker rm -f "${RUNTIME_CONTAINER}" "${PG_CONTAINER}" "${REDIS_CONTAINER}" "${MONGO_CONTAINER}" >/dev/null 2>&1 || true
  docker network rm "${NETWORK_NAME}" >/dev/null 2>&1 || true
}

validate_inputs() {
  [ -n "${BASE_IMAGE}" ] || fail "Cal BASE_IMAGE (ex: harbor.example.com/erp/openerp:20260514)"
  [ -n "${TARGET_IMAGE}" ] || fail "Cal TARGET_IMAGE (ex: harbor.example.com/erp/openerp:20260514-prewarmed)"
  [ -n "${GITHUB_TOKEN}" ] || fail "Cal GITHUB_TOKEN (read access repos privats)"
}

wait_for_runtime_ready() {
  local timeout="$1"
  local start now
  start=$(date +%s)

  while true; do
    if ! docker ps --format '{{.Names}}' | grep -Fxq "${RUNTIME_CONTAINER}"; then
      docker logs "${RUNTIME_CONTAINER}" >&2 || true
      fail "El contenidor runtime s'ha aturat abans d'acabar el bootstrap"
    fi

    if docker logs "${RUNTIME_CONTAINER}" 2>&1 | grep -Fq 'ERP runtime ready on port'; then
      return
    fi

    now=$(date +%s)
    if [ $((now - start)) -ge "${timeout}" ]; then
      docker logs "${RUNTIME_CONTAINER}" >&2 || true
      fail "Timeout esperant final del bootstrap (${timeout}s)"
    fi
    sleep 5
  done
}

main() {
  require_cmd docker
  validate_inputs

  trap cleanup EXIT

  log "Pull base image ${BASE_IMAGE}"
  docker pull "${BASE_IMAGE}" >/dev/null

  log "Crear xarxa temporal ${NETWORK_NAME}"
  docker network create "${NETWORK_NAME}" >/dev/null

  log "Arrencar dependències temporals"
  docker run -d --name "${PG_CONTAINER}" --network "${NETWORK_NAME}" --network-alias postgres \
    -e POSTGRES_USER=erp -e POSTGRES_PASSWORD=erp -e POSTGRES_DB=erp \
    "${POSTGRES_IMAGE}" >/dev/null
  docker run -d --name "${REDIS_CONTAINER}" --network "${NETWORK_NAME}" --network-alias redis "${REDIS_IMAGE}" >/dev/null
  docker run -d --name "${MONGO_CONTAINER}" --network "${NETWORK_NAME}" --network-alias mongo "${MONGO_IMAGE}" >/dev/null

  log "Arrencar runtime per fer bootstrap"
  docker run -d --name "${RUNTIME_CONTAINER}" --network "${NETWORK_NAME}" \
    -e GITHUB_TOKEN="${GITHUB_TOKEN}" \
    -e ERP_BRANCH="${ERP_BRANCH}" \
    -e ERP_DATABASE="${ERP_DATABASE}" \
    -e OPENERP_DB_USER=erp \
    -e OPENERP_DB_PASSWORD=erp \
    "${BASE_IMAGE}" >/dev/null

  log "Esperant final del bootstrap (timeout ${WAIT_TIMEOUT_SECONDS}s)"
  wait_for_runtime_ready "${WAIT_TIMEOUT_SECONDS}"

  log "Aturant runtime bootstrapat"
  docker stop "${RUNTIME_CONTAINER}" >/dev/null

  log "Committant imatge prewarmed -> ${TARGET_IMAGE}"
  docker commit "${RUNTIME_CONTAINER}" "${TARGET_IMAGE}" >/dev/null

  log "Publicant ${TARGET_IMAGE}"
  docker push "${TARGET_IMAGE}"

  log "Imatge prewarmed publicada correctament"
}

main "$@"
