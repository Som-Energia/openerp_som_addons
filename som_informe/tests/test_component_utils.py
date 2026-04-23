# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class ComponentUtilsTests(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test__get_unit_magnitude_AE(self):
        from som_informe.report.components.component_utils import get_unit_magnitude

        result = get_unit_magnitude("AE")
        self.assertEqual(result, "kWh")

    def test__get_unit_magnitude_AS(self):
        from som_informe.report.components.component_utils import get_unit_magnitude

        result = get_unit_magnitude("AS")
        self.assertEqual(result, "kWh")

    def test__get_unit_magnitude_PM(self):
        from som_informe.report.components.component_utils import get_unit_magnitude

        result = get_unit_magnitude("PM")
        self.assertEqual(result, "kW")

    def test__get_unit_magnitude_EP(self):
        from som_informe.report.components.component_utils import get_unit_magnitude

        result = get_unit_magnitude("EP")
        self.assertEqual(result, "kW")

    def test__get_unit_magnitude_R1(self):
        from som_informe.report.components.component_utils import get_unit_magnitude

        result = get_unit_magnitude("R1")
        self.assertEqual(result, "kVarh")

    def test__get_unit_magnitude_R2(self):
        from som_informe.report.components.component_utils import get_unit_magnitude

        result = get_unit_magnitude("R2")
        self.assertEqual(result, "kVarh")

    def test__get_unit_magnitude_R3(self):
        from som_informe.report.components.component_utils import get_unit_magnitude

        result = get_unit_magnitude("R3")
        self.assertEqual(result, "kVarh")

    def test__get_unit_magnitude_R4(self):
        from som_informe.report.components.component_utils import get_unit_magnitude

        result = get_unit_magnitude("R4")
        self.assertEqual(result, "kVarh")

    def test__get_unit_magnitude_unknown(self):
        from som_informe.report.components.component_utils import get_unit_magnitude

        result = get_unit_magnitude("UNKNOWN")
        self.assertEqual(result, "eV")

    def test__dateformat_with_valid_date(self):
        from som_informe.report.components.component_utils import dateformat

        result = dateformat("2021-10-01")
        self.assertEqual(result, "01-10-2021")

    def test__dateformat_with_empty_string(self):
        from som_informe.report.components.component_utils import dateformat

        result = dateformat("")
        self.assertEqual(result, "")

    def test__dateformat_with_none(self):
        from som_informe.report.components.component_utils import dateformat

        result = dateformat(None)
        self.assertEqual(result, "")

    def test__dateformat_with_date_and_hours(self):
        from som_informe.report.components.component_utils import dateformat

        result = dateformat("2021-10-01 14:30:00", hours=True)
        self.assertEqual(result, "01-10-2021 14:30:00")

    def test__to_date_with_valid_date(self):
        from som_informe.report.components.component_utils import to_date

        result = to_date("2021-10-01")
        self.assertEqual(result.strftime("%Y-%m-%d"), "2021-10-01")

    def test__to_date_with_empty_string(self):
        from som_informe.report.components.component_utils import to_date

        result = to_date("")
        self.assertEqual(result, None)

    def test__to_date_with_none(self):
        from som_informe.report.components.component_utils import to_date

        result = to_date(None)
        self.assertEqual(result, None)

    def test__to_date_with_date_and_hours(self):
        from som_informe.report.components.component_utils import to_date

        result = to_date("2021-10-01 14:30:00", hours=True)
        self.assertEqual(result.strftime("%Y-%m-%d %H:%M:%S"), "2021-10-01 14:30:00")

    def test__to_string_with_valid_date(self):
        from som_informe.report.components.component_utils import to_string
        from datetime import datetime

        result = to_string(datetime(2021, 10, 1))
        self.assertEqual(result, "01-10-2021")

    def test__to_string_with_none(self):
        from som_informe.report.components.component_utils import to_string

        result = to_string(None)
        self.assertEqual(result, "")

    def test__to_string_with_date_and_hours(self):
        from som_informe.report.components.component_utils import to_string
        from datetime import datetime

        result = to_string(datetime(2021, 10, 1, 14, 30, 00), hours=True)
        self.assertEqual(result, "01-10-2021 14:30:00")

    def test__is_domestic_with_domestic_category(self):
        from som_informe.report.components.component_utils import is_domestic

        class MockCategory:
            def __init__(self, code):
                self.code = code

        class MockPol:
            def __init__(self):
                self.category_id = [MockCategory("DOM")]

        result = is_domestic(MockPol())
        self.assertEqual(result, True)

    def test__is_domestic_without_domestic_category(self):
        from som_informe.report.components.component_utils import is_domestic

        class MockCategory:
            def __init__(self, code):
                self.code = code

        class MockPol:
            def __init__(self):
                self.category_id = [MockCategory("EIE")]

        result = is_domestic(MockPol())
        self.assertEqual(result, False)

    def test__is_enterprise_with_enterprise_category(self):
        from som_informe.report.components.component_utils import is_enterprise

        class MockCategory:
            def __init__(self, code):
                self.code = code

        class MockPol:
            def __init__(self):
                self.category_id = [MockCategory("EIE")]

        result = is_enterprise(MockPol())
        self.assertEqual(result, True)

    def test__is_enterprise_with_domestic_category(self):
        from som_informe.report.components.component_utils import is_enterprise

        class MockCategory:
            def __init__(self, code):
                self.code = code

        class MockPol:
            def __init__(self):
                self.category_id = [MockCategory("DOM")]

        result = is_enterprise(MockPol())
        self.assertEqual(result, False)

    def test__has_category_with_matching_category(self):
        from som_informe.report.components.component_utils import has_category

        class MockCategory:
            def __init__(self, id):
                self.id = id

        class MockPol:
            def __init__(self):
                self.category_id = [MockCategory(1), MockCategory(2)]

        result = has_category(MockPol(), [2])
        self.assertEqual(result, True)

    def test__has_category_without_matching_category(self):
        from som_informe.report.components.component_utils import has_category

        class MockCategory:
            def __init__(self, id):
                self.id = id

        class MockPol:
            def __init__(self):
                self.category_id = [MockCategory(1), MockCategory(2)]

        result = has_category(MockPol(), [3])
        self.assertEqual(result, False)

    def test__get_invoice_lines_with_valid_data(self):
        from som_informe.report.components.component_utils import get_invoice_lines

        class MockLinia:
            def __init__(self, name, tipus):
                self.name = name
                self.tipus = tipus

        class MockInvoice:
            def __init__(self):
                self.linia_ids = [
                    MockLinia("P1", "energia"),
                    MockLinia("P2", "energia"),
                ]

        result = get_invoice_lines(MockInvoice(), "AE", "91")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "P1")

    def test__get_invoice_lines_with_PM_93_becomes_9392(self):
        from som_informe.report.components.component_utils import get_invoice_lines

        class MockLinia:
            def __init__(self, name, tipus):
                self.name = name
                self.tipus = tipus

        class MockInvoice:
            def __init__(self):
                self.linia_ids = [
                    MockLinia("P2", "potencia"),
                ]

        # PM with periode 93 should become 9392 and look for P2
        result = get_invoice_lines(MockInvoice(), "PM", "93")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "P2")

    def test__get_invoice_lines_with_unknown_magnitude(self):
        from som_informe.report.components.component_utils import get_invoice_lines

        class MockInvoice:
            def __init__(self):
                self.linia_ids = []

        result = get_invoice_lines(MockInvoice(), "UNKNOWN", "91")
        self.assertEqual(result, [])

    def test__get_invoice_lines_with_unknown_periode(self):
        from som_informe.report.components.component_utils import get_invoice_lines

        class MockInvoice:
            def __init__(self):
                self.linia_ids = []

        result = get_invoice_lines(MockInvoice(), "AE", "UNKNOWN")
        self.assertEqual(result, [])
