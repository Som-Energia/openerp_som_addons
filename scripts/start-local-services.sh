#!/usr/bin/env bash
# Use the primary checkout's Compose project, also when called from a worktree.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
common_git_dir="$(git -C "$script_dir" rev-parse --path-format=absolute --git-common-dir)"
primary_checkout="$(dirname -- "$common_git_dir")"
compose_file="$primary_checkout/docker-compose.yaml"
timeout="${OPENERP_LOCAL_SERVICES_TIMEOUT:-120}"
[[ "$timeout" =~ ^[0-9]+$ ]] || { printf 'Error: service timeout must be a non-negative integer\n' >&2; exit 2; }
[[ -f "$compose_file" ]] || { printf 'Error: missing %s\n' "$compose_file" >&2; exit 2; }
command -v docker >/dev/null || { printf 'Error: Docker is required\n' >&2; exit 2; }
command -v timeout >/dev/null || { printf 'Error: GNU timeout is required\n' >&2; exit 2; }
timeout=$((10#$timeout))
# Match Compose's default directory-name normalization before making it explicit.
project_name="$(basename -- "$primary_checkout" | LC_ALL=C tr '[:upper:]' '[:lower:]' | LC_ALL=C tr -cd 'a-z0-9_-')"
project_name="${project_name#"${project_name%%[a-z0-9]*}"}"
[[ -n "$project_name" ]] || { printf 'Error: directory produces an empty Compose project name\n' >&2; exit 2; }

# Explicit flags override COMPOSE_FILE/COMPOSE_PROJECT_NAME inherited by a pane.
# Keep the default project name to reuse its containers and PostgreSQL volume.
compose=(docker compose --project-name "$project_name"
    --project-directory "$primary_checkout" -f "$compose_file")
"${compose[@]}" up -d postgres mongo redis

deadline=$((SECONDS + timeout))
for service in postgres mongo redis; do
    while :; do
        case "$service" in
            postgres) probe=(pg_isready -h 127.0.0.1 -U "${OPENERP_DB_USER:-erp}") ;;
            mongo) probe=(mongo --quiet --host 127.0.0.1 --eval 'quit(db.adminCommand("ping").ok ? 0 : 1)') ;;
            redis) probe=(redis-cli ping) ;;
        esac
        remaining=$((deadline - SECONDS))
        # Bound the command itself, including a Docker client stuck in exec.
        # SIGKILL after one extra second also handles probes that ignore SIGTERM.
        if ((remaining > 0)) && timeout --kill-after=1s "${remaining}s" \
            "${compose[@]}" exec -T "$service" "${probe[@]}" >/dev/null 2>&1; then
            break
        fi
        if ((SECONDS >= deadline)); then
            printf 'Error: %s was not ready within %ss (project %s)\n' \
                "$service" "$timeout" "$project_name" >&2
            # Do not launch another potentially blocked Docker command here.
            exit 1
        fi
        sleep 1
    done
done
printf 'PostgreSQL, MongoDB and Redis are ready (project %s).\n' "$project_name"
