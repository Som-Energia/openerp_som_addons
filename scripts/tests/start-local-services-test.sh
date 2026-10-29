#!/usr/bin/env bash
# Isolated Git/Compose fixtures; no Docker daemon or ERP environment is needed.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
primary="$tmp/primary checkout"
mkdir -p "$primary/scripts" "$tmp/bin"
cp "$script_dir/start-local-services.sh" "$primary/scripts/"
printf 'services: {}\n' > "$primary/docker-compose.yaml"
git -C "$primary" init -q
git -C "$primary" add scripts docker-compose.yaml
git -C "$primary" -c user.name=Test -c user.email=test@example.invalid commit -qm initial
git -C "$primary" worktree add --detach "$tmp/linked worktree" HEAD >/dev/null 2>&1
export TEST_DOCKER_LOG="$tmp/docker.log" TEST_DOCKER_STATE="$tmp/state"
cat > "$tmp/bin/docker" <<'DOCKER'
#!/usr/bin/env bash
printf '%s\t' "$@" >> "$TEST_DOCKER_LOG"
printf '\n' >> "$TEST_DOCKER_LOG"
while [[ "$1" != up && "$1" != exec && "$1" != ps ]]; do shift; done
if [[ "$1" == up && "${TEST_START_FAIL:-0}" == 1 ]]; then exit 42; fi
if [[ "$1" == exec && "$3" == "${TEST_UNREADY:-}" ]]; then exit 1; fi
if [[ "$1" == exec && "${TEST_RETRY:-0}" == 1 && ! -e "$TEST_DOCKER_STATE" ]]; then
    touch "$TEST_DOCKER_STATE"
    exit 1
fi
DOCKER
chmod +x "$tmp/bin/docker"
export PATH="$tmp/bin:$PATH"
export COMPOSE_PROJECT_NAME=wrong_project COMPOSE_FILE=wrong_compose.yaml
bash "$primary/scripts/start-local-services.sh" > "$tmp/output"
cp "$TEST_DOCKER_LOG" "$tmp/primary.log"
: > "$TEST_DOCKER_LOG"
bash "$tmp/linked worktree/scripts/start-local-services.sh" > "$tmp/output"
cmp "$tmp/primary.log" "$TEST_DOCKER_LOG" || fail 'worktree used a different Compose project'
grep -Fq -- "--project-name" "$TEST_DOCKER_LOG" || fail 'missing explicit project'
grep -Fq -- "$primary/docker-compose.yaml" "$TEST_DOCKER_LOG" || fail 'missing primary compose file'
grep -Fq $'up\t-d\tpostgres\tmongo\tredis' "$TEST_DOCKER_LOG" || fail 'not all services started'
for service in postgres mongo redis; do
    grep -Fq $'exec\t-T\t'"$service" "$TEST_DOCKER_LOG" || fail "missing readiness probe: $service"
    if OPENERP_LOCAL_SERVICES_TIMEOUT=0 TEST_UNREADY="$service" \
        bash "$primary/scripts/start-local-services.sh" > "$tmp/output" 2>&1; then
        fail "unready service accepted: $service"
    fi
    grep -Fq "$service was not ready" "$tmp/output" || fail 'missing timeout diagnosis'
done
TEST_RETRY=1 bash "$primary/scripts/start-local-services.sh" > "$tmp/output"
[[ -f "$TEST_DOCKER_STATE" ]] || fail 'readiness was not retried'
set +e
TEST_START_FAIL=1 bash "$primary/scripts/start-local-services.sh" > "$tmp/output" 2>&1
status=$?
set -e
[[ "$status" == 42 ]] || fail 'Compose startup failure was hidden'
if OPENERP_LOCAL_SERVICES_TIMEOUT=invalid bash "$primary/scripts/start-local-services.sh" > "$tmp/output" 2>&1; then
    fail 'invalid timeout accepted'
fi
printf 'PASS: shared Compose project, readiness, retries and failures\n'
