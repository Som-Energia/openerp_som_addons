# -*- coding: utf-8 -*-
"""
Tests for Collectors and Processors in som_informe module.
"""
import inspect
from som_informe.tests.test_base import BaseTestCase


COLLECTORS = [
    "CollectHeader",
    "CollectContractData",
    "CollectDetailsInvoices",
    "CollectExpectedCutOffDate",
]

TABLES = [
    "TableInvoices",
    "TableReadings",
]

PROCESSORS = [
    "ProcesA3",
    "ProcesB1",
    "ProcesB2",
    "ProcesC1",
    "ProcesC2",
    "ProcesM1",
    "ProcesATR",
]


class CollectorTests(BaseTestCase):
    """Tests for collector components."""

    def test_collector_instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        for name in COLLECTORS:
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

    def test_collector_signature(self):
        """Test collectors have expected signature: (cursor, uid, wiz, context)."""
        for name in COLLECTORS:
            extractor_class = self._get_extractor_class(name)
            argspec = inspect.getargspec(extractor_class.get_data)
            params = argspec.args
            self.assertIn("cursor", params)
            self.assertIn("uid", params)
            self.assertIn("wiz", params)
            self.assertIn("context", params)


class TableComponentsTests(BaseTestCase):
    """Tests for table components."""

    def test_table_instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        for name in TABLES:
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

    def test_table_signature(self):
        """Test tables have expected signature: (cursor, uid, wiz, invoice_ids, context)."""
        for name in TABLES:
            extractor_class = self._get_extractor_class(name)
            argspec = inspect.getargspec(extractor_class.get_data)
            params = argspec.args
            self.assertIn("cursor", params)
            self.assertIn("uid", params)
            self.assertIn("wiz", params)
            self.assertIn("invoice_ids", params)


class ProcessorTests(BaseTestCase):
    """Tests for processor components."""

    def test_processor_instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        for name in PROCESSORS:
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

    def test_processor_signature(self):
        """Test processors have expected signature: (wiz, cursor, uid, step)."""
        for name in PROCESSORS:
            extractor_class = self._get_extractor_class(name)
            argspec = inspect.getargspec(extractor_class.get_data)
            params = argspec.args
            self.assertIn("wiz", params)
            self.assertIn("cursor", params)
            self.assertIn("uid", params)
            self.assertIn("step", params)
