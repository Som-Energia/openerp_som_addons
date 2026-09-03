# -*- coding: utf-8 -*-
from datetime import datetime

import mock
from destral import testing

from som_crawlers.api_downloaders.cide import (
    Cide,
    DOWNLOAD_REQUEST_TIMEOUT,
    REQUEST_TIMEOUT,
)
from som_crawlers.api_downloaders.cide_f1 import CideF1
from som_crawlers.api_downloaders.cide_switching import CideSwitching
from som_crawlers.models.exceptions import CrawlingProcessException


class CideConfig(object):
    url_portal = "https://cide.example/api"
    usuari = "user"
    contrasenya = "password"
    pending_files_only = False


class CideApiDownloadersTests(testing.OOTestCase):
    def build_downloader(self, downloader_class):
        downloader = downloader_class(CideConfig(), retailer_cdos="0762")
        downloader._auth_headers = {"Authorization": "Bearer token"}
        return downloader

    def response(self, data=None, content="zip content"):
        response = mock.Mock(status_code=200, content=content)
        response.json.return_value = data or {}
        return response

    def test_requires_retailer_cdos(self):
        with self.assertRaises(CrawlingProcessException):
            Cide(CideConfig())

    @mock.patch("som_crawlers.api_downloaders.cide.requests.get")
    def test_login_does_not_send_retailer_cdos(self, request_get):
        request_get.return_value = self.response({"token": "token"})
        downloader = self.build_downloader(Cide)

        downloader.login()

        request_get.assert_called_once_with(
            "https://cide.example/api/token",
            auth=mock.ANY,
            timeout=REQUEST_TIMEOUT,
        )

    @mock.patch("som_crawlers.api_downloaders.cide_f1.requests.get")
    def test_f1_list_sends_retailer_cdos(self, request_get):
        request_get.return_value = self.response({"results": []})
        downloader = self.build_downloader(CideF1)
        downloader.get_intervals = mock.Mock(
            return_value=(datetime(2026, 9, 1), datetime(2026, 9, 3))
        )

        downloader.get_files_list()

        request_get.assert_called_once_with(
            "https://cide.example/api/invoices",
            headers=downloader._auth_headers,
            params={
                "limit": -1,
                "document_type": "F1",
                "generation_date_from": "2026-09-01",
                "generation_date_to": "2026-09-03",
                "retailer_cdos": "0762",
            },
            timeout=REQUEST_TIMEOUT,
        )

    @mock.patch("som_crawlers.api_downloaders.cide_f1.requests.get")
    def test_f1_download_sends_retailer_cdos(self, request_get):
        request_get.return_value = self.response({"signedUrl": "https://files.example/f1.zip"})
        downloader = self.build_downloader(CideF1)
        downloader.get_files_list = mock.Mock(return_value=[{"id": 1}, {"id": 2}])
        downloader.download_file = mock.Mock()

        downloader.download_files()

        request_get.assert_called_once_with(
            "https://cide.example/api/invoices/files",
            headers=downloader._auth_headers,
            params={"file_id": [1, 2], "retailer_cdos": "0762"},
            timeout=REQUEST_TIMEOUT,
        )

    @mock.patch("som_crawlers.api_downloaders.cide_switching.requests.get")
    def test_switching_list_sends_retailer_cdos(self, request_get):
        request_get.return_value = self.response({"results": []})
        downloader = self.build_downloader(CideSwitching)
        downloader.get_intervals = mock.Mock(
            return_value=(datetime(2026, 9, 1), datetime(2026, 9, 3))
        )

        downloader.get_files_list()

        request_get.assert_called_once_with(
            "https://cide.example/api/switching",
            headers=downloader._auth_headers,
            params={
                "limit": -1,
                "generation_date_from": "2026-09-01",
                "generation_date_to": "2026-09-03",
                "type": ["OUT"],
                "retailer_cdos": "0762",
            },
            timeout=REQUEST_TIMEOUT,
        )

    @mock.patch("som_crawlers.api_downloaders.cide_switching.requests.get")
    def test_switching_download_sends_retailer_cdos(self, request_get):
        request_get.return_value = self.response(
            {"signedUrl": "https://files.example/switching.zip"}
        )
        downloader = self.build_downloader(CideSwitching)
        downloader.get_files_list = mock.Mock(return_value=[{"id": 3}])
        downloader.download_file = mock.Mock()

        downloader.download_files()

        request_get.assert_called_once_with(
            "https://cide.example/api/switching/files",
            headers=downloader._auth_headers,
            params={"file_id": [3], "retailer_cdos": "0762"},
            timeout=REQUEST_TIMEOUT,
        )

    @mock.patch("__builtin__.open", new_callable=mock.mock_open)
    @mock.patch("som_crawlers.api_downloaders.cide.requests.get")
    def test_signed_url_does_not_send_retailer_cdos(self, request_get, _open):
        request_get.return_value = self.response()
        downloader = self.build_downloader(Cide)
        downloader.target_filename = "/tmp/cide.zip"

        downloader.download_file("https://files.example/file.zip")

        request_get.assert_called_once_with(
            "https://files.example/file.zip", timeout=DOWNLOAD_REQUEST_TIMEOUT
        )
