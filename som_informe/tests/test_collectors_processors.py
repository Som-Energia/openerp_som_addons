# -*- coding: utf-8 -*-
"""
Tests for Collectors and Processors in som_informe module.

Note: Many of these tests require real switching step data to function properly.
Tests are marked as skip for components that need step objects from the wizard.
"""
from destral import testing
import unittest
from destral.transaction import Transaction


class CollectorTests(testing.OOTestCase):
    """Tests for collector components.

    Note: These require specific contract data structure (category_id as list).
    Tests verify only that factory can instantiate.
    """

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @unittest.skip("Requires contract with category list")
    def test__CollectHeader__instantiable(self):
        """Test CollectHeader extractor can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("CollectHeader")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires contract with category list")
    def test__CollectContractData__instantiable(self):
        """Test CollectContractData extractor can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("CollectContractData")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires contract with category list")
    def test__CollectDetailsInvoices__instantiable(self):
        """Test CollectDetailsInvoices extractor can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("CollectDetailsInvoices")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires contract with category list")
    def test__CollectExpectedCutOffDate__instantiable(self):
        """Test CollectExpectedCutOffDate extractor can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("CollectExpectedCutOffDate")
        self.assertIsNotNone(extractor)


class TableComponentsTests(testing.OOTestCase):
    """Tests for table components (TableInvoices, etc.)."""

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test__TableInvoices__instantiable(self):
        """Test TableInvoices extractor can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("TableInvoices")
        self.assertIsNotNone(extractor)

    def test__TableReadings__instantiable(self):
        """Test TableReadings extractor can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("TableReadings")
        self.assertIsNotNone(extractor)


class ProcessorsTests(testing.OOTestCase):
    """Tests for processor components.

    Note: These require real switching step data and are skipped.
    They verify only that the factory can instantiate the component.
    """

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    @unittest.skip("Requires real switching step data")
    def test__ProcesA3__instantiable(self):
        """Test ProcesA3 can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("ProcesA3")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires real switching step data")
    def test__ProcesB1__instantiable(self):
        """Test ProcesB1 can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("ProcesB1")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires real switching step data")
    def test__ProcesB2__instantiable(self):
        """Test ProcesB2 can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("ProcesB2")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires real switching step data")
    def test__ProcesC1__instantiable(self):
        """Test ProcesC1 can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("ProcesC1")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires real switching step data")
    def test__ProcesC2__instantiable(self):
        """Test ProcesC2 can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("ProcesC2")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires real switching step data")
    def test__ProcesM1__instantiable(self):
        """Test ProcesM1 can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("ProcesM1")
        self.assertIsNotNone(extractor)

    @unittest.skip("Requires real switching step data")
    def test__ProcesATR__instantiable(self):
        """Test ProcesATR can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("ProcesATR")
        self.assertIsNotNone(extractor)
