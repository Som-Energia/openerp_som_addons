#!/bin/bash

set -euo pipefail

: "${ERP_DATABASE:?ERP_DATABASE is required}"

ROOT_DIR_SRC="${ROOT_DIR_SRC:-${GITHUB_WORKSPACE:-$PWD}/..}"
ERP_XMLRPC_PORT="${ERP_XMLRPC_PORT:-8069}"
ERP_BIND_ADDRESS="${ERP_BIND_ADDRESS:-0.0.0.0}"
ERP_HEALTH_TIMEOUT="${ERP_HEALTH_TIMEOUT:-180}"
ERP_IGNORE_DESTRAL_FAILURES="${ERP_IGNORE_DESTRAL_FAILURES:-1}"

export CI_REPO="${CI_REPO:-som-energia/openerp_som_addons}"
export CI_PULL_REQUEST="${CI_PULL_REQUEST:-0}"
export LANG="${LANG:-C.UTF-8}"
export LC_ALL="${LC_ALL:-C.UTF-8}"
export PYTHONIOENCODING="${PYTHONIOENCODING:-UTF-8}"
export PYTHONPATH="${ROOT_DIR_SRC}/erp/server/bin:${ROOT_DIR_SRC}/erp/server/bin/addons:${ROOT_DIR_SRC}/erp/server/sitecustomize:${PYTHONPATH:-}"
export OPENERP_PRICE_ACCURACY="${OPENERP_PRICE_ACCURACY:-6}"
export OORQ_ASYNC="${OORQ_ASYNC:-False}"
export OPENERP_SRID="${OPENERP_SRID:-25831}"
export OPENERP_ESIOS_TOKEN="${OPENERP_ESIOS_TOKEN:-}"
export OPENERP_MONGODB_HOST="${OPENERP_MONGODB_HOST:-localhost}"
export OPENERP_REDIS_URL="${OPENERP_REDIS_URL:-redis://localhost:6379/0}"
export OPENERP_ROOT_PATH="${ROOT_DIR_SRC}/erp/server/bin"
export OPENERP_ADDONS_PATH="${OPENERP_ROOT_PATH}/addons"
export OPENERP_DB_HOST="${OPENERP_DB_HOST:-localhost}"
export OPENERP_DB_USER="${OPENERP_DB_USER:-erp}"
export OPENERP_DB_PASSWORD="${OPENERP_DB_PASSWORD:-erp}"
export OPENERP_SII_TEST_MODE="${OPENERP_SII_TEST_MODE:-1}"
export OPENERP_SECRET="${OPENERP_SECRET:-verysecret}"
export OPENERP_IGNORE_PUBSUB="${OPENERP_IGNORE_PUBSUB:-1}"
export OPENERP_ENVIRONMENT="${OPENERP_ENVIRONMENT:-ci}"
export OPENERP_RUN_SCRIPTS_INTERACTIVE_RESULT="${OPENERP_RUN_SCRIPTS_INTERACTIVE_RESULT:-skip}"
export ERP_REQUIREMENTS_MODULES="${ERP_REQUIREMENTS_MODULES:-base_extended_som,l10n_ES_partner,l10n_ES_aeat_sii,l10n_ES_remesas}"

ERP_SERVER="${ROOT_DIR_SRC}/erp/server/bin/openerp-server.py"
READY_FILE="${RUNNER_TEMP:-/tmp}/erp-ready-${ERP_DATABASE}.flag"
PID_FILE="${RUNNER_TEMP:-/tmp}/erp-${ERP_DATABASE}.pid"
LOG_FILE="${RUNNER_TEMP:-/tmp}/erp-${ERP_DATABASE}.log"
START_SERVER_SCRIPT="${ROOT_DIR_SRC}/openerp_som_addons/scripts/start-openerp-server.sh"

if command -v destral >/dev/null 2>&1; then
  DESTRAL_RUN=(destral)
elif [ -f "${ROOT_DIR_SRC}/destral/destral/cli.py" ]; then
  DESTRAL_RUN=(python "${ROOT_DIR_SRC}/destral/destral/cli.py")
else
  echo "Destral command not found and CLI path is missing" >&2
  exit 1
fi

if [ ! -f "$ERP_SERVER" ]; then
  echo "OpenERP server not found: $ERP_SERVER" >&2
  exit 1
fi

if [ ! -f "$START_SERVER_SCRIPT" ]; then
  echo "Start server script not found: $START_SERVER_SCRIPT" >&2
  exit 1
fi

python - <<'PY'
import os
from destral.utils import install_requirements

addons_path = os.environ.get('OPENERP_ADDONS_PATH')
modules = [m.strip() for m in os.environ.get('ERP_REQUIREMENTS_MODULES', '').split(',') if m.strip()]

if addons_path and modules:
    for module in modules:
        install_requirements(module, addons_path)
PY

echo "Building ERP model in database '$ERP_DATABASE'"
SAVED_OPENERP_CONFIG="${OPENERP_CONFIG:-}"
unset OPENERP_CONFIG
set +e
"${DESTRAL_RUN[@]}" -m som_modul_fulla -d "$ERP_DATABASE
DESTRAL_EXIT_CODE=$?
set -e
if [ -n "$SAVED_OPENERP_CONFIG" ]; then
  export OPENERP_CONFIG="$SAVED_OPENERP_CONFIG"
fi

if [ "$DESTRAL_EXIT_CODE" -ne 0 ]; then
  if [ "$ERP_IGNORE_DESTRAL_FAILURES" = "1" ]; then
    echo "Destral finished with errors (exit $DESTRAL_EXIT_CODE), continuing startup"
  else
    echo "Destral failed with exit code $DESTRAL_EXIT_CODE" >&2
    exit "$DESTRAL_EXIT_CODE"
  fi
fi

ERP_LOG_FILE="$LOG_FILE" \
ERP_PID_FILE="$PID_FILE" \
ERP_READY_FILE="$READY_FILE" \
ERP_SERVER="$ERP_SERVER" \
ERP_DATABASE="$ERP_DATABASE" \
ERP_BIND_ADDRESS="$ERP_BIND_ADDRESS" \
ERP_XMLRPC_PORT="$ERP_XMLRPC_PORT" \
ERP_HEALTH_TIMEOUT="$ERP_HEALTH_TIMEOUT" \
OPENERP_CONFIG="${OPENERP_CONFIG:-${ROOT_DIR_SRC}/openerp_som_addons/runtime-docker/erp.conf}" \
OPENERP_PRICE_ACCURACY="$OPENERP_PRICE_ACCURACY" \
bash "$START_SERVER_SCRIPT"

echo "ERP runtime exported at ${ERP_BIND_ADDRESS}:${ERP_XMLRPC_PORT}"
