#!/bin/bash

set -euo pipefail

: "${ERP_SERVER:?ERP_SERVER is required}"
: "${ERP_DATABASE:?ERP_DATABASE is required}"

ERP_BIND_ADDRESS="${ERP_BIND_ADDRESS:-0.0.0.0}"
ERP_XMLRPC_PORT="${ERP_XMLRPC_PORT:-8069}"
OPENERP_PRICE_ACCURACY="${OPENERP_PRICE_ACCURACY:-6}"
ERP_LOG_FILE="${ERP_LOG_FILE:-/tmp/erp-${ERP_DATABASE}.log}"
ERP_PID_FILE="${ERP_PID_FILE:-/tmp/erp-${ERP_DATABASE}.pid}"
ERP_HEALTH_TIMEOUT="${ERP_HEALTH_TIMEOUT:-180}"
ERP_READY_FILE="${ERP_READY_FILE:-/tmp/erp-ready-${ERP_DATABASE}.flag}"
OPENERP_CONFIG="${OPENERP_CONFIG:-}"
OPENERP_EXTRA_ARGS="${OPENERP_EXTRA_ARGS:-}"

SERVER_ARGS=(
  --no-netrpc
  --price_accuracy="${OPENERP_PRICE_ACCURACY}"
  --interface="${ERP_BIND_ADDRESS}"
  --port="${ERP_XMLRPC_PORT}"
  -d "$ERP_DATABASE"
)

if [ -n "$OPENERP_CONFIG" ]; then
  SERVER_ARGS+=(--config="$OPENERP_CONFIG")
fi

if [ -n "$OPENERP_EXTRA_ARGS" ]; then
  # shellcheck disable=SC2206
  EXTRA_ARGS=( $OPENERP_EXTRA_ARGS )
  SERVER_ARGS+=("${EXTRA_ARGS[@]}")
fi

echo "Starting ERP runtime on ${ERP_BIND_ADDRESS}:${ERP_XMLRPC_PORT}"
nohup python "$ERP_SERVER" \
  "${SERVER_ARGS[@]}" \
  >"$ERP_LOG_FILE" 2>&1 &

ERP_PID=$!
echo "$ERP_PID" > "$ERP_PID_FILE"
echo "ERP runtime PID: $ERP_PID"
echo "ERP runtime logs: $ERP_LOG_FILE"

python - "$ERP_BIND_ADDRESS" "$ERP_XMLRPC_PORT" "$ERP_HEALTH_TIMEOUT" "$ERP_READY_FILE" <<'PY'
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

if [ -n "${GITHUB_ENV:-}" ]; then
  echo "ERP_READY_FILE=$ERP_READY_FILE" >> "$GITHUB_ENV"
  echo "ERP_PID_FILE=$ERP_PID_FILE" >> "$GITHUB_ENV"
  echo "ERP_LOG_FILE=$ERP_LOG_FILE" >> "$GITHUB_ENV"
  echo "ERP_XMLRPC_PORT=$ERP_XMLRPC_PORT" >> "$GITHUB_ENV"
fi
