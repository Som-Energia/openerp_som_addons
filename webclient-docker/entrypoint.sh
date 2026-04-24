#!/bin/bash
set -e

CHECK_INTERVAL="${CHECK_INTERVAL:-21600}"  # 6h

/usr/local/bin/update-webclient.sh

(
    while true; do
        sleep "$CHECK_INTERVAL"
        /usr/local/bin/update-webclient.sh \
            || echo "[entrypoint] update failed, retry in ${CHECK_INTERVAL}s" >&2
    done
) &

exec nginx -g 'daemon off;'
