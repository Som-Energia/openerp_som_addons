# -*- coding: utf-8 -*-
"""
Tests for Invoice Extractors in som_informe module.
"""
import inspect
from som_informe.tests.test_base import BaseTestCase


INVOICE_EXTRACTORS = [
    "InvoiceF1NG",
    "InvoiceF1A",
    "InvoiceF1C",
    "InvoiceF1R",
    "InvoiceFE",
]


class InvoiceExtractorsTests(BaseTestCase):
    """Tests for InvoiceF1* extractor components."""

    def test_invoice_instantiable(self):
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

    def test_invoice_signature(self):
        """Test invoice extractors have expected signature: (cursor, uid, wiz, invoice, context)."""
        for name in INVOICE_EXTRACTORS:
            extractor_class = self._get_extractor_class(name)
            argspec = inspect.getargspec(extractor_class.get_data)
            params = argspec.args
            self.assertIn("cursor", params)
            self.assertIn("uid", params)
            self.assertIn("wiz", params)
            self.assertIn("invoice", params)


class ComponentUtilsTests(BaseTestCase):
    """Tests for component_utils helper functions."""

    def test_dateformat(self):
        from som_informe.report.components.component_utils import dateformat
        result = dateformat("2021-10-01")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_get_description(self):
        from som_informe.report.components.component_utils import get_description
        result = get_description("AE", "TABLA_43")
        self.assertIsInstance(result, (str, unicode, dict))

    def test_get_unit_magnitude(self):
        from som_informe.report.components.component_utils import get_unit_magnitude
        result = get_unit_magnitude("AE")
        self.assertIsInstance(result, (str, dict))
