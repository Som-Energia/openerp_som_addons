#!/usr/bin/env bash
set -Eeuo pipefail

usage() { printf 'Usage: %s --addon NAME [--addon NAME ...] -- [run-tests.sh arguments...]\n' "${0##*/}"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 2; }

addons=()
while (($#)); do
    case "$1" in
        --addon)
            (($# >= 2)) || die "--addon requires a name"
            addons+=("$2")
            shift 2
            ;;
        --)
            shift
            break
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "expected --addon NAME or -- before test arguments"
            ;;
    esac
done
((${#addons[@]})) || die "at least one --addon is required"
runner_args=("$@")
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
worktree="${OPENERP_WORKTREE_TEST_WORKTREE:-$(git -C "$script_dir" rev-parse --show-toplevel)}"
if [[ -n "${OPENERP_WORKTREE_TEST_WORKSPACE:-}" ]]; then
    workspace="$OPENERP_WORKTREE_TEST_WORKSPACE"
else
    common_git_dir="$(git -C "$worktree" rev-parse --path-format=absolute --git-common-dir)"
    workspace="$(dirname -- "$(dirname -- "$common_git_dir")")"
fi
addons_dir="${OPENERP_WORKTREE_TEST_ADDONS_DIR:-$workspace/erp/server/bin/addons}"
runner="${OPENERP_WORKTREE_TEST_RUNNER:-$worktree/scripts/run-tests.sh}"
state_dir="${OPENERP_WORKTREE_TEST_STATE_DIR:-$workspace/.openerp-worktree-tests}"
lock_timeout="${OPENERP_WORKTREE_TEST_LOCK_TIMEOUT:-600}"
[[ "$lock_timeout" =~ ^[0-9]+([.][0-9]+)?$ ]] || die "lock timeout must be a non-negative number"
command -v flock >/dev/null 2>&1 || die "flock is required to serialize addon tests"
[[ -d "$addons_dir" ]] || die "shared addons directory does not exist: $addons_dir"
[[ -x "$runner" ]] || die "test runner is not executable: $runner"
for path in "$worktree" "$addons_dir" "$state_dir"; do
    [[ "$path" != *$'\n'* && "$path" != *$'\t'* ]] || die "unsafe newline or tab in path: $path"
done
for ((i = 0; i < ${#addons[@]}; i++)); do
    name="${addons[$i]}"
    [[ "$name" =~ ^[A-Za-z0-9][A-Za-z0-9_]*$ ]] || die "unsafe addon name: $name"
    [[ -d "$worktree/$name" && -f "$worktree/$name/__terp__.py" ]] ||
        die "addon is missing or has no __terp__.py: $worktree/$name"
    for ((j = 0; j < i; j++)); do
        [[ "$name" != "${addons[$j]}" ]] || die "duplicate addon: $name"
    done
done
umask 077
mkdir -p -- "$state_dir"
chmod 700 "$state_dir"
lock_file="$state_dir/lock"
metadata="$state_dir/owner"
manifest="$state_dir/manifest"
exec 9>"$lock_file"
if ! flock -w "$lock_timeout" 9; then
    printf 'Error: addon test lock remained busy for %ss: %s\n' "$lock_timeout" "$lock_file" >&2
    if [[ -s "$metadata" ]]; then
        printf 'Current owner:\n' >&2
        while IFS= read -r line; do printf '  %s\n' "$line" >&2; done < "$metadata"
    else
        printf 'No owner metadata is available; wait for the running test or inspect the lock holder.\n' >&2
    fi
    exit 75
fi
matches_original() {
    local link="$1" entry="$2" state
    state="$(<"$entry/state")"
    if [[ "$state" == ABSENT ]]; then
        [[ ! -e "$link" && ! -L "$link" ]]
    else
        [[ -L "$link" && "$(readlink -- "$link")" == "$(<"$entry/original")" ]]
    fi
}
restore_manifest() {
    local entry name link installed state original current replacement errors=0
    [[ -d "$manifest" ]] || return 0
    shopt -s nullglob
    for entry in "$manifest"/*; do
        name="${entry##*/}"
        link="$addons_dir/$name"
        if [[ ! -f "$entry/installed" || ! -f "$entry/state" ]]; then
            printf 'Error: incomplete abandoned manifest entry: %s\n' "$entry" >&2
            return 1
        fi
        if ! installed="$(<"$entry/installed")" || ! state="$(<"$entry/state")"; then
            printf 'Error: cannot read abandoned manifest entry: %s\n' "$entry" >&2
            errors=1
            continue
        fi
        [[ "$state" == ABSENT || "$state" == SYMLINK ]] || {
            printf 'Error: invalid abandoned manifest entry: %s\n' "$entry" >&2
            errors=1
            continue
        }
        if [[ "$state" == SYMLINK && ! -f "$entry/original" ]]; then
            printf 'Error: incomplete abandoned manifest entry: %s\n' "$entry" >&2
            errors=1
            continue
        fi
        original=""
        if [[ "$state" == SYMLINK ]] && ! original="$(<"$entry/original")"; then
            printf 'Error: cannot read original target from %s\n' "$entry" >&2
            errors=1
            continue
        fi
        current=""
        if [[ -L "$link" ]] && ! current="$(readlink -- "$link")"; then
            printf 'Error: cannot inspect addon symlink: %s\n' "$link" >&2
            errors=1
            continue
        fi
        if [[ -L "$link" && "$current" == "$installed" ]]; then
            if [[ "$state" == ABSENT ]]; then
                if ! rm -- "$link"; then
                    printf 'Error: failed to remove installed addon symlink: %s\n' "$link" >&2
                    errors=1
                fi
            else
                replacement="$entry/replacement"
                if ! rm -f -- "$replacement" || ! ln -s -- "$original" "$replacement" ||
                    ! mv -Tf -- "$replacement" "$link"; then
                    printf 'Error: failed to restore original addon symlink: %s\n' "$link" >&2
                    errors=1
                fi
            fi
        elif ! { [[ "$state" == ABSENT && ! -e "$link" && ! -L "$link" ]] ||
            [[ "$state" == SYMLINK && -L "$link" && "$current" == "$original" ]]; }; then
            printf 'Error: external alteration at %s; leaving it and manifest %s untouched.\n' "$link" "$manifest" >&2
            errors=1
        fi
    done
    if ((errors)); then
        printf 'Error: addon restoration failed; manifest retained at %s\n' "$manifest" >&2
        return 1
    fi
    if ! rm -rf -- "$manifest"; then
        printf 'Error: restored addons but failed to remove manifest: %s\n' "$manifest" >&2
        return 1
    fi
}
# A prior SIGKILL may leave a manifest. Recover only states this manifest proves safe.
if ! restore_manifest; then
    die "cannot safely recover the abandoned addon manifest"
fi
rm -f -- "$metadata"
for name in "${addons[@]}"; do
    link="$addons_dir/$name"
    [[ ! -e "$link" || -L "$link" ]] || die "refusing to replace non-symlink entry: $link"
done
addons_csv="$(IFS=,; printf '%s' "${addons[*]}")"
printf 'pid=%s\nworktree=%s\naddons=%s\nstarted=%s\n' \
    "$$" "$worktree" "$addons_csv" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$metadata"
active=0
cleanup() {
    local status=$?
    trap - EXIT INT TERM HUP
    if ((active)) && ! restore_manifest; then
        printf 'Error: test cleanup could not restore all addons (original exit %s).\n' "$status" >&2
        exit 1
    fi
    if ! rm -f -- "$metadata"; then
        printf 'Error: failed to remove lock owner metadata: %s\n' "$metadata" >&2
        exit 1
    fi
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP
mkdir -- "$manifest"
active=1
for name in "${addons[@]}"; do
    link="$addons_dir/$name"
    entry="$manifest/$name"
    mkdir -- "$entry"
    printf '%s' "$worktree/$name" > "$entry/installed"
    if [[ -L "$link" ]]; then
        target="$(readlink -- "$link")"
        [[ "$target" != *$'\n'* && "$target" != *$'\t'* ]] || die "unsafe newline or tab in symlink target: $link"
        printf 'SYMLINK' > "$entry/state"
        printf '%s' "$target" > "$entry/original"
    else
        printf 'ABSENT' > "$entry/state"
    fi
done
for name in "${addons[@]}"; do
    link="$addons_dir/$name"
    entry="$manifest/$name"
    matches_original "$link" "$entry" || die "external alteration before installing addon: $link"
    rm -f -- "$link"
    ln -s -- "$worktree/$name" "$link"
done
set +e
WORKSPACE="$workspace" "$runner" "${runner_args[@]}"
status=$?
set -e
exit "$status"
