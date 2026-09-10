#!/usr/bin/env bash
set -euo pipefail

wrapper="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)/run-tests-worktree.sh"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
assert_link() { [[ -L "$1" && "$(readlink -- "$1")" == "$2" ]] || fail "$1 does not point to $2"; }
wait_for() {
    local path="$1"
    for _ in {1..200}; do [[ -e "$path" ]] && return 0; sleep 0.01; done
    fail "timed out waiting for $path"
}
new_case() {
    case_root="$tmp/$1"
    worktree="$case_root/worktree"
    shared="$case_root/shared"
    state="$case_root/state"
    mkdir -p "$worktree/addon_one" "$worktree/addon_two" "$shared" "$case_root/original"
    : > "$worktree/addon_one/__terp__.py"; : > "$worktree/addon_two/__terp__.py"
    addon_args=(--addon addon_one)
    unset TEST_LINK_TWO TEST_SEEN_TWO
    runner="$case_root/runner.sh"
    cat > "$runner" <<'RUNNER'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$TEST_ARGS"
printf '%s' "$(readlink -- "$TEST_LINK")" > "$TEST_SEEN"
[[ -z "${TEST_LINK_TWO:-}" ]] || printf '%s' "$(readlink -- "$TEST_LINK_TWO")" > "$TEST_SEEN_TWO"
if [[ "${TEST_MODE:-}" == hold ]]; then
    : > "$TEST_READY"
    while [[ ! -e "$TEST_RELEASE" ]]; do sleep 0.01; done
elif [[ "${TEST_MODE:-}" == alter ]]; then
    rm -- "$TEST_LINK"
    ln -s -- "$TEST_EXTERNAL" "$TEST_LINK"
elif [[ "${TEST_MODE:-}" == fail-restore ]]; then
    : > "$TEST_FAIL_LN"
fi
exit "${TEST_EXIT:-0}"
RUNNER
    chmod +x "$runner"
    export TEST_ARGS="$case_root/args" TEST_SEEN="$case_root/seen" TEST_LINK="$shared/addon_one"
}
run_wrapper() {
    OPENERP_WORKTREE_TEST_WORKTREE="$worktree" \
    OPENERP_WORKTREE_TEST_WORKSPACE="$case_root" \
    OPENERP_WORKTREE_TEST_ADDONS_DIR="$shared" \
    OPENERP_WORKTREE_TEST_RUNNER="$runner" \
    OPENERP_WORKTREE_TEST_STATE_DIR="$state" \
    "$wrapper" "${addon_args[@]}" -- "$@"
}
new_case restore
ln -s "$case_root/missing" "$shared/addon_one"
ln -s "$case_root/original" "$shared/addon_two"
addon_args+=(--addon addon_two)
export TEST_LINK_TWO="$shared/addon_two" TEST_SEEN_TWO="$case_root/seen-two"
run_wrapper database --no-requirements -m addon_one
assert_link "$shared/addon_one" "$case_root/missing"
assert_link "$shared/addon_two" "$case_root/original"
[[ "$(<"$TEST_SEEN")" == "$worktree/addon_one" ]] || fail "runner did not see worktree addon"
[[ "$(<"$TEST_SEEN_TWO")" == "$worktree/addon_two" ]] || fail "runner did not see second addon"
[[ "$(printf '%s\n' database --no-requirements -m addon_one)" == "$(<"$TEST_ARGS")" ]] || fail "arguments changed"
new_case absent
run_wrapper --no-requirements -m addon_one
[[ ! -e "$shared/addon_one" && ! -L "$shared/addon_one" ]] || fail "ABSENT state was not restored"
new_case regular
: > "$shared/addon_one"
if run_wrapper --no-requirements 2> "$case_root/error"; then fail "regular entry was accepted"; fi
grep -q 'non-symlink' "$case_root/error" || fail "regular entry error missing"
new_case exit-code
export TEST_EXIT=42
set +e
run_wrapper --no-requirements
code=$?
set -e
unset TEST_EXIT
[[ "$code" == 42 ]] || fail "runner exit code became $code"
new_case serialization
export TEST_MODE=hold TEST_READY="$case_root/ready" TEST_RELEASE="$case_root/release"
run_wrapper --no-requirements & holder=$!
wait_for "$TEST_READY"
set +e
OPENERP_WORKTREE_TEST_LOCK_TIMEOUT=0 run_wrapper --no-requirements 2> "$case_root/error"
code=$?
set -e
: > "$TEST_RELEASE"
wait "$holder"
[[ "$code" == 75 ]] || fail "lock timeout exit code became $code"
grep -q '^  pid=[0-9]' "$case_root/error" || fail "owner metadata missing on timeout"
grep -q "worktree=$worktree" "$case_root/error" || fail "owner worktree missing on timeout"
unset TEST_MODE TEST_READY TEST_RELEASE
new_case alteration
export TEST_MODE=alter TEST_EXTERNAL="$case_root/external"
set +e
run_wrapper --no-requirements 2> "$case_root/error"
code=$?
set -e
unset TEST_MODE TEST_EXTERNAL
[[ "$code" == 1 ]] || fail "external alteration was not reported"
assert_link "$shared/addon_one" "$case_root/external"
[[ -d "$state/manifest" ]] || fail "unsafe manifest was removed"
new_case restore-failure
ln -s "$case_root/original" "$shared/addon_one"
mkdir "$case_root/bin"
cat > "$case_root/bin/ln" <<'FAIL_LN'
#!/usr/bin/env bash
[[ ! -e "$TEST_FAIL_LN" ]] || { printf 'forced ln failure\n' >&2; exit 73; }
exec /bin/ln "$@"
FAIL_LN
chmod +x "$case_root/bin/ln"
export TEST_MODE=fail-restore TEST_FAIL_LN="$case_root/fail-ln"
set +e
PATH="$case_root/bin:$PATH" run_wrapper --no-requirements 2> "$case_root/error"
code=$?
set -e
unset TEST_MODE TEST_FAIL_LN
[[ "$code" != 0 ]] || fail "restoration failure returned success"
assert_link "$shared/addon_one" "$worktree/addon_one"
[[ -d "$state/manifest" && -f "$state/owner" ]] || fail "recovery state was removed"
grep -q 'addon restoration failed; manifest retained' "$case_root/error" || fail "restoration error missing"
printf 'PASS: wrapper; restore_failure_exit=%s link=%s manifest=retained metadata=retained diagnostic=matched\n' "$code" "$(readlink -- "$shared/addon_one")"
