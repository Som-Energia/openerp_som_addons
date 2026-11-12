#!/usr/bin/env bash

"$HOME/bin/gh-release-downloader" \
    gisce/webclient \
    --version-prefix v3 \
    --output-dir "$HOME/src/webclient-build"
exit_code=$?

# Exit code 17 means that the downloaded release is already up to date.
if [ "$exit_code" -eq 17 ]; then
    exit 0
fi

exit "$exit_code"
