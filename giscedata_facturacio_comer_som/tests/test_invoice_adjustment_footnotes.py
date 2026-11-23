# -*- coding: utf-8 -*-
"""Database-free tests of the actual TD builders and unchanged Mako components."""
import ast
import copy
import os
import unittest

from mako.lookup import TemplateLookup
from yamlns import namespace as ns


ADDON = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDERS = (
    "get_sub_component_energy_consumption_detail_td_active_data",
    "get_sub_component_energy_consumption_detail_td_surplus_data",
)


def load_report_methods():
    """Avoid importing the addon and its database-dependent OpenERP registry."""
    filename = os.path.join(ADDON, "giscedata_facturacio_report.py")
    with open(filename, "rb") as source:
        tree = ast.parse(source.read(), filename=filename)
    names = BUILDERS + ("adjust_readings_priority",)
    methods = [node for node in ast.walk(tree)
               if isinstance(node, ast.FunctionDef) and node.name in names]
    if sorted(node.name for node in methods) != sorted(names):
        raise AssertionError("Expected exactly one definition of each report method")
    tree.body = methods
    environment = {
        "_": lambda text: text,
        "get_lang_partner": lambda fact: "ca_ES",
        "te_autoconsum_amb_excedents": lambda fact, pol: True,
        "te_autoconsum_no_collectiu": lambda fact, pol: True,
        "te_autoconsum_collectiu": lambda fact, pol: False,
    }
    eval(compile(tree, filename, "exec"), environment)
    return type("ReportMethods", (object,),
                dict((name, environment[name]) for name in names))


ReportMethods = load_report_methods()


def readings_for(adjustments):
    return [
        ("P%s" % (index + 1), 100.0, 120.0, 20.0 + adjustment,
         "2026-01-01", "2026-01-31", u"real", u"real", adjustment, reason)
        for index, (adjustment, reason) in enumerate(adjustments)
    ]


class TestInvoiceAdjustmentFootnotes(unittest.TestCase):
    def setUp(self):
        self.report = ReportMethods()
        self.report.get_matrix_show_periods = lambda pol: [
            "P1", "P2", "P3", "P4", "P5", "P6",
        ]
        self.lookup = TemplateLookup(
            directories=[os.path.join(ADDON, "report", "components")],
            input_encoding="utf-8",
        )

    def build(self, builder, readings, missing_meter=False):
        inputs = [{} for unused in range(19)]
        inputs[4] = inputs[7] = {} if missing_meter else {"test-meter": readings}
        self.report.get_readings_data = lambda fact: inputs
        return getattr(self.report, builder)(None, None, ns(name="test-meter"))

    def render(self, component, **values):
        template = self.lookup.get_template("{0}/{0}.mako".format(component))
        return template.render_unicode(
            _=lambda text: text,
            formatLang=lambda value, digits=2: ("%.*f" % (digits, value)),
            **values
        )

    def assert_case(self, builder, adjustments, expected_reason):
        readings = readings_for(adjustments)
        original = copy.deepcopy(readings)
        data = self.build(builder, readings)
        self.assertEqual(data["adjust_reason"], expected_reason, (builder, adjustments))
        self.assertTrue(data["is_visible"])
        self.assertEqual(readings, original)
        for reading in readings:
            self.assertEqual(data[reading[0]], {
                "initial": reading[1], "final": reading[2], "total": reading[3],
            })
        self.assertEqual(data["initial_date"], "2026-01-01")
        self.assertEqual(data["final_date"], "2026-01-31")
        data["last_visible"] = True
        row = self.render("energy_consumption_detail_td_base", meter=ns(data))
        info = ns(
            adjust_reason=data["adjust_reason"], diari_factura_actual_eur=1.0,
            diari_factura_actual_kwh=2.0, dies_factura=31, lang="ca_ES",
            has_web=False, distri_name="Synthetic distributor",
        )
        note = self.render("energy_consumption_detail_td_info", id_info=info, col=False)
        self.assertEqual("<sup>(2)</sup>" in row, expected_reason is not False)
        note_texts = {
            "99": u"ajustos aplicats per la companyia distribuïdora.",
            "98": u"ajustos corresponents al balanç horari",
            "97": u"ajustos perquè les lectures informades",
        }
        for reason, text in note_texts.items():
            self.assertEqual(text in note, expected_reason == reason, (builder, reason))
        self.assertEqual("(2)" in note, expected_reason is not False)
        self.assertIn("100.000", row)
        self.assertIn("120.000", row)

    def test_nonzero_generic_reasons(self):
        for builder in BUILDERS:
            for reason in ("95", "99", "01"):
                for adjustment in (5, -5):
                    self.assert_case(builder, [(adjustment, reason)], "99")

    def test_special_reason_priority(self):
        cases = [
            (["98"], "98"), (["97"], "97"), (["96"], False),
            (["98", "97"], "98"), (["98", "95"], "99"),
            (["97", "95"], "99"), (["98", "97", "96", "95"], "99"),
        ]
        for builder in BUILDERS:
            for reasons, expected in cases:
                self.assert_case(builder, [(5, reason) for reason in reasons], expected)

    def test_nonzero_without_reason_has_no_fallback(self):
        for builder in BUILDERS:
            self.assert_case(builder, [(5, False)], False)

    def test_zero_reason_95_active_has_no_note_or_marker(self):
        self.assert_case(BUILDERS[0], [(0, "95"), (0.000, "95"), (0, "95")], False)

    def test_zero_reason_95_surplus_has_no_note_or_marker(self):
        self.assert_case(BUILDERS[1], [(0, "95"), (0.000, "95"), (0, "95")], False)

    def test_other_generic_reasons_on_zero_readings(self):
        for builder in BUILDERS:
            for reason in ("99", "01"):
                self.assert_case(builder, [(0, reason), (0.000, reason)], False)

    def test_offsetting_nonzero_periods_still_have_generic_note(self):
        for builder in BUILDERS:
            self.assert_case(builder, [(5, "95"), (-5, "95")], "99")

    def test_small_nonzero_adjustments_are_not_rounded_out(self):
        for builder in BUILDERS:
            for adjustment in (0.0001, -0.0001):
                self.assert_case(builder, [(adjustment, "95")], "99")

    def test_zero_generic_reason_does_not_override_special_reason(self):
        for builder in BUILDERS:
            for reason in ("98", "97"):
                self.assert_case(builder, [(0, "95"), (5, reason)], reason)
                without_reason = self.build(builder, readings_for([(0, False), (5, reason)]))
                with_reason = self.build(builder, readings_for([(0, "95"), (5, reason)]))
                self.assertEqual(with_reason, without_reason)

    def test_empty_and_missing_meter_readings_remain_invisible(self):
        for builder in BUILDERS:
            for missing_meter in (False, True):
                data = self.build(builder, [], missing_meter=missing_meter)
                self.assertFalse(data["is_visible"])
                self.assertIs(data["adjust_reason"], False)
                self.assertNotIn("P1", data)
                self.assertNotIn("initial_date", data)
                data["last_visible"] = True
                row = self.render("energy_consumption_detail_td_base", meter=ns(data))
                self.assertEqual(row.strip(), "")


if __name__ == "__main__":
    unittest.main()
