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
#   LOG_PREFIX=[dataset-cron]

REPO_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
MAIN_BRANCH="${MAIN_BRANCH:-main}"
REMOTE_NAME="${REMOTE_NAME:-origin}"
STATE_FILE="${STATE_FILE:-/var/tmp/openerp_som_addons-${MAIN_BRANCH}.sha}"
PRODUCER_ENV_FILE="${PRODUCER_ENV_FILE:-${REPO_DIR}/runtime-docker/.env.producer}"
LOG_PREFIX="${LOG_PREFIX:-[dataset-cron]}"

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

if [ -n "$(git status --porcelain)" ]; then
	fail "Working tree is dirty. Use a clean dedicated clone for this cron job."
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

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "${CURRENT_BRANCH}" != "${MAIN_BRANCH}" ]; then
	log "Switching branch ${CURRENT_BRANCH} -> ${MAIN_BRANCH}"
	if git switch --help >/dev/null 2>&1; then
		git switch "${MAIN_BRANCH}"
	else
		git checkout "${MAIN_BRANCH}"
	fi
fi

git reset --hard "${REMOTE_NAME}/${MAIN_BRANCH}"

log "Running make -C runtime-docker dataset-producer-all"
make -C runtime-docker dataset-producer-all

printf '%s\n' "${REMOTE_SHA}" >"${STATE_FILE}"
log "Publish completed. Saved state to ${STATE_FILE}"
