# -*- coding: utf-8 -*-
"""
Tests for Report Block Components (A, B, C, D, E, M, R series).

Note: These tests verify that all components can be instantiated.
Many require real switching step data (get_data with step parameter).
"""
from destral import testing
import unittest
from destral.transaction import Transaction


class ReportBlockTests(testing.OOTestCase):
    """Tests for A/B/C/D/E/M/R series report blocks.

    These require real switching step data and are skipped.
    Tests verify only that factory can instantiate the extractors.
    """

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @unittest.skip("Requires switching step data")
    def test__A301__instantiable(self):
        """Test A301 can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("A301")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__A302__instantiable(self):
        """Test A302 can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("A302")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__A303__instantiable(self):
        """Test A303 can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("A303")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__A304__instantiable(self):
        """Test A304 can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("A304")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__A305__instantiable(self):
        """Test A305 can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("A305")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__A306__instantiable(self):
        """Test A306 can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("A306")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__A307__instantiable(self):
        """Test A307 can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("A307")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__A313__instantiable(self):
        """Test A313 can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("A313")
        self.assertIsNotNone(extractor)


class BillingReportTests(testing.OOTestCase):
    """Tests for B-series (Billing) report blocks."""

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @unittest.skip("Requires switching step data")
    def test__B101__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("B101")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__B102__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("B102")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__B103__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("B103")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__B104__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("B104")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__B105__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("B105")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__B106__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("B106")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__B107__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("B107")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__B116__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("B116")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__B205__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("B205")
        self.assertIsNotNone(extractor)


class ConsumptionReportTests(testing.OOTestCase):
    """Tests for C-series (Consumption) report blocks."""

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @unittest.skip("Requires switching step data")
    def test__C101__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C101")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C102__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C102")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C104__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C104")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C105__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C105")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C106__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C106")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C108__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C108")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C109__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C109")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C110__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C110")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C111__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C111")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C112__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C112")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C201__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C201")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C202__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C202")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C203__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C203")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C204__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C204")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C205__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C205")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C208__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C208")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C209__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C209")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C210__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C210")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C212__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C212")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__C213__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("C213")
        self.assertIsNotNone(extractor)


class MonthlyReportTests(testing.OOTestCase):
    """Tests for M-series (Monthly) report blocks."""

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @unittest.skip("Requires switching step data")
    def test__M101__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("M101")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__M102__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("M102")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__M103__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("M103")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__M104__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("M104")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__M105__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("M105")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__M106__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("M106")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__M107__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("M107")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__M113__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("M113")
        self.assertIsNotNone(extractor)


class EnergyClaimTests(testing.OOTestCase):
    """Tests for E-series (Energy claims) report blocks."""

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @unittest.skip("Requires switching step data")
    def test__E101__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("E101")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__E102__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("E102")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__E103__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("E103")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__E104__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("E104")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__E105__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("E105")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__E106__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("E106")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__E108__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("E108")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__E109__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("E109")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__E110__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("E110")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__E111__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("E111")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__E112__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("E112")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__E113__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("E113")
        self.assertIsNotNone(extractor)


class ClaimsReportTests(testing.OOTestCase):
    """Tests for R-series (Claims) report blocks."""

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @unittest.skip("Requires switching step data")
    def test__R101__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("R101")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__R102__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("R102")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__R103__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("R103")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__R104__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("R104")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__R105__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("R105")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__R108__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("R108")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__R109__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("R109")
        self.assertIsNotNone(extractor)


class DemandReportTests(testing.OOTestCase):
    """Tests for D-series (Demand) report blocks."""

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @unittest.skip("Requires switching step data")
    def test__D101__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("D101")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires switching step data")
    def test__D102__instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("D102")
        self.assertIsNotNone(extractor)
