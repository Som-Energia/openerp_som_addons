#!/usr/bin/env bash
# Synchronize the local ERP workspace with the dependency refs used by CI.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/.." && pwd)"
manifest="$repo_root/.agents/workspace-repositories.tsv"
local_overrides="$repo_root/.agents/workspace-repositories.local"

workspace="${WORKSPACE:-}"
python_version="${PYTHON_VERSION:-}"
dry_run=0
allow_missing=0
persist=0
persist_only=0
declare -a supplied_overrides=()
declare -a clear_overrides=()
declare -a accepted_rewrites=()

usage() {
    cat >&2 <<EOF
Usage: ${0##*/} [options]

Synchronize the CI dependency repositories in the surrounding workspace.

Options:
  --workspace <path>          Workspace containing erp, oorq, etc.
  --python-version <version>  Python profile to synchronize (defaults to the
                               active python interpreter or PYTHON_VERSION).
  --branch <repository>=<ref> Override one repository with a remote branch.
                               May be given more than once.
  --clear-branch <repository> Remove a saved branch override. May be repeated.
  --persist                   Save overrides only after a successful sync.
  --persist-only              Save overrides without synchronizing repositories.
  --accept-rewritten-branch <repository>
                               Back up and reset a non-fast-forward target branch.
                               May be given more than once.
  --allow-missing             Warn and skip unavailable dependencies instead of
                               failing. This does not produce a complete CI profile.
  --dry-run                   Show the intended synchronization without fetching,
                               switching repositories, or writing overrides.
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
        --python-version)
            [[ "$#" -ge 2 ]] || usage
            python_version="$2"
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
        --accept-rewritten-branch)
            [[ "$#" -ge 2 ]] || usage
            accepted_rewrites+=("$2")
            shift 2
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

if [[ "$dry_run" -eq 1 ]] && [[ "$persist_only" -eq 1 ]]; then
    error '--dry-run cannot be combined with --persist-only.'
    exit 2
fi

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

if [[ -z "$python_version" ]] && command -v python >/dev/null 2>&1; then
    python_version="$(python -c 'import sys; print("%s.%s" % sys.version_info[:2])' 2>/dev/null || true)"
fi
if [[ -z "$python_version" ]]; then
    error 'Cannot determine the Python profile; pass --python-version <version>.'
    exit 1
fi

declare -a repositories=()
declare -A known_repositories=()
declare -A remote_candidates=()
declare -A strategies=()
declare -A configured_refs=()
declare -A profiles=()

while IFS=$'\t' read -r repository remotes strategy ref profile extra; do
    [[ -z "$repository" ]] && continue
    [[ "$repository" == \#* ]] && continue

    if [[ -n "${extra:-}" ]] || [[ -z "${remotes:-}" ]] || [[ -z "${strategy:-}" ]] || \
        [[ -z "${ref:-}" ]] || [[ -z "${profile:-}" ]]; then
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
    case "$profile" in
        all|py2) ;;
        *)
            error "Unknown profile for $repository: $profile"
            exit 1
            ;;
    esac

    repositories+=("$repository")
    known_repositories[$repository]=1
    remote_candidates[$repository]="$remotes"
    strategies[$repository]="$strategy"
    configured_refs[$repository]="$ref"
    profiles[$repository]="$profile"
done < "$manifest"

if [[ "${#repositories[@]}" -eq 0 ]]; then
    error "The manifest is empty: $manifest"
    exit 1
fi

declare -A overrides=()
declare -A accepted_rewrite_repositories=()

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
    unset "overrides[$repository]"
done

for repository in "${accepted_rewrites[@]}"; do
    if [[ -z "${known_repositories[$repository]:-}" ]]; then
        error "Unknown repository passed to --accept-rewritten-branch: $repository"
        exit 1
    fi
    accepted_rewrite_repositories[$repository]=1
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

if [[ "$persist_only" -eq 1 ]]; then
    write_local_overrides
    exit 0
fi

if ! command -v flock >/dev/null 2>&1; then
    error 'flock is required to synchronize shared workspace repositories safely.'
    exit 1
fi
sync_lock_timeout="${OPENERP_WORKSPACE_SYNC_LOCK_TIMEOUT:-600}"
if ! [[ "$sync_lock_timeout" =~ ^[0-9]+$ ]]; then
    error "OPENERP_WORKSPACE_SYNC_LOCK_TIMEOUT must be a non-negative integer: $sync_lock_timeout"
    exit 1
fi
sync_lock_file="${OPENERP_WORKSPACE_SYNC_LOCK_FILE:-$workspace/.openerp-workspace-sync.lock}"
exec {sync_lock_fd}>"$sync_lock_file"
if ! flock -w "$sync_lock_timeout" "$sync_lock_fd"; then
    error "Timed out waiting for workspace synchronization lock: $sync_lock_file"
    exit 75
fi

declare -a temporary_tag_prefixes=()
cleanup_temporary_tag_refs() {
    local entry path prefix ref

    for entry in "${temporary_tag_prefixes[@]}"; do
        path="${entry%%$'\t'*}"
        prefix="${entry#*$'\t'}"
        while IFS= read -r ref; do
            [[ -z "$ref" ]] || git -C "$path" update-ref -d "$ref" || true
        done < <(git -C "$path" for-each-ref --format='%(refname)' "$prefix")
    done
}
trap cleanup_temporary_tag_refs EXIT

declare -a available_repositories=()
declare -A selected_remotes=()
problems=0

for repository in "${repositories[@]}"; do
    if [[ "${profiles[$repository]}" == py2 ]] && [[ "$python_version" != 2.* ]]; then
        printf 'Skipping %-36s (requires Python 2; active profile is %s)\n' \
            "$repository" "$python_version"
        continue
    fi

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
        elif [[ "${strategies[$repository]}" == branch ]]; then
            target="branch ${configured_refs[$repository]}"
        else
            target="${strategies[$repository]}"
        fi
        printf 'Would synchronize %-36s via %-8s to %s\n' \
            "$repository" "${selected_remotes[$repository]}" "$target"
    done
    exit 0
fi

fetch_branch_target() {
    local repository="$1"
    local path="$2"
    local remote="$3"
    local branch="$4"

    if ! git -C "$path" fetch "$remote" --no-tags \
        "+refs/heads/$branch:refs/remotes/$remote/$branch"; then
        error "$repository does not have a fetchable $remote/$branch"
        problems=1
        return 1
    fi
    if ! git -C "$path" show-ref --verify --quiet "refs/remotes/$remote/$branch"; then
        error "$repository does not have $remote/$branch"
        problems=1
        return 1
    fi
}

declare -A target_kinds=()
declare -A target_refs=()
declare -A target_object_refs=()
declare -A target_displays=()
declare -A target_ready=()

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
            fetch_branch_target "$repository" "$path" "$remote" "$branch" || continue
            target_object_refs[$repository]="$remote/$branch"
            target_displays[$repository]="$branch"
            target_ready[$repository]=1
            ;;
        default-branch)
            if ! remote_head="$(git -C "$path" ls-remote --symref "$remote" HEAD | awk '
                $1 == "ref:" && $2 ~ /^refs\/heads\// {
                    sub(/^refs\/heads\//, "", $2); print $2; exit
                }
            ')"; then
                error "Cannot query the default branch of $repository remote $remote"
                problems=1
                continue
            fi
            if [[ -z "$remote_head" ]]; then
                error "$repository remote $remote has no advertised default branch"
                problems=1
                continue
            fi
            target_kinds[$repository]=branch
            target_refs[$repository]="$remote_head"
            fetch_branch_target "$repository" "$path" "$remote" "$remote_head" || continue
            target_object_refs[$repository]="$remote/$remote_head"
            target_displays[$repository]="$remote_head"
            target_ready[$repository]=1
            ;;
        latest-tag)
            tag_prefix="refs/workspace-sync/$remote/tags"
            temporary_tag_prefixes+=("$path"$'\t'"$tag_prefix")
            if ! git -C "$path" fetch "$remote" --no-tags --prune \
                "+refs/tags/*:$tag_prefix/*"; then
                error "Cannot fetch tags for $repository remote $remote"
                problems=1
                continue
            fi

            latest_tag_ref=""
            latest_tag_timestamp=-1
            while IFS= read -r tag_ref; do
                tag_commit="$(git -C "$path" rev-parse "$tag_ref^{}^{commit}" 2>/dev/null || true)"
                [[ -n "$tag_commit" ]] || continue
                tag_timestamp="$(git -C "$path" show -s --format=%ct "$tag_commit")"
                if [[ "$tag_timestamp" -gt "$latest_tag_timestamp" ]] || \
                    { [[ "$tag_timestamp" -eq "$latest_tag_timestamp" ]] && [[ "$tag_ref" > "$latest_tag_ref" ]]; }; then
                    latest_tag_ref="$tag_ref"
                    latest_tag_timestamp="$tag_timestamp"
                fi
            done < <(git -C "$path" for-each-ref --format='%(refname)' "$tag_prefix")

            if [[ -z "$latest_tag_ref" ]]; then
                error "$repository has no commit tag on remote $remote"
                problems=1
                continue
            fi
            target_kinds[$repository]=tag
            target_refs[$repository]="$latest_tag_ref"
            target_object_refs[$repository]="$latest_tag_ref"
            target_displays[$repository]="${latest_tag_ref#"$tag_prefix/"}"
            target_ready[$repository]=1
            ;;
    esac
done

# Reject ignored untracked paths only if the selected target tracks the same
# path. This protects user files without blocking ordinary ignored build output.
for repository in "${available_repositories[@]}"; do
    [[ -n "${target_ready[$repository]:-}" ]] || continue
    path="$workspace/$repository"
    target_ref="${target_object_refs[$repository]}"
    ignored_conflict=""

    while IFS= read -r -d '' ignored_path; do
        if git -C "$path" cat-file -e "$target_ref:$ignored_path" 2>/dev/null; then
            ignored_conflict="$ignored_path"
            break
        fi
    done < <(git -C "$path" ls-files --others --ignored --exclude-standard -z)

    if [[ -n "$ignored_conflict" ]]; then
        error "$repository has an ignored local path tracked by target ${target_displays[$repository]}: $ignored_conflict"
        problems=1
    fi
done

# Refuse to overwrite a local target branch that cannot reach the fetched ref.
# A force-updated branch needs explicit approval and is backed up before reset.
declare -A recovery_backups=()
for repository in "${available_repositories[@]}"; do
    [[ "${target_kinds[$repository]:-}" == branch ]] || continue
    [[ -n "${target_ready[$repository]:-}" ]] || continue
    path="$workspace/$repository"
    remote="${selected_remotes[$repository]}"
    branch="${target_refs[$repository]}"

    occupied_worktree="$(git -C "$path" worktree list --porcelain | awk -v requested="refs/heads/$branch" '
        /^worktree / { worktree = substr($0, 10); next }
        /^branch / && substr($0, 8) == requested { print worktree }
    ')"
    if [[ -n "$occupied_worktree" ]] && [[ "$occupied_worktree" != "$path" ]]; then
        error "$repository/$branch is already checked out in $occupied_worktree"
        problems=1
        continue
    fi

    if git -C "$path" show-ref --verify --quiet "refs/heads/$branch" && \
        ! git -C "$path" merge-base --is-ancestor "$branch" "$remote/$branch"; then
        if [[ -z "${accepted_rewrite_repositories[$repository]:-}" ]]; then
            error "$repository/$branch has local commits or diverged from $remote/$branch; use --accept-rewritten-branch $repository to back it up and reset explicitly"
            problems=1
            continue
        fi
        backup_base="workspace-sync-backup/$branch/$(date -u +%Y%m%dT%H%M%SZ)"
        backup="$backup_base"
        backup_suffix=1
        while git -C "$path" show-ref --verify --quiet "refs/heads/$backup"; do
            backup="$backup_base-$backup_suffix"
            backup_suffix=$((backup_suffix + 1))
        done
        recovery_backups[$repository]="$backup"
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
        if [[ -n "${recovery_backups[$repository]:-}" ]]; then
            backup="${recovery_backups[$repository]}"
            git -C "$path" branch "$backup" "$target"
            git -C "$path" switch "$target"
            git -C "$path" reset --hard "$remote/$target"
            git -C "$path" branch --set-upstream-to="$remote/$target" "$target"
            printf 'Backed up %-29s -> %s\n' "$repository/$target" "$backup"
        elif git -C "$path" show-ref --verify --quiet "refs/heads/$target"; then
            git -C "$path" switch "$target"
            git -C "$path" branch --set-upstream-to="$remote/$target" "$target"
            git -C "$path" merge --ff-only "$remote/$target"
        else
            git -C "$path" switch --track -c "$target" "$remote/$target"
        fi
    else
        git -C "$path" switch --detach "$target"
    fi

    printf 'Synchronized %-36s -> %s\n' "$repository" "${target_displays[$repository]}"
done

if [[ "$persist" -eq 1 ]]; then
    write_local_overrides
fi
