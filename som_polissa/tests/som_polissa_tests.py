# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction
import unittest
from osv import fields
import mock
from mock import Mock, ANY


class TestSomPolissa(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.polissa_obj = self.openerp.pool.get("giscedata.polissa")
        self.contract1_id = self.get_ref("giscedata_polissa", "polissa_0001")
        self.contract2_id = self.get_ref("giscedata_polissa", "polissa_autoconsum_03a")
        self.contract3_id = self.get_ref("som_polissa", "polissa_domestica_0100")

        self.domestic_id = self.get_ref("som_polissa", "categ_domestic")
        self.eie_id = self.get_ref("som_polissa", "categ_entitat_o_empresa")
        self.eie_cnae_id = self.get_ref("som_polissa", "categ_eie_CNAE_no_domestic")
        self.eie_vat_id = self.get_ref("som_polissa", "categ_eie_persona_juridic")
        self.eie_cnae_vat_id = self.get_ref("som_polissa", "categ_eie_CNAE_CIF")

    def tearDown(self):
        self.txn.stop()

    def getCategories(self, polissa_id):
        Polissa = self.openerp.pool.get("giscedata.polissa")
        polissa = Polissa.read(
            self.cursor,
            self.uid,
            polissa_id,
            [
                "category_id",
            ],
        )
        return polissa["category_id"]

    def get_ref(self, module, ref):
        IrModel = self.openerp.pool.get("ir.model.data")
        return IrModel._get_obj(self.cursor, self.uid, module, ref).id

    def test__set_category_eie_both_eie_categories(self):
        oldCategories = self.getCategories(self.contract1_id)

        self.polissa_obj.set_category_eie(self.cursor, self.uid, self.contract1_id)
        self.assertEqual(
            sorted(oldCategories + ([self.eie_id, self.eie_cnae_vat_id])),
            sorted(self.getCategories(self.contract1_id)),
        )

    def test__set_category_eie_domestic_category(self):
        oldCategories = self.getCategories(self.contract3_id)

        self.polissa_obj.set_category_eie(self.cursor, self.uid, self.contract3_id)
        self.assertEqual(
            sorted(oldCategories + [self.domestic_id]),
            sorted(self.getCategories(self.contract3_id)),
        )

    def test__set_category_eie_many_contracts(self):
        oldCategories1 = self.getCategories(self.contract1_id)
        oldCategories2 = self.getCategories(self.contract2_id)

        self.polissa_obj.set_category_eie(
            self.cursor, self.uid, [self.contract1_id, self.contract2_id]
        )
        self.assertEqual(
            sorted(oldCategories1 + [self.eie_id, self.eie_cnae_vat_id]),
            sorted(self.getCategories(self.contract1_id)),
        )
        self.assertEqual(
            sorted(oldCategories2 + [self.eie_id, self.eie_vat_id]),
            sorted(self.getCategories(self.contract2_id)),
        )

    @mock.patch("som_polissa.giscedata_polissa.GiscedataPolissa.set_category_eie")
    def test__set_category_eie_on_change_contract(self, mock_func):
        oldCategories1 = self.getCategories(self.contract1_id)
        titular_id = self.get_ref("som_polissa", "res_partner_domestic")
        vals = {"titular": titular_id}
        pol = self.polissa_obj.write(self.cursor, self.uid, self.contract1_id, vals)

        self.assertEqual(mock_func.call_count, 1)

    @mock.patch("som_polissa.giscedata_polissa.GiscedataPolissa.set_category_eie")
    def test__set_category_eie_on_create_contract(self, mock_func):
        oldCategories1 = self.getCategories(self.contract1_id)
        titular_id = self.get_ref("som_polissa", "res_partner_domestic")
        cups_id = self.get_ref("giscedata_cups", "cups_tarifa_018")
        tensio_id = self.get_ref("giscedata_tensions", "tensio_127")
        tarifa_id = self.get_ref("giscedata_polissa", "tarifa_20TD")
        vals = {
            "name": "0101",
            "active": True,
            "cups": cups_id,
            "potencia": 4.600,
            "tarifa": tarifa_id,
            "titular": titular_id,
            "tensio_normalitzada": tensio_id,
            "state": "esborrany",
            "data_alta": "2021-06-01",
        }
        pol = self.polissa_obj.create(self.cursor, self.uid, vals)

        self.assertEqual(mock_func.call_count, 1)
