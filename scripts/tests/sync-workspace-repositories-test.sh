#!/usr/bin/env bash
set -euo pipefail

wrapper="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)/sync-workspace-repositories.sh"
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

    git init -q "$seed"
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

mkdir -p "$tmp/openerp_som_addons/scripts" "$tmp/openerp_som_addons/.agents"
cp "$wrapper" "$tmp/openerp_som_addons/scripts/"
chmod +x "$tmp/openerp_som_addons/scripts/sync-workspace-repositories.sh"
printf '%s\n' \
    $'branchrepo\torigin\tbranch\trolling_erp01' \
    $'defaultrepo\torigin\tdefault-branch\t-' \
    $'tagrepo\torigin\tlatest-tag\t-' \
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

"$tmp/openerp_som_addons/scripts/sync-workspace-repositories.sh" --workspace "$tmp"
assert_equal "$(git -C "$tmp/branchrepo" branch --show-current)" rolling_erp01
assert_equal "$(git -C "$tmp/defaultrepo" branch --show-current)" master
assert_equal "$(git -C "$tmp/tagrepo" describe --exact-match --tags HEAD)" v2

"$tmp/openerp_som_addons/scripts/sync-workspace-repositories.sh" \
    --workspace "$tmp" --branch branchrepo=developer --persist
assert_equal "$(git -C "$tmp/branchrepo" branch --show-current)" developer
grep -Fx 'branchrepo developer' \
    "$tmp/openerp_som_addons/.agents/workspace-repositories.local" >/dev/null \
    || fail 'persistent override was not written'
"$tmp/openerp_som_addons/scripts/sync-workspace-repositories.sh" \
    --workspace "$tmp" --clear-branch branchrepo --persist-only
if grep -Fqx 'branchrepo developer' \
    "$tmp/openerp_som_addons/.agents/workspace-repositories.local"; then
    fail 'persistent override was not removed'
fi

printf '%s\n' dirty > "$tmp/branchrepo/untracked"
if "$tmp/openerp_som_addons/scripts/sync-workspace-repositories.sh" \
    --workspace "$tmp" --dry-run >/dev/null 2>&1; then
    fail 'dirty dependency was accepted'
fi

printf '%s\n' 'PASS: workspace dependency synchronization'
