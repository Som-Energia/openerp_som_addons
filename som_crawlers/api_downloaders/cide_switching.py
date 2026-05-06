# -*- coding: utf-8 -*-
import requests

from som_crawlers.api_downloaders.cide import Cide
from som_crawlers.models.exceptions import CrawlingProcessException, NoResultsException


def instance(_config):
    return CideSwitching(_config)


class CideSwitching(Cide):
    name = 'cide_switching'

    def start(self):
        self.login()
        self.download_files()

    def get_files_list(self):
        list_url = self.config.url_portal + "/switching"
        inici, final = self.get_intervals()

        params = {
            "limit": -1,
            "generation_date_from": inici.strftime("%Y-%m-%d"),
            "generation_date_to": final.strftime("%Y-%m-%d"),
            "type": ["OUT"],
        }

        if self.config.pending_files_only:
            params["downloaded"] = False

        try:
            res = requests.get(list_url, headers=self._auth_headers, params=params)
            if res.status_code != 200:
                raise CrawlingProcessException(
                    "Error en obtenir el llistat de switching. Codi d'estat: {}".format(
                        res.status_code
                    )
                )
            data = res.json()
            return data.get('results', [])
        except CrawlingProcessException as e:
            raise e
        except Exception as e:
            raise CrawlingProcessException("Error inesperat en obtenir el llistat: " + str(e))

    def download_files(self):
        files = self.get_files_list()

        if not files:
            raise NoResultsException("No s'han trobat fitxers de switching per descarregar")

        download_url = self.config.url_portal + "/switching/files"
        file_ids = [f['id'] for f in files if 'id' in f]

        if not file_ids:
            raise NoResultsException("No s'han trobat fitxers de switching amb identificador")

        params = {"id": file_ids}

        try:
            res = requests.get(download_url, headers=self._auth_headers, params=params)
            if res.status_code != 200:
                raise CrawlingProcessException(
                    "Error en la descàrrega de switching. Codi d'estat: {}".format(res.status_code)
                )
        except CrawlingProcessException as e:
            raise e
        except Exception as e:
            raise CrawlingProcessException("Error inesperat durant la descàrrega: " + str(e))

        # The API returns a signed URL that we need to follow
        try:
            response_data = res.json()
            if 'signedUrl' in response_data:
                self.download_file(response_data['signedUrl'])
            else:
                raise CrawlingProcessException("La resposta no conté signedUrl")
        except CrawlingProcessException as e:
            raise e
        except Exception as e:
            raise CrawlingProcessException("Error en processar la resposta: " + str(e))
