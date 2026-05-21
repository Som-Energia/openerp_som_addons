#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DATASET_REPOSITORY="${DATASET_REPOSITORY:-harbor.example.com/openerp/datasets}"
OUTPUT_DIR="${OUTPUT_DIR:-${ROOT_DIR}/build/datasets}"
PREWARMED_DB_DUMP_PATH="${PREWARMED_DB_DUMP_PATH:-${ROOT_DIR}/build/prewarmed/prewarmed-db.dump.zst}"
USE_PREWARMED_DB="${USE_PREWARMED_DB:-1}"
DATASET_FILE="${DATASET_FILE:-}"
METADATA_FILE="${METADATA_FILE:-}"
DATE_TAG="${DATE_TAG:-$(date -u +%Y%m%d)}"

log() {
	printf '[publish_dataset] %s\n' "$*"
}

fail() {
	printf '[publish_dataset] ERROR: %s\n' "$*" >&2
	exit 1
}

require_cmd() {
	command -v "$1" >/dev/null 2>&1 || fail "Falta l'eina requerida: $1"
}

validate_repository() {
	case "${DATASET_REPOSITORY}" in
	*/*) ;;
	*) fail "DATASET_REPOSITORY invàlid: ${DATASET_REPOSITORY}. Exemple vàlid: harbor.example.com/openerp/datasets" ;;
	esac
}

resolve_latest_files() {
	if [ -z "${DATASET_FILE}" ] && [ "${USE_PREWARMED_DB}" = "1" ] && [ -f "${PREWARMED_DB_DUMP_PATH}" ]; then
		DATASET_FILE="${PREWARMED_DB_DUMP_PATH}"
	fi

	if [ -z "${DATASET_FILE}" ]; then
		local f
		shopt -s nullglob
		for f in "${OUTPUT_DIR}"/*.dump.zst; do
			DATASET_FILE="${f}"
		done
		shopt -u nullglob
	fi
	[ -n "${DATASET_FILE}" ] || fail "No s'ha trobat cap fitxer .dump.zst a ${OUTPUT_DIR}"
	[ -f "${DATASET_FILE}" ] || fail "No existeix DATASET_FILE: ${DATASET_FILE}"

	if [ -z "${METADATA_FILE}" ]; then
		METADATA_FILE="${DATASET_FILE%.dump.zst}.metadata.json"
	fi
	[ -f "${METADATA_FILE}" ] || fail "No s'ha trobat metadata: ${METADATA_FILE}"
}

push_tag() {
	local tag="$1"
	local ref="${DATASET_REPOSITORY}:${tag}"
	local stage_dir

	stage_dir="$(mktemp -d -t dataset-publish.XXXXXX)"
	cp "${DATASET_FILE}" "${stage_dir}/$(basename "${DATASET_FILE}")"
	cp "${METADATA_FILE}" "${stage_dir}/metadata.json"

	log "Publicant ${ref}"
	(
		cd "${stage_dir}"
		oras push "${ref}" \
			"$(basename "${DATASET_FILE}"):application/zstd" \
			"metadata.json:application/json" \
			--artifact-type application/vnd.somenergia.pg-dataset.v1 \
			--insecure
	)

	rm -rf "${stage_dir}"
}

retag_as_latest() {
	local source_ref="${DATASET_REPOSITORY}:${DATE_TAG}"
	log "Assignant tag latest al mateix artefacte: ${source_ref} -> ${DATASET_REPOSITORY}:latest"
	oras tag "${source_ref}" latest
}

main() {
	require_cmd oras
	validate_repository

	resolve_latest_files

	push_tag "${DATE_TAG}"
	retag_as_latest

	log "Publicació completada"
}

main "$@"
