#!/bin/bash

set -euo pipefail

ROOT_DIR_SRC="${ROOT_DIR_SRC:-/opt/somenergia/src}"
export PYENV_VERSION="${PYENV_VERSION:-2.7.18}"
ERP_DATABASE="${ERP_DATABASE:-erp_runtime}"
ERP_XMLRPC_PORT="${ERP_XMLRPC_PORT:-8069}"
ERP_BIND_ADDRESS="${ERP_BIND_ADDRESS:-0.0.0.0}"
ERP_HEALTH_TIMEOUT="${ERP_HEALTH_TIMEOUT:-300}"
ERP_BOOTSTRAP_TIMEOUT="${ERP_BOOTSTRAP_TIMEOUT:-180}"

wait_for_port() {
	local host="$1"
	local port="$2"
	local timeout="$3"
	local start
	start=$(date +%s)
	while true; do
		if nc -z "$host" "$port" >/dev/null 2>&1; then
			return 0
		fi
		if [ $(($(date +%s) - start)) -ge "$timeout" ]; then
			echo "Timeout waiting for ${host}:${port}" >&2
			return 1
		fi
		sleep 2
	done
}

echo "Waiting dependencies: postgres, redis, mongo"
wait_for_port "postgres" "5432" "$ERP_BOOTSTRAP_TIMEOUT"
wait_for_port "redis" "6379" "$ERP_BOOTSTRAP_TIMEOUT"
wait_for_port "mongo" "27017" "$ERP_BOOTSTRAP_TIMEOUT"

if [ ! -d "${ROOT_DIR_SRC}/erp" ]; then
	if [ -z "${GITHUB_TOKEN:-}" ]; then
		echo "GITHUB_TOKEN is required to bootstrap ERP workspace (read access to private repos)" >&2
		exit 1
	fi

	echo "Bootstrapping ERP workspace in ${ROOT_DIR_SRC}"
	export PYTHON_VERSION="2.7"
	export ERP_BRANCH="${ERP_BRANCH:-rolling_erp01}"
	export BOOTSTRAP_SKIP_APT=1
	/opt/somenergia/src/openerp_som_addons/scripts/bootstrap-erp-env.sh
else
	echo "ERP workspace already bootstrapped, skipping clone/setup"
fi

export OPENERP_DB_HOST="postgres"
export OPENERP_DB_USER="${OPENERP_DB_USER:-erp}"
: "${OPENERP_DB_PASSWORD:?OPENERP_DB_PASSWORD is required}"
export OPENERP_DB_PASSWORD
export OPENERP_MONGODB_HOST="mongo"
export OPENERP_REDIS_URL="redis://redis:6379/0"

export ERP_DATABASE
export ERP_XMLRPC_PORT
export ERP_BIND_ADDRESS
export ERP_HEALTH_TIMEOUT

/opt/somenergia/src/openerp_som_addons/scripts/build-openerp-server.sh

ERP_PID_FILE="/tmp/erp-${ERP_DATABASE}.pid"
ERP_LOG_FILE="/tmp/erp-${ERP_DATABASE}.log"

if [ ! -f "$ERP_PID_FILE" ]; then
	echo "ERP PID file not found: $ERP_PID_FILE" >&2
	exit 1
fi

ERP_PID=$(cat "$ERP_PID_FILE")
echo "ERP runtime ready on port ${ERP_XMLRPC_PORT}. PID=${ERP_PID}"

tail --pid="$ERP_PID" -f "$ERP_LOG_FILE"
