# -*- coding: utf-8 -*-
import requests
from requests.auth import HTTPBasicAuth

from som_crawlers.api_downloaders import BaseApiDownloader
from som_crawlers.models.exceptions import (
    CrawlingProcessException, CrawlingLoginException, NoResultsException)


class Cide(BaseApiDownloader):
    name = 'cide'
    cod_portal = '0023'

    def login(self):
        token_url = self.config.url_portal + "/token"

        try:
            res = requests.get(
                token_url,
                auth=HTTPBasicAuth(self.config.usuari, self.config.contrasenya)
            )
            if res.status_code != 200:
                raise CrawlingLoginException(
                    "Error d'autenticació a la API. Codi d'estat: {}".format(res.status_code)
                )

            res_obj = res.json()
            if 'token' not in res_obj:
                raise CrawlingLoginException(
                    "Error d'autenticació a la API. No s'ha rebut el token."
                )
        except CrawlingLoginException as e:
            raise e
        except Exception as e:
            raise CrawlingLoginException("Error inesperat durant el login: " + str(e))

        self._auth_headers = {
            "Authorization": "Bearer " + res_obj["token"],
        }

    def download_file(self, signed_url):
        res = requests.get(signed_url)
        if res.status_code != 200:
            raise CrawlingProcessException(
                "Error en descarregar des de l'URL signat. Codi: {}".format(res.status_code)
            )

        if len(res.content) == 0:
            raise NoResultsException("S'ha descarregat un fitxer buit")

        with open(self.target_filename, "wb") as f:
            f.write(res.content)

    def download_files(self):
        raise NotImplementedError("Subclasses must implement download_files()")


def instance(_config):
    return Cide(_config)
