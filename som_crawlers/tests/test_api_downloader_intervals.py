# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import datetime, timedelta

import mock
from destral import testing

from som_crawlers.api_downloaders import BaseApiDownloader
from som_crawlers.api_downloaders.anselmo import Anselmo
from som_crawlers.api_downloaders.anselmo_f1 import Anselmo_F1
from som_crawlers.api_downloaders.cide import Cide
from som_crawlers.api_downloaders.cide_f1 import CideF1
from som_crawlers.api_downloaders.cide_switching import CideSwitching
from som_crawlers.api_downloaders.conquense import Conquense
from som_crawlers.api_downloaders.conquense_f1 import Conquense_F1
from som_crawlers.api_downloaders.iberdrola import Iberdrola
from som_crawlers.api_downloaders.iberdrola_f1 import Iberdrola_F1


class ApiDownloaderIntervalsTests(testing.OOTestCase):
    def setUp(self):
        # get_intervals only needs the configuration; do not create output
        # directories or HTTP sessions when testing this pure date calculation.
        self.downloader = BaseApiDownloader.__new__(BaseApiDownloader)
        self.downloader.config = mock.Mock(days_of_margin=7)

    @mock.patch('som_crawlers.api_downloaders.datetime')
    def test_interval_uses_current_time_once_and_preserves_time_of_day(self, clock):
        now = datetime(2026, 11, 26, 14, 30, 45, 123456)
        clock.now.return_value = now

        start, end = self.downloader.get_intervals()

        self.assertEqual(end, now)
        self.assertEqual(start, datetime(2026, 11, 19, 14, 30, 45, 123456))
        clock.now.assert_called_once_with()

    @mock.patch('som_crawlers.api_downloaders.datetime')
    def test_interval_does_not_depend_on_hostname(self, clock):
        now = datetime(2027, 2, 15, 8, 15, 0)
        clock.now.return_value = now
        for hostname in ('erp01', 'erpwork05', 'staging', 'new-production-server'):
            with mock.patch('socket.gethostname', return_value=hostname) as get_hostname:
                start, end = self.downloader.get_intervals()

            self.assertEqual(end, now)
            self.assertEqual(start, now - timedelta(days=7))
            self.assertFalse(get_hostname.called)

    @mock.patch('som_crawlers.api_downloaders.datetime')
    def test_interval_respects_configured_margin_across_year_boundary(self, clock):
        clock.now.return_value = datetime(2027, 1, 3, 10, 20, 30)
        self.downloader.config.days_of_margin = 5

        start, end = self.downloader.get_intervals()

        self.assertEqual(start, datetime(2026, 12, 29, 10, 20, 30))
        self.assertEqual(end, datetime(2027, 1, 3, 10, 20, 30))

    @mock.patch('som_crawlers.api_downloaders.datetime')
    def test_zero_margin_returns_current_instant(self, clock):
        clock.now.return_value = datetime(2027, 1, 3, 10, 20, 30)
        self.downloader.config.days_of_margin = 0

        start, end = self.downloader.get_intervals()

        self.assertEqual(start, clock.now.return_value)
        self.assertEqual(end, clock.now.return_value)

    @mock.patch('som_crawlers.api_downloaders.datetime')
    def test_ide_and_cide_downloaders_share_current_date_rule(self, clock):
        now = datetime(2027, 3, 2, 9, 45, 0)
        clock.now.return_value = now
        for downloader_class in (
            Iberdrola, Iberdrola_F1, Anselmo, Anselmo_F1, Conquense, Conquense_F1,
            Cide, CideF1, CideSwitching,
        ):
            downloader = downloader_class.__new__(downloader_class)
            downloader.config = self.downloader.config

            self.assertEqual(downloader.get_intervals(), (now - timedelta(days=7), now))
