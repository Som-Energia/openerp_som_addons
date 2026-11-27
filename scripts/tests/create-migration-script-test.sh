#!/usr/bin/env bash
# Exercise migration generation without importing ERP or connecting to services.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
PYTHONPATH="$script_dir${PYTHONPATH:+:$PYTHONPATH}" \
    "${TEST_PYTHON:-python3}" "$script_dir/tests/test_create_migration_script.py"
