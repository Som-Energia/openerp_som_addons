#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${ROOT_DIR}/.." && pwd)"

BASE_IMAGE="${BASE_IMAGE:-}"
HARBOR_IMAGE_REPOSITORY="${HARBOR_IMAGE_REPOSITORY:-${TARGET_IMAGE_REPOSITORY:-${TARGET_IMAGE:-}}}"
HARBOR_DOMAIN="${HARBOR_DOMAIN:-}"
HARBOR_USERNAME="${HARBOR_USERNAME:-}"
HARBOR_PASSWORD="${HARBOR_PASSWORD:-}"
DATE_TAG="${DATE_TAG:-$(date -u +%Y%m%d)}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
ERP_BRANCH="${ERP_BRANCH:-rolling_erp01}"
ERP_DATABASE="${ERP_DATABASE:-erp}"
POSTGRES_IMAGE="${POSTGRES_IMAGE:-timescale/timescaledb:2.14.2-pg13}"
REDIS_IMAGE="${REDIS_IMAGE:-redis:5.0}"
MONGO_IMAGE="${MONGO_IMAGE:-mongo:3.0}"
MONGO_ARGS="${MONGO_ARGS:---smallfiles}"
WAIT_TIMEOUT_SECONDS="${WAIT_TIMEOUT_SECONDS:-4000}"
DOCKERFILE_PATH="${DOCKERFILE_PATH:-${ROOT_DIR}/Dockerfile}"
BUILD_CONTEXT="${BUILD_CONTEXT:-${REPO_ROOT}}"
EXPORT_PREWARMED_DB="${EXPORT_PREWARMED_DB:-1}"
PREWARMED_DB_DUMP_PATH="${PREWARMED_DB_DUMP_PATH:-${ROOT_DIR}/build/prewarmed/prewarmed-db.dump.zst}"
PREWARMED_DB_METADATA_PATH="${PREWARMED_DB_METADATA_PATH:-${PREWARMED_DB_DUMP_PATH%.dump.zst}.metadata.json}"
PREWARM_ONLY_DB_EXPORT="${PREWARM_ONLY_DB_EXPORT:-0}"
EXCLUDE_TIMESCALE_INTERNALS="${EXCLUDE_TIMESCALE_INTERNALS:-1}"

WORK_ID="prewarm-$(date +%Y%m%d%H%M%S)-$$"
NETWORK_NAME="${NETWORK_NAME:-${WORK_ID}-net}"
PG_CONTAINER="${PG_CONTAINER:-${WORK_ID}-postgres}"
REDIS_CONTAINER="${REDIS_CONTAINER:-${WORK_ID}-redis}"
MONGO_CONTAINER="${MONGO_CONTAINER:-${WORK_ID}-mongo}"
RUNTIME_CONTAINER="${RUNTIME_CONTAINER:-${WORK_ID}-runtime}"
LOCAL_BASE_IMAGE="${LOCAL_BASE_IMAGE:-openerp-runtime-base:${WORK_ID}}"
SECRET_DIR=""
GITHUB_TOKEN_FILE=""

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
	if [ -n "${SECRET_DIR}" ]; then
		rm -rf "${SECRET_DIR}"
	fi
}

validate_inputs() {
	if [ "${PREWARM_ONLY_DB_EXPORT}" != "1" ]; then
		[ -n "${HARBOR_IMAGE_REPOSITORY}" ] || fail "Cal HARBOR_IMAGE_REPOSITORY (ex: harbor.example.com/erp/openerp)"
	fi
	[ -n "${GITHUB_TOKEN}" ] || fail "Cal GITHUB_TOKEN (read access repos privats)"
	[ -f "${DOCKERFILE_PATH}" ] || fail "No existeix DOCKERFILE_PATH: ${DOCKERFILE_PATH}"
	[ -d "${BUILD_CONTEXT}" ] || fail "No existeix BUILD_CONTEXT: ${BUILD_CONTEXT}"
}

prepare_base_image() {
	if [ -n "${BASE_IMAGE}" ]; then
		log "Pull base image ${BASE_IMAGE}"
		docker pull "${BASE_IMAGE}" >/dev/null
		return
	fi

	BASE_IMAGE="${LOCAL_BASE_IMAGE}"
	log "Build base image ${BASE_IMAGE} des de ${DOCKERFILE_PATH}"
	if docker buildx version >/dev/null 2>&1; then
		DOCKER_BUILDKIT=1 docker build -f "${DOCKERFILE_PATH}" -t "${BASE_IMAGE}" "${BUILD_CONTEXT}"
	else
		log "buildx no disponible; faig fallback a docker build clàssic"
		DOCKER_BUILDKIT=0 docker build -f "${DOCKERFILE_PATH}" -t "${BASE_IMAGE}" "${BUILD_CONTEXT}"
	fi
}

prepare_github_token_secret() {
	SECRET_DIR="$(mktemp -d)"
	GITHUB_TOKEN_FILE="${SECRET_DIR}/github_token"
	printf '%s' "${GITHUB_TOKEN}" >"${GITHUB_TOKEN_FILE}"
	chmod 600 "${GITHUB_TOKEN_FILE}"
}

export_prewarmed_db_dump() {
	if [ "${EXPORT_PREWARMED_DB}" != "1" ]; then
		log "EXPORT_PREWARMED_DB=${EXPORT_PREWARMED_DB}; omitint export de la BD prewarmed"
		return
	fi

	require_cmd zstd
	require_cmd sha256sum
	require_cmd git
	mkdir -p "$(dirname "${PREWARMED_DB_DUMP_PATH}")"

	local -a dump_args
	dump_args=(-Fc)
	if [ "${EXCLUDE_TIMESCALE_INTERNALS}" = "1" ]; then
		dump_args+=(
			--exclude-schema=_timescaledb_cache
			--exclude-schema=_timescaledb_catalog
			--exclude-schema=_timescaledb_config
			--exclude-schema=_timescaledb_functions
			--exclude-schema=_timescaledb_internal
		)
	fi

	log "Exportant dump prewarmed de la BD ${ERP_DATABASE}"
	docker exec "${PG_CONTAINER}" pg_dump -U erp -d "${ERP_DATABASE}" "${dump_args[@]}" |
		zstd -f -o "${PREWARMED_DB_DUMP_PATH}"

	local checksum pg_version git_commit created_at
	checksum="$(sha256sum "${PREWARMED_DB_DUMP_PATH}" | cut -d' ' -f1)"
	pg_version="$(docker exec "${PG_CONTAINER}" psql -U erp -d postgres -tAc 'SHOW server_version;' | tr -d '[:space:]')"
	git_commit="$(git -C "${REPO_ROOT}" rev-parse --short HEAD 2>/dev/null || printf 'unknown')"
	created_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

	cat >"${PREWARMED_DB_METADATA_PATH}" <<EOF
{
  "dataset_version": "prewarmed-${WORK_ID}",
  "created_at": "${created_at}",
  "git_commit": "${git_commit}",
  "postgres_version": "${pg_version}",
  "odoo_version": "OpenERP 5",
  "checksum_sha256": "${checksum}",
  "compressed_file": "$(basename "${PREWARMED_DB_DUMP_PATH}")"
}
EOF

	log "Dump prewarmed exportat: ${PREWARMED_DB_DUMP_PATH}"
	log "Metadata prewarmed exportada: ${PREWARMED_DB_METADATA_PATH}"
}

sanitize_runtime_container() {
	log "Sanejant imatge abans del commit: eliminant .git i GITHUB_TOKEN"
	docker exec "${RUNTIME_CONTAINER}" bash -lc '
    set -euo pipefail
    find / -path /proc -prune \
      -o -path /sys -prune \
      -o -path /dev -prune \
      -o -path /run -prune \
      -o -name .git -type d -prune -exec rm -rf {} +
    unset GITHUB_TOKEN
  '
}

wait_for_dependencies_ready() {
	local timeout="$1"
	local start now
	start=$(date +%s)

	while true; do
		if ! docker ps --format '{{.Names}}' | grep -Fxq "${PG_CONTAINER}"; then
			docker logs "${PG_CONTAINER}" >&2 || true
			fail "PostgreSQL container s'ha aturat abans d'estar llest"
		fi
		if ! docker ps --format '{{.Names}}' | grep -Fxq "${REDIS_CONTAINER}"; then
			docker logs "${REDIS_CONTAINER}" >&2 || true
			fail "Redis container s'ha aturat abans d'estar llest"
		fi
		if ! docker ps --format '{{.Names}}' | grep -Fxq "${MONGO_CONTAINER}"; then
			docker logs "${MONGO_CONTAINER}" >&2 || true
			fail "Mongo container s'ha aturat abans d'estar llest"
		fi

		if docker exec "${PG_CONTAINER}" pg_isready -U erp -d postgres >/dev/null 2>&1 \
			&& docker exec "${REDIS_CONTAINER}" redis-cli ping 2>/dev/null | grep -Fq PONG \
			&& docker exec "${MONGO_CONTAINER}" mongo --quiet --eval 'db.runCommand({ ping: 1 }).ok' 2>/dev/null | grep -Fxq 1; then
			return
		fi

		now=$(date +%s)
		if [ $((now - start)) -ge "${timeout}" ]; then
			docker logs "${PG_CONTAINER}" >&2 || true
			docker logs "${REDIS_CONTAINER}" >&2 || true
			docker logs "${MONGO_CONTAINER}" >&2 || true
			fail "Timeout esperant dependències llestes (${timeout}s)"
		fi
		sleep 5
	done
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

resolve_target_repository() {
	if [[ "${HARBOR_IMAGE_REPOSITORY}" =~ ^.+:[^/]+$ ]]; then
		HARBOR_IMAGE_REPOSITORY="${HARBOR_IMAGE_REPOSITORY%:*}"
	fi
}

login_harbor_if_configured() {
	local registry
	registry="${HARBOR_IMAGE_REPOSITORY%%/*}"

	if [ -z "${HARBOR_DOMAIN}" ] && [ -z "${HARBOR_USERNAME}" ] && [ -z "${HARBOR_PASSWORD}" ]; then
		log "Sense HARBOR_* configurat; confiant en credencials docker existents"
		return
	fi

	[ -n "${HARBOR_DOMAIN}" ] || fail "Cal HARBOR_DOMAIN per fer docker login"
	[ -n "${HARBOR_USERNAME}" ] || fail "Cal HARBOR_USERNAME per fer docker login"
	[ -n "${HARBOR_PASSWORD}" ] || fail "Cal HARBOR_PASSWORD per fer docker login"
	[ "${HARBOR_DOMAIN}" = "${registry}" ] || fail "HARBOR_DOMAIN (${HARBOR_DOMAIN}) no coincideix amb registry de HARBOR_IMAGE_REPOSITORY (${registry})"

	log "Fent docker login a ${HARBOR_DOMAIN}"
	printf '%s' "${HARBOR_PASSWORD}" | docker login "${HARBOR_DOMAIN}" --username "${HARBOR_USERNAME}" --password-stdin >/dev/null
}

main() {
	require_cmd docker
	validate_inputs

	trap cleanup EXIT

	prepare_base_image
	prepare_github_token_secret

	log "Crear xarxa temporal ${NETWORK_NAME}"
	docker network create "${NETWORK_NAME}" >/dev/null

	log "Arrencar dependències temporals"
	docker run -d --name "${PG_CONTAINER}" --network "${NETWORK_NAME}" --network-alias postgres \
		-e POSTGRES_USER=erp -e POSTGRES_PASSWORD=erp -e POSTGRES_DB=erp \
		"${POSTGRES_IMAGE}" >/dev/null
	docker run -d --name "${REDIS_CONTAINER}" --network "${NETWORK_NAME}" --network-alias redis "${REDIS_IMAGE}" >/dev/null
	docker run -d --name "${MONGO_CONTAINER}" --network "${NETWORK_NAME}" --network-alias mongo "${MONGO_IMAGE}" ${MONGO_ARGS} >/dev/null

	log "Esperant dependències llestes"
	wait_for_dependencies_ready 300

	log "Arrencar runtime per fer bootstrap"
	docker run -d --name "${RUNTIME_CONTAINER}" --network "${NETWORK_NAME}" \
		-v "${GITHUB_TOKEN_FILE}:/run/secrets/github_token:ro" \
		-e ERP_BRANCH="${ERP_BRANCH}" \
		-e ERP_DATABASE="${ERP_DATABASE}" \
		-e ERP_BOOTSTRAP_TIMEOUT="${WAIT_TIMEOUT_SECONDS}" \
		-e OPENERP_DB_USER=erp \
		-e OPENERP_DB_PASSWORD=erp \
		--entrypoint bash \
		"${BASE_IMAGE}" \
		-lc 'export GITHUB_TOKEN="$(cat /run/secrets/github_token)"; exec /opt/somenergia/src/openerp_som_addons/runtime-docker/entrypoint.sh' >/dev/null

	log "Esperant final del bootstrap (timeout ${WAIT_TIMEOUT_SECONDS}s)"
	wait_for_runtime_ready "${WAIT_TIMEOUT_SECONDS}"

	export_prewarmed_db_dump

	if [ "${PREWARM_ONLY_DB_EXPORT}" = "1" ]; then
		log "PREWARM_ONLY_DB_EXPORT=1: ometent commit/push de la imatge"
		log "Aturant runtime bootstrapat"
		docker stop "${RUNTIME_CONTAINER}" >/dev/null
		return
	fi

	resolve_target_repository
	login_harbor_if_configured

	sanitize_runtime_container

	log "Aturant runtime bootstrapat"
	docker stop "${RUNTIME_CONTAINER}" >/dev/null

	log "Committant imatge prewarmed -> ${HARBOR_IMAGE_REPOSITORY}:latest"
	docker commit \
		--change 'ENTRYPOINT ["/opt/somenergia/src/openerp_som_addons/runtime-docker/entrypoint.sh"]' \
		--change 'CMD []' \
		"${RUNTIME_CONTAINER}" "${HARBOR_IMAGE_REPOSITORY}:latest" >/dev/null

	log "Taggant imatge prewarmed -> ${HARBOR_IMAGE_REPOSITORY}:${DATE_TAG}"
	docker tag "${HARBOR_IMAGE_REPOSITORY}:latest" "${HARBOR_IMAGE_REPOSITORY}:${DATE_TAG}"

	log "Publicant ${HARBOR_IMAGE_REPOSITORY}:latest"
	docker push "${HARBOR_IMAGE_REPOSITORY}:latest"
	log "Publicant ${HARBOR_IMAGE_REPOSITORY}:${DATE_TAG}"
	docker push "${HARBOR_IMAGE_REPOSITORY}:${DATE_TAG}"

	log "Imatge prewarmed publicada correctament"
}

main "$@"
