#!/bin/bash

set -euo pipefail

DEVCONTAINER_HELPERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVCONTAINER_DIR="$(dirname "$DEVCONTAINER_HELPERS_DIR")"
REPO_ROOT="$(dirname "$DEVCONTAINER_DIR")"

ROOT_DIR_SRC="${ROOT_DIR_SRC:-/opt/somenergia/src}"
ERP_BOOTSTRAP_TIMEOUT="${ERP_BOOTSTRAP_TIMEOUT:-180}"
ERP_DATABASE="${ERP_DATABASE:-erp_runtime}"
ERP_XMLRPC_PORT="${ERP_XMLRPC_PORT:-8069}"
ERP_BIND_ADDRESS="${ERP_BIND_ADDRESS:-0.0.0.0}"
ERP_HEALTH_TIMEOUT="${ERP_HEALTH_TIMEOUT:-300}"
ERP_BRANCH="${ERP_BRANCH:-rolling_erp01}"
OPENERP_DB_USER="${OPENERP_DB_USER:-erp}"
OPENERP_DB_PASSWORD="${OPENERP_DB_PASSWORD:-erp}"
PYENV_ROOT="${PYENV_ROOT:-/opt/pyenv}"
PYENV_BASE_VERSION="${PYENV_BASE_VERSION:-2.7.18}"
PYENV_DEFAULT_VERSION="${PYENV_DEFAULT_VERSION:-erp}"

DEVCONTAINER_LOCAL_PYTHON_REPOS=(
	"destral"
	"libFacturacioATR"
	"ooop"
	"OMIE"
	"cchloader"
	"gestionatr"
	"somenergia-generationkwh"
	"plantmeter"
	"somenergia-utils"
)

BOOTSTRAP_CLONED_REPOS=()
TEMP_OMIE_REQUIREMENTS_BACKUP=""

wait_for_port() {
	local host="$1"
	local port="$2"
	local timeout="$3"
	local start

	start=$(date +%s)
	while true; do
		if nc -z "$host" "$port" >/dev/null 2>&1; then
			return 0
		fi

		if [ $(($(date +%s) - start)) -ge "$timeout" ]; then
			echo "Timeout waiting for ${host}:${port}" >&2
			return 1
		fi

		sleep 2
	done
}

wait_for_dependencies() {
	if [ "${DEVCONTAINER_SKIP_WAIT:-0}" = "1" ]; then
		echo "Skipping dependency wait because DEVCONTAINER_SKIP_WAIT=1"
		return 0
	fi

	echo "Waiting for postgres, redis, and mongo"
	wait_for_port "postgres" "5432" "$ERP_BOOTSTRAP_TIMEOUT"
	wait_for_port "redis" "6379" "$ERP_BOOTSTRAP_TIMEOUT"
	wait_for_port "mongo" "27017" "$ERP_BOOTSTRAP_TIMEOUT"
}

require_real_github_token() {
	if [ -z "${GITHUB_TOKEN:-}" ] || [ "${GITHUB_TOKEN}" = "devcontainer-placeholder-token" ]; then
		echo "A real GITHUB_TOKEN is required to bootstrap the ERP workspace." >&2
		echo "Export GITHUB_TOKEN inside the devcontainer or reopen it with the host token available." >&2
		return 1
	fi
}

has_real_github_token() {
	[ -n "${GITHUB_TOKEN:-}" ] && [ "${GITHUB_TOKEN}" != "devcontainer-placeholder-token" ]
}

ensure_workspace_bootstrapped() {
	if [ ! -d "${ROOT_DIR_SRC}/erp" ]; then
		echo "ERP workspace not found at ${ROOT_DIR_SRC}/erp" >&2
		echo "Run .devcontainer/bin/bootstrap-erp-workspace first." >&2
		return 1
	fi
}

ensure_pyenv_runtime() {
	export PYENV_ROOT
	export PYENV_VERSION="${PYENV_VERSION:-$PYENV_DEFAULT_VERSION}"
	export PATH="${PYENV_ROOT}/bin:${PYENV_ROOT}/shims:${PATH}"

	local requested_path="${PYENV_ROOT}/versions/${PYENV_VERSION}"
	local base_path="${PYENV_ROOT}/versions/${PYENV_BASE_VERSION}"

	if [ "$PYENV_VERSION" = "$PYENV_BASE_VERSION" ]; then
		return 0
	fi

	if [ -e "$requested_path" ]; then
		return 0
	fi

	if [ -d "$base_path" ]; then
		echo "Pyenv environment '${PYENV_VERSION}' is not available in the container; falling back to ${PYENV_BASE_VERSION}"
		export PYENV_VERSION="$PYENV_BASE_VERSION"
	fi
}

devcontainer_python_bin() {
	ensure_pyenv_runtime

	local candidate="${PYENV_ROOT}/versions/${PYENV_VERSION}/bin/python"
	if [ -x "$candidate" ]; then
		printf '%s\n' "$candidate"
		return 0
	fi

	if command -v python >/dev/null 2>&1; then
		command -v python
		return 0
	fi

	echo "python interpreter not found for PYENV_VERSION=${PYENV_VERSION}" >&2
	return 1
}

devcontainer_pip_bin() {
	ensure_pyenv_runtime

	local candidate="${PYENV_ROOT}/versions/${PYENV_VERSION}/bin/pip"
	if [ -x "$candidate" ]; then
		printf '%s\n' "$candidate"
		return 0
	fi

	if command -v pip >/dev/null 2>&1; then
		command -v pip
		return 0
	fi

	echo "pip not found for PYENV_VERSION=${PYENV_VERSION}" >&2
	return 1
}

devcontainer_python() {
	local python_bin
	python_bin="$(devcontainer_python_bin)"
	"$python_bin" "$@"
}

devcontainer_pip() {
	local pip_bin
	pipefail_return=0
	pip_bin="$(devcontainer_pip_bin)" || pipefail_return=$?
	if [ "$pipefail_return" -ne 0 ]; then
		return "$pipefail_return"
	fi
	"$pip_bin" "$@"
}

append_pythonpath_entry() {
	local entry="$1"
	if [ ! -d "$entry" ]; then
		return 0
	fi

	case ":${PYTHONPATH:-}:" in
	*":${entry}:"*) ;;
	*)
		if [ -n "${PYTHONPATH:-}" ]; then
			PYTHONPATH="${entry}:${PYTHONPATH}"
		else
			PYTHONPATH="$entry"
		fi
		;;
	esac
}

export_workspace_pythonpath() {
	append_pythonpath_entry "${ROOT_DIR_SRC}/erp/server/bin"
	append_pythonpath_entry "${ROOT_DIR_SRC}/erp/server/bin/addons"
	append_pythonpath_entry "${ROOT_DIR_SRC}/erp/server/sitecustomize"

	local repo
	for repo in "${DEVCONTAINER_LOCAL_PYTHON_REPOS[@]}"; do
		append_pythonpath_entry "${ROOT_DIR_SRC}/${repo}"
	done

	export PYTHONPATH
}

python_import_check() {
	local module_name="$1"
	devcontainer_python -c "import ${module_name}" >/dev/null 2>&1
}

workspace_python_is_ready() {
	ensure_workspace_bootstrapped || return 1
	export_runtime_environment
	python_import_check six && python_import_check destral.utils
}

clone_repo_if_missing() {
	local destination="$1"
	local repo_url="$2"
	local branch="${3:-}"

	if [ -d "$destination/.git" ] || [ -d "$destination" ]; then
		echo "Keeping existing repository: $destination"
		return 0
	fi

	echo "Cloning missing repository into $destination"
	if [ -n "$branch" ]; then
		git clone --depth 1 -b "$branch" "$repo_url" "$destination"
	else
		git clone --depth 1 "$repo_url" "$destination"
	fi
	BOOTSTRAP_CLONED_REPOS+=("$destination")
}

checkout_latest_tag_if_available() {
	local repo_path="$1"
	local cloned_repo
	local was_cloned=0

	if [ ! -d "$repo_path/.git" ]; then
		return 0
	fi

	for cloned_repo in "${BOOTSTRAP_CLONED_REPOS[@]}"; do
		if [ "$cloned_repo" = "$repo_path" ]; then
			was_cloned=1
			break
		fi
	done

	if [ "$was_cloned" -ne 1 ]; then
		return 0
	fi

	(
		cd "$repo_path"
		local latest_tag
		latest_tag=$(git describe --tags "$(git rev-list --tags --max-count=1 2>/dev/null)" 2>/dev/null || true)
		if [ -n "$latest_tag" ]; then
			git checkout "$latest_tag"
		fi
	)
}

bootstrap_workspace_sources() {
	echo "Ensuring ERP workspace sources exist under ${ROOT_DIR_SRC}"
	clone_repo_if_missing "${ROOT_DIR_SRC}/erp" "https://${GITHUB_TOKEN}@github.com/Som-Energia/erp.git" "$ERP_BRANCH"
	clone_repo_if_missing "${ROOT_DIR_SRC}/destral" "https://github.com/gisce/destral.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/libFacturacioATR" "https://${GITHUB_TOKEN}@github.com/Som-Energia/libFacturacioATR.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/OMIE" "https://${GITHUB_TOKEN}@github.com/Som-Energia/OMIE.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/omie-modules" "https://${GITHUB_TOKEN}@github.com/Som-Energia/omie-modules.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/somenergia-utils" "https://github.com/Som-Energia/somenergia-utils.git" "py2"
	clone_repo_if_missing "${ROOT_DIR_SRC}/poweremail2" "https://github.com/Som-Energia/poweremail.git" "v5_backport"
	clone_repo_if_missing "${ROOT_DIR_SRC}/openerp-sentry" "https://github.com/gisce/openerp-sentry.git" "v5_legacy"
	clone_repo_if_missing "${ROOT_DIR_SRC}/ws_transactions" "https://github.com/gisce/ws_transactions.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/ir_attachment_mongodb" "https://github.com/gisce/ir_attachment_mongodb.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/mongodb_backend" "https://github.com/gisce/mongodb_backend.git" "gisce"
	clone_repo_if_missing "${ROOT_DIR_SRC}/poweremail-modules" "https://github.com/gisce/poweremail-modules.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/crm_poweremail" "https://github.com/gisce/crm_poweremail.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/ooop" "https://github.com/gisce/ooop.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/cchloader" "https://${GITHUB_TOKEN}@github.com/Som-Energia/cchloader.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/gestionatr" "https://${GITHUB_TOKEN}@github.com/Som-Energia/gestionatr.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/somenergia-generationkwh" "https://github.com/Som-Energia/somenergia-generationkwh.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/plantmeter" "https://github.com/Som-Energia/plantmeter.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/som_sync_openerp_modules" "https://github.com/Som-Energia/som_sync_openerp_modules.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/giscedata_facturacio_indexada_som" "https://github.com/Som-Energia/giscedata_facturacio_indexada_som.git"
	clone_repo_if_missing "${ROOT_DIR_SRC}/oorq" "https://github.com/gisce/oorq.git" "api_v5"

}

workspace_needs_private_repo_access() {
	local repo
	for repo in erp libFacturacioATR OMIE omie-modules cchloader gestionatr; do
		if [ ! -d "${ROOT_DIR_SRC}/${repo}" ]; then
			return 0
		fi
	done
	return 1
}

install_workspace_python_packages() {
	echo "Preparing Python environment with PYENV_VERSION=${PYENV_VERSION}"

	checkout_latest_tag_if_available "${ROOT_DIR_SRC}/libFacturacioATR"
	checkout_latest_tag_if_available "${ROOT_DIR_SRC}/ooop"
	checkout_latest_tag_if_available "${ROOT_DIR_SRC}/OMIE"
	checkout_latest_tag_if_available "${ROOT_DIR_SRC}/cchloader"
	checkout_latest_tag_if_available "${ROOT_DIR_SRC}/gestionatr"

	if [ -d "${ROOT_DIR_SRC}/libFacturacioATR" ]; then
		devcontainer_pip install -e "${ROOT_DIR_SRC}/libFacturacioATR"
	fi
	if [ -d "${ROOT_DIR_SRC}/ooop" ]; then
		devcontainer_pip install -e "${ROOT_DIR_SRC}/ooop"
	fi
	if [ -d "${ROOT_DIR_SRC}/OMIE" ]; then
		devcontainer_pip install --no-build-isolation -e "${ROOT_DIR_SRC}/OMIE"
	fi
	if [ -d "${ROOT_DIR_SRC}/cchloader" ]; then
		devcontainer_pip install --no-build-isolation -e "${ROOT_DIR_SRC}/cchloader"
	fi
	if [ -d "${ROOT_DIR_SRC}/gestionatr" ]; then
		devcontainer_pip install --no-build-isolation -e "${ROOT_DIR_SRC}/gestionatr"
	fi
	if [ -d "${ROOT_DIR_SRC}/somenergia-generationkwh" ]; then
		devcontainer_pip install -e "${ROOT_DIR_SRC}/somenergia-generationkwh" || true
	fi
	if [ -d "${ROOT_DIR_SRC}/plantmeter" ]; then
		devcontainer_pip install -e "${ROOT_DIR_SRC}/plantmeter" || true
	fi
	if [ -f "${ROOT_DIR_SRC}/erp/requirements-dev.txt" ]; then
		devcontainer_pip install lazy-object-proxy==1.6.0
		devcontainer_pip install -r "${ROOT_DIR_SRC}/erp/requirements-dev.txt"
	fi
	if [ -f "${ROOT_DIR_SRC}/erp/requirements.txt" ]; then
		devcontainer_pip install -r "${ROOT_DIR_SRC}/erp/requirements.txt"
	fi
	devcontainer_pip install "rq-scheduler<0.11" "Pympler<0.8" "Flask-RESTful<0.4" "Flask-Login<0.5" "Flask-Cors<3" "Flask-SSE<1.0" "msgpack-python<1.0" "Cerberus<1.3" "cachelib<0.2" "Mako<1.2" "pypdftk<0.5" "paramiko<2.8" "pudb==2019.2"
	if [ -d "${ROOT_DIR_SRC}/somenergia-utils" ]; then
		devcontainer_pip install -e "${ROOT_DIR_SRC}/somenergia-utils" || true
	fi
	devcontainer_pip install "dm.xmlsec.binding<=1.3.2"

	if [ -x "${ROOT_DIR_SRC}/erp/tools/link_addons.sh" ]; then
		echo "Linking ERP addons"
		(
			cd "${ROOT_DIR_SRC}/erp"
			bash "tools/link_addons.sh"
		)
	fi
}

prepare_authenticated_omie_requirements() {
	local requirements_file="${ROOT_DIR_SRC}/omie-modules/giscedata_omie_api/requirements.txt"

	if [ ! -f "$requirements_file" ] || ! has_real_github_token; then
		return 0
	fi

	TEMP_OMIE_REQUIREMENTS_BACKUP="$(mktemp)"
	cp "$requirements_file" "$TEMP_OMIE_REQUIREMENTS_BACKUP"
	printf '%s\n' "git+https://${GITHUB_TOKEN}@github.com/som-energia/omie.git" >"$requirements_file"
}

restore_authenticated_omie_requirements() {
	local requirements_file="${ROOT_DIR_SRC}/omie-modules/giscedata_omie_api/requirements.txt"

	if [ -n "$TEMP_OMIE_REQUIREMENTS_BACKUP" ] && [ -f "$TEMP_OMIE_REQUIREMENTS_BACKUP" ]; then
		mv "$TEMP_OMIE_REQUIREMENTS_BACKUP" "$requirements_file"
		TEMP_OMIE_REQUIREMENTS_BACKUP=""
	fi
}

export_runtime_environment() {
	ensure_pyenv_runtime
	export ROOT_DIR_SRC
	export ERP_DATABASE
	export ERP_XMLRPC_PORT
	export ERP_BIND_ADDRESS
	export ERP_HEALTH_TIMEOUT
	export OPENERP_DB_HOST="${OPENERP_DB_HOST:-postgres}"
	export OPENERP_DB_USER
	export OPENERP_DB_PASSWORD
	export OPENERP_MONGODB_HOST="${OPENERP_MONGODB_HOST:-mongo}"
	export OPENERP_REDIS_URL="${OPENERP_REDIS_URL:-redis://redis:6379/0}"
	export OPENERP_CONFIG="${OPENERP_CONFIG:-${REPO_ROOT}/runtime-docker/erp.conf}"
	export_workspace_pythonpath
}
