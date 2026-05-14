#!/bin/bash

set -euo pipefail

: "${ERP_DATABASE:?ERP_DATABASE is required}"

ROOT_DIR_SRC="${ROOT_DIR_SRC:-${GITHUB_WORKSPACE:-$PWD}/..}"
ERP_XMLRPC_PORT="${ERP_XMLRPC_PORT:-8069}"
ERP_BIND_ADDRESS="${ERP_BIND_ADDRESS:-0.0.0.0}"
ERP_HEALTH_TIMEOUT="${ERP_HEALTH_TIMEOUT:-180}"

export CI_REPO="${CI_REPO:-som-energia/openerp_som_addons}"
export CI_PULL_REQUEST="${CI_PULL_REQUEST:-0}"
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
export DESTRAL_TESTING_LANGS="${DESTRAL_TESTING_LANGS:-['es_ES']}"

DESTRAL_CLI="${ROOT_DIR_SRC}/destral/destral/cli.py"
ERP_SERVER="${ROOT_DIR_SRC}/erp/server/bin/openerp-server.py"
READY_FILE="${RUNNER_TEMP:-/tmp}/erp-ready-${ERP_DATABASE}.flag"
PID_FILE="${RUNNER_TEMP:-/tmp}/erp-${ERP_DATABASE}.pid"
LOG_FILE="${RUNNER_TEMP:-/tmp}/erp-${ERP_DATABASE}.log"

if [ ! -f "$DESTRAL_CLI" ]; then
  echo "Destral CLI not found: $DESTRAL_CLI" >&2
  exit 1
fi

if [ ! -f "$ERP_SERVER" ]; then
  echo "OpenERP server not found: $ERP_SERVER" >&2
  exit 1
fi

echo "Building ERP model in database '$ERP_DATABASE'"
python "$DESTRAL_CLI" -t OOBaseTests.test_translate_modules -d "$ERP_DATABASE"

echo "Starting ERP runtime on ${ERP_BIND_ADDRESS}:${ERP_XMLRPC_PORT}"
nohup python "$ERP_SERVER" \
  --no-netrpc \
  --price_accuracy="${OPENERP_PRICE_ACCURACY}" \
  --xmlrpc-interface="${ERP_BIND_ADDRESS}" \
  --xmlrpc-port="${ERP_XMLRPC_PORT}" \
  -d "$ERP_DATABASE" \
  >"$LOG_FILE" 2>&1 &

ERP_PID=$!
echo "$ERP_PID" > "$PID_FILE"
echo "ERP runtime PID: $ERP_PID"
echo "ERP runtime logs: $LOG_FILE"

python - "$ERP_BIND_ADDRESS" "$ERP_XMLRPC_PORT" "$ERP_HEALTH_TIMEOUT" "$READY_FILE" <<'PY'
import socket
import sys
import time

host = sys.argv[1]
port = int(sys.argv[2])
timeout = int(sys.argv[3])
ready_file = sys.argv[4]

deadline = time.time() + timeout
while time.time() < deadline:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        sock.connect((host, port))
        sock.close()
        with open(ready_file, 'w') as handler:
            handler.write('ready\n')
        print('ERP runtime is ready')
        sys.exit(0)
    except Exception:
        time.sleep(2)
    finally:
        sock.close()

print('ERP runtime did not become ready in {} seconds'.format(timeout))
sys.exit(1)
PY

echo "ERP_READY_FILE=$READY_FILE" >> "$GITHUB_ENV"
echo "ERP_PID_FILE=$PID_FILE" >> "$GITHUB_ENV"
echo "ERP_LOG_FILE=$LOG_FILE" >> "$GITHUB_ENV"
echo "ERP_XMLRPC_PORT=$ERP_XMLRPC_PORT" >> "$GITHUB_ENV"

echo "ERP runtime exported at ${ERP_BIND_ADDRESS}:${ERP_XMLRPC_PORT}"
