# -*- coding: utf-8 -*-
from __future__ import absolute_import
import base64
from expects import expect
from expects import contain
import mock
from addons import get_module_resource
from destral import testing
from destral.transaction import Transaction


class TestsFacturesValidation(testing.OOTestCase):
    def setUp(self):
        self.fact_obj = self.openerp.pool.get("giscedata.facturacio.factura")
        self.fact_linia_obj = self.openerp.pool.get("giscedata.facturacio.factura.linia")
        warn_obj = self.openerp.pool.get("giscedata.facturacio.validation.warning.template")
        self.imd_obj = self.openerp.pool.get("ir.model.data")
        self.pol_obj = self.openerp.pool.get("giscedata.polissa")
        self.lectures_obj = self.openerp.pool.get("giscedata.lectures.lectura")
        self.invoice_energy_readings_obj = self.openerp.pool.get(
            "giscedata.facturacio.lectures.energia"
        )
        self.cnt_lot_obj = self.openerp.pool.get("giscedata.facturacio.contracte_lot")
        self.lot_obj = self.openerp.pool.get("giscedata.facturacio.lot")
        self.vali_obj = self.openerp.pool.get("giscedata.facturacio.validation.validator")
        self.origen_comer_obj = self.openerp.pool.get("giscedata.lectures.origen_comer")

        self.txn = Transaction().start(self.database)
        cursor = self.txn.cursor
        uid = self.txn.user

        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.pol_obj.write(cursor, uid, pol_id, {"category_id": [(6, 0, [])]})

        ctx = {"active_test": False}

        # We make sure that all warnings are active
        warn_ids = warn_obj.search(cursor, uid, [], context=ctx)
        warn_obj.write(cursor, uid, warn_ids, {"active": True})

    def tearDown(self):
        self.txn.stop()

    def activate_contract(self, contract_id):
        polissa_obj = self.model("giscedata.polissa")

        polissa_obj.send_signal(
            self.txn.cursor, self.txn.user, contract_id, ["validar", "contracte"]
        )

    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def get_fixture(self, model, reference):
        imd_obj = self.model("ir.model.data")
        return imd_obj.get_object_reference(self.txn.cursor, self.txn.user, model, reference)[1]

    def validation_warnings(self, factura_id):
        vali_obj = self.model("giscedata.facturacio.validation.validator")
        warn_obj = self.model("giscedata.facturacio.validation.warning")

        warning_ids = vali_obj.validate_invoice(self.txn.cursor, self.txn.user, factura_id)
        warning_vals = warn_obj.read(self.txn.cursor, self.txn.user, warning_ids, ["name"])
        return [warn["name"] for warn in warning_vals]

    # Scenario contruction helpers
    def prepare_contract(self, pol_id, data_alta, data_ultima_lectura):
        contract_obj = self.model("giscedata.polissa")
        cursor = self.txn.cursor
        uid = self.txn.user

        vals = {
            "data_alta": data_alta,
            "data_baixa": False,
            "data_ultima_lectura": data_ultima_lectura,
            "facturacio": 1,
            "facturacio_potencia": "icp",
            "tg": "1",
            "lot_facturacio": False,
        }
        contract_obj.write(cursor, uid, pol_id, vals)
        contract_obj.send_signal(cursor, uid, [pol_id], ["validar", "contracte"])
        contract = contract_obj.browse(cursor, uid, pol_id)
        for meter in contract.comptadors:
            for l in meter.lectures:  # noqa: E741
                l.unlink(context={})
            for lp in meter.lectures_pot:
                lp.unlink(context={})
            meter.write({"lloguer": False})
        return contract.comptadors[0].id

    def create_category_to_contract_by_name(self, pol_id, category_name):
        pol_obj = self.model("giscedata.polissa")
        pcat_obj = self.model("giscedata.polissa.category")
        cursor = self.txn.cursor
        uid = self.txn.user

        pcat_ids = pcat_obj.search(cursor, uid, [("name", "like", "%" + category_name + "%")])
        if pcat_ids:
            pcat_id = pcat_ids[0]
        else:
            pcat_id = pcat_obj.create(
                cursor,
                uid,
                {
                    "name": category_name,
                    "code": "ZZ",
                },
            )
        pol_obj.write(cursor, uid, pol_id, {"category_id": [(4, pcat_id)]})

    def create_measure(self, meter_id, date_measure, measure, origen_code, origen_comer_code):
        measure_obj = self.model("giscedata.lectures.lectura")
        lo_obj = self.model("giscedata.lectures.origen")
        loc_obj = self.model("giscedata.lectures.origen_comer")
        periode_id = self.get_fixture("giscedata_polissa", "p1_e_tarifa_20A_new")
        origins_ids = (
            lo_obj.search(self.txn.cursor, self.txn.user, [("codi", "=", origen_code)])
            if origen_code
            else []
        )
        origins_comer_ids = (
            loc_obj.search(self.txn.cursor, self.txn.user, [("codi", "=", origen_comer_code)])
            if origen_code
            else []
        )

        vals = {
            "name": date_measure,
            "periode": periode_id,
            "lectura": measure,
            "tipus": "A",
            "comptador": meter_id,
            "observacions": "",
        }
        if origins_ids:
            vals["origen_id"] = origins_ids[0]
        if origins_comer_ids:
            vals["origen_comer_id"] = origins_comer_ids[0]

        return measure_obj.create(self.txn.cursor, self.txn.user, vals)

    def modify_invoice(self, fact_id, pol_id, start, end, amount=1):
        attach_obj = self.openerp.pool.get('ir.attachment')

        self.fact_obj.write(
            self.txn.cursor,
            self.txn.user,
            fact_id,
            {
                "data_inici": start,
                "data_final": end,
                "polissa_id": pol_id,
                "state": "open",
                "type": "out_invoice",
                "energia_kwh": amount,
            },
        )

        # polissa_0001 is indexed and needs a coef file for validations
        csv_path = get_module_resource(
            'giscedata_facturacio_indexada', 'tests', 'data', 'PMD_1612092_20200401_20200430.csv'
        )
        with open(csv_path, 'r') as f:
            csv_file = f.read()
        vals = {
            'name': 'PMD_1612092_20200401_20200430.csv',
            'datas': base64.b64encode(csv_file),
            'res_model': 'giscedata.facturacio.factura',
            'res_id': fact_id
        }
        attach_obj.create(self.txn.cursor, self.txn.user, vals)

    def crear_modcon(self, polissa_id, teoric_max, ini, fi):
        cursor = self.txn.cursor
        uid = self.txn.user
        pool = self.openerp.pool
        polissa_obj = pool.get("giscedata.polissa")

        pol = polissa_obj.browse(cursor, uid, polissa_id)
        pol.send_signal(["modcontractual"])
        polissa_obj.write(cursor, uid, polissa_id, {"teoric_maximum_consume_gc": teoric_max})
        wz_crear_mc_obj = pool.get("giscedata.polissa.crear.contracte")

        ctx = {"active_id": polissa_id}
        params = {"duracio": "nou"}

        wz_id_mod = wz_crear_mc_obj.create(cursor, uid, params, ctx)
        wiz_mod = wz_crear_mc_obj.browse(cursor, uid, wz_id_mod, ctx)
        wz_crear_mc_obj.onchange_duracio(
            cursor, uid, [wz_id_mod], wiz_mod.data_inici, wiz_mod.duracio, ctx
        )
        wiz_mod.write({"data_inici": ini, "data_final": fi})
        wiz_mod.action_crear_contracte(ctx)

    def create_inv_line(self, inv_id, quantity):
        self.fact_linia_obj.create(
            self.txn.cursor,
            self.txn.user,
            {
                "name": "Linia 1",
                "tipus": "energia",
                "price_unit": 1,
                "factura_id": inv_id,
                "product_id": False,
                "account_id": 1,
                "quantity": quantity,
            },
        )

    def create_invoice_energy_reading(self, inv_id, meter_id, origin_code):
        origen_obj = self.model("giscedata.lectures.origen")
        origin_ids = origen_obj.search(
            self.txn.cursor, self.txn.user, [("codi", "=", origin_code)]
        ) if origin_code else []
        values = {
            "name": "P1",
            "comptador_id": meter_id,
            "factura_id": inv_id,
            "tipus": "activa",
            "magnitud": "AE",
            "data_actual": "2017-03-17",
            "lect_actual": 1000,
            "data_anterior": "2017-02-18",
            "lect_anterior": 0,
            "consum": 1000,
        }
        if origin_ids:
            values["origen_id"] = origin_ids[0]
        self.invoice_energy_readings_obj.create(
            self.txn.cursor, self.txn.user, values
        )

    def prepare_som_20td_fact(self, fact, price_list_name=u"2.0TD_SOM"):
        """Apply validation-only tariff values without altering shared fixtures."""
        fact.tarifa_acces_id.name = u"2.0TD"
        fact.polissa_id.llista_preu.name = price_list_name
        fact.polissa_id.autoconsumo = u"00"
        return fact

    def prepare_f001_fact(self, energy_kwh, origin_codes):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17", energy_kwh)
        reading_ids = self.invoice_energy_readings_obj.search(
            self.txn.cursor, self.txn.user, [("factura_id", "=", inv_id)]
        )
        self.invoice_energy_readings_obj.unlink(
            self.txn.cursor, self.txn.user, reading_ids
        )
        for origin_code in origin_codes:
            self.create_invoice_energy_reading(inv_id, meter_id, origin_code)
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        fact.energia_kwh = energy_kwh
        return self.prepare_som_20td_fact(fact)

    def f001_parameters(self):
        return {
            "n_months": 14,
            "overuse_percentage": 50.0,
            "min_periods": 4,
            "som_skip_if_20TD_00_and_less_than_kWh": 1000,
        }

    def f017_parameters(self):
        return {
            "max_delayed_days": 70,
            "today": "2017-05-30",
            "som_skip_if_20TD_00_and_less_than_days": 90,
        }

    def assign_gkwh(self, polissa):
        cursor = self.txn.cursor
        uid = self.txn.user

        assign_obj = self.model("generationkwh.assignment")
        soci_obj = self.model("somenergia.soci")
        soci_id = soci_obj.search(cursor, uid, [], limit=1)[0]
        assign_obj.create(
            cursor, uid, {"contract_id": polissa.id, "member_id": soci_id, "priority": 0}
        )

    def test_check_origin_readings_by_contract_category__contract_without_category(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        self.create_measure(meter_id, "2017-02-18", 8000, "40", "F1")
        self.create_measure(meter_id, "2017-03-17", 8600, "40", "F1")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain("SF01"))

    def test_check_origin_readings_by_contract_category__contract_with_wrong_category(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.create_category_to_contract_by_name(pol_id, "Petit Contracte")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        self.create_measure(meter_id, "2017-02-18", 8000, "40", "F1")
        self.create_measure(meter_id, "2017-03-17", 8600, "40", "F1")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain("SF01"))

    def test_check_origin_readings_by_contract_category__contract_with_category_readings_ok(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.create_category_to_contract_by_name(pol_id, "Gran Contracte")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        self.create_measure(meter_id, "2017-02-18", 8000, "40", "Q1")
        self.create_measure(meter_id, "2017-03-17", 8600, "40", "Q1")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain("SF01"))

    def test_check_origin_readings_by_contract_category__contract_with_category_all_readings_not_ok(
        self,
    ):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.create_category_to_contract_by_name(pol_id, "Gran Contracte")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        self.create_measure(meter_id, "2017-02-18", 8000, "40", "F1")
        self.create_measure(meter_id, "2017-03-17", 8600, "40", "F1")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        warnings = self.validation_warnings(inv_id)
        expect(warnings).to(contain("SF01"))

    def test_check_origin_readings_by_contract_category__contract_with_category_one_reading_not_ok(
        self,
    ):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.create_category_to_contract_by_name(pol_id, "Gran Contracte")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        self.create_measure(meter_id, "2017-02-18", 8000, "40", "F1")
        self.create_measure(meter_id, "2017-03-17", 8600, "30", "Q1")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        warnings = self.validation_warnings(inv_id)
        expect(warnings).to(contain("SF01"))

    def test_check_min_periods_and_teoric_maximum_consum__contract_without_category(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain("SF02"))

    def test_check_min_periods_and_teoric_maximum_consum__contract_with_wrong_category(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.create_category_to_contract_by_name(pol_id, "Petit Contracte")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain("SF02"))

    def test_check_min_periods_and_teoric_maximum_consum__contract_with_category_not_periods_not_teoric(  # noqa: E501
        self,
    ):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.create_category_to_contract_by_name(pol_id, "Gran Contracte")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        warnings = self.validation_warnings(inv_id)
        expect(warnings).to(contain("SF02"))

    def test_check_min_periods_and_teoric_maximum_consum__contract_with_category_and_teoric_zero(
        self,
    ):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.create_category_to_contract_by_name(pol_id, "Gran Contracte")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        self.crear_modcon(pol_id, 0, "2017-02-18", "2017-03-17")
        warnings = self.validation_warnings(inv_id)
        expect(warnings).to(contain("SF02"))

    def test_check_min_periods_and_teoric_maximum_consum__contract_with_category_and_teoric_ok(
        self,
    ):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.create_category_to_contract_by_name(pol_id, "Gran Contracte")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        self.create_measure(meter_id, "2017-02-18", 8000, "40", "Q1")
        self.create_measure(meter_id, "2017-03-17", 8600, "40", "Q1")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        self.crear_modcon(pol_id, 500, "2017-02-18", "2018-02-17")
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain("SF02"))

    def test_check_consume_by_percentage_and_category__contract_without_category(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain("SF03"))

    def test_check_consume_by_percentage_and_category__contract_with_wrong_category(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.create_category_to_contract_by_name(pol_id, "Petit Contracte")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        warnings = self.validation_warnings(inv_id)
        expect(warnings).not_to(contain("SF03"))

    def test_check_consume_by_percentage_and_category__contract_with_category_and_teoric_consumption(  # noqa: E501
        self,
    ):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.create_category_to_contract_by_name(pol_id, "Gran Contracte")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        self.create_inv_line(inv_id, 200)
        self.crear_modcon(pol_id, 5, "2017-02-18", "2018-02-17")
        warnings = self.validation_warnings(inv_id)
        expect(warnings).to(contain("SF03"))

    def test_check_exceding_days_overwrite__No(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        params = {
            "inc_days_maximeter": 1,
            "n_days_bimensual": 10,
            "n_days_first_invoice": 14,
            "n_days_mensual": 10,
            "n_days_not_estimable": 14
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        result = self.vali_obj.check_exceding_days(self.txn.cursor, self.txn.user, fact, params)
        self.assertEqual(result, None)

    def test_check_exceding_days_overwrite__Yes(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-11", "2017-03-27")
        params = {
            "inc_days_maximeter": 1,
            "n_days_bimensual": 10,
            "n_days_first_invoice": 14,
            "n_days_mensual": 10,
            "n_days_not_estimable": 14
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        result = self.vali_obj.check_exceding_days(self.txn.cursor, self.txn.user, fact, params)
        expected = {
            u'polissa_state': u'activa',
            u'expected_days': 28,
            u'margin': 10,
            u'actual_days': 45
        }
        self.assertEqual(result, expected)

    def test_check_exceding_days_overwrite__Yes_but_jumped(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")

        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-11", "2017-03-27")
        params = {
            "som_skip_if_20TD_00_and_less_than_days": 69,
            "inc_days_maximeter": 1,
            "n_days_bimensual": 10,
            "n_days_first_invoice": 14,
            "n_days_mensual": 10,
            "n_days_not_estimable": 14
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        fact.tarifa_acces_id.name = u'2.0TD'
        fact.polissa_id.llista_preu.name = u'2.0TD_SOM'
        fact.polissa_id.autoconsumo = u'00'
        result = self.vali_obj.check_exceding_days(self.txn.cursor, self.txn.user, fact, params)
        self.assertEqual(result, None)

    def test_check_exceding_days_overwrite__Yes_but_not_jumped(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")

        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-11", "2017-03-27")
        params = {
            "som_skip_if_20TD_00_and_less_than_days": 33,
            "inc_days_maximeter": 1,
            "n_days_bimensual": 10,
            "n_days_first_invoice": 14,
            "n_days_mensual": 10,
            "n_days_not_estimable": 14
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        fact.tarifa_acces_id.name = u'2.0TD'
        fact.polissa_id.llista_preu.name = u'2.0TD_SOM'
        fact.polissa_id.autoconsumo = u'00'

        result = self.vali_obj.check_exceding_days(self.txn.cursor, self.txn.user, fact, params)
        expected = {
            u'polissa_state': u'activa',
            u'expected_days': 28,
            u'margin': 10,
            u'actual_days': 45
        }
        self.assertEqual(result, expected)

    def test_check_exceding_days_overwrite__not_jumped_wrong_tarifa(self):
        """Skip no s'aplica si tarifa_acces != 2.0TD"""
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-11", "2017-03-27")
        params = {
            "som_skip_if_20TD_00_and_less_than_days": 69,
            "inc_days_maximeter": 1,
            "n_days_bimensual": 10,
            "n_days_first_invoice": 14,
            "n_days_mensual": 10,
            "n_days_not_estimable": 14
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        fact.tarifa_acces_id.name = u'3.0TD'  # <-- diferent!
        fact.polissa_id.llista_preu.name = u'2.0TD_SOM'
        fact.polissa_id.autoconsumo = u'00'
        result = self.vali_obj.check_exceding_days(
            self.txn.cursor, self.txn.user, fact, params
        )
        self.assertIsNotNone(result)

    def test_check_exceding_days_overwrite__not_jumped_with_autoconsum(self):
        """Skip no s'aplica si autoconsum != 00"""
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-11", "2017-03-27")
        params = {
            "som_skip_if_20TD_00_and_less_than_days": 69,
            "inc_days_maximeter": 1,
            "n_days_bimensual": 10,
            "n_days_first_invoice": 14,
            "n_days_mensual": 10,
            "n_days_not_estimable": 14
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        fact.tarifa_acces_id.name = u'2.0TD'
        fact.polissa_id.llista_preu.name = u'2.0TD_SOM'
        fact.polissa_id.autoconsumo = u'41'  # <-- té autoconsum!
        result = self.vali_obj.check_exceding_days(
            self.txn.cursor, self.txn.user, fact, params
        )
        self.assertIsNotNone(result)

    @mock.patch('giscedata_facturacio.giscedata_facturacio.GiscedataFacturacioFactura.get_max_consume_by_contract')  # noqa: E501
    def test_check_consume_by_amount_overwrite__Yes(self, get_max_consume_by_contract_mock_function):  # noqa: E501
        get_max_consume_by_contract_mock_function.return_value = 1.0
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-11", "2017-03-27")
        params = {
            "min_periods": 12,
            "n_months": 12,
            "overuse_amount": 1.0,
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        result = self.vali_obj.check_consume_by_amount(self.txn.cursor, self.txn.user, fact, params)
        expected = {
            u'n_months': 12,
            u'invoice_consume': 3.0,
            u'margin': 1.0,
            u'maximum_consume': 1.0,
        }
        self.assertEqual(result, expected)

    @mock.patch('giscedata_facturacio.giscedata_facturacio.GiscedataFacturacioFactura.get_max_consume_by_contract')  # noqa: E501
    def test_check_consume_by_amount_overwrite__Yes_but_jumped(self, get_max_consume_by_contract_mock_function):  # noqa: E501
        get_max_consume_by_contract_mock_function.return_value = 1.0
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-11", "2017-03-27")
        params = {
            "som_skip_if_20TD_00_and_less_than_kWh": 1000,
            "min_periods": 12,
            "n_months": 12,
            "overuse_amount": 1.0,
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        fact.tarifa_acces_id.name = u'2.0TD'
        fact.polissa_id.llista_preu.name = u'2.0TD_SOM'
        fact.polissa_id.autoconsumo = u'00'
        result = self.vali_obj.check_consume_by_amount(self.txn.cursor, self.txn.user, fact, params)
        self.assertEqual(result, None)

    @mock.patch('giscedata_facturacio.giscedata_facturacio.GiscedataFacturacioFactura.get_max_consume_by_contract')  # noqa: E501
    def test_check_consume_by_amount_overwrite__Yes_but_not_jumped(self, get_max_consume_by_contract_mock_function):  # noqa: E501
        get_max_consume_by_contract_mock_function.return_value = 1.0
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-11", "2017-03-27")
        params = {
            "som_skip_if_20TD_00_and_less_than_kWh": 2,
            "min_periods": 12,
            "n_months": 12,
            "overuse_amount": 1.0,
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        fact.tarifa_acces_id.name = u'2.0TD'
        fact.polissa_id.llista_preu.name = u'2.0TD_SOM'
        fact.polissa_id.autoconsumo = u'00'
        result = self.vali_obj.check_consume_by_amount(self.txn.cursor, self.txn.user, fact, params)
        expected = {
            u'n_months': 12,
            u'invoice_consume': 3.0,
            u'margin': 1.0,
            u'maximum_consume': 1.0,
        }
        self.assertEqual(result, expected)

    @mock.patch('giscedata_facturacio.giscedata_facturacio.GiscedataFacturacioFactura.get_max_consume_by_contract')  # noqa: E501
    def test_check_consume_by_amount_overwrite__not_jumped_wrong_tarifa(self, get_max_consume_by_contract_mock_function):  # noqa: E501
        """Skip no s'aplica si tarifa_acces != 2.0TD"""
        get_max_consume_by_contract_mock_function.return_value = 1.0
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-11", "2017-03-27")
        params = {
            "som_skip_if_20TD_00_and_less_than_kWh": 1000,
            "min_periods": 12,
            "n_months": 12,
            "overuse_amount": 1.0,
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        fact.tarifa_acces_id.name = u'3.0TD'  # <-- diferent!
        fact.polissa_id.llista_preu.name = u'2.0TD_SOM'
        fact.polissa_id.autoconsumo = u'00'
        result = self.vali_obj.check_consume_by_amount(self.txn.cursor, self.txn.user, fact, params)
        self.assertIsNotNone(result)

    @mock.patch('giscedata_facturacio.giscedata_facturacio.GiscedataFacturacioFactura.get_max_consume_by_contract')  # noqa: E501
    def test_check_consume_by_amount_overwrite__not_jumped_with_autoconsum(self, get_max_consume_by_contract_mock_function):  # noqa: E501
        """Skip no s'aplica si autoconsum != 00"""
        get_max_consume_by_contract_mock_function.return_value = 1.0
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-11", "2017-03-27")
        params = {
            "som_skip_if_20TD_00_and_less_than_kWh": 1000,
            "min_periods": 12,
            "n_months": 12,
            "overuse_amount": 1.0,
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        fact.tarifa_acces_id.name = u'2.0TD'
        fact.polissa_id.llista_preu.name = u'2.0TD_SOM'
        fact.polissa_id.autoconsumo = u'41'  # <-- té autoconsum!
        result = self.vali_obj.check_consume_by_amount(self.txn.cursor, self.txn.user, fact, params)
        self.assertIsNotNone(result)

    def test_check_invoice_from_delayed_contract_overwrite__No(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        params = {
            "max_delayed_days": 70,
            "today": "2017-04-29",
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        result = self.vali_obj.check_invoice_from_delayed_contract(
            self.txn.cursor, self.txn.user, fact, params)
        self.assertEqual(result, None)

    def test_check_invoice_from_delayed_contract_overwrite__Yes(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        params = {
            "max_delayed_days": 70,
            "today": "2017-05-30",
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        result = self.vali_obj.check_invoice_from_delayed_contract(
            self.txn.cursor, self.txn.user, fact, params)
        self.assertIsNotNone(result)

    def test_check_invoice_from_delayed_contract_overwrite__Yes_but_jumped(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        self.pol_obj.write(
            self.txn.cursor,
            self.txn.user,
            pol_id,
            {"data_ultima_lectura": "2017-03-10"},
        )
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        params = {
            "max_delayed_days": 70,
            "today": "2017-05-30",
            "som_skip_if_20TD_00_and_less_than_days": 90,
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        fact.tarifa_acces_id.name = u'2.0TD'
        fact.polissa_id.llista_preu.name = u'2.0TD_SOM'
        fact.polissa_id.autoconsumo = u'00'
        result = self.vali_obj.check_invoice_from_delayed_contract(
            self.txn.cursor, self.txn.user, fact, params)
        self.assertEqual(result, None)

    def test_check_invoice_from_delayed_contract_overwrite__Yes_but_not_jumped(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        params = {
            "max_delayed_days": 70,
            "today": "2017-05-30",
            "som_skip_if_20TD_00_and_less_than_days": 70,
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        fact.tarifa_acces_id.name = u'2.0TD'
        fact.polissa_id.llista_preu.name = u'2.0TD_SOM'
        fact.polissa_id.autoconsumo = u'00'
        result = self.vali_obj.check_invoice_from_delayed_contract(
            self.txn.cursor, self.txn.user, fact, params)
        self.assertIsNotNone(result)

    def test_check_consume_by_percentage_overwrite__No(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        params = {
            "min_amount": 0.0,
            "min_periods": 24,
            "n_months": 24,
            "overuse_percentage": 65.0
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        result = self.vali_obj.check_consume_by_percentage(
            self.txn.cursor, self.txn.user, fact, params)
        self.assertEqual(result, None)

    @mock.patch(
        'giscedata_facturacio.giscedata_facturacio.'
        'GiscedataFacturacioFactura.get_max_consume_by_contract'
    )
    def test_check_consume_by_percentage_overwrite__Yes(
        self, get_max_consume_by_contract
    ):
        get_max_consume_by_contract.return_value = 0.1
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        self.prepare_contract(pol_id, "2017-01-01", "2017-02-18")
        inv_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.modify_invoice(inv_id, pol_id, "2017-02-18", "2017-03-17")
        params = {
            "min_amount": 0.0,
            "min_periods": 24,
            "n_months": 24,
            "overuse_percentage": 65.0
        }
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, inv_id)
        result = self.vali_obj.check_consume_by_percentage(
            self.txn.cursor, self.txn.user, fact, params)
        self.assertIsNotNone(result)

    def test_prefilter_parameters_are_configured(self):
        warning_obj = self.model("giscedata.facturacio.validation.warning.template")
        warning_ids = warning_obj.search(
            self.txn.cursor, self.txn.user,
            [("code", "in", ["F001", "F003", "F009", "F017"])]
        )
        parameters_by_code = dict([
            (warning["code"], warning["parameters"])
            for warning in warning_obj.read(
                self.txn.cursor, self.txn.user, warning_ids, ["code", "parameters"]
            )
        ])
        self.assertEqual(
            parameters_by_code["F001"]["som_skip_if_20TD_00_and_less_than_kWh"], 1000
        )
        self.assertEqual(
            parameters_by_code["F003"]["som_skip_if_20TD_00_and_less_than_kWh"], 1000
        )
        self.assertEqual(
            parameters_by_code["F009"]["som_skip_if_20TD_00_and_less_than_days"], 90
        )
        self.assertEqual(
            parameters_by_code["F017"]["som_skip_if_20TD_00_and_less_than_days"], 90
        )

    @mock.patch(
        'giscedata_facturacio.giscedata_facturacio.'
        'GiscedataFacturacioFactura.get_max_consume_by_contract'
    )
    def test_check_consume_by_percentage_prefilter__suppresses_at_1000_kwh_with_real_origins(
        self, get_max_consume_by_contract
    ):
        get_max_consume_by_contract.return_value = 1.0
        fact = self.prepare_f001_fact(1000, ["10", "30"])
        result = self.vali_obj.check_consume_by_percentage(
            self.txn.cursor, self.txn.user, fact, self.f001_parameters()
        )
        self.assertIsNone(result)

    @mock.patch(
        'giscedata_facturacio.giscedata_facturacio.'
        'GiscedataFacturacioFactura.get_max_consume_by_contract'
    )
    def test_check_consume_by_percentage_prefilter__does_not_suppress_with_estimated_origin(
        self, get_max_consume_by_contract
    ):
        get_max_consume_by_contract.return_value = 1.0
        fact = self.prepare_f001_fact(1000, ["40"])
        result = self.vali_obj.check_consume_by_percentage(
            self.txn.cursor, self.txn.user, fact, self.f001_parameters()
        )
        self.assertIsNotNone(result)

    @mock.patch(
        'giscedata_facturacio.giscedata_facturacio.'
        'GiscedataFacturacioFactura.get_max_consume_by_contract'
    )
    def test_check_consume_by_percentage_prefilter__does_not_suppress_without_origin(
        self, get_max_consume_by_contract
    ):
        get_max_consume_by_contract.return_value = 1.0
        fact = self.prepare_f001_fact(1000, [False])
        result = self.vali_obj.check_consume_by_percentage(
            self.txn.cursor, self.txn.user, fact, self.f001_parameters()
        )
        self.assertIsNotNone(result)

    @mock.patch(
        'giscedata_facturacio.giscedata_facturacio.'
        'GiscedataFacturacioFactura.get_max_consume_by_contract'
    )
    def test_check_consume_by_percentage_prefilter__does_not_suppress_without_active_energy_readings(  # noqa: E501
        self, get_max_consume_by_contract
    ):
        get_max_consume_by_contract.return_value = 1.0
        fact = self.prepare_f001_fact(1000, [])
        result = self.vali_obj.check_consume_by_percentage(
            self.txn.cursor, self.txn.user, fact, self.f001_parameters()
        )
        self.assertIsNotNone(result)

    @mock.patch(
        'giscedata_facturacio.giscedata_facturacio.'
        'GiscedataFacturacioFactura.get_max_consume_by_contract'
    )
    def test_check_consume_by_percentage_prefilter__does_not_suppress_above_1000_kwh(
        self, get_max_consume_by_contract
    ):
        get_max_consume_by_contract.return_value = 1.0
        fact = self.prepare_f001_fact(1001, ["10"])
        result = self.vali_obj.check_consume_by_percentage(
            self.txn.cursor, self.txn.user, fact, self.f001_parameters()
        )
        self.assertTrue(get_max_consume_by_contract.called)
        self.assertIsNotNone(result)

    @mock.patch(
        'giscedata_facturacio.giscedata_facturacio.'
        'GiscedataFacturacioFactura.get_max_consume_by_contract'
    )
    def test_check_consume_by_percentage_prefilter__suppresses_with_insular_tariff(
        self, get_max_consume_by_contract
    ):
        get_max_consume_by_contract.return_value = 1.0
        fact = self.prepare_f001_fact(1000, ["10"])
        self.prepare_som_20td_fact(fact, u"2.0TD_SOM_INSULAR")
        result = self.vali_obj.check_consume_by_percentage(
            self.txn.cursor, self.txn.user, fact, self.f001_parameters()
        )
        self.assertIsNone(result)

    def prepare_f017_fact(self, policy_reference_date, origin_codes):
        fact = self.prepare_f001_fact(1000, origin_codes)
        self.pol_obj.write(
            self.txn.cursor,
            self.txn.user,
            fact.polissa_id.id,
            {"data_ultima_lectura": policy_reference_date},
        )
        fact = self.fact_obj.browse(self.txn.cursor, self.txn.user, fact.id)
        return self.prepare_som_20td_fact(fact)

    def test_check_invoice_from_delayed_contract_prefilter__suppresses_at_90_days(self):
        fact = self.prepare_f017_fact("2017-03-01", [])
        self.assertLess(fact.dies, 90)
        result = self.vali_obj.check_invoice_from_delayed_contract(
            self.txn.cursor, self.txn.user, fact, self.f017_parameters()
        )
        self.assertIsNone(result)

    def test_check_invoice_from_delayed_contract_prefilter__does_not_suppress_at_91_days(self):
        fact = self.prepare_f017_fact("2017-02-28", [])
        self.assertLess(fact.dies, 90)
        result = self.vali_obj.check_invoice_from_delayed_contract(
            self.txn.cursor, self.txn.user, fact, self.f017_parameters()
        )
        self.assertIsNotNone(result)

    def test_check_invoice_from_delayed_contract_prefilter__suppresses_with_insular_tariff(self):
        fact = self.prepare_f017_fact("2017-03-01", [])
        self.assertLess(fact.dies, 90)
        self.prepare_som_20td_fact(fact, u"2.0TD_SOM_INSULAR")
        result = self.vali_obj.check_invoice_from_delayed_contract(
            self.txn.cursor, self.txn.user, fact, self.f017_parameters()
        )
        self.assertIsNone(result)

    def test_check_invoice_from_delayed_contract_prefilter__suppresses_with_non_real_and_missing_origins(  # noqa: E501
        self,
    ):
        fact = self.prepare_f017_fact("2017-03-01", ["40", False])
        self.assertLess(fact.dies, 90)
        result = self.vali_obj.check_invoice_from_delayed_contract(
            self.txn.cursor, self.txn.user, fact, self.f017_parameters()
        )
        self.assertIsNone(result)
