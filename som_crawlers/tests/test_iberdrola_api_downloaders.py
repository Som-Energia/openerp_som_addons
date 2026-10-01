# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import datetime

import mock
from destral import testing

from som_crawlers.api_downloaders import get_instance_from_api_module
from som_crawlers.api_downloaders.iberdrola import Iberdrola
from som_crawlers.models.exceptions import NoResultsException


class IberdrolaConfig(object):
    url_portal = "https://wwwd.i-de.es/pwelconq/services/arq/"
    usuari = "api-user"
    contrasenya = "api-password"
    pending_files_only = True
    days_of_margin = 7


class IberdrolaApiDownloadersTests(testing.OOTestCase):
    def test_factory_accepts_optional_downloader_arguments(self):
        downloader = get_instance_from_api_module(
            IberdrolaConfig(), "iberdrola", process="c2", retailer_cdos="0762"
        )

        self.assertEqual(downloader.name, "iberdrola_c2")

    @mock.patch("som_crawlers.api_downloaders.iberdrola.requests.post")
    def test_login_uses_documented_headers(self, request_post):
        request_post.return_value = mock.Mock(status_code=200)
        request_post.return_value.json.return_value = {
            "descripcion": "OK",
            "jwt": "jwt-token",
            "nombreCookie": "token-name",
            "tokenSeguridad": "security-token",
        }
        downloader = Iberdrola(IberdrolaConfig())

        downloader.login()

        request_post.assert_called_once_with(
            "https://wwwd.i-de.es/pwelconq/services/arq/LoginAPI",
            json={"codPortal": "0021"},
            auth=mock.ANY,
            headers={"Accept": "application/json", "Portal": "0021"},
        )

    @mock.patch("som_crawlers.api_downloaders.iberdrola.requests.post")
    def test_download_uses_documented_payload(self, request_post):
        request_post.return_value = mock.Mock(
            status_code=200,
            text="PK",
            content=(
                b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00\x00"
            ),
        )
        downloader = Iberdrola(IberdrolaConfig())
        downloader._auth_headers = {"Portal": "0021"}
        downloader.get_intervals = mock.Mock(
            return_value=(datetime(2025, 12, 1), datetime(2025, 12, 31))
        )

        with self.assertRaises(NoResultsException):
            downloader.download_files()

        request_post.assert_called_once_with(
            "https://wwwd.i-de.es/pwelconq/services/arq/DescargarMensajesMasivos",
            json={
                "loginUsuario": "api-user",
                "firmado": False,
                "marcados": False,
                "filtros": {
                    "fechaDesde": "01/12/2025 00:00:00",
                    "fechaHasta": "31/12/2025 00:00:00",
                    "tipoInformacion": "Pendientes Descargar",
                    "proceso": "",
                    "cups": "",
                },
            },
            headers={"Portal": "0021"},
        )
