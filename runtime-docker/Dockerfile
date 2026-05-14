FROM python:2.7-bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV ROOT_DIR_SRC=/opt/somenergia/src

RUN apt-get update && apt-get install -y --no-install-recommends \
  git \
  curl \
  ca-certificates \
  netcat-openbsd \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/somenergia/src/openerp_som_addons
COPY . /opt/somenergia/src/openerp_som_addons

RUN chmod +x /opt/somenergia/src/openerp_som_addons/scripts/bootstrap-erp-env.sh \
  /opt/somenergia/src/openerp_som_addons/scripts/start-erp-runtime.sh \
  /opt/somenergia/src/openerp_som_addons/runtime-docker/entrypoint.sh

EXPOSE 8069

ENTRYPOINT ["/opt/somenergia/src/openerp_som_addons/runtime-docker/entrypoint.sh"]
