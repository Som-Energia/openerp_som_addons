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

# Explicit flags override COMPOSE_FILE/COMPOSE_PROJECT_NAME inherited by a pane.
# Keep the existing project name to reuse its containers and PostgreSQL volume.
compose=(docker compose --project-name "$(basename -- "$primary_checkout")"
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
        if "${compose[@]}" exec -T "$service" "${probe[@]}" >/dev/null 2>&1; then
            break
        fi
        if ((SECONDS >= deadline)); then
            printf 'Error: %s was not ready within %ss (project %s)\n' \
                "$service" "$timeout" "$(basename -- "$primary_checkout")" >&2
            "${compose[@]}" ps --all >&2 || true
            exit 1
        fi
        sleep 1
    done
done
printf 'PostgreSQL, MongoDB and Redis are ready (project %s).\n' "$(basename -- "$primary_checkout")"
