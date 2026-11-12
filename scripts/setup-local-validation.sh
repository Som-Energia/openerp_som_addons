#!/usr/bin/env bash
# Prepare an existing ERP virtualenv; never clone repositories or switch refs.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(dirname -- "$script_dir")"
command -v python >/dev/null || { printf 'Activate the ERP Python 2.7 virtualenv first.\n' >&2; exit 2; }
python -c 'import sys; sys.exit(0 if sys.version_info[:2] == (2, 7) and hasattr(sys, "real_prefix") else 1)' || {
    printf 'Activate the ERP Python 2.7 virtualenv first; system Python is not modified.\n' >&2
    exit 2
}
common_git_dir="$(git -C "$script_dir" rev-parse --path-format=absolute --git-common-dir)"
workspace="${WORKSPACE:-$(dirname -- "$(dirname -- "$common_git_dir")")}"
[[ -f "$workspace/somenergia-generationkwh/setup.py" ]] || {
    printf 'Missing %s/somenergia-generationkwh; prepare the ERP workspace first.\n' "$workspace" >&2
    exit 2
}

python -m pip install -r "$repo_root/requirements-local-validation.txt"
# The base ERP dependencies must already exist. Do not upgrade them implicitly.
python -m pip install --no-deps -e "$workspace/somenergia-generationkwh"
python "$script_dir/check_local_env.py" --workspace "$workspace"
# Install Git hooks only after the environment passes its import smoke tests.
cd -- "$repo_root"
python -m pre_commit install --install-hooks
