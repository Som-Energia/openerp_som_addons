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

    def get_demo_pricelist_list(self):
        imd_obj = self.model("ir.model.data")

        pricelist_som_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_peninsula"
        )[1]
        pricelist_som_insular_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_periodes_20td_insular"
        )[1]
        pricelist_electricidad_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio", "pricelist_tarifas_electricidad"
        )[1]
        pricelist_som_indexada_2024_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_indexada_20td_peninsula_2024"
        )[1]
        pricelist_som_indexada_balears_2024_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_indexada_20td_balears_2024"
        )[1]
        pricelist_som_indexada_canaries_2024_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_indexada", "pricelist_indexada_20td_canaries_2024"
        )[1]

        return [
            pricelist_som_id,
            pricelist_som_insular_id,
            pricelist_electricidad_id,
            pricelist_som_indexada_2024_id,
            pricelist_som_indexada_balears_2024_id,
            pricelist_som_indexada_canaries_2024_id,
        ]

    def test_escull_llista_preus_peninsular(self):
        pol = self.get_demo_contract()
        pricelist_list = self.get_demo_pricelist_list()

        result = pol.escull_llista_preus(pricelist_list)

        self.assertEqual(result.id, pricelist_list[0])

    def test_escull_llista_preus_insular(self):
        pol = self.get_demo_contract(location="balears")
        pricelist_list = self.get_demo_pricelist_list()

        result = pol.escull_llista_preus(pricelist_list)

        self.assertEqual(result.id, pricelist_list[1])

    @mock.patch(
        "som_indexada.giscedata_polissa.GiscedataPolissa._get_tariff_zone_from_location"
    )
    def test_escull_llista_preus_insular_canaries(self, mock_function):
        mock_function.return_value = "canaries"
        pol = self.get_demo_contract()
        pricelist_list = self.get_demo_pricelist_list()

        result = pol.escull_llista_preus(pricelist_list)

        self.assertEqual(result.id, pricelist_list[1])

    def test_escull_llista_preus_no_compatible(self):
        imd_obj = self.model("ir.model.data")

        pol = self.get_demo_contract()

        default_pricelist_id = imd_obj.get_object_reference(
            self.cursor,
            self.uid,
            "giscedata_facturacio",
            "pricelist_tarifas_electricidad",
        )[1]

        result = pol.escull_llista_preus([default_pricelist_id])

        self.assertEqual(result, False)

    def test_escull_llista_preus_indexada_peninsular(self):
        pol = self.get_demo_contract(indexed=True)
        pricelist_list = self.get_demo_pricelist_list()

        result = pol.escull_llista_preus(pricelist_list)

        self.assertEqual(result.id, pricelist_list[6])

    def test_escull_llista_preus_indexada_balears(self):
        pol = self.get_demo_contract(indexed=True, location="balears")
        pricelist_list = self.get_demo_pricelist_list()

        result = pol.escull_llista_preus(pricelist_list)

        self.assertEqual(result.id, pricelist_list[7])

    @mock.patch(
        "som_indexada.giscedata_polissa.GiscedataPolissa._get_tariff_zone_from_location"
    )
    def test_escull_llista_preus_indexada_canaries(self, mock_function):
        mock_function.return_value = "canaries"
        pol = self.get_demo_contract(indexed=True)
        pricelist_list = self.get_demo_pricelist_list()

        result = pol.escull_llista_preus(pricelist_list)

        self.assertEqual(result.id, pricelist_list[8])
