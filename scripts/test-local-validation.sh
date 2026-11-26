#!/usr/bin/env bash
# The same isolated checks run locally and in CI; no shared ERP state is touched.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(dirname -- "$script_dir")"
export PYTHONDONTWRITEBYTECODE=1
for script in "$script_dir"/*.sh "$script_dir"/tests/*.sh \
    "$repo_root"/.github/actions/bootstrap-erp/*.sh; do
    bash -n "$script"
done
for test in "$script_dir"/tests/*-test.sh; do
    printf '\nRunning %s\n' "${test##*/}"
    bash "$test"
done
printf '\nPASS: all local validation script tests\n'
