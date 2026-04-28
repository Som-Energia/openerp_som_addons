# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from destral import testing
from destral.transaction import Transaction


class TestGiscedataPolissa(testing.OOTestCase):

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.pol_obj = self.openerp.pool.get("giscedata.polissa")
        self.fp_obj = self.openerp.pool.get("account.fiscal.position")
        self.partner_obj = self.openerp.pool.get("res.partner")
        self.conf_obj = self.openerp.pool.get('res.config')
        self.tax_obj = self.openerp.pool.get('account.tax')
        self.imd_obj = self.openerp.pool.get('ir.model.data')

        self.conf_obj.set(
            self.cursor, self.uid, 'default_iva_21_tax_id',
            self.tax_obj.search(self.cursor, self.uid, [("name", "=", "IVA 21%")])[0],
        )
        self.conf_obj.set(
            self.cursor, self.uid, 'default_iese_tax_id',
            self.tax_obj.search(self.cursor, self.uid, [
                ("name", "=", "Impuesto especial sobre la electricidad")
            ])[0],
        )

        fp_ids = self.fp_obj.search(
            self.cursor, self.uid,
            [("name", "=", "IVA Reduït (IVA 5%)")]
        )
        self.fp_iva_reduit_id = fp_ids[0] if fp_ids else None

        self._pol_id = 1  # Any polissa can work

    def tearDown(self):
        self.txn.stop()

    def test_get_simplified_taxes__no_fiscal_position__returns_iva_21_default(self):
        pol_id = self._pol_id
        self.pol_obj.write(
            self.cursor, self.uid, pol_id,
            {"fiscal_position_id": False}
        )

        result = self.pol_obj.get_simplified_taxes(self.cursor, self.uid, pol_id, context={})

        expected = {"IVA": 0.21, "IE": 0.4864}
        self.assertEqual(result, expected)

    def test_get_simplified_taxes__context_iva10__returns_iva_10_context_override(self):
        pol_id = self._pol_id
        self.pol_obj.write(
            self.cursor, self.uid, pol_id,
            {"fiscal_position_id": False}
        )

        result = self.pol_obj.get_simplified_taxes(
            self.cursor, self.uid, pol_id, context={"iva10": True}
        )

        expected = {"IVA": 0.1, "IE": 0.4864}
        self.assertEqual(result, expected)

    def test_get_simplified_taxes__iva_reduit_fp__returns_iva_5_with_ie(self):
        pol_id = self._pol_id
        self.pol_obj.write(
            self.cursor, self.uid, pol_id,
            {"fiscal_position_id": self.fp_iva_reduit_id, "titular": False}
        )

        result = self.pol_obj.get_simplified_taxes(self.cursor, self.uid, pol_id, context={})

        expected = {"IVA": 0.05, "IE": 0.005}
        self.assertEqual(result, expected)

    def test_get_simplified_taxes__fp_without_tax_ids__returns_default_iva(self):
        pol_id = self._pol_id
        self.pol_obj.write(
            self.cursor, self.uid, pol_id,
            {"fiscal_position_id": 1, "titular": False}
        )

        result = self.pol_obj.get_simplified_taxes(self.cursor, self.uid, pol_id, context={})

        expected = {"IVA": 0.21, "IE": 0.4864}
        self.assertEqual(result, expected)

    def test_get_simplified_taxes__context_iva10_overrides_fp_with_lowest_iva(self):
        if not self.fp_iva_reduit_id:
            self.skipTest("No IVA Reduït fiscal position")

        pol_id = self._pol_id
        self.pol_obj.write(
            self.cursor, self.uid, pol_id,
            {"fiscal_position_id": self.fp_iva_reduit_id, "titular": False}
        )

        result = self.pol_obj.get_simplified_taxes(
            self.cursor, self.uid, pol_id, context={"iva10": True}
        )

        expected = {"IVA": 0.1, "IE": 0.005}
        self.assertEqual(result, expected)

    def test_get_simplified_taxes__with_igic(self):
        pol_id = self._pol_id

        # Create and map IGIC 3% tax
        igic3_template_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'l10n_es_igic', 'igic_rep_3')[1]
        igic3_tax_id = self.tax_obj.create_tax_from_template(
            self.cursor, self.uid, igic3_template_id)

        iva_map_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_polissa_condicions_generals', 'fp_iva_reduit_map')[1]
        self.openerp.pool.get('account.fiscal.position.tax').write(
            self.cursor, self.uid, iva_map_id, {"tax_dest_id": igic3_tax_id}
        )

        self.pol_obj.write(
            self.cursor, self.uid, pol_id,
            {"fiscal_position_id": self.fp_iva_reduit_id, "titular": False}
        )

        result = self.pol_obj.get_simplified_taxes(self.cursor, self.uid, pol_id, context={})

        expected = {"IGIC": 0.03, "IE": 0.005}  # IE is reduced in fp_iva_reduit
        self.assertEqual(result, expected)
