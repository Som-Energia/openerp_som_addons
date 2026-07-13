#!/bin/bash

set -euo pipefail

ROOT_DIR_SRC="${ROOT_DIR_SRC:-${GITHUB_WORKSPACE:-$PWD}/..}"
ERP_BRANCH="${ERP_BRANCH:-rolling_erp01}"
PYTHON_VERSION="${PYTHON_VERSION:-2.7}"

if [ -z "${GITHUB_TOKEN:-}" ]; then
	echo "GITHUB_TOKEN is required to clone private repositories" >&2
	exit 1
fi

export GIT_TERMINAL_PROMPT=0

git config --global \
  url."https://x-access-token:${GITHUB_TOKEN}@github.com/".insteadOf \
  "ssh://git@github.com/"

git clone --depth 1 "https://${GITHUB_TOKEN}@github.com/Som-Energia/erp.git" -b "$ERP_BRANCH" "$ROOT_DIR_SRC/erp"
git clone --depth 1 "https://${GITHUB_TOKEN}@github.com/Som-Energia/libFacturacioATR.git" "$ROOT_DIR_SRC/libFacturacioATR"
git clone --depth 1 "https://${GITHUB_TOKEN}@github.com/Som-Energia/OMIE.git" "$ROOT_DIR_SRC/OMIE"
git clone --depth 1 "https://${GITHUB_TOKEN}@github.com/Som-Energia/omie-modules.git" "$ROOT_DIR_SRC/omie-modules"
printf '%s\n' "git+https://${GITHUB_TOKEN}@github.com/som-energia/omie.git" >"$ROOT_DIR_SRC/omie-modules/giscedata_omie_api/requirements.txt"
if [ ! -d "$ROOT_DIR_SRC/openerp_som_addons" ]; then
	git clone --depth 1 https://github.com/Som-Energia/openerp_som_addons.git "$ROOT_DIR_SRC/openerp_som_addons"
fi
if [ ! -d "$ROOT_DIR_SRC/somenergia-generationkwh" ]; then
	git clone --depth 1 https://github.com/Som-Energia/somenergia-generationkwh.git "$ROOT_DIR_SRC/somenergia-generationkwh"
fi
if [ ! -d "$ROOT_DIR_SRC/plantmeter" ]; then
	git clone --depth 1 https://github.com/Som-Energia/plantmeter.git "$ROOT_DIR_SRC/plantmeter"
fi
if [ ! -d "$ROOT_DIR_SRC/som_sync_openerp_modules" ]; then
	git clone --depth 1 https://github.com/Som-Energia/som_sync_openerp_modules.git "$ROOT_DIR_SRC/som_sync_openerp_modules"
fi
if [ ! -d "$ROOT_DIR_SRC/giscedata_facturacio_indexada_som" ]; then
	git clone --depth 1 https://github.com/Som-Energia/giscedata_facturacio_indexada_som.git "$ROOT_DIR_SRC/giscedata_facturacio_indexada_som"
fi
if [ ! -d "$ROOT_DIR_SRC/oorq" ]; then
	git clone --depth 1 https://github.com/gisce/oorq.git -b api_v5 "$ROOT_DIR_SRC/oorq"
fi
git clone --depth 1 https://github.com/Som-Energia/poweremail.git -b v5_backport "$ROOT_DIR_SRC/poweremail2"
git clone --depth 1 https://github.com/gisce/openerp-sentry.git -b v5_legacy "$ROOT_DIR_SRC/openerp-sentry"
git clone --depth 1 https://github.com/gisce/ws_transactions.git "$ROOT_DIR_SRC/ws_transactions"
git clone --depth 1 https://github.com/gisce/ir_attachment_mongodb.git "$ROOT_DIR_SRC/ir_attachment_mongodb"
git clone --depth 1 https://github.com/gisce/mongodb_backend.git -b gisce "$ROOT_DIR_SRC/mongodb_backend"
git clone --depth 1 https://github.com/gisce/poweremail-modules.git "$ROOT_DIR_SRC/poweremail-modules"
git clone --depth 1 https://github.com/gisce/crm_poweremail.git "$ROOT_DIR_SRC/crm_poweremail"
git clone --depth 1 https://github.com/gisce/ooop.git "$ROOT_DIR_SRC/ooop"
git clone --depth 1 "https://${GITHUB_TOKEN}@github.com/Som-Energia/cchloader.git" "$ROOT_DIR_SRC/cchloader"
git clone --depth 1 "https://${GITHUB_TOKEN}@github.com/Som-Energia/gestionatr.git" "$ROOT_DIR_SRC/gestionatr"

if [ "${BOOTSTRAP_SKIP_APT:-0}" != "1" ]; then
	SUDO=""
	if [ "$(id -u)" -ne 0 ]; then
		SUDO="sudo"
	fi

	$SUDO apt-get --allow-releaseinfo-change update
	$SUDO apt-get install python2-dev python3-dev libxml2-dev libxmlsec1 libxmlsec1-dev libgdal-dev pdftk -y
fi

cd "$ROOT_DIR_SRC/libFacturacioATR"
if latest_tag=$(git describe --tags "$(git rev-list --tags --max-count=1 2>/dev/null)" 2>/dev/null); then
	git checkout "$latest_tag"
fi
pip install -e .

cd "$ROOT_DIR_SRC/ooop"
if latest_tag=$(git describe --tags "$(git rev-list --tags --max-count=1 2>/dev/null)" 2>/dev/null); then
	git checkout "$latest_tag"
fi
pip install -e .

cd "$ROOT_DIR_SRC/OMIE"
if latest_tag=$(git describe --tags "$(git rev-list --tags --max-count=1 2>/dev/null)" 2>/dev/null); then
	git checkout "$latest_tag"
fi
pip install --no-build-isolation -e .

cd "$ROOT_DIR_SRC/cchloader"
if latest_tag=$(git describe --tags "$(git rev-list --tags --max-count=1 2>/dev/null)" 2>/dev/null); then
	git checkout "$latest_tag"
fi
pip install --no-build-isolation -e .

cd "$ROOT_DIR_SRC/gestionatr"
if latest_tag=$(git describe --tags "$(git rev-list --tags --max-count=1 2>/dev/null)" 2>/dev/null); then
	git checkout "$latest_tag"
fi
pip install --no-build-isolation -e .

cd "$ROOT_DIR_SRC/somenergia-generationkwh"
pip install -e . || true

cd "$ROOT_DIR_SRC/plantmeter"
pip install -e . || true

pip install lazy-object-proxy==1.6.0
pip install -r "$ROOT_DIR_SRC/erp/requirements-dev.txt"
pip install -r "$ROOT_DIR_SRC/erp/requirements.txt"

# Fallback for legacy ERP imports on Python 2
pip install "rq-scheduler<0.11"
pip install "Pympler<0.8"
pip install "Flask-RESTful<0.4"
pip install "Flask-Login<0.5"
pip install "Flask-Cors<3"
pip install "Flask-SSE<1.0"
pip install "msgpack-python<1.0"
pip install "Cerberus<1.3"
pip install "cachelib<0.2"
pip install "Mako<1.2"
pip install "pypdftk<0.5"
pip install "paramiko<2.8"
pip install "pudb==2019.2"

if [ "$PYTHON_VERSION" != "2.7" ]; then
	pip install somutils
	pip install dm.xmlsec.binding
else
	git clone --depth 1 https://github.com/Som-Energia/somenergia-utils.git -b py2 "$ROOT_DIR_SRC/somenergia-utils"
	cd "$ROOT_DIR_SRC/somenergia-utils"
	pip install -e . || true
	pip install "dm.xmlsec.binding<=1.3.2"
fi

cd "$ROOT_DIR_SRC/erp"
./tools/link_addons.sh
