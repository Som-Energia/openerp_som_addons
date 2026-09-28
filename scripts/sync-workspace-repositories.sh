#!/usr/bin/env bash
# Synchronize the local ERP workspace with the dependency refs used by CI.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/.." && pwd)"
manifest="$repo_root/.agents/workspace-repositories.tsv"
local_overrides="$repo_root/.agents/workspace-repositories.local"

workspace="${WORKSPACE:-}"
dry_run=0
allow_missing=0
persist=0
persist_only=0
declare -a supplied_overrides=()
declare -a clear_overrides=()

usage() {
    cat >&2 <<EOF
Usage: ${0##*/} [options]

Synchronize the CI dependency repositories in the surrounding workspace.

Options:
  --workspace <path>          Workspace containing erp, oorq, etc.
  --branch <repository>=<ref> Override one repository with a remote branch.
                               May be given more than once.
  --clear-branch <repository> Remove a saved branch override. May be repeated.
  --persist                   Save the resulting overrides in this checkout's
                               .agents/workspace-repositories.local file.
  --persist-only              Save overrides without synchronizing repositories.
  --allow-missing             Warn and skip unavailable dependencies instead of
                               failing. This does not produce a complete CI profile.
  --dry-run                   Show the intended synchronization without fetching
                               or switching any repository.
  -h, --help                  Show this help.
EOF
    exit 2
}

error() {
    printf 'ERROR: %s\n' "$*" >&2
}

warn() {
    printf 'WARNING: %s\n' "$*" >&2
}

validate_branch() {
    local repository="$1"
    local branch="$2"

    if [[ -z "$branch" ]] || ! git check-ref-format --branch "$branch" >/dev/null 2>&1; then
        error "Invalid branch override for $repository: $branch"
        return 1
    fi
}

parse_override() {
    local value="$1"
    local repository branch

    if [[ "$value" != *=* ]]; then
        error "Expected <repository>=<branch>, got: $value"
        return 1
    fi

    repository="${value%%=*}"
    branch="${value#*=}"
    if [[ -z "$repository" ]] || [[ -z "$branch" ]]; then
        error "Expected <repository>=<branch>, got: $value"
        return 1
    fi

    printf '%s\t%s\n' "$repository" "$branch"
}

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --workspace)
            [[ "$#" -ge 2 ]] || usage
            workspace="$2"
            shift 2
            ;;
        --branch)
            [[ "$#" -ge 2 ]] || usage
            supplied_overrides+=("$(parse_override "$2")")
            shift 2
            ;;
        --clear-branch)
            [[ "$#" -ge 2 ]] || usage
            clear_overrides+=("$2")
            shift 2
            ;;
        --persist)
            persist=1
            shift
            ;;
        --persist-only)
            persist=1
            persist_only=1
            shift
            ;;
        --allow-missing)
            allow_missing=1
            shift
            ;;
        --dry-run)
            dry_run=1
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            error "Unknown option: $1"
            usage
            ;;
    esac
done

if [[ ! -f "$manifest" ]]; then
    error "CI dependency manifest not found: $manifest"
    exit 1
fi

if [[ -z "$workspace" ]]; then
    parent="$(dirname "$repo_root")"
    if [[ "$(basename "$parent")" == "openerp_som_addons-worktrees" ]]; then
        workspace="$(dirname "$parent")"
    else
        workspace="$parent"
    fi
fi

if [[ ! -d "$workspace" ]]; then
    error "Workspace does not exist: $workspace"
    exit 1
fi
workspace="$(cd -- "$workspace" && pwd)"

declare -a repositories=()
declare -A known_repositories=()
declare -A remote_candidates=()
declare -A strategies=()
declare -A configured_refs=()

while IFS=$'\t' read -r repository remotes strategy ref extra; do
    [[ -z "$repository" ]] && continue
    [[ "$repository" == \#* ]] && continue

    if [[ -n "${extra:-}" ]] || [[ -z "${remotes:-}" ]] || [[ -z "${strategy:-}" ]] || [[ -z "${ref:-}" ]]; then
        error "Invalid manifest entry for $repository in $manifest"
        exit 1
    fi
    if [[ -n "${known_repositories[$repository]:-}" ]]; then
        error "Duplicate manifest entry: $repository"
        exit 1
    fi
    case "$strategy" in
        branch)
            if [[ "$ref" == "-" ]]; then
                error "A branch strategy needs a ref for $repository"
                exit 1
            fi
            ;;
        default-branch|latest-tag)
            if [[ "$ref" != "-" ]]; then
                error "$strategy must use '-' as ref for $repository"
                exit 1
            fi
            ;;
        *)
            error "Unknown strategy for $repository: $strategy"
            exit 1
            ;;
    esac

    repositories+=("$repository")
    known_repositories[$repository]=1
    remote_candidates[$repository]="$remotes"
    strategies[$repository]="$strategy"
    configured_refs[$repository]="$ref"
done < "$manifest"

if [[ "${#repositories[@]}" -eq 0 ]]; then
    error "The manifest is empty: $manifest"
    exit 1
fi

declare -A overrides=()
read_local_overrides() {
    local repository branch extra

    [[ -f "$local_overrides" ]] || return 0
    while read -r repository branch extra; do
        [[ -z "$repository" ]] && continue
        [[ "$repository" == \#* ]] && continue
        if [[ -n "${extra:-}" ]] || [[ -z "${branch:-}" ]]; then
            error "Invalid local override entry in $local_overrides: $repository"
            return 1
        fi
        if [[ -z "${known_repositories[$repository]:-}" ]]; then
            error "Unknown repository in $local_overrides: $repository"
            return 1
        fi
        validate_branch "$repository" "$branch" || return 1
        overrides[$repository]="$branch"
    done < "$local_overrides"
}

read_local_overrides

for override in "${supplied_overrides[@]}"; do
    repository="${override%%$'\t'*}"
    branch="${override#*$'\t'}"
    if [[ -z "${known_repositories[$repository]:-}" ]]; then
        error "Unknown repository override: $repository"
        exit 1
    fi
    validate_branch "$repository" "$branch"
    overrides[$repository]="$branch"
done

for repository in "${clear_overrides[@]}"; do
    if [[ -z "${known_repositories[$repository]:-}" ]]; then
        error "Unknown repository override: $repository"
        exit 1
    fi
    unset 'overrides[$repository]'
done

write_local_overrides() {
    local temporary_file
    temporary_file="$(mktemp "$local_overrides.XXXXXX")"
    {
        printf '%s\n' '# Local branch overrides for scripts/sync-workspace-repositories.sh.'
        printf '%s\n' '# This file is intentionally ignored by Git.'
        for repository in "${repositories[@]}"; do
            if [[ -n "${overrides[$repository]:-}" ]]; then
                printf '%s %s\n' "$repository" "${overrides[$repository]}"
            fi
        done
    } > "$temporary_file"
    mv "$temporary_file" "$local_overrides"
    printf 'Saved local branch overrides to %s\n' "$local_overrides"
}

if [[ "$persist" -eq 1 ]]; then
    write_local_overrides
fi

if [[ "$persist_only" -eq 1 ]]; then
    exit 0
fi

declare -a available_repositories=()
declare -A selected_remotes=()
problems=0

for repository in "${repositories[@]}"; do
    path="$workspace/$repository"
    if ! git -C "$path" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        if [[ "$allow_missing" -eq 1 ]]; then
            warn "$repository is unavailable at $path; skipped by --allow-missing"
            continue
        fi
        error "$repository is required by the CI profile but is unavailable at $path"
        problems=1
        continue
    fi

    if [[ -n "$(git -C "$path" status --porcelain --untracked-files=normal)" ]]; then
        error "$repository has local changes: $path"
        problems=1
        continue
    fi

    selected_remote=""
    IFS=',' read -r -a candidates <<< "${remote_candidates[$repository]}"
    for candidate in "${candidates[@]}"; do
        if git -C "$path" remote get-url "$candidate" >/dev/null 2>&1; then
            selected_remote="$candidate"
            break
        fi
    done
    if [[ -z "$selected_remote" ]]; then
        error "$repository has none of the configured remotes: ${remote_candidates[$repository]}"
        problems=1
        continue
    fi

    available_repositories+=("$repository")
    selected_remotes[$repository]="$selected_remote"
done

if [[ "$problems" -ne 0 ]]; then
    error 'No repository was fetched or switched. Commit, remove, or explicitly allow the reported blockers.'
    exit 1
fi

if [[ "$dry_run" -eq 1 ]]; then
    for repository in "${available_repositories[@]}"; do
        if [[ -n "${overrides[$repository]:-}" ]]; then
            target="branch ${overrides[$repository]} (override)"
        elif [[ "${strategies[$repository]}" == "branch" ]]; then
            target="branch ${configured_refs[$repository]}"
        else
            target="${strategies[$repository]}"
        fi
        printf 'Would synchronize %-36s via %-8s to %s\n' \
            "$repository" "${selected_remotes[$repository]}" "$target"
    done
    exit 0
fi

# Fetching updates refs only. No checkout occurs until every target is resolved
# and confirmed fast-forwardable below.
for repository in "${available_repositories[@]}"; do
    path="$workspace/$repository"
    remote="${selected_remotes[$repository]}"
    case "${strategies[$repository]}" in
        latest-tag)
            git -C "$path" fetch "$remote" --tags
            ;;
        *)
            # A specific target ref is fetched after default-branch resolution.
            git -C "$path" fetch "$remote" --tags
            ;;
    esac
done

declare -A target_kinds=()
declare -A target_refs=()

for repository in "${available_repositories[@]}"; do
    path="$workspace/$repository"
    remote="${selected_remotes[$repository]}"

    if [[ -n "${overrides[$repository]:-}" ]]; then
        target_kinds[$repository]=branch
        target_refs[$repository]="${overrides[$repository]}"
    else
        target_kinds[$repository]="${strategies[$repository]}"
        target_refs[$repository]="${configured_refs[$repository]}"
    fi

    case "${target_kinds[$repository]}" in
        branch)
            branch="${target_refs[$repository]}"
            git -C "$path" fetch "$remote" --no-tags \
                "+refs/heads/$branch:refs/remotes/$remote/$branch"
            if ! git -C "$path" show-ref --verify --quiet "refs/remotes/$remote/$branch"; then
                error "$repository does not have $remote/$branch"
                problems=1
            fi
            ;;
        default-branch)
            remote_head="$(git -C "$path" symbolic-ref --quiet --short "refs/remotes/$remote/HEAD" || true)"
            if [[ "$remote_head" != "$remote/"* ]]; then
                error "$repository has no advertised default branch for remote $remote"
                problems=1
                continue
            fi
            branch="${remote_head#"$remote/"}"
            target_kinds[$repository]=branch
            target_refs[$repository]="$branch"
            git -C "$path" fetch "$remote" --no-tags \
                "+refs/heads/$branch:refs/remotes/$remote/$branch"
            ;;
        latest-tag)
            tag_commit="$(git -C "$path" rev-list --tags --max-count=1 || true)"
            if [[ -z "$tag_commit" ]]; then
                error "$repository has no tag from which to select the CI latest-tag target"
                problems=1
                continue
            fi
            tag="$(git -C "$path" describe --tags "$tag_commit")"
            target_refs[$repository]="$tag"
            ;;
    esac
done

# Refuse to overwrite a local target branch that cannot reach the fetched ref.
for repository in "${available_repositories[@]}"; do
    [[ "${target_kinds[$repository]}" == branch ]] || continue
    path="$workspace/$repository"
    remote="${selected_remotes[$repository]}"
    branch="${target_refs[$repository]}"

    if git -C "$path" show-ref --verify --quiet "refs/heads/$branch" && \
        ! git -C "$path" merge-base --is-ancestor "$branch" "$remote/$branch"; then
        error "$repository/$branch has local commits or diverged from $remote/$branch"
        problems=1
    fi

    occupied_worktree="$(git -C "$path" worktree list --porcelain | awk -v requested="refs/heads/$branch" '
        /^worktree / { worktree = substr($0, 10); next }
        /^branch / && substr($0, 8) == requested { print worktree }
    ')"
    if [[ -n "$occupied_worktree" ]] && [[ "$occupied_worktree" != "$path" ]]; then
        error "$repository/$branch is already checked out in $occupied_worktree"
        problems=1
    fi
done

if [[ "$problems" -ne 0 ]]; then
    error 'Dependencies were fetched but none were switched; resolve the reported ref blockers.'
    exit 1
fi

for repository in "${available_repositories[@]}"; do
    path="$workspace/$repository"
    remote="${selected_remotes[$repository]}"
    target="${target_refs[$repository]}"

    if [[ "${target_kinds[$repository]}" == branch ]]; then
        if git -C "$path" show-ref --verify --quiet "refs/heads/$target"; then
            git -C "$path" switch "$target"
            git -C "$path" branch --set-upstream-to="$remote/$target" "$target"
            git -C "$path" merge --ff-only "$remote/$target"
        else
            git -C "$path" switch --track -c "$target" "$remote/$target"
        fi
    else
        git -C "$path" switch --detach "$target"
    fi

    printf 'Synchronized %-36s -> %s\n' "$repository" "$target"
done
