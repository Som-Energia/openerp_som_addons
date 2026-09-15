#!/usr/bin/env bash
# Create or reuse a sibling Herdr pane rooted at an explicitly chosen Git worktree.
set -euo pipefail

usage() {
    printf 'Usage: %s <existing-worktree-path>\n' "${0##*/}" >&2
    exit 2
}

[ "${1:-}" = "--help" ] && usage
[ "$#" -eq 1 ] || usage

if [ "${HERDR_ENV:-}" != "1" ] || [ -z "${HERDR_PANE_ID:-}" ]; then
    printf 'Run this from a Herdr-managed pane.\n' >&2
    exit 1
fi

herdr="${HERDR_BIN_PATH:-herdr}"
worktree="$(git -C "$1" rev-parse --show-toplevel)"
worktree="$(realpath "$worktree")"

# Refuse arbitrary Git subdirectories: the target must be one of Git's registered worktrees.
registered_worktrees="$(git -C "$worktree" worktree list --porcelain | awk '/^worktree / {print substr($0, 10)}' | \
    while IFS= read -r candidate; do realpath "$candidate"; done)"
if ! printf '%s\n' "$registered_worktrees" | grep -Fx "$worktree" >/dev/null; then
    printf 'Not a registered Git worktree: %s\n' "$worktree" >&2
    exit 1
fi

pane_json="$($herdr pane current --pane "$HERDR_PANE_ID")"
tab_id="$(printf '%s' "$pane_json" | python3 -c 'import json, sys; print(json.load(sys.stdin)["result"]["pane"]["tab_id"])')"

# Reuse an existing companion in this tab rather than growing duplicate splits.
existing="$($herdr pane list | python3 -c '
import json, os, sys
worktree = sys.argv[1]
tab_id = sys.argv[2]
for pane in json.load(sys.stdin)["result"]["panes"]:
    if pane["tab_id"] == tab_id and os.path.realpath(pane["cwd"]) == worktree:
        print(pane["pane_id"])
        break
' "$worktree" "$tab_id")"

if [ -n "$existing" ]; then
    printf 'Reusing worktree companion: %s\n' "$existing"
    exit 0
fi

created="$($herdr pane split "$HERDR_PANE_ID" --direction right --cwd "$worktree" --no-focus)"
companion="$(printf '%s' "$created" | python3 -c 'import json, sys; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')"
$herdr pane rename "$companion" "worktree · $(basename "$worktree")"
$herdr pane report-metadata "$HERDR_PANE_ID" --source worktree-companion --token "worktree=$(basename "$worktree")"
printf 'Created worktree companion: %s (%s)\n' "$companion" "$worktree"
