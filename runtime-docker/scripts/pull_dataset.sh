#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

HARBOR_DATASET_REPOSITORY="${HARBOR_DATASET_REPOSITORY:-harbor.example.com/openerp/datasets}"
HARBOR_DOMAIN="${HARBOR_DOMAIN:-}"
HARBOR_USERNAME="${HARBOR_USERNAME:-}"
HARBOR_PASSWORD="${HARBOR_PASSWORD:-}"
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

registry_from_repository() {
  printf '%s' "${HARBOR_DATASET_REPOSITORY%%/*}"
}

oras_login_if_configured() {
  local registry
  registry="$(registry_from_repository)"

  if [ -z "${HARBOR_DOMAIN}" ] && [ -z "${HARBOR_USERNAME}" ] && [ -z "${HARBOR_PASSWORD}" ]; then
    return
  fi

  [ -n "${HARBOR_DOMAIN}" ] || fail "Cal HARBOR_DOMAIN per fer login"
  [ -n "${HARBOR_USERNAME}" ] || fail "Cal HARBOR_USERNAME per fer login"
  [ -n "${HARBOR_PASSWORD}" ] || fail "Cal HARBOR_PASSWORD per fer login"

  if [ "${HARBOR_DOMAIN}" != "${registry}" ]; then
    fail "HARBOR_DOMAIN (${HARBOR_DOMAIN}) no coincideix amb el registry de HARBOR_DATASET_REPOSITORY (${registry})"
  fi

  log "Fent login ORAS a ${HARBOR_DOMAIN}"
  printf '%s' "${HARBOR_PASSWORD}" | oras login "${HARBOR_DOMAIN}" --username "${HARBOR_USERNAME}" --password-stdin --insecure
}

main() {
  require_cmd oras
  oras_login_if_configured

  local target_dir ref
  target_dir="${CACHE_DIR}/${DATASET_TAG}"
  ref="${HARBOR_DATASET_REPOSITORY}:${DATASET_TAG}"

  mkdir -p "${target_dir}"
  log "Descarregant ${ref} a ${target_dir}"
  oras pull --output "${target_dir}" "${ref}" --insecure

  log "Dataset descarregat"
}

main "$@"
