#!/bin/bash
set -e

CHECK_INTERVAL="${CHECK_INTERVAL:-21600}"  # 6h
WEBCLIENT_LISTEN_PORT="${WEBCLIENT_LISTEN_PORT:-8081}"
WEBCLIENT_API_UPSTREAM="${WEBCLIENT_API_UPSTREAM:-http://localhost:8068/}"

export WEBCLIENT_LISTEN_PORT
export WEBCLIENT_API_UPSTREAM

envsubst '${WEBCLIENT_LISTEN_PORT} ${WEBCLIENT_API_UPSTREAM}' \
    < /etc/nginx/templates/default.conf.template \
    > /etc/nginx/conf.d/default.conf

/usr/local/bin/update-webclient.sh

(
    while true; do
        sleep "$CHECK_INTERVAL"
        /usr/local/bin/update-webclient.sh \
            || echo "[entrypoint] update failed, retry in ${CHECK_INTERVAL}s" >&2
    done
) &

exec nginx -g 'daemon off;'
