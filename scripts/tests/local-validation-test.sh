#!/usr/bin/env bash
# Verify setup and runner failure paths without installing packages or opening DBs.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="$script_dir${PYTHONPATH:+:$PYTHONPATH}" \
    "${TEST_PYTHON:-python3}" "$script_dir/tests/test_local_env.py"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
mkdir -p "$tmp/bin" "$tmp/workspace/somenergia-generationkwh"
: > "$tmp/workspace/somenergia-generationkwh/setup.py"
export TEST_PYTHON_LOG="$tmp/python.log"
cat > "$tmp/bin/python" <<'PYTHON'
#!/usr/bin/env bash
printf '%s\t' "$@" >> "$TEST_PYTHON_LOG"
printf '\n' >> "$TEST_PYTHON_LOG"
if [[ "$1" == -c ]]; then exit "${TEST_NOT_VENV:-0}"; fi
if [[ "$1" == -m && "$2" == pip ]]; then
    if [[ "$*" == *--no-deps* ]]; then exit "${TEST_EDITABLE_FAIL:-0}"; fi
    exit "${TEST_PIP_FAIL:-0}"
fi
if [[ "$1" == -m && "$2" == pre_commit ]]; then exit 0; fi
if [[ "$1" == */check_local_env.py ]]; then exit "${TEST_PREFLIGHT_FAIL:-0}"; fi
if [[ "$1" == */destral/destral/cli.py ]]; then exit 0; fi
exit 99
PYTHON
chmod +x "$tmp/bin/python"
export PATH="$tmp/bin:$PATH" WORKSPACE="$tmp/workspace"
bash "$script_dir/setup-local-validation.sh" > "$tmp/output" 2>&1
cp "$TEST_PYTHON_LOG" "$tmp/first-run"
: > "$TEST_PYTHON_LOG"
bash "$script_dir/setup-local-validation.sh" > "$tmp/output" 2>&1
cmp "$tmp/first-run" "$TEST_PYTHON_LOG" || fail 'setup is not repeatable'
grep -Fq -- 'requirements-local-validation.txt' "$TEST_PYTHON_LOG" || fail 'tool pins ignored'
grep -Fq -- $'--no-deps\t-e\t'"$WORKSPACE/somenergia-generationkwh" "$TEST_PYTHON_LOG" || fail 'missing editable install'
grep -Fq -- $'pre_commit\tinstall\t--install-hooks' "$TEST_PYTHON_LOG" || fail 'Git hooks not installed'
for failure in TEST_NOT_VENV TEST_PIP_FAIL TEST_EDITABLE_FAIL TEST_PREFLIGHT_FAIL; do
    : > "$TEST_PYTHON_LOG"
    if env "$failure=42" bash "$script_dir/setup-local-validation.sh" > "$tmp/output" 2>&1; then
        fail "$failure was hidden"
    fi
    if grep -Fq $'pre_commit\tinstall' "$TEST_PYTHON_LOG"; then fail 'hooks installed after failed setup'; fi
    if [[ "$failure" == TEST_NOT_VENV ]] && grep -Fq -- $'-m\tpip' "$TEST_PYTHON_LOG"; then
        fail 'packages installed without a Python 2 virtualenv'
    fi
done
: > "$TEST_PYTHON_LOG"
if TEST_PREFLIGHT_FAIL=42 bash "$script_dir/run-tests.sh" fixture_db --no-requirements -m example > "$tmp/output" 2>&1; then
    fail 'runner ignored failing preflight'
fi
if grep -Fq '/destral/destral/cli.py' "$TEST_PYTHON_LOG"; then fail 'Destral started before preflight passed'; fi
: > "$TEST_PYTHON_LOG"
bash "$script_dir/run-tests.sh" fixture_db --no-requirements -m example > "$tmp/output" 2>&1
grep -Fq $'/destral/destral/cli.py\tfixture_db\t--no-requirements\t-m\texample' "$TEST_PYTHON_LOG" || fail 'Destral arguments changed'
printf 'PASS: repeatable setup and fail-fast runner\n'
