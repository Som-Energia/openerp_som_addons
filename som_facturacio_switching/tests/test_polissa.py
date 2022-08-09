# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from mock import patch, PropertyMock
from osv import osv


class TestsEscullLlistaPreus(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def get_demo_contract(self):
        imd_obj = self.model('ir.model.data')
        pol_obj = self.model("giscedata.polissa")

        pol_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_polissa', 'polissa_0001'
        )[1]

        return pol_obj.browse(self.cursor, self.uid, pol_id)

    def get_demo_pricelist_list(self):
        imd_obj = self.model('ir.model.data')

        pricelist_som_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_facturacio_switching', 'pricelist_20A_SOM'
        )[1]
        pricelist_som_insular_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'som_facturacio_switching', 'pricelist_20A_SOM_INSULAR'
        )[1]
        pricelist_electricidad_id = imd_obj.get_object_reference(
            self.cursor, self.uid, 'giscedata_facturacio', 'pricelist_tarifas_electricidad'
        )[1]

        return [
            pricelist_som_id, pricelist_som_insular_id, pricelist_electricidad_id
        ]

    def test_escull_llista_preus_peninsular(self):
        pol = self.get_demo_contract()
        pricelist_list = self.get_demo_pricelist_list()

        with patch.object(
                pol.cups.id_municipi.subsistema_id, 'code',
                new_callable=PropertyMock(return_value="PE")
            ) as mock:
            result = pol.escull_llista_preus(pricelist_list)

            # pricelist_20A_SOM is the first one
            self.assertEqual(result.id, pricelist_list[0])

    def test_escull_llista_preus_insular(self):
        pol = self.get_demo_contract()
        pricelist_list = self.get_demo_pricelist_list()

        with patch.object(
                pol.cups.id_municipi.subsistema_id, 'code',
                new_callable=PropertyMock(return_value="TF")
            ) as mock:
            result = pol.escull_llista_preus(pricelist_list)

            # pricelist_20A_SOM_INSULAR is the second one
            self.assertEqual(result.id, pricelist_list[0])

    def test_escull_llista_preus_1_llista(self):
        imd_obj = self.model('ir.model.data')

        pol = self.get_demo_contract()
        pricelist_list = self.get_demo_pricelist_list()

        with patch.object(
                pol.cups.id_municipi.subsistema_id, 'code',
                new_callable=PropertyMock(return_value="TF")
            ) as mock:

            default_pricelist_id = imd_obj.get_object_reference(
                self.cursor, self.uid, 'giscedata_facturacio', 'pricelist_tarifas_electricidad'
            )[1]
            result = pol.escull_llista_preus([default_pricelist_id])

            self.assertEqual(result.id, default_pricelist_id)
