#!/bin/bash
set -euo pipefail

# WORKSPACE: carpeta arrel on hi ha tots els repositoris del projecte
# Ex: export WORKSPACE=/home/<user>/src o /home/<user>/projects
: "${WORKSPACE:?WORKSPACE no definit. Ex: export WORKSPACE=/home/<user>/src}"

export PYTHONIOENCODING="UTF-8"
export PYTHONPATH="$WORKSPACE/erp/server/bin:$WORKSPACE/erp/server/bin/addons:$WORKSPACE/erp/server/sitecustomize:${PYTHONPATH:-}"
export PYTHONUNBUFFERED="1"

export DEBUG_ENABLED=0
export OORQ_ASYNC=0
export DESTRAL_TESTING_LANGS="['es_ES']"

# export OPENERP_DB_NAME="destral_db"

export OPENERP_ADDONS_PATH="$WORKSPACE/erp/server/bin/addons"
export OPENERP_DB_HOST="localhost"
export OPENERP_DB_USER="${OPENERP_DB_USER:-erp}"
export OPENERP_DB_PASSWORD="${OPENERP_DB_PASSWORD:-erp}"
export OPENERP_OORQ_ASYNC="False"
export OPENERP_PRICE_ACCURACY=6
export OPENERP_SECRET="verysecret"
export OPENERP_ROOT_PATH="$WORKSPACE/erp/server/bin/"
export OPENERP_REDIS_URL="redis://localhost"
export OPENERP_MONGODB_HOST="localhost"
export OPENERP_RUN_SCRIPTS_INTERACTIVE_RESULT=skip
export OPENERP_ENVIRONMENT=local
export OPENERP_SII_TEST_MODE=1
export OPENERP_IGNORE_PUBSUB=1

sanitize_db_name() {
  local value="${1:-}"
  value="$(printf '%s' "$value" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '_')"
  value="${value#_}"
  value="${value%_}"
  if [ -z "$value" ]; then
    value="default"
  fi
  printf '%s' "$value"
}

detect_ref_name() {
  if [ -n "${OPENERP_TEST_DB_REF:-}" ]; then
    printf '%s' "$OPENERP_TEST_DB_REF"
    return 0
  fi
  if [ -n "${GITHUB_HEAD_REF:-}" ]; then
    printf '%s' "$GITHUB_HEAD_REF"
    return 0
  fi
  if [ -n "${CI_COMMIT_REF_NAME:-}" ]; then
    printf '%s' "$CI_COMMIT_REF_NAME"
    return 0
  fi
  if [ -n "${BRANCH_NAME:-}" ]; then
    printf '%s' "$BRANCH_NAME"
    return 0
  fi
  if ref_name="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"; then
    printf '%s' "$ref_name"
    return 0
  fi
  printf 'default'
}

build_reuse_db_name() {
  local pr_number="${PR_NUMBER:-${CI_MERGE_REQUEST_IID:-${GITHUB_PR_NUMBER:-}}}"
  local ref_name
  local slug
  local name

  ref_name="$(detect_ref_name)"
  slug="$(sanitize_db_name "$ref_name")"

  if [ -n "$pr_number" ]; then
    name="test_pr_${pr_number}_${slug}"
  else
    name="test_branch_${slug}"
  fi

  printf '%.63s' "$(sanitize_db_name "$name")"
}

fresh_db_name() {
  local base="$1"
  local suffix
  local max_base_len

  suffix="$(date +%s)_$$"
  max_base_len=$((63 - ${#suffix} - 1))
  if [ "$max_base_len" -lt 1 ]; then
    max_base_len=1
  fi

  printf '%s_%s' "${base:0:max_base_len}" "$suffix"
}

db_name=""
if [ "$#" -gt 0 ] && [ "${1#-}" = "$1" ]; then
  db_name="$1"
  shift
else
  db_name="$(build_reuse_db_name)"
  if [ "${OPENERP_TEST_DB_FRESH:-0}" = "1" ]; then
    db_name="$(fresh_db_name "$db_name")"
  fi
fi

args=("$db_name" "$@")

export OPENERP_DB_NAME="$db_name"

# --no-requirements evita que destral intenti instal·lar dependències (recomanat en entorns locals)
python "$WORKSPACE/destral/destral/cli.py" "${args[@]}"
