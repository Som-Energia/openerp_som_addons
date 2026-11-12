#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DATASET_TAG="${DATASET_TAG:-latest}"
CACHE_DIR="${CACHE_DIR:-${ROOT_DIR}/.cache/datasets}"
CONSUMER_STATE_DIR="${CONSUMER_STATE_DIR:-${ROOT_DIR}/.cache/consumer-state}"
CONSUMER_STATE_FILE="${CONSUMER_STATE_FILE:-${CONSUMER_STATE_DIR}/dataset-state.env}"
CONSUMER_COMPOSE_FILE="${CONSUMER_COMPOSE_FILE:-${ROOT_DIR}/docker-compose.consumer.yml}"
CONSUMER_DB_SERVICE="${CONSUMER_DB_SERVICE:-postgres}"
FORCE_RESTORE="${FORCE_RESTORE:-0}"

RESTORED_REQUESTED_TAG=""
RESTORED_RESOLVED_TAG=""
RESTORED_AT=""

log() {
	printf '[consumer_sync] %s\n' "$*"
}

fail() {
	printf '[consumer_sync] ERROR: %s\n' "$*" >&2
	exit 1
}

metadata_value() {
	local key="$1"
	local metadata_file="$2"

	grep -Eo '"'"${key}"'"[[:space:]]*:[[:space:]]*"[^"]+"' "${metadata_file}" \
		| head -n1 \
		| sed -E 's/^[^:]+:[[:space:]]*"([^"]+)"$/\1/'
}

resolve_metadata_file() {
	local metadata_file="${CACHE_DIR}/${DATASET_TAG}/metadata.json"
	[ -f "${metadata_file}" ] || fail "No s'ha trobat metadata del dataset a ${metadata_file}"
	printf '%s\n' "${metadata_file}"
}

load_state() {
	if [ ! -f "${CONSUMER_STATE_FILE}" ]; then
		return
	fi

	# shellcheck disable=SC1090
	source "${CONSUMER_STATE_FILE}"
	RESTORED_REQUESTED_TAG="${requested_tag:-}"
	RESTORED_RESOLVED_TAG="${resolved_tag:-}"
	RESTORED_AT="${restored_at:-}"
}

write_state() {
	local requested_tag="$1"
	local resolved_tag="$2"
	local restored_at="$3"

	mkdir -p "${CONSUMER_STATE_DIR}"
	cat >"${CONSUMER_STATE_FILE}" <<EOF
requested_tag=${requested_tag}
resolved_tag=${resolved_tag}
restored_at=${restored_at}
last_sync_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
compose_file=${CONSUMER_COMPOSE_FILE}
db_service=${CONSUMER_DB_SERVICE}
EOF
}

should_restore() {
	local resolved_tag="$1"

	if [ "${FORCE_RESTORE}" = "1" ]; then
		log "FORCE_RESTORE=1; forço restore"
		return 0
	fi

	if [ ! -f "${CONSUMER_STATE_FILE}" ]; then
		log "No hi ha marca de dataset restaurat; cal restore"
		return 0
	fi

	if [ -z "${RESTORED_RESOLVED_TAG}" ]; then
		log "La marca no té resolved_tag; cal restore"
		return 0
	fi

	if [ "${RESTORED_RESOLVED_TAG}" != "${resolved_tag}" ]; then
		log "Dataset resolt nou (${RESTORED_RESOLVED_TAG} -> ${resolved_tag}); cal restore"
		return 0
	fi

	log "El dataset resolt ${resolved_tag} ja està restaurat"
	return 1
}

main() {
	local metadata_file resolved_tag restored_at

	[ -f "${CONSUMER_COMPOSE_FILE}" ] || fail "No existeix el compose consumidor: ${CONSUMER_COMPOSE_FILE}"

	./scripts/consumer_prepare_assets.sh
	metadata_file="$(resolve_metadata_file)"
	resolved_tag="$(metadata_value dataset_version "${metadata_file}")"
	[ -n "${resolved_tag}" ] || fail "No s'ha pogut resoldre dataset_version de ${metadata_file}"

	load_state

	if should_restore "${resolved_tag}"; then
		COMPOSE_FILE="${CONSUMER_COMPOSE_FILE}" DB_SERVICE="${CONSUMER_DB_SERVICE}" ./scripts/restore_dataset.sh
		restored_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
	else
		restored_at="${RESTORED_AT:-unknown}"
	fi

	write_state "${DATASET_TAG}" "${resolved_tag}" "${restored_at}"
	log "Sync consumidor completat (requested=${DATASET_TAG}, resolved=${resolved_tag})"
}

main "$@"
