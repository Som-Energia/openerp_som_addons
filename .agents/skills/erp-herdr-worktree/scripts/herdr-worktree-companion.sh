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
$herdr pane rename "$HERDR_PANE_ID" agent

report_companion() {
    $herdr pane report-metadata "$HERDR_PANE_ID" --source worktree-companion \
        --token "worktree=$(basename "$worktree")" --token "companion=$1"
}

shell_quote() {
    python3 -c 'import shlex, sys; print(shlex.quote(sys.argv[1]))' "$1"
}

safe_shell_pane() {
    $herdr pane process-info --pane "$1" | python3 -c '
import json
import sys

info = json.load(sys.stdin)["result"]["process_info"]
processes = info["foreground_processes"]
shell_pid = info["shell_pid"]
if len(processes) != 1:
    sys.exit(1)
process = processes[0]
if process["pid"] != shell_pid or process["name"] not in {"sh", "bash", "zsh", "fish"}:
    sys.exit(1)
'
}

foreground_cwd_is() {
    $herdr pane process-info --pane "$1" | python3 -c '
import json
import os
import sys

expected = sys.argv[1]
info = json.load(sys.stdin)["result"]["process_info"]
processes = info["foreground_processes"]
if len(processes) != 1 or os.path.realpath(processes[0].get("cwd", "")) != expected:
    sys.exit(1)
' "$worktree"
}

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
    report_companion "$existing"
    printf 'Reusing worktree companion: %s\n' "$existing"
    exit 0
fi

mapfile -t reusable < <($herdr pane list | python3 -c '
import json
import sys

tab_id = sys.argv[1]
for pane in json.load(sys.stdin)["result"]["panes"]:
    if pane["tab_id"] == tab_id and pane.get("label", "").startswith("worktree · "):
        print(pane["pane_id"])
' "$tab_id")

if [ "${#reusable[@]}" -gt 1 ]; then
    printf 'Cannot select a worktree companion: %s labeled companions exist in this tab.\n' "${#reusable[@]}" >&2
    exit 1
fi

if [ "${#reusable[@]}" -eq 1 ]; then
    companion="${reusable[0]}"
    if ! safe_shell_pane "$companion"; then
        printf 'Cannot retarget worktree companion %s: its foreground process is busy or ambiguous.\n' "$companion" >&2
        exit 1
    fi

    $herdr pane run "$companion" "cd -- $(shell_quote "$worktree")"
    for ((attempt = 0; attempt < 20; attempt++)); do
        if foreground_cwd_is "$companion"; then
            $herdr pane rename "$companion" "worktree · $(basename "$worktree")"
            report_companion "$companion"
            printf 'Retargeted worktree companion: %s (%s)\n' "$companion" "$worktree"
            exit 0
        fi
        sleep 0.1
    done

    printf 'Could not confirm worktree companion %s changed to %s; no pane was created.\n' "$companion" "$worktree" >&2
    exit 1
fi

created="$($herdr pane split "$HERDR_PANE_ID" --direction right --cwd "$worktree" --no-focus)"
companion="$(printf '%s' "$created" | python3 -c 'import json, sys; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')"
$herdr pane rename "$companion" "worktree · $(basename "$worktree")"
report_companion "$companion"
printf 'Created worktree companion: %s (%s)\n' "$companion" "$worktree"
