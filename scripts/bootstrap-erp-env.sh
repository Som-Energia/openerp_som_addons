#!/bin/bash

set -euo pipefail

ROOT_DIR_SRC="${ROOT_DIR_SRC:-${GITHUB_WORKSPACE:-$PWD}/..}"
ERP_BRANCH="${ERP_BRANCH:-rolling_erp01}"
PYTHON_VERSION="${PYTHON_VERSION:-2.7}"

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "GITHUB_TOKEN is required to clone private repositories" >&2
  exit 1
fi

git clone --depth 1 "https://${GITHUB_TOKEN}@github.com/Som-Energia/erp.git" -b "$ERP_BRANCH" "$ROOT_DIR_SRC/erp"
git clone --depth 1 "https://${GITHUB_TOKEN}@github.com/Som-Energia/libFacturacioATR.git" "$ROOT_DIR_SRC/libFacturacioATR"
git clone --depth 1 "https://${GITHUB_TOKEN}@github.com/Som-Energia/omie-modules.git" "$ROOT_DIR_SRC/omie-modules"
git clone --depth 1 "https://${GITHUB_TOKEN}@github.com/Som-Energia/OMIE.git" "$ROOT_DIR_SRC/OMIE"
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
git clone --depth 1 https://github.com/Som-Energia/giscedata_facturacio_indexada_som.git "$ROOT_DIR_SRC/giscedata_facturacio_indexada_som"
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

sudo apt-get --allow-releaseinfo-change update
sudo apt-get install python2-dev python3-dev libxml2-dev libxmlsec1 libxmlsec1-dev libgdal-dev pdftk -y

cd "$ROOT_DIR_SRC/libFacturacioATR"
git checkout "$(git describe --tags "$(git rev-list --tags --max-count=1)")"
pip install -e .

cd "$ROOT_DIR_SRC/ooop"
git checkout "$(git describe --tags "$(git rev-list --tags --max-count=1)")"
pip install -e .

cd "$ROOT_DIR_SRC/OMIE"
git checkout "$(git describe --tags "$(git rev-list --tags --max-count=1)")"
pip install --no-build-isolation -e .

cd "$ROOT_DIR_SRC/somenergia-generationkwh"
pip install -e . || true

cd "$ROOT_DIR_SRC/plantmeter"
pip install -e . || true

pip install lazy-object-proxy==1.6.0
pip install -r "$ROOT_DIR_SRC/erp/requirements-dev.txt"
pip install -r "$ROOT_DIR_SRC/erp/requirements.txt"

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
