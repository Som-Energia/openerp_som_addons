#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
wrapper="$script_dir/sync-workspace-repositories.sh"
test_wrapper="$script_dir/run-tests-worktree.sh"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

assert_equal() {
    [[ "$1" == "$2" ]] || fail "expected '$2', got '$1'"
}

make_seed() {
    local name="$1"
    local seed="$tmp/$name-seed"

    git -c init.defaultBranch=master init -q "$seed"
    git -C "$seed" config user.name 'Workspace sync test'
    git -C "$seed" config user.email 'workspace-sync@example.invalid'
    printf '%s\n' initial > "$seed/data"
    git -C "$seed" add data
    GIT_AUTHOR_DATE='2020-01-01T00:00:00Z' \
        GIT_COMMITTER_DATE='2020-01-01T00:00:00Z' \
        git -C "$seed" commit -qm initial
}

make_clone() {
    local name="$1"

    git clone -q --bare "$tmp/$name-seed" "$tmp/$name-remote.git"
    git clone -q "$tmp/$name-remote.git" "$tmp/$name"
}

sync() {
    "$tmp/openerp_som_addons/scripts/sync-workspace-repositories.sh" \
        --workspace "$tmp" --python-version 3.10 "$@"
}

mkdir -p "$tmp/openerp_som_addons/scripts" "$tmp/openerp_som_addons/.agents"
cp "$wrapper" "$tmp/openerp_som_addons/scripts/"
chmod +x "$tmp/openerp_som_addons/scripts/sync-workspace-repositories.sh"
printf '%s\n' \
    $'branchrepo\torigin\tbranch\trolling_erp01\tall' \
    $'defaultrepo\torigin\tdefault-branch\t-\tall' \
    $'tagrepo\torigin\tlatest-tag\t-\tall' \
    $'py2repo\torigin\tbranch\tpy2\tpy2' \
    > "$tmp/openerp_som_addons/.agents/workspace-repositories.tsv"

make_seed branchrepo
git -C "$tmp/branchrepo-seed" branch rolling_erp01
git -C "$tmp/branchrepo-seed" branch developer
make_clone branchrepo

make_seed defaultrepo
make_clone defaultrepo

make_seed tagrepo
git -C "$tmp/tagrepo-seed" tag v1
printf '%s\n' next >> "$tmp/tagrepo-seed/data"
GIT_AUTHOR_DATE='2021-01-01T00:00:00Z' \
    GIT_COMMITTER_DATE='2021-01-01T00:00:00Z' \
    git -C "$tmp/tagrepo-seed" commit -qam next
git -C "$tmp/tagrepo-seed" tag v2
make_clone tagrepo

sync
assert_equal "$(git -C "$tmp/branchrepo" branch --show-current)" rolling_erp01
assert_equal "$(git -C "$tmp/defaultrepo" branch --show-current)" master
assert_equal "$(git -C "$tmp/tagrepo" describe --exact-match --tags HEAD)" v2

# A tag that exists only in the local clone must not be selected over remote v2.
git -C "$tmp/tagrepo" config user.name 'Workspace sync test'
git -C "$tmp/tagrepo" config user.email 'workspace-sync@example.invalid'
git -C "$tmp/tagrepo" commit --allow-empty -qm stale-local-tag
git -C "$tmp/tagrepo" tag v999
sync
assert_equal "$(git -C "$tmp/tagrepo" describe --exact-match --tags HEAD)" v2

# The remote's HEAD changes from master to main after the local clone is made.
git -C "$tmp/defaultrepo-seed" branch main
git -C "$tmp/defaultrepo-seed" push -q "$tmp/defaultrepo-remote.git" main
git -C "$tmp/defaultrepo-remote.git" symbolic-ref HEAD refs/heads/main
sync
assert_equal "$(git -C "$tmp/defaultrepo" branch --show-current)" main

# A rewritten branch requires opt-in and preserves its former local tip.
git -C "$tmp/branchrepo-seed" switch -q rolling_erp01
printf '%s\n' first-rolling-tip > "$tmp/branchrepo-seed/data"
git -C "$tmp/branchrepo-seed" commit -qam first-rolling-tip
git -C "$tmp/branchrepo-seed" push -q "$tmp/branchrepo-remote.git" rolling_erp01
sync
previous_head="$(git -C "$tmp/branchrepo" rev-parse HEAD)"
git -C "$tmp/branchrepo-seed" reset --hard -q master
printf '%s\n' rewritten-rolling-tip > "$tmp/branchrepo-seed/data"
git -C "$tmp/branchrepo-seed" commit -qam rewritten-rolling-tip
git -C "$tmp/branchrepo-seed" push -q --force "$tmp/branchrepo-remote.git" rolling_erp01
if sync >/dev/null 2>&1; then
    fail 'rewritten branch was accepted without explicit approval'
fi
assert_equal "$(git -C "$tmp/branchrepo" rev-parse HEAD)" "$previous_head"
sync --accept-rewritten-branch branchrepo
assert_equal "$(git -C "$tmp/branchrepo" rev-parse HEAD)" \
    "$(git -C "$tmp/branchrepo" rev-parse origin/rolling_erp01)"
git -C "$tmp/branchrepo" branch --list 'workspace-sync-backup/rolling_erp01/*' | \
    grep -q . || fail 'rewritten branch backup was not created'

sync --branch branchrepo=developer --persist
assert_equal "$(git -C "$tmp/branchrepo" branch --show-current)" developer
grep -Fx 'branchrepo developer' \
    "$tmp/openerp_som_addons/.agents/workspace-repositories.local" >/dev/null \
    || fail 'persistent override was not written'
sync --clear-branch branchrepo --persist-only
if grep -Fqx 'branchrepo developer' \
    "$tmp/openerp_som_addons/.agents/workspace-repositories.local"; then
    fail 'persistent override was not removed'
fi

# The workspace-wide lock rejects another sync before it performs preflight.
lock_file="$tmp/.openerp-workspace-sync.lock"
lock_ready="$tmp/lock-ready"
(
    exec 9>"$lock_file"
    flock -n 9
    : > "$lock_ready"
    sleep 3
) &
locker_pid=$!
for _ in {1..100}; do [[ -e "$lock_ready" ]] && break; sleep 0.01; done
[[ -e "$lock_ready" ]] || fail 'lock holder did not start'
if OPENERP_WORKSPACE_SYNC_LOCK_TIMEOUT=0 sync --dry-run > "$tmp/lock-out" 2> "$tmp/lock-err"; then
    fail 'concurrent synchronization acquired the workspace lock'
fi
wait "$locker_pid"
grep -q 'Timed out waiting for workspace synchronization lock' "$tmp/lock-err" \
    || fail 'lock timeout was not reported'

# A real worktree test keeps the addon lock for the full runner execution.
# Synchronization must not change branchrepo until the runner has finished.
mkdir -p "$tmp/openerp_som_addons/testaddon" "$tmp/erp/server/bin/addons"
: > "$tmp/openerp_som_addons/testaddon/__terp__.py"
runner="$tmp/test-runner.sh"
cat > "$runner" <<'RUNNER'
#!/usr/bin/env bash
: > "$TEST_READY"
for _ in {1..1000}; do
    [[ ! -e "$TEST_RELEASE" ]] || exit 0
    sleep 0.01
done
exit 1
RUNNER
chmod +x "$runner"
ready="$tmp/test-ready"
release="$tmp/test-release"
OPENERP_WORKTREE_TEST_WORKTREE="$tmp/openerp_som_addons" \
OPENERP_WORKTREE_TEST_WORKSPACE="$tmp" \
OPENERP_WORKTREE_TEST_RUNNER="$runner" \
TEST_READY="$ready" TEST_RELEASE="$release" \
    "$test_wrapper" --addon testaddon -- fake-test > "$tmp/test-out" 2> "$tmp/test-err" &
tester_pid=$!
for _ in {1..500}; do [[ -e "$ready" ]] && break; sleep 0.01; done
[[ -e "$ready" ]] || fail 'worktree test runner did not start'
before_test_head="$(git -C "$tmp/branchrepo" rev-parse HEAD)"
OPENERP_WORKTREE_TEST_LOCK_TIMEOUT=0 sync --dry-run \
    > "$tmp/test-dry-run-out" 2> "$tmp/test-dry-run-err" || \
    fail 'dry run waited for a running worktree test'
grep -q 'Would synchronize branchrepo' "$tmp/test-dry-run-out" || \
    fail 'dry run did not display a plan during a worktree test'
assert_equal "$(git -C "$tmp/branchrepo" rev-parse HEAD)" "$before_test_head"
if OPENERP_WORKTREE_TEST_LOCK_TIMEOUT=0 sync > "$tmp/test-lock-out" 2> "$tmp/test-lock-err"; then
    fail 'synchronization changed dependencies during a running worktree test'
fi
assert_equal "$(git -C "$tmp/branchrepo" rev-parse HEAD)" "$before_test_head"
assert_equal "$(git -C "$tmp/branchrepo" branch --show-current)" developer
grep -q 'Timed out waiting for addon test lock' "$tmp/test-lock-err" \
    || fail 'addon test lock timeout was not reported'
: > "$release"
wait "$tester_pid"
sync > "$tmp/after-test-out" 2> "$tmp/after-test-err"
assert_equal "$(git -C "$tmp/branchrepo" branch --show-current)" rolling_erp01

# A dry run is still informative with an abandoned test manifest; only a
# real synchronization must refuse it until the wrapper recovers it safely.
mkdir "$tmp/.openerp-worktree-tests/manifest"
sync --dry-run > "$tmp/manifest-plan" 2> "$tmp/manifest-plan-err" || \
    fail 'dry run refused to display a plan with an abandoned manifest'
if sync > "$tmp/manifest-out" 2> "$tmp/manifest-err"; then
    fail 'synchronization accepted an abandoned addon manifest'
fi
grep -q 'Abandoned addon test manifest' "$tmp/manifest-err" \
    || fail 'abandoned addon test manifest was not reported'
rmdir "$tmp/.openerp-worktree-tests/manifest"

# An ignored file is still protected if the target branch tracks that path.
make_seed ignoredrepo
printf '%s\n' local.txt > "$tmp/ignoredrepo-seed/.gitignore"
git -C "$tmp/ignoredrepo-seed" add .gitignore
git -C "$tmp/ignoredrepo-seed" commit -qm ignore-local-file
git -C "$tmp/ignoredrepo-seed" switch -qc target
git -C "$tmp/ignoredrepo-seed" mv data local.txt
git -C "$tmp/ignoredrepo-seed" commit -qm track-local-file
git -C "$tmp/ignoredrepo-seed" switch -q master
make_clone ignoredrepo
printf '%s\n' ignored-local-content > "$tmp/ignoredrepo/local.txt"
printf '%s\n' $'ignoredrepo\torigin\tbranch\ttarget\tall' \
    >> "$tmp/openerp_som_addons/.agents/workspace-repositories.tsv"
if sync > "$tmp/ignored-out" 2> "$tmp/ignored-err"; then
    fail 'ignored path tracked by the target branch was accepted'
fi
assert_equal "$(<"$tmp/ignoredrepo/local.txt")" ignored-local-content
grep -q 'ignored local path tracked by target' "$tmp/ignored-err" \
    || fail 'ignored-path collision was not reported'

# Failed synchronization must not persist a requested branch override.
printf '%s\n' dirty > "$tmp/branchrepo/untracked"
if sync --branch branchrepo=developer --persist > "$tmp/dirty-out" 2> "$tmp/dirty-err"; then
    fail 'dirty dependency was accepted'
fi
if grep -Fqx 'branchrepo developer' \
    "$tmp/openerp_som_addons/.agents/workspace-repositories.local"; then
    fail 'failed synchronization persisted an override'
fi

printf '%s\n' 'PASS: workspace dependency synchronization'
