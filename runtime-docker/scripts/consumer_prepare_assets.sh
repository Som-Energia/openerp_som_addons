#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ERP_RUNTIME_IMAGE="${ERP_RUNTIME_IMAGE:-example.com/erp/openerp:latest}"
DATASET_TAG="${DATASET_TAG:-latest}"
CACHE_DIR="${CACHE_DIR:-${ROOT_DIR}/.cache/datasets}"
FORCE_REFRESH_LATEST="${FORCE_REFRESH_LATEST:-1}"

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

get_local_digest() {
	local image="$1"
	local repodigest
	repodigest="$(docker image inspect --format '{{index .RepoDigests 0}}' "${image}" 2>/dev/null || true)"
	[ -n "${repodigest}" ] || return 1
	printf '%s\n' "${repodigest##*@}"
}

get_remote_digest() {
	local image="$1"
	local manifest
	manifest="$(docker manifest inspect "${image}" 2>/dev/null || true)"
	[ -n "${manifest}" ] || return 1
	printf '%s\n' "${manifest}" | grep -m1 -o 'sha256:[a-f0-9]\{64\}'
}

should_pull_latest_image() {
	local local_digest remote_digest
	local_digest="$(get_local_digest "${ERP_RUNTIME_IMAGE}" || true)"
	remote_digest="$(get_remote_digest "${ERP_RUNTIME_IMAGE}" || true)"

	if [ -z "${remote_digest}" ]; then
		log "No s'ha pogut resoldre digest remot; faig pull per seguretat"
		return 0
	fi

	if [ -z "${local_digest}" ]; then
		log "No hi ha digest local; faig pull"
		return 0
	fi

	if [ "${local_digest}" != "${remote_digest}" ]; then
		log "Digest latest diferent (local=${local_digest}, remot=${remote_digest}); faig pull"
		return 0
	fi

	log "Digest latest local=remot (${local_digest}); no cal pull"
	return 1
}

main() {
	require_cmd docker

	if [[ "${ERP_RUNTIME_IMAGE}" == *":latest" ]] && [ "${FORCE_REFRESH_LATEST}" = "1" ]; then
		if should_pull_latest_image; then
			log "Refrescant imatge latest: ${ERP_RUNTIME_IMAGE}"
			docker pull "${ERP_RUNTIME_IMAGE}"
		fi
	elif docker image inspect "${ERP_RUNTIME_IMAGE}" >/dev/null 2>&1; then
		log "Imatge ja disponible localment: ${ERP_RUNTIME_IMAGE}"
	else
		log "Descarregant imatge prewarmed: ${ERP_RUNTIME_IMAGE}"
		docker pull "${ERP_RUNTIME_IMAGE}"
	fi

	local target_dir
	target_dir="${CACHE_DIR}/${DATASET_TAG}"
	if [ "${DATASET_TAG}" = "latest" ] && [ "${FORCE_REFRESH_LATEST}" = "1" ]; then
		log "Refrescant dataset latest"
		./scripts/pull_dataset.sh
	elif has_dataset_cached "${target_dir}"; then
		log "Dataset ja disponible a cache: ${target_dir}"
	else
		log "Dataset no trobat a cache; descarregant tag ${DATASET_TAG}"
		./scripts/pull_dataset.sh
	fi

	log "Assets consumidor preparats"
}

main "$@"
