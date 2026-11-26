# -*- coding: utf-8 -*-
from __future__ import absolute_import
import io
import os
import re
import tempfile
import zipfile
import zlib

import requests
from requests.auth import HTTPBasicAuth

from som_crawlers.api_downloaders import BaseApiDownloader
from som_crawlers.models.exceptions import (
    CrawlingProcessException, CrawlingLoginException, NoResultsException)


def instance(_config, **_kwargs):
    return Iberdrola(_config)


class Iberdrola(BaseApiDownloader):
    name = 'iberdrola'
    cod_portal = '0021'
    process = None
    request_timeout = 60
    download_timeout = 300
    default_url = 'https://www.i-de.es/pwelconq/services/arq/'

    def __init__(self, config):
        super(Iberdrola, self).__init__(config)
        self.session = requests.Session()
        self.base_url = (config.url_portal or self.default_url).rstrip('/') + '/'

    def _post(self, endpoint, payload, timeout=None, **kwargs):
        try:
            response = self.session.post(
                self.base_url + endpoint,
                json=payload,
                timeout=timeout or self.request_timeout,
                allow_redirects=False,
                **kwargs
            )
        except requests.RequestException:
            response = None

        # Raise outside the handler to avoid leaking the original exception
        # through Python 3's implicit exception chaining.
        if response is None:
            raise CrawlingProcessException(
                "Error de comunicació amb la API d'i-DE"
            )

        renewed_jwt = response.headers.get('jwt')
        if renewed_jwt:
            self.session.headers['jwt'] = renewed_jwt
        return response

    def start(self):
        try:
            self.login()
            self.download_files()
        finally:
            self.session.close()

    def login(self):
        if not self.config.api_key:
            raise CrawlingLoginException("Cal configurar l'API-Key d'i-DE")

        self.session.headers.update({
            "API-Key": self.config.api_key,
            "User-Agent": "portal_agentes",
            "Portal": self.cod_portal,
        })
        login_auth = HTTPBasicAuth(self.config.usuari, self.config.contrasenya)

        try:
            res = self._post(
                "LoginAPI",
                {"codPortal": self.cod_portal},
                auth=login_auth,
                headers={"Accept": "application/json"},
            )
        except CrawlingProcessException:
            raise CrawlingLoginException(
                "Error de comunicació durant el login a la API d'i-DE"
            )

        if res.status_code != 200:
            raise CrawlingLoginException(
                "Error d'autenticació a la API d'i-DE (HTTP {})".format(
                    res.status_code
                )
            )

        try:
            res_obj = res.json()
        except ValueError:
            raise CrawlingLoginException("La resposta del login no és JSON")

        required_keys = ('jwt', 'nombreCookie', 'tokenSeguridad')
        if (
            not isinstance(res_obj, dict)
            or res_obj.get('codigo') != 'OK'
            or res_obj.get('descripcion') != 'OK'
            or not all(res_obj.get(key) for key in required_keys)
        ):
            raise CrawlingLoginException(
                "Login rebutjat o resposta incompleta de la API d'i-DE"
            )

        self.session.headers.update({
            "jwt": res.headers.get('jwt') or res_obj['jwt'],
            "NOMBRETOKEN": res_obj['nombreCookie'],
            "IDEAUTH": res_obj['tokenSeguridad'],
        })

    def download_files(self):
        info_type = "Pendientes Descargar" if self.config.pending_files_only else "Todos"
        process = self.process or ""
        inici, final = self.get_intervals()

        download_body = {
            "marcados": False,
            "mensajesFirmados": False,
            "filtros": {
                "fechaDesde": inici.strftime("%d/%m/%Y %H:%M:%S"),
                "fechaHasta": final.strftime("%d/%m/%Y %H:%M:%S"),
                "tipoInformacion": info_type,
                "proceso": process,
                "cups": "",
            }
        }

        res = self._post(
            "DescargarMensajesMasivosAPI", download_body,
            timeout=self.download_timeout,
        )
        self._check_download_response(res)
        self._validate_zip(res.content)
        self._save_zip(res.content)

    def _check_download_response(self, response):
        if response.status_code in (401, 403):
            raise CrawlingLoginException(
                "Accés rebutjat durant la descàrrega d'i-DE (HTTP {})".format(
                    response.status_code
                )
            )

        if response.status_code == 400:
            # i-DE returns UTF-8 text without always declaring the encoding.
            message = response.content.decode('utf-8', 'replace').strip()
            if message.startswith('No se han encontrado mensajes para descargar.'):
                raise NoResultsException("No hi ha missatges per descarregar")
            if re.match(
                u'El número de mensajes [(][0-9]*[)] supera el límite '
                u'permitido [(]1000[)][.]', message
            ):
                raise CrawlingProcessException(
                    "La consulta supera el límit de 1000 missatges d'i-DE. "
                    "Cal reduir els filtres de descàrrega."
                )

        if response.status_code != 200:
            # Do not include arbitrary server response bodies in ERP logs.
            raise CrawlingProcessException(
                "Error en la descàrrega d'i-DE (HTTP {})".format(
                    response.status_code
                )
            )

    def _validate_zip(self, content):
        invalid_zip = False
        has_files = False
        try:
            with zipfile.ZipFile(io.BytesIO(content), 'r') as archive:
                has_files = any(
                    not item.filename.endswith('/') for item in archive.infolist()
                )
                invalid_zip = archive.testzip() is not None
        except (zipfile.BadZipfile, RuntimeError, NotImplementedError,
                EOFError, zlib.error):
            invalid_zip = True

        if invalid_zip:
            raise CrawlingProcessException(
                "La resposta d'i-DE no és un ZIP vàlid o està corrupte"
            )
        if not has_files:
            raise NoResultsException("El ZIP s'ha descarregat buit")

    def _save_zip(self, content):
        temporary_path = None
        write_failed = False
        try:
            descriptor, temporary_path = tempfile.mkstemp(
                prefix='.ide-', suffix='.part',
                # Keep partial files outside the directory scanned by the importer.
                dir=os.path.dirname(os.path.dirname(self.target_filename)),
            )
            with os.fdopen(descriptor, 'wb') as output:
                output.write(content)
            os.rename(temporary_path, self.target_filename)
            temporary_path = None
        except (IOError, OSError):
            write_failed = True
        finally:
            if temporary_path is not None:
                try:
                    os.unlink(temporary_path)
                except OSError:
                    write_failed = True

        if write_failed:
            raise CrawlingProcessException("No s'ha pogut desar el ZIP d'i-DE")
