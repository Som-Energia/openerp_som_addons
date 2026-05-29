# -*- coding: utf-8 -*-
"""
Tests for wizard.create.technical.report
"""
from som_informe.tests.test_base import BaseTestCase


INVOICE_EXTRACTORS = [
    "InvoiceF1NG",
]


class WizardTests(BaseTestCase):
    """Tests for wizard.create.technical.report."""

    def test_wizard_exists(self):
        """Test wizard exists in pool."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        self.assertIsNotNone(wiz_obj)

    def test_invoice_instantiable(self):
        """Test factory can instantiate invoice extractors."""
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        for name in INVOICE_EXTRACTORS:
            extractor = wiz_obj.factory_metadata_extractor(name)
            self.assertIsInstance(extractor, object)
            self.assertTrue(
                hasattr(extractor, 'get_data'),
                msg="{} must have 'get_data' attribute".format(name)
            )
            self.assertTrue(
                callable(extractor.get_data),
                msg="{} 'get_data' must be callable".format(name)
            )
