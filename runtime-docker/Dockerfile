FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV ROOT_DIR_SRC=/opt/somenergia/src
ENV PYENV_ROOT=/opt/pyenv
ENV PYENV_VERSION=2.7.18
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONIOENCODING=UTF-8
ENV PATH=/opt/pyenv/bin:/opt/pyenv/shims:$PATH

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  bash \
  build-essential \
  ca-certificates \
  curl \
  git \
  libbz2-dev \
  libffi-dev \
  libgdal-dev \
  libmagic1 \
  liblzma-dev \
  libncurses5-dev \
  libncursesw5-dev \
  libreadline-dev \
  libsqlite3-dev \
  libssl-dev \
  libxml2-dev \
  libxmlsec1 \
  libxmlsec1-dev \
  locales \
  lsb-release \
  netcat-openbsd \
  openssl \
  pdftk-java \
  file \
  tk-dev \
  xz-utils \
  zlib1g-dev \
  && rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8

RUN git clone https://github.com/pyenv/pyenv.git "$PYENV_ROOT" \
  && cd "$PYENV_ROOT" \
  && git checkout -q 06fd1ce78890d8f79a0795e0fdfbe9a53916b82e \
  && pyenv install 2.7.18 \
  && pyenv global 2.7.18 \
  && python -m ensurepip \
  && python -m pip install --upgrade pip setuptools wheel

WORKDIR /opt/somenergia/src/openerp_som_addons
COPY . /opt/somenergia/src/openerp_som_addons

RUN chmod +x /opt/somenergia/src/openerp_som_addons/scripts/bootstrap-erp-env.sh \
  /opt/somenergia/src/openerp_som_addons/scripts/build-openerp-server.sh \
  /opt/somenergia/src/openerp_som_addons/scripts/start-openerp-server.sh \
  /opt/somenergia/src/openerp_som_addons/runtime-docker/entrypoint.sh

EXPOSE 8069

ENTRYPOINT ["/opt/somenergia/src/openerp_som_addons/runtime-docker/entrypoint.sh"]
