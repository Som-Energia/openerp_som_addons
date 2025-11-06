# -*- coding: utf-8 -*-
import io
import zipfile
import requests
from requests.auth import HTTPBasicAuth

from som_crawlers.api_downloaders import BaseApiDownloader
from som_crawlers.models.exceptions import (
    CrawlingProcessException, CrawlingLoginException, NoResultsException)


def is_empty_zip(bytes_zip):
    bio = io.BytesIO(bytes_zip)
    with zipfile.ZipFile(bio, 'r') as zf:
        return len(zf.namelist()) == 0


def instance(_config):
    return Iberdrola(_config)


class Iberdrola(BaseApiDownloader):
    name = 'iberdrola'
    cod_portal = '0021'
    process = None

    def start(self):
        self.login()
        self.download_files()

    def login(self):
        login_url = self.config.url_portal + "LoginAPI"
        login_auth = HTTPBasicAuth(self.config.usuari, self.config.contrasenya)
        login_body = {"codPortal": self.cod_portal}

        try:
            res = requests.post(login_url, json=login_body, auth=login_auth)
            if res.status_code != 200 or res.json().get("descripcion") != "OK":
                raise CrawlingLoginException(
                    "Error d'autenticació a la API. Verifiqui usuari i contrasenya!"
                )
        except CrawlingLoginException as e:
            raise e
        except Exception as e:
            raise CrawlingLoginException("Error inesperat durant el login: " + str(e))

        res_obj = res.json()
        self._auth_headers = {
            "jwt": res_obj["jwt"],
            "Portal": self.cod_portal,
            "NOMBRETOKEN": res_obj["nombreCookie"],
            "IDEAUTH": res_obj["tokenSeguridad"],
        }

    def download_files(self):
        download_url = self.config.url_portal + "DescargarMensajesMasivos"

        info_type = "Pendientes Descargar" if self.config.pending_files_only else "Todos"
        process = self.process or ""
        inici, final = self.get_intervals()

        download_body = {
            "loginUsuario": self.config.usuari,
            "marcados": True,  # this mark the files as downloaded
            "firmados": False,
            "filtros": {
                "fechaDesde": inici.strftime("%d/%m/%Y %H:%M:%S"),
                "fechaHasta": final.strftime("%d/%m/%Y %H:%M:%S"),
                "tipoInformacion": info_type,
                "proceso": process,
                "cups": "",
            }
        }

        res = requests.post(download_url, json=download_body, headers=self._auth_headers)
        if res.status_code != 200 or res.text[:2] != 'PK':
            raise CrawlingProcessException("Error en la descàrrega del ZIP")

        if is_empty_zip(res.content):
            raise NoResultsException("El ZIP d'ha descarregat buit")

        with open(self.target_filename, "wb") as f:
            f.write(res.content)
