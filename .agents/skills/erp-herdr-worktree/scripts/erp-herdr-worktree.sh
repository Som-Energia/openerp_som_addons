#!/usr/bin/env bash
# Create or open an ERP worktree and attach a Herdr companion pane.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
companion="$script_dir/herdr-worktree-companion.sh"

usage() {
    cat >&2 <<EOF
Usage:
  ${0##*/} open <existing-worktree-path>
  ${0##*/} create <worktree-path> <branch-name>
EOF
    exit 2
}

worktree_root() {
    git -C "$script_dir" worktree list --porcelain | awk '
        /^worktree / { print substr($0, 10); exit }
    '
}

[ "$#" -ge 1 ] || usage

case "$1" in
    open)
        [ "$#" -eq 2 ] || usage
        exec "$companion" "$2"
        ;;
    create)
        [ "$#" -eq 3 ] || usage
        [ "${HERDR_ENV:-}" = "1" ] && [ -n "${HERDR_PANE_ID:-}" ] || {
            printf 'Create a Herdr companion only from a Herdr-managed pane.\n' >&2
            exit 1
        }

        requested_path="$2"
        branch="$3"
        git check-ref-format --branch "$branch" >/dev/null

        primary_worktree="$(worktree_root)"
        workspace="$(dirname "$primary_worktree")"
        expected_root="$workspace/$(basename "$primary_worktree")-worktrees"
        worktree="$(realpath -m "$requested_path")"

        case "$worktree" in
            "$expected_root"/*) ;;
            *)
                printf 'Worktree path must be below %s\n' "$expected_root" >&2
                exit 1
                ;;
        esac

        if [ -e "$worktree" ]; then
            printf 'Worktree path already exists; use open instead: %s\n' "$worktree" >&2
            exit 1
        fi

        if git -C "$primary_worktree" show-ref --verify --quiet "refs/heads/$branch"; then
            git -C "$primary_worktree" worktree add "$worktree" "$branch"
        else
            git -C "$primary_worktree" worktree add -b "$branch" "$worktree" HEAD
        fi

        exec "$companion" "$worktree"
        ;;
    *)
        usage
        ;;
esac
