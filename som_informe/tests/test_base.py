# -*- coding: utf-8 -*-
"""
Base test case for som_informe tests.
"""
from destral import testing
from destral.transaction import Transaction


class BaseTestCase(testing.OOTestCase):
    """Base test case with common setup/teardown."""

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def _get_extractor_class(self, name):
        """Import and return an extractor class by name."""
        import importlib
        module = importlib.import_module(
            "som_informe.report.components.{0}.{0}".format(name)
        )
        return getattr(module, name)
