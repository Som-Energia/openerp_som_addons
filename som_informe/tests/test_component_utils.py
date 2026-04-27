# -*- coding: utf-8 -*-
from destral import testing
from som_informe.report.components.component_utils import (
    get_unit_magnitude,
    get_invoice_lines,
    to_date,
    to_string,
    dateformat,
    is_domestic,
    is_enterprise,
    has_category,
    get_description,
)
from datetime import datetime


class MockCategory:
    def __init__(self, code=None, id=None):
        self.code = code
        self.id = id


class MockPol:
    def __init__(self, category_id):
        self.category_id = category_id


class MockLinia:
    def __init__(self, name, tipus):
        self.name = name
        self.tipus = tipus


class MockInvoice:
    def __init__(self, linia_ids):
        self.linia_ids = linia_ids


class TestGetUnitMagnitude(testing.OOTestCase):
    def test_get_unit_magnitude_AE(self):
        result = get_unit_magnitude("AE")
        self.assertEqual(result, "kWh")

    def test_get_unit_magnitude_AS(self):
        result = get_unit_magnitude("AS")
        self.assertEqual(result, "kWh")

    def test_get_unit_magnitude_PM(self):
        result = get_unit_magnitude("PM")
        self.assertEqual(result, "kW")

    def test_get_unit_magnitude_EP(self):
        result = get_unit_magnitude("EP")
        self.assertEqual(result, "kW")

    def test_get_unit_magnitude_R1(self):
        result = get_unit_magnitude("R1")
        self.assertEqual(result, "kVarh")

    def test_get_unit_magnitude_R2(self):
        result = get_unit_magnitude("R2")
        self.assertEqual(result, "kVarh")

    def test_get_unit_magnitude_R3(self):
        result = get_unit_magnitude("R3")
        self.assertEqual(result, "kVarh")

    def test_get_unit_magnitude_R4(self):
        result = get_unit_magnitude("R4")
        self.assertEqual(result, "kVarh")

    def test_get_unit_magnitude_unknown(self):
        result = get_unit_magnitude("UNKNOWN")
        self.assertEqual(result, "eV")


class TestDateformat(testing.OOTestCase):
    def test_dateformat_with_valid_date(self):
        result = dateformat("2021-10-01")
        self.assertEqual(result, "01-10-2021")

    def test_dateformat_with_empty_string(self):
        result = dateformat("")
        self.assertEqual(result, "")

    def test_dateformat_with_none(self):
        result = dateformat(None)
        self.assertEqual(result, "")

    def test_dateformat_with_date_and_hours(self):
        result = dateformat("2021-10-01 14:30:00", hours=True)
        self.assertEqual(result, "01-10-2021 14:30:00")


class TestToDate(testing.OOTestCase):
    def test_to_date_with_valid_date(self):
        result = to_date("2021-10-01")
        self.assertEqual(result.strftime("%Y-%m-%d"), "2021-10-01")

    def test_to_date_with_empty_string(self):
        result = to_date("")
        self.assertEqual(result, None)

    def test_to_date_with_none(self):
        result = to_date(None)
        self.assertEqual(result, None)

    def test_to_date_with_date_and_hours(self):
        result = to_date("2021-10-01 14:30:00", hours=True)
        self.assertEqual(result.strftime("%Y-%m-%d %H:%M:%S"), "2021-10-01 14:30:00")


class TestToString(testing.OOTestCase):
    def test_to_string_with_valid_date(self):
        result = to_string(datetime(2021, 10, 1))
        self.assertEqual(result, "01-10-2021")

    def test_to_string_with_none(self):
        result = to_string(None)
        self.assertEqual(result, "")

    def test_to_string_with_date_and_hours(self):
        result = to_string(datetime(2021, 10, 1, 14, 30, 00), hours=True)
        self.assertEqual(result, "01-10-2021 14:30:00")


class TestIsDomestic(testing.OOTestCase):
    def test_is_domestic_with_domestic_category(self):
        pol = MockPol([MockCategory(code="DOM")])
        result = is_domestic(pol)
        self.assertEqual(result, True)

    def test_is_domestic_without_domestic_category(self):
        pol = MockPol([MockCategory(code="EIE")])
        result = is_domestic(pol)
        self.assertEqual(result, False)


class TestIsEnterprise(testing.OOTestCase):
    def test_is_enterprise_with_enterprise_category(self):
        pol = MockPol([MockCategory(code="EIE")])
        result = is_enterprise(pol)
        self.assertEqual(result, True)

    def test_is_enterprise_with_domestic_category(self):
        pol = MockPol([MockCategory(code="DOM")])
        result = is_enterprise(pol)
        self.assertEqual(result, False)


class TestHasCategory(testing.OOTestCase):
    def test_has_category_with_matching_category(self):
        pol = MockPol([MockCategory(id=1), MockCategory(id=2)])
        result = has_category(pol, [2])
        self.assertEqual(result, True)

    def test_has_category_without_matching_category(self):
        pol = MockPol([MockCategory(id=1), MockCategory(id=2)])
        result = has_category(pol, [3])
        self.assertEqual(result, False)


class TestGetInvoiceLines(testing.OOTestCase):
    def test_get_invoice_lines_with_valid_data(self):
        invoice = MockInvoice([
            MockLinia("P1", "energia"),
            MockLinia("P2", "energia"),
        ])
        result = get_invoice_lines(invoice, "AE", "91")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "P1")

    def test_get_invoice_lines_with_PM_93_becomes_9392(self):
        invoice = MockInvoice([
            MockLinia("P2", "potencia"),
        ])
        result = get_invoice_lines(invoice, "PM", "93")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "P2")

    def test_get_invoice_lines_with_unknown_magnitude(self):
        invoice = MockInvoice([])
        result = get_invoice_lines(invoice, "UNKNOWN", "91")
        self.assertEqual(result, [])

    def test_get_invoice_lines_with_unknown_periode(self):
        invoice = MockInvoice([])
        result = get_invoice_lines(invoice, "AE", "UNKNOWN")
        self.assertEqual(result, [])


class TestGetDescription(testing.OOTestCase):
    def test_get_description_with_valid_key(self):
        result = get_description("01", "tarifaATR")
        self.assertIsNotNone(result)

    def test_get_description_with_invalid_key_on_error_false(self):
        result = get_description("INVALID_KEY", "tarifaATR", on_error_return_false=False)
        self.assertIn("ERROR", result)
        self.assertIn("INVALID_KEY", result)

    def test_get_description_with_invalid_key_on_error_true(self):
        result = get_description("INVALID_KEY", "tarifaATR", on_error_return_false=True)
        self.assertEqual(result, False)
