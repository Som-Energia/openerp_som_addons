# Devcontainer setup

This directory adds a devcontainer entrypoint on top of the existing `runtime-docker` stack while keeping the runtime files as the source of truth for ERP services.

## Files

- `devcontainer.json` — standard devcontainer definition that starts the existing compose stack and attaches to `erp-runtime`.
- `docker-compose.devcontainer.yml` — compose override that keeps the main container alive for editor attachment and mounts the full host workspace into the expected source root.
- `bin/bootstrap-erp-workspace` — waits for compose dependencies, requires a real `GITHUB_TOKEN` only when private sibling repositories are missing, clones only missing sibling repositories, and prepares the mounted Python environment.
- `bin/start-erp-runtime` — waits for compose dependencies, exports the runtime environment, auto-runs bootstrap if required imports are still missing, and then runs the existing ERP build/start script.
- `bin/show-pudb-remote-debug` — prints the exact PuDB remote breakpoint snippet and the connection steps for this devcontainer setup.
- `helpers/common.sh` — shared shell helpers used by the devcontainer-only commands.

## How it works

The devcontainer reuses:

- `runtime-docker/Dockerfile`
- `runtime-docker/docker-compose.yml`

The override file changes only devcontainer behavior:

- overrides the runtime image `entrypoint` and `command` so the container stays alive for attachment,
- bind-mounts the full host workspace root at `/opt/somenergia/src`,
- keeps this repository available at `/opt/somenergia/src/openerp_som_addons` and sibling repositories such as `/opt/somenergia/src/erp`,
- defaults devcontainer helpers to the pyenv environment name `erp`, but falls back to the image's Python `2.7.18` interpreter when that alias is not available in the container,
- exposes `.devcontainer/bin` on `PATH` inside the container so the helper commands can be run directly.

## Environment expectations

- Export a real `GITHUB_TOKEN` on the host **before** opening the devcontainer so Docker Compose can resolve the existing runtime stack configuration.
- Application flows that truly need GitHub authentication will still require a real token.
- The current bind mount assumes this repository lives under `/home/pau/src` and mounts that full host workspace into `/opt/somenergia/src`.

## Manual ERP workflow inside the devcontainer

Open the devcontainer first. You can run the helpers either from a shell inside the container or through the versioned VS Code tasks in `.vscode/tasks.json`.

### Editor task flow

After the devcontainer is attached:

1. If you want to use the editor task for bootstrap, export a real `GITHUB_TOKEN` on the host before opening the devcontainer.
2. Run `Tasks: Run Task` from the command palette.
3. Choose `ERP: Bootstrap workspace` the first time you prepare the workspace.
4. After bootstrap completes, run `ERP: Start runtime` whenever you want to start ERP manually.

These tasks stay manual on purpose. They do not auto-bootstrap on container creation or editor startup.

### 1. Provide a real GitHub token

Before opening the devcontainer, export `GITHUB_TOKEN` on the host:

```bash
export GITHUB_TOKEN=ghp_your_real_token_here
```

The bootstrap helper fails fast only when it must clone private repositories and `GITHUB_TOKEN` is missing.

### 2. Bootstrap the ERP workspace

```bash
bootstrap-erp-workspace
```

What it does:

- waits for `postgres`, `redis`, and `mongo`,
- defaults `PYENV_VERSION` to `erp` and falls back to `2.7.18` when the alias is not available in the container,
- ensures the mounted workspace repositories exist without recloning directories that are already present,
- installs the Python requirements needed by the ERP runtime even if `/opt/somenergia/src/erp` already existed before the container started,
- refreshes editable installs and addon links for the mounted workspace,
- verifies the selected interpreter can import `six` and `destral.utils`,
- is the same command used by the `ERP: Bootstrap workspace` editor task.

### 3. Start ERP manually

```bash
start-erp-runtime
```

What it does:

- waits for `postgres`, `redis`, and `mongo`,
- verifies the workspace was bootstrapped,
- exports the same runtime variables used by the existing runtime flow,
- prepends the mounted workspace repositories such as `destral/`, `libFacturacioATR/`, `OMIE/`, `cchloader/`, and `gestionatr/` to `PYTHONPATH`,
- temporarily patches the OMIE private requirement during startup when a real `GITHUB_TOKEN` is available, then restores your mounted file afterwards,
- auto-runs `bootstrap-erp-workspace` when the selected interpreter still cannot import the required runtime modules,
- reuses `scripts/build-openerp-server.sh`, which in turn starts ERP through `scripts/start-openerp-server.sh`,
- is the same command used by the `ERP: Start runtime` editor task.

### Optional runtime overrides

You can override the same environment values before running `start-erp-runtime`:

```bash
export ERP_DATABASE=my_dev_db
export ERP_XMLRPC_PORT=8070
start-erp-runtime
```

The defaults match the runtime container flow:

- `ROOT_DIR_SRC=/opt/somenergia/src`
- `PYENV_VERSION=erp` (with automatic fallback to `2.7.18` if needed)
- `OPENERP_DB_HOST=postgres`
- `OPENERP_DB_USER=erp`
- `OPENERP_DB_PASSWORD=erp`
- `OPENERP_MONGODB_HOST=mongo`
- `OPENERP_REDIS_URL=redis://redis:6379/0`
- `OPENERP_CONFIG=/opt/somenergia/src/openerp_som_addons/runtime-docker/erp.conf`

This matches the devcontainer mount layout: the host workspace `/home/pau/src` is exposed at `/opt/somenergia/src`, while the editor still attaches to `/opt/somenergia/src/openerp_som_addons`.

If you need a different interpreter selection for troubleshooting, override it explicitly before running a helper:

```bash
export PYENV_VERSION=2.7.18
start-erp-runtime
```

## PuDB remote debugging from the devcontainer

This repository already exposes the PuDB remote debugger port through the runtime stack and forwards it in the devcontainer. The devcontainer-only workflow is:

1. Open the devcontainer.
2. Bootstrap once if needed:

   ```bash
   bootstrap-erp-workspace
   ```

3. Start ERP manually:

   ```bash
   start-erp-runtime
   ```

4. Add this breakpoint in the code path you want to inspect:

   ```python
   import pudb.remote
   pudb.remote.set_trace(host="0.0.0.0", port=6899, term_size=(120, 40))
   ```

5. Trigger that code path so ERP stops on the remote breakpoint.
6. Open a second terminal in the same devcontainer and connect to the debugger:

   ```bash
   telnet 127.0.0.1 6899
   ```

   If `telnet` is not installed in your environment, try:

   ```bash
   nc 127.0.0.1 6899
   ```

7. Use PuDB in the second terminal. When you continue or quit the debugger, ERP resumes in the first terminal.

If you want the instructions printed for quick copy/paste inside the container, run:

```bash
bash .devcontainer/bin/show-pudb-remote-debug
```

Or use the editor task `ERP: PuDB remote debugging help`.

## Validation

From the repository root, a lightweight validation is:

```bash
docker compose \
  -f runtime-docker/docker-compose.yml \
  -f .devcontainer/docker-compose.devcontainer.yml \
  config
```

This checks that the compose merge is valid without editing or starting the existing runtime files. Use a placeholder token for this validation if you do not want to expose a real token in your shell history:

```bash
GITHUB_TOKEN=devcontainer-placeholder-token docker compose \
  -f runtime-docker/docker-compose.yml \
  -f .devcontainer/docker-compose.devcontainer.yml \
  config
```

Inside the repository, shell syntax can also be validated without secrets:

```bash
bash -n .devcontainer/helpers/common.sh \
  && bash -n .devcontainer/bin/bootstrap-erp-workspace \
  && bash -n .devcontainer/bin/start-erp-runtime \
  && bash -n .devcontainer/bin/show-pudb-remote-debug
```

The bootstrap/start helpers cannot be fully executed without the running compose services and, for bootstrap, a real `GITHUB_TOKEN` with access to the private repositories.
