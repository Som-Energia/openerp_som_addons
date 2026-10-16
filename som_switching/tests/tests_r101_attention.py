# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from ast import literal_eval
from destral.testing import OOTestCaseWithCursor
from giscedata_switching.tests.common_tests import TestSwitchingImport
from gestionatr.defs import TABLA_87
from osv import osv


class TestR101Attention(OOTestCaseWithCursor, TestSwitchingImport):
    def setUp(self):
        super(TestR101Attention, self).setUp()
        self.switch(self.txn, "comer")
        self.contract_id = self.get_contract_id(self.txn)
        self.wizard = self.openerp.pool.get("wizard.subtype.r1")
        self.switching = self.openerp.pool.get("giscedata.switching")
        self.atc = self.openerp.pool.get("giscedata.atc")

    def subtype_id(self, code):
        return self.openerp.pool.get("giscedata.subtipus.reclamacio").search(
            self.cursor, self.uid, [("name", "=", code)]
        )[0]

    def prepare_atc_r1_wizard(self, subtype="001", values=None):
        context = {"active_ids": [self.contract_id], "from_model": "giscedata.polissa"}
        atc_wizard = self.openerp.pool.get("wizard.create.atc.from.polissa")
        wizard_id = atc_wizard.create(
            self.cursor, self.uid, {"subtipus_id": self.subtype_id(subtype)}, context=context
        )
        atc_wizard.create_atc_case(
            self.cursor, self.uid, [wizard_id], "giscedata.polissa", context=context
        )
        action = atc_wizard.open_r1_wizard(
            self.cursor, self.uid, [wizard_id], context=context
        )
        context = action["context"]
        generate_wizard = self.openerp.pool.get(action["res_model"])
        wizard_id = generate_wizard.create(self.cursor, self.uid, {}, context=context)
        action = generate_wizard.generate_r1(
            self.cursor, self.uid, [wizard_id], context=context
        )
        context = action["context"]
        atc_id = context["extra_values"]["ref_id"][0]
        create_wizard = self.openerp.pool.get(action["res_model"])
        wizard_id = create_wizard.create(self.cursor, self.uid, {}, context=context)
        action = create_wizard.action_subtype_fields_view(
            self.cursor, self.uid, [wizard_id], context=context
        )
        context.update(literal_eval(action["context"]))
        self.assertEqual(action["res_model"], "wizard.subtype.r1")
        wizard_values = {"comentaris": "TEST"}
        wizard_values.update(values or {})
        wizard_id = self.wizard.create(
            self.cursor, self.uid, wizard_values, context=context
        )
        return atc_id, wizard_id, context

    def creation_snapshot(self):
        return [
            self.openerp.pool.get(model).search(self.cursor, self.uid, [])
            for model in [
                "giscedata.switching",
                "giscedata.switching.r1.01",
                "giscedata.switching.step.header",
                "giscedata.switching.reclamacio",
            ]
        ]

    def assert_attention_type(self, switching_id, attention_type):
        step = self.switching.get_pas(self.cursor, self.uid, [switching_id])
        self.assertEqual(step.tipus, "01")
        self.assertEqual(step.subtipus_id.name, "001")
        self.assertTrue(step.reclamacio_ids)
        self.assertEqual(
            [detail.tipus_atencio_incorrecte for detail in step.reclamacio_ids],
            [attention_type],
        )

    def test_atc_can_be_created_without_attention_type(self):
        atc_id, wizard_id, context = self.prepare_atc_r1_wizard()
        case = self.atc.browse(self.cursor, self.uid, atc_id)
        self.assertEqual(case.subtipus_id.name, "001")
        self.assertFalse(case.ref)
        self.assertFalse(self.wizard.read(
            self.cursor, self.uid, [wizard_id], ["reclamacio_tipus_atencio_incorrecte"],
            context=context,
        )[0]["reclamacio_tipus_atencio_incorrecte"])

    def test_atc_r1_creation_requires_attention_type(self):
        atc_id, wizard_id, context = self.prepare_atc_r1_wizard()
        before = self.creation_snapshot()
        with self.assertRaises(osv.except_osv) as error:
            self.wizard.action_create_r1_case(
                self.cursor, self.uid, [wizard_id], context=context
            )
        self.assertIn("Tipus atenció incorrecte", error.exception.value)
        self.assertEqual(self.creation_snapshot(), before)
        self.assertFalse(self.atc.browse(self.cursor, self.uid, atc_id).ref)
        self.wizard.write(self.cursor, self.uid, [wizard_id], {
            "reclamacio_tipus_atencio_incorrecte": "05",
        }, context=context)
        result = self.wizard.action_create_r1_case(
            self.cursor, self.uid, [wizard_id], context=context
        )
        self.assert_attention_type(result["domain"][0][2], "05")
        self.assertTrue(self.atc.browse(self.cursor, self.uid, atc_id).ref)

    def test_atc_r1_creation_accepts_attention_type(self):
        atc_id, wizard_id, context = self.prepare_atc_r1_wizard(
            values={"reclamacio_tipus_atencio_incorrecte": "05"}
        )
        result = self.wizard.action_create_r1_case(
            self.cursor, self.uid, [wizard_id], context=context
        )
        switching_id = result["domain"][0][2]
        self.assert_attention_type(switching_id, "05")
        switching = self.switching.browse(self.cursor, self.uid, switching_id)
        case = self.atc.browse(self.cursor, self.uid, atc_id)
        self.assertEqual(
            [value.strip() for value in switching.ref.split(",")],
            ["giscedata.atc", str(atc_id)],
        )
        self.assertEqual(
            [value.strip() for value in case.ref.split(",")],
            ["giscedata.switching", str(switching_id)],
        )
        self.assertEqual(case.state, "pending")

    def test_other_atc_subtype_does_not_require_attention_type(self):
        atc_id, wizard_id, context = self.prepare_atc_r1_wizard(subtype="002")
        result = self.wizard.action_create_r1_case(
            self.cursor, self.uid, [wizard_id], context=context
        )
        step = self.switching.get_pas(self.cursor, self.uid, [result["domain"][0][2]])
        self.assertEqual(step.subtipus_id.name, "002")
        self.assertTrue(self.atc.browse(self.cursor, self.uid, atc_id).ref)

    def test_direct_creation_rejects_missing_or_empty_attention_type(self):
        values = {"tipus": "01", "subtipus_id": self.subtype_id("001"), "comentaris": "TEST"}
        before = self.creation_snapshot()
        for attention_values in [
            {},
            {"reclamacio_tipus_atencio_incorrecte": False},
            {"reclamacio_tipus_atencio_incorrecte": None},
            {"reclamacio_tipus_atencio_incorrecte": ""},
        ]:
            case_values = values.copy()
            case_values.update(attention_values)
            with self.assertRaises(osv.except_osv):
                self.wizard.action_create_r1_case_from_dict(
                    self.cursor, self.uid, self.contract_id, case_values
                )
            self.assertEqual(self.creation_snapshot(), before)

    def test_direct_creation_accepts_all_attention_types(self):
        for attention in TABLA_87:
            attention_type = attention[0]
            values = {
                "tipus": "01",
                "subtipus_id": self.subtype_id("001"),
                "comentaris": "TEST",
                "reclamacio_tipus_atencio_incorrecte": attention_type,
            }
            result = self.wizard.action_create_r1_case_from_dict(
                self.cursor, self.uid, self.contract_id, values
            )
            self.assert_attention_type(result[-1], attention_type)

    def prepare_batch_wizard(self, values=None):
        context = {
            "contract_ids": [self.contract_id, self.get_contract_id(self.txn, "polissa_0002")],
            "subtipus_id": self.subtype_id("001"),
        }
        wizard = self.openerp.pool.get("wizard.r101.from.multiple.contracts")
        wizard_values = {"tipus": "01", "comentarios": "TEST"}
        wizard_values.update(values or {})
        wizard_id = wizard.create(self.cursor, self.uid, wizard_values, context=context)
        return wizard, wizard_id, context

    def test_batch_creation_requires_attention_type(self):
        wizard, wizard_id, context = self.prepare_batch_wizard()
        before = self.creation_snapshot()
        with self.assertRaises(osv.except_osv):
            wizard.create_r1_from_contracts(self.cursor, self.uid, [wizard_id], context=context)
        self.assertEqual(self.creation_snapshot(), before)

    def test_batch_creation_accepts_attention_type(self):
        wizard, wizard_id, context = self.prepare_batch_wizard(
            values={"reclamacio_tipus_atencio_incorrecte": "05"}
        )
        result = wizard.create_r1_from_contracts(
            self.cursor, self.uid, [wizard_id], context=context
        )
        switching_ids = literal_eval(result["domain"])[0][2]
        self.assertEqual(len(switching_ids), 2)
        for switching_id in switching_ids:
            self.assert_attention_type(switching_id, "05")
