# -*- coding: utf-8 -*-
"""
Tests for Report Block Components (A, B, C, D, E, M, R series).
"""
import inspect
from som_informe.tests.test_base import BaseTestCase


A_SERIES = ["A301", "A302", "A303", "A304", "A305", "A306", "A307", "A313"]
B_SERIES = ["B101", "B102", "B103", "B104", "B105", "B106", "B107", "B116", "B205"]
C_SERIES = [
    "C101", "C102", "C104", "C105", "C106", "C108", "C109", "C110",
    "C111", "C112", "C201", "C202", "C203", "C204", "C205", "C208",
    "C209", "C210", "C212", "C213",
]
D_SERIES = ["D101", "D102"]
E_SERIES = ["E101", "E102", "E103", "E104", "E105",
            "E106", "E108", "E109", "E110", "E111", "E112", "E113"]
M_SERIES = ["M101", "M102", "M103", "M104", "M105", "M106", "M107", "M113"]
R_SERIES = ["R101", "R102", "R103", "R104", "R105", "R108", "R109"]


def _test_extractor_instantiable(test_case, wiz_obj, name):
    extractor = wiz_obj.factory_metadata_extractor(name)
    test_case.assertIsInstance(extractor, object)
    test_case.assertTrue(
        hasattr(extractor, 'get_data'),
        msg="{} must have 'get_data' attribute".format(name)
    )
    test_case.assertTrue(
        callable(extractor.get_data),
        msg="{} 'get_data' must be callable".format(name)
    )


def _test_signature(test_case, name, required_params):
    extractor_class = test_case._get_extractor_class(name)
    argspec = inspect.getargspec(extractor_class.get_data)
    params = argspec.args
    for param in required_params:
        test_case.assertIn(param, params, msg="{} must have '{}' param".format(name, param))


class ASeriesTests(BaseTestCase):
    """Tests for A-series report blocks."""

    def test_a_series_instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        for name in A_SERIES:
            _test_extractor_instantiable(self, wiz_obj, name)

    def test_a_series_signature(self):
        for name in A_SERIES:
            _test_signature(self, name, ["wiz", "cursor", "uid", "step"])


class BSeriesTests(BaseTestCase):
    """Tests for B-series (Billing) report blocks."""

    def test_b_series_instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        for name in B_SERIES:
            _test_extractor_instantiable(self, wiz_obj, name)

    def test_b_series_signature(self):
        for name in B_SERIES:
            _test_signature(self, name, ["wiz", "cursor", "uid", "step"])


class CSeriesTests(BaseTestCase):
    """Tests for C-series (Consumption) report blocks."""

    def test_c_series_instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        for name in C_SERIES:
            _test_extractor_instantiable(self, wiz_obj, name)

    def test_c_series_signature(self):
        for name in C_SERIES:
            _test_signature(self, name, ["wiz", "cursor", "uid", "step"])


class DSeriesTests(BaseTestCase):
    """Tests for D-series (Demand) report blocks."""

    def test_d_series_instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        for name in D_SERIES:
            _test_extractor_instantiable(self, wiz_obj, name)

    def test_d_series_signature(self):
        for name in D_SERIES:
            _test_signature(self, name, ["wiz", "cursor", "uid", "step"])


class ESeriesTests(BaseTestCase):
    """Tests for E-series (Energy claims) report blocks."""

    def test_e_series_instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        for name in E_SERIES:
            _test_extractor_instantiable(self, wiz_obj, name)

    def test_e_series_signature(self):
        for name in E_SERIES:
            _test_signature(self, name, ["wiz", "cursor", "uid", "step"])


class MSeriesTests(BaseTestCase):
    """Tests for M-series (Monthly) report blocks."""

    def test_m_series_instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        for name in M_SERIES:
            _test_extractor_instantiable(self, wiz_obj, name)

    def test_m_series_signature(self):
        for name in M_SERIES:
            _test_signature(self, name, ["wiz", "cursor", "uid", "step"])


class RSeriesTests(BaseTestCase):
    """Tests for R-series (Claims) report blocks."""

    def test_r_series_instantiable(self):
        wiz_obj = self.openerp.pool.get("wizard.create.technical.report")
        for name in R_SERIES:
            _test_extractor_instantiable(self, wiz_obj, name)

    def test_r_series_signature(self):
        for name in R_SERIES:
            _test_signature(self, name, ["wiz", "cursor", "uid", "step"])
