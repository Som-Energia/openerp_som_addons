#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   scripts/cron_publish_dataset_on_main_change.sh [/path/to/repo]
#
# Optional env vars:
#   MAIN_BRANCH=main
#   REMOTE_NAME=origin
#   STATE_FILE=/var/tmp/openerp_som_addons-main.sha
#   PRODUCER_ENV_FILE=/secure/path/.env.producer
#   USE_LOCAL_CODE=1   # 1=sempre executa codi local, 0=segueix origin/main
#   LOG_PREFIX=[dataset-cron]

REPO_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
MAIN_BRANCH="${MAIN_BRANCH:-main}"
REMOTE_NAME="${REMOTE_NAME:-origin}"
STATE_FILE="${STATE_FILE:-/var/tmp/openerp_som_addons-${MAIN_BRANCH}.sha}"
PRODUCER_ENV_FILE="${PRODUCER_ENV_FILE:-${REPO_DIR}/runtime-docker/.env.producer}"
LOG_PREFIX="${LOG_PREFIX:-[dataset-cron]}"
USE_LOCAL_CODE="${USE_LOCAL_CODE:-1}"

log() {
	printf '%s %s\n' "${LOG_PREFIX}" "$*"
}

fail() {
	printf '%s ERROR: %s\n' "${LOG_PREFIX}" "$*" >&2
	exit 1
}

require_cmd() {
	command -v "$1" >/dev/null 2>&1 || fail "Missing command: $1"
}

require_cmd git
require_cmd make

[ -d "${REPO_DIR}/.git" ] || fail "Not a git repo: ${REPO_DIR}"
[ -f "${PRODUCER_ENV_FILE}" ] || fail "Missing producer env file: ${PRODUCER_ENV_FILE}"

cd "${REPO_DIR}"

if [ "${USE_LOCAL_CODE}" = "1" ]; then
	log "USE_LOCAL_CODE=1 -> executant codi local (sense fetch/worktree)"

	if [ "${PRODUCER_ENV_FILE}" != "${REPO_DIR}/runtime-docker/.env.producer" ]; then
		log "Applying PRODUCER_ENV_FILE into runtime-docker/.env.producer"
		cp "${PRODUCER_ENV_FILE}" "${REPO_DIR}/runtime-docker/.env.producer"
	fi

	log "Running make -C runtime-docker dataset-producer-all"
	make -C "${REPO_DIR}/runtime-docker" dataset-producer-all
	log "Publish completed with local code"
	exit 0
fi

log "Fetching ${REMOTE_NAME}/${MAIN_BRANCH}"
git fetch --prune "${REMOTE_NAME}" "${MAIN_BRANCH}"

REMOTE_SHA="$(git rev-parse "${REMOTE_NAME}/${MAIN_BRANCH}")"
LAST_SHA=""
if [ -f "${STATE_FILE}" ]; then
	LAST_SHA="$(tr -d '[:space:]' <"${STATE_FILE}")"
fi

if [ "${REMOTE_SHA}" = "${LAST_SHA}" ]; then
	log "No changes on ${REMOTE_NAME}/${MAIN_BRANCH} (sha=${REMOTE_SHA:0:12}). Nothing to do."
	exit 0
fi

log "New commit detected on ${MAIN_BRANCH}: ${LAST_SHA:0:12} -> ${REMOTE_SHA:0:12}"

WORKTREE_DIR="$(mktemp -d -t dataset-producer-worktree.XXXXXX)"
cleanup() {
	set +e
	git -C "${REPO_DIR}" worktree remove --force "${WORKTREE_DIR}" >/dev/null 2>&1 || true
	rm -rf "${WORKTREE_DIR}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

log "Creating isolated worktree at ${WORKTREE_DIR} (${REMOTE_SHA:0:12})"
git -C "${REPO_DIR}" worktree add --detach "${WORKTREE_DIR}" "${REMOTE_SHA}" >/dev/null

if [ "${PRODUCER_ENV_FILE}" != "${WORKTREE_DIR}/runtime-docker/.env.producer" ]; then
	log "Applying PRODUCER_ENV_FILE into worktree runtime-docker/.env.producer"
	cp "${PRODUCER_ENV_FILE}" "${WORKTREE_DIR}/runtime-docker/.env.producer"
fi

log "Running make -C runtime-docker dataset-producer-all"
make -C "${WORKTREE_DIR}/runtime-docker" dataset-producer-all

printf '%s\n' "${REMOTE_SHA}" >"${STATE_FILE}"
log "Publish completed. Saved state to ${STATE_FILE}"
