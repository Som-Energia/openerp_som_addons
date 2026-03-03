# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
import mock


class TestsEscullLlistaPreus(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def get_demo_contract(self, indexed=False, location=False):
        imd_obj = self.model("ir.model.data")
        pol_obj = self.model("giscedata.polissa")
        municipi_obj = self.model("res.municipi")
        cups_obj = self.model("giscedata.cups.ps")

        pol_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_0001"
        )[1]

        tariff_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "tarifa_20TD"
        )[1]

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        pol_obj.write(self.cursor, self.uid, pol_id, {"tarifa": tariff_id})

        if location == "balears":
            xml_id_prov = "ES07"
            id_prov = imd_obj.get_object_reference(
                self.cursor, self.uid, "l10n_ES_toponyms", xml_id_prov
            )[1]
            municipi_id = municipi_obj.search(
                self.cursor, self.uid, [("state", "=", id_prov)], limit=1
            )[0]

            cups_obj.write(
                self.cursor,
                self.uid,
                pol.cups.id,
                {"id_municipi": municipi_id},
            )

        if indexed:
            pol_obj.write(self.cursor, self.uid, pol_id, {"mode_facturacio": "index"})

        return pol

    def get_demo_pricelist_dict(self):
        imd_obj = self.model("ir.model.data")

        mapping = {
            'peninsula': ("som_indexada", "pricelist_periodes_20td_peninsula"),
            'insular': ("som_indexada", "pricelist_periodes_20td_insular"),
            'electricitat': ("giscedata_facturacio", "pricelist_tarifas_electricidad"),
            'indexada_2024': ("som_indexada", "pricelist_indexada_20td_peninsula_2024"),
            'indexada_balears_2024': ("som_indexada", "pricelist_indexada_20td_balears_2024"),
            'indexada_canaries_2024': ("som_indexada", "pricelist_indexada_20td_canaries_2024"),
        }

        return {
            key: imd_obj.get_object_reference(self.cursor, self.uid, module, xml_id)[1]
            for key, (module, xml_id) in mapping.items()
        }

    def test_escull_llista_preus_peninsular(self):
        pol = self.get_demo_contract()
        pricelists = self.get_demo_pricelist_dict()

        result = pol.escull_llista_preus(list(pricelists.values()))

        self.assertEqual(result.id, pricelists['peninsula'])

    def test_escull_llista_preus_insular(self):
        pol = self.get_demo_contract(location="balears")
        pricelists = self.get_demo_pricelist_dict()

        result = pol.escull_llista_preus(list(pricelists.values()))

        self.assertEqual(result.id, pricelists['insular'])

    @mock.patch("som_indexada.giscedata_polissa.GiscedataPolissa._get_tariff_zone_from_location")
    def test_escull_llista_preus_insular_canaries(self, mock_function):
        mock_function.return_value = "canaries"
        pol = self.get_demo_contract()
        pricelists = self.get_demo_pricelist_dict()

        result = pol.escull_llista_preus(list(pricelists.values()))

        self.assertEqual(result.id, pricelists['insular'])

    def test_escull_llista_preus_indexada_peninsular(self):
        pol = self.get_demo_contract(indexed=True)
        pricelists = self.get_demo_pricelist_dict()

        result = pol.escull_llista_preus(list(pricelists.values()))

        self.assertEqual(result.id, pricelists['indexada_2024'])

    def test_escull_llista_preus_indexada_balears(self):
        pol = self.get_demo_contract(indexed=True, location="balears")
        pricelists = self.get_demo_pricelist_dict()

        result = pol.escull_llista_preus(list(pricelists.values()))

        self.assertEqual(result.id, pricelists['indexada_balears_2024'])
