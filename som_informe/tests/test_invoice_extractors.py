# -*- coding: utf-8 -*-
"""
Tests for Invoice Extractors in som_informe module.

Tests all invoice type extractors: InvoiceF1NG, InvoiceF1A, InvoiceF1C, InvoiceF1R, InvoiceFE
"""
from destral import testing
from destral.transaction import Transaction


class InvoiceExtractorsTests(testing.OOTestCase):
    """Tests for InvoiceF1* extractor components."""

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test__InvoiceF1NG__instantiable(self):
        """Test InvoiceF1NG extractor can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("InvoiceF1NG")
        self.assertIsNotNone(extractor)

    def test__InvoiceF1A__instantiable(self):
        """Test InvoiceF1A extractor can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("InvoiceF1A")
        self.assertIsNotNone(extractor)

    def test__InvoiceF1C__instantiable(self):
        """Test InvoiceF1C extractor can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("InvoiceF1C")
        self.assertIsNotNone(extractor)

    def test__InvoiceF1R__instantiable(self):
        """Test InvoiceF1R extractor can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("InvoiceF1R")
        self.assertIsNotNone(extractor)

    def test__InvoiceFE__instantiable(self):
        """Test InvoiceFE extractor can be instantiated."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        extractor = wiz_obj.factory_metadata_extractor("InvoiceFE")
        self.assertIsNotNone(extractor)


class ComponentUtilsTests(testing.OOTestCase):
    """Tests for component_utils helper functions."""

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test__component_utils__dateformat(self):
        """Test dateformat utility function."""
        from som_informe.report.components.component_utils import dateformat

        # Test with date object
        result = dateformat("2021-10-01")
        self.assertIsNotNone(result)

    def test__component_utils__get_description(self):
        """Test get_description utility function."""
        from som_informe.report.components.component_utils import get_description

        # Test getting description from a table
        result = get_description("AE", "TABLA_43")
        self.assertIsNotNone(result)

    def test__component_utils__get_unit_magnitude(self):
        """Test get_unit_magnitude utility function."""
        from som_informe.report.components.component_utils import get_unit_magnitude

        result = get_unit_magnitude("AE")
        self.assertIsNotNone(result)
