# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction

from datetime import date, datetime, timedelta
from .. import res_partner
import mock

class TestPolissaWwwAutolectura(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def get_fixture(self, model, reference):
        return self.imd_obj.get_object_reference(self.cursor, self.uid, model, reference)[1]

    def setUp(self):
        self.pol_obj = self.model("giscedata.polissa")
        self.pool_lect_obj = self.model("giscedata.lectures.lectura.pool")
        self.fact_lect_obj = self.model("giscedata.lectures.lectura")
        self.meter_obj = self.model("giscedata.lectures.comptador")
        self.period_obj = self.model("giscedata.polissa.tarifa.periodes")
        self.origin_comer_obj = self.model("giscedata.lectures.origen_comer")
        self.origin_obj = self.model("giscedata.lectures.origen")
        self.tarif_obj = self.model("giscedata.polissa.tarifa")
        self.imd_obj = self.model("ir.model.data")
        self.swproc_obj = self.model("giscedata.switching.proces")
        self.sw_obj = self.model("giscedata.switching")

        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    # Helper functions
    def create_lect_pool(
        self, pol_id, date, period, lect_type, value, observations, origen_comer_code, origin_code
    ):
        return self.create_lect(
            pol_id,
            date,
            period,
            lect_type,
            value,
            observations,
            origen_comer_code,
            origin_code,
            True,
        )

    def create_lect_fact(
        self, pol_id, date, period, lect_type, value, observations, origen_comer_code, origin_code
    ):
        return self.create_lect(
            pol_id,
            date,
            period,
            lect_type,
            value,
            observations,
            origen_comer_code,
            origin_code,
            False,
        )

    def create_lect(
        self,
        pol_id,
        date,
        period,
        lect_type,
        value,
        observations,
        origen_comer_code,
        origin_code,
        pool,
    ):
        # avaliable codes for origin_comer_code
        # ['Q1','F1','MA','OV','AL','ES','AT','CC']

        # available codes for origin_code
        # ['10','20','30','40','50','99','40','40','60']

        pol_val = self.pol_obj.read(self.cursor, self.uid, pol_id, ["comptador", "tarifa"])
        if not pol_val:
            return None

        meter_search = [("polissa.id", "=", pol_id), ("name", "=", pol_val["comptador"])]
        meter_ids = self.meter_obj.search(self.cursor, self.uid, meter_search)
        if not meter_ids:
            return None

        period_search = [
            ("tarifa.id", "=", pol_val["tarifa"][0]),
            ("tipus", "=", "te"),
            ("agrupat_amb", "=", False),
            ("name", "=", period),
        ]
        period_ids = self.period_obj.search(self.cursor, self.uid, period_search)
        if not period_ids:
            return None

        origin_comer_ids = self.origin_comer_obj.search(
            self.cursor, self.uid, [("codi", "=", origen_comer_code)]
        )
        if not origin_comer_ids:
            return None

        origin_id = self.origin_obj.search(self.cursor, self.uid, [("codi", "=", origin_code)])[0]

        vals = {
            "comptador": meter_ids[0],
            "name": date,
            "periode": period_ids[0],
            "tipus": lect_type,
            "lectura": value,
            "observacions": observations,
            "origen_comer_id": origin_comer_ids[0],
            "origen_id": origin_id,
        }
        if pool:
            return self.pool_lect_obj.create(self.cursor, self.uid, vals)
        else:
            return self.fact_lect_obj.create(self.cursor, self.uid, vals)

    def change_polissa_power_method(self, pol_id, method):
        self.pol_obj.write(self.cursor, self.uid, pol_id, {"facturacio_potencia": method})

    def test_www_ultimes_lectures_reals_retorna_reals_i_estimades(self):
        pol_obj = self.openerp.pool.get("giscedata.polissa")
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0002")
        test_date = date.today() - timedelta(days=1)
        self.change_polissa_power_method(pol_id, "icp")

        self.create_lect_pool(pol_id, str(test_date), "P1", "A", 22287, "test", "OV", "50")

        self.create_lect_pool(
            pol_id, str(test_date - timedelta(days=31)), "P1", "A", 33387, "test", "OV", "40"
        )

        self.create_lect_pool(
            pol_id, str(test_date - timedelta(days=61)), "P1", "A", 99987, "test", "OV", "99"
        )

        res = pol_obj.www_ultimes_lectures_reals(self.cursor, self.uid, pol_id)
        kw_lects = [i["lectura"] for i in res]

        self.assertIn(22287, kw_lects)
        self.assertIn(33387, kw_lects)
        self.assertNotIn(99987, kw_lects)

        # Test origen correcto
        for lectura in res:
            if lectura["lectura"] == 22287:
                self.assertEqual(lectura["origen"], "Autolectura")
            elif lectura["lectura"] == 33387:
                self.assertEqual(lectura["origen"], "Distribuidora (Estimada)")

    def _open_polissa(self, xml_ref):
        polissa_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", xml_ref
        )[1]

        self.pol_obj.send_signal(self.cursor, self.uid, [polissa_id], ["validar", "contracte"])

        return polissa_id

    def test_www_check_modifiable_polissa_not_modifiable_for_atr(self):
        pol_id = self._open_polissa("polissa_tarifa_018")

        ctx = {"lang": "en_US"}

        proces_id = self.swproc_obj.search(self.cursor, self.uid, [("name", "=", "M1")])[0]

        sw_params = {
            "proces_id": proces_id,
            "cups_polissa_id": pol_id,
            "ref_contracte": pol_id,
            "polissa_ref_id": pol_id,
        }

        self.sw_obj.create(self.cursor, self.uid, sw_params, context=ctx)

        result = self.pol_obj.www_check_modifiable_polissa(
            self.cursor, self.uid, pol_id, context=ctx
        )

        self.assertEqual(result["error"], u"Pòlissa 0018 with simultaneous ATR")
        self.assertEqual(result["code"], u"PolissaSimultaneousATR")

    def test_www_check_modifiable_polissa_modifiable_atr_skip_check(self):
        pol_id = self._open_polissa("polissa_tarifa_018")

        ctx = {"lang": "en_US"}

        proces_id = self.swproc_obj.search(self.cursor, self.uid, [("name", "=", "M1")])[0]

        sw_params = {
            "proces_id": proces_id,
            "cups_polissa_id": pol_id,
            "ref_contracte": pol_id,
            "polissa_ref_id": pol_id,
        }

        self.sw_obj.create(self.cursor, self.uid, sw_params, context=ctx)

        result = self.pol_obj.www_check_modifiable_polissa(
            self.cursor, self.uid, pol_id, skip_atr_check=True, context=ctx
        )

        self.assertEqual(result, True)

    def test_www_check_modifiable_polissa_not_modifiable_for_pending_modcon(self):
        pol_id = self._open_polissa("polissa_tarifa_018")

        ctx = {"lang": "en_US"}

        today_plus_10_days = (datetime.today() + timedelta(days=10)).strftime("%Y-%m-%d")
        today_plus_100_days = (datetime.today() + timedelta(days=10)).strftime("%Y-%m-%d")

        values = {"autoconsumo": "41"}

        self.pol_obj.crear_modcon(
            self.cursor,
            self.uid,
            pol_id,
            values,
            today_plus_10_days,
            today_plus_100_days,
            context=ctx,
        )

        result = self.pol_obj.www_check_modifiable_polissa(
            self.cursor, self.uid, pol_id, context=ctx
        )
        self.assertEqual(result["error"], u"Pòlissa 0018 already has a pending modcon")
        self.assertEqual(result["code"], u"PolissaModconPending")

    def test_www_check_modifiable_polissa_modifiable(self):
        pol_id = self._open_polissa("polissa_tarifa_018")

        ctx = {"lang": "en_US"}

        result = self.pol_obj.www_check_modifiable_polissa(
            self.cursor, self.uid, pol_id, context=ctx
        )

        self.assertEqual(result, True)

    def test_www_check_modifiable_polissa_not_modifiable_for_not_active(self):
        pol_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_polissa", "polissa_tarifa_018"
        )[1]

        ctx = {"lang": "en_US"}

        result = self.pol_obj.www_check_modifiable_polissa(
            self.cursor, self.uid, pol_id, context=ctx
        )
        self.assertEqual(result["error"], u"Pòlissa 0018 not active")
        self.assertEqual(result["code"], u"PolissaNotActive")

class TestPolissaWwwDistri(testing.OOTestCase):
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.pol_obj = self.model("giscedata.polissa")
        self.partner_obj = self.model("res.partner")

        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

    def tearDown(self):
        self.txn.stop()

    def test_www_get_distributor_id__without_REE_CODE_TRANSLATION(self):
        cups = 'ES0031XXXXXXXXXXXXXXXX' #ENDESA DISTRIBUCIÓN ELÉCTRICA S. L.

        result = self.pol_obj.www_get_distributor_id(
            self.cursor, self.uid, cups
        )

        self.assertEqual(result, 56)

    @mock.patch.object(res_partner.ResPartner, "search")
    def test_www_get_distributor_id__with_REE_CODE_TRANSLATION(self, mock_res_partner_search):
        cups = 'ES0390XXXXXXXXXXXXXXXX' #Electra del Jallas -> Fenosa

        mock_res_partner_search.return_value = [1]

        result = self.pol_obj.www_get_distributor_id(
            self.cursor, self.uid, cups
        )

        self.assertEqual(result, 1)

    def test_www_get_distributor_id__distri_non_exists(self):
        cups = 'ES0390XXXXXXXXXXXXXXXX' #Electra del Jallas -> Fenosa

        result = self.pol_obj.www_get_distributor_id(
            self.cursor, self.uid, cups
        )

        self.assertEqual(result, None)