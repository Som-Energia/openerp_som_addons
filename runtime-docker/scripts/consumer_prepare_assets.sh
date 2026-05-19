#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ERP_RUNTIME_IMAGE="${ERP_RUNTIME_IMAGE:-}"
DATASET_TAG="${DATASET_TAG:-latest}"
CACHE_DIR="${CACHE_DIR:-${ROOT_DIR}/.cache/datasets}"

log() {
  printf '[consumer_prepare_assets] %s\n' "$*"
}

fail() {
  printf '[consumer_prepare_assets] ERROR: %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Falta l'eina requerida: $1"
}

has_dataset_cached() {
  local target_dir="$1"
  shopt -s nullglob
  local dumps=("${target_dir}"/*.dump.zst)
  shopt -u nullglob
  [ ${#dumps[@]} -gt 0 ]
}

main() {
  require_cmd docker

  [ -n "${ERP_RUNTIME_IMAGE}" ] || fail "Cal ERP_RUNTIME_IMAGE"

  if docker image inspect "${ERP_RUNTIME_IMAGE}" >/dev/null 2>&1; then
    log "Imatge ja disponible localment: ${ERP_RUNTIME_IMAGE}"
  else
    log "Descarregant imatge prewarmed: ${ERP_RUNTIME_IMAGE}"
    docker pull "${ERP_RUNTIME_IMAGE}"
  fi

  local target_dir
  target_dir="${CACHE_DIR}/${DATASET_TAG}"
  if has_dataset_cached "${target_dir}"; then
    log "Dataset ja disponible a cache: ${target_dir}"
  else
    log "Dataset no trobat a cache; descarregant tag ${DATASET_TAG}"
    ./scripts/pull_dataset.sh
  fi

  log "Assets consumidor preparats"
}

main "$@"
