#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DATASET_REPOSITORY="${DATASET_REPOSITORY:-harbor.example.com/openerp/datasets}"
DATASET_TAG="${DATASET_TAG:-latest}"
CACHE_DIR="${CACHE_DIR:-${ROOT_DIR}/.cache/datasets}"

log() {
  printf '[pull_dataset] %s\n' "$*"
}

fail() {
  printf '[pull_dataset] ERROR: %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Falta l'eina requerida: $1"
}

main() {
  require_cmd oras

  local target_dir ref
  target_dir="${CACHE_DIR}/${DATASET_TAG}"
  ref="${DATASET_REPOSITORY}:${DATASET_TAG}"

  mkdir -p "${target_dir}"
  log "Descarregant ${ref} a ${target_dir}"
  oras pull --output "${target_dir}" "${ref}"

  log "Dataset descarregat"
}

main "$@"
