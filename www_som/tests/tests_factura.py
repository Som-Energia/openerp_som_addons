# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction
from datetime import datetime
import json


def remove_ids(results):
    return remove_from(results, ["id", "amount_total", "enviat", "visible"])


def remove_from(results, to_remove):
    for result in results:
        for item in to_remove:
            result.pop(item)
    return results


class TestFacturaWwwUltimesFactures(testing.OOTestCase):
    @classmethod
    def setUpClass(cls):
        """To avoid calling it for each test"""
        super(TestFacturaWwwUltimesFactures, cls).setUpClass()
        cls.openerp.install_module("giscedata_tarifas_pagos_capacidad_20170101")
        cls.openerp.install_module("giscedata_tarifas_peajes_20170101")
        cls.openerp.install_module("som_account_invoice_pending")

    def setUp(self):
        self.imd_obj = self.model("ir.model.data")
        self.cfg = self.model("res.config")
        self.par_obj = self.model("res.partner")
        self.pol_obj = self.model("giscedata.polissa")
        self.fact_obj = self.model("giscedata.facturacio.factura")
        self.i_obj = self.model("account.invoice")
        self.ips_obj = self.model("account.invoice.pending.state")
        self.msr_obj = self.model("giscedata.lectures.lectura")
        self.wz_mi_obj = self.model("wizard.manual.invoice")
        self.journal_obj = self.model("account.journal")
        self.am_obj = self.model("account.move")
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.correct_ps_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "account_invoice_pending", "default_invoice_pending_state"
        )[1]
        self.fraccio_ps_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_account_invoice_pending", "pacte_fraccio_pending_state"
        )[1]
        self.no_pagable_ps_id = self.imd_obj.get_object_reference(
            self.cursor, self.uid, "som_account_invoice_pending", "pacte_fraccio_pending_state"
        )[1]

        self.ps_correct = []
        for module, name in [
            ("giscedata_facturacio_comer_bono_social", "correct_bono_social_pending_state"),
            ("account_invoice_pending", "default_invoice_pending_state"),
        ]:
            self.ps_correct.append(
                str(self.imd_obj.get_object_reference(self.cursor, self.uid, module, name)[1])
            )

        self.ps_fraccio = []
        for module, name in [
            ("som_account_invoice_pending", "pacte_fraccio_pending_state"),
            ("som_account_invoice_pending", "default_pacte_fraccio_pending_state"),
            ("som_account_invoice_pending", "fracc_manual_bo_social_pending_state"),
            ("som_account_invoice_pending", "fracc_manual_default_pending_state"),
        ]:
            self.ps_fraccio.append(
                str(self.imd_obj.get_object_reference(self.cursor, self.uid, module, name)[1])
            )

        self.ps_no_pagables = []
        for module, name in [
            ("som_account_invoice_pending", "pacte_fraccio_pending_state"),
            ("som_account_invoice_pending", "default_pacte_fraccio_pending_state"),
            ("som_account_invoice_pending", "fracc_manual_bo_social_pending_state"),
            ("som_account_invoice_pending", "fracc_manual_default_pending_state"),
        ]:
            self.ps_no_pagables.append(
                str(self.imd_obj.get_object_reference(self.cursor, self.uid, module, name)[1])
            )

        self.cfg.set(
            self.cursor,
            self.uid,
            "cobraments_ps_correcte",
            "[{}]".format(",".join(self.ps_correct)),
        )
        self.cfg.set(
            self.cursor, self.uid, "cobraments_ps_fraccio", "[{}]".format(",".join(self.ps_fraccio))
        )
        self.cfg.set(
            self.cursor,
            self.uid,
            "cobraments_ps_no_pagable",
            "[{}]".format(",".join(self.ps_no_pagables)),
        )

    def tearDown(self):
        self.txn.stop()

    # Scenario contruction helpers
    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def get_fixture(self, model, reference):
        return self.imd_obj.get_object_reference(self.txn.cursor, self.txn.user, model, reference)[
            1
        ]

    def get_contract_payer_vat_name(self, pol_id):
        cursor = self.txn.cursor
        uid = self.txn.user

        payer_id = self.pol_obj.read(cursor, uid, pol_id, ["pagador"])["pagador"][0]
        vat = self.par_obj.read(cursor, uid, payer_id, ["vat"])["vat"]
        return vat

    def prepare_contract(self, pol_id, data_alta, data_ultima_lectura):
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
        self.pol_obj.write(cursor, uid, pol_id, vals)
        self.pol_obj.send_signal(cursor, uid, [pol_id], ["validar", "contracte"])
        contract = self.pol_obj.browse(cursor, uid, pol_id)
        for meter in contract.comptadors:
            for l in meter.lectures:
                l.unlink(context={})
            for lp in meter.lectures_pot:
                lp.unlink(context={})
            meter.write({"lloguer": False})
        return contract.comptadors[0].id

    def create_measure(self, meter_id, date_measure, measure):
        periode_id = self.get_fixture("giscedata_polissa", "p1_e_tarifa_20A_new")
        origen_id = self.get_fixture("giscedata_lectures", "origen10")

        vals = {
            "name": date_measure,
            "periode": periode_id,
            "lectura": measure,
            "tipus": "A",
            "comptador": meter_id,
            "observacions": "",
            "origen_id": origen_id,
        }
        return self.msr_obj.create(self.txn.cursor, self.txn.user, vals)

    def create_invoice(self, pol_id, meter_id, date_start, date_end, name, context=None):
        cursor = self.txn.cursor
        uid = self.txn.user

        journal_id = self.journal_obj.search(cursor, uid, [("code", "=", "ENERGIA")])[0]
        wz_fact_id = self.wz_mi_obj.create(cursor, uid, {})
        wz_fact = self.wz_mi_obj.browse(cursor, uid, wz_fact_id)
        wz_fact.write(
            {
                "polissa_id": pol_id,
                "date_start": date_start,
                "date_end": date_end,
                "journal_id": journal_id,
            }
        )
        wz_fact.action_manual_invoice()
        wz_fact = self.wz_mi_obj.browse(cursor, uid, wz_fact_id)
        inv_id = json.loads(wz_fact.invoice_ids)[0]

        if not context:
            context = {}
        context["number"] = name
        self.fact_obj.write(cursor, uid, inv_id, context)

        return inv_id

    def create_invoice_related(self, pol_id, meter_id, fact_id, context):
        cursor = self.txn.cursor
        uid = self.txn.user

        fact_vals = self.fact_obj.read(cursor, uid, fact_id, ["data_inici", "data_final", "number"])

        head = context.pop("number_head")
        return self.create_invoice(
            pol_id,
            meter_id,
            fact_vals["data_inici"],
            fact_vals["data_final"],
            head + fact_vals["number"],
            context,
        )

    def create_invoice_ab(self, pol_id, meter_id, fact_id, context):
        if not context:
            context = {}
        context["tipo_rectificadora"] = "B"
        context["type"] = "out_refund"
        context["ref"] = fact_id
        context["number_head"] = "AB-"

        return self.create_invoice_related(pol_id, meter_id, fact_id, context)

    def create_invoice_re(self, pol_id, meter_id, fact_id, context=None):
        if not context:
            context = {}
        context["tipo_rectificadora"] = "R"
        context["type"] = "out_invoice"
        context["ref"] = fact_id
        context["number_head"] = "RE-"

        return self.create_invoice_related(pol_id, meter_id, fact_id, context)

    def create_pending_state(self, fact_id, name, weight=10, process_id=1):
        ips_id = self.ips_obj.create(
            self.cursor,
            self.uid,
            {
                "process_id": process_id,
                "name": name,
                "weight": weight,
            },
        )
        self.set_pending_state(fact_id, ips_id)
        return ips_id

    def set_pending_state(self, fact_id, pending_state_id):
        inv_id = self.fact_obj.read(self.cursor, self.uid, fact_id, ["invoice_id"])["invoice_id"][0]
        self.i_obj.set_pending(self.cursor, self.uid, inv_id, pending_state_id)

    def create_dummy_group_move(self, inv_id):
        am_id = self.am_obj.create(
            self.cursor,
            self.uid,
            {
                "name": "dummy",
                "journal_id": 1,
            },
        )
        self.fact_obj.write(self.cursor, self.uid, inv_id, {"group_move_id": am_id})

    # ------------------------------------------------------
    # Main cases testing functions for www_ultimes_factures
    # ------------------------------------------------------
    def test_www_ultimes_factures__bad_vat_nok(self):
        results = remove_ids(self.fact_obj.www_ultimes_factures(self.cursor, self.uid, "Not_a_VAT"))
        self.assertEqual([], results)

    def test_www_ultimes_factures__unknown_vat_nok(self):
        results = remove_ids(self.fact_obj.www_ultimes_factures(self.cursor, self.uid, "12345678Z"))
        self.assertEqual([], results)

    def test_www_ultimes_factures__vat_ok_empty(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        vat_name = self.get_contract_payer_vat_name(pol_id)
        results = remove_ids(self.fact_obj.www_ultimes_factures(self.cursor, self.uid, vat_name))
        self.assertEqual([], results)

    def test_www_ultimes_factures__1ok_ok(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        vat_name = self.get_contract_payer_vat_name(pol_id)
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-15")
        self.create_measure(meter_id, "2017-02-15", 8000)
        self.create_measure(meter_id, "2017-03-15", 8600)
        self.create_invoice(
            pol_id, meter_id, "2017-02-18", "2017-03-17", "FE0001", {"state": "paid"}
        )

        results = remove_ids(self.fact_obj.www_ultimes_factures(self.cursor, self.uid, vat_name))

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0],
            {
                "polissa_id": 1,
                "number": u"FE0001",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-02-18",
                "data_final": "2017-03-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )

    def test_www_ultimes_factures__2ok_ok(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-15")
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, "2017-02-15", 8000)
        self.create_measure(meter_id, "2017-03-15", 8600)
        self.create_measure(meter_id, "2017-04-15", 9000)
        self.create_invoice(
            pol_id, meter_id, "2017-02-18", "2017-03-17", "FE0001", {"state": "paid"}
        )
        self.create_invoice(
            pol_id, meter_id, "2017-03-18", "2017-04-17", "FE0002", {"state": "paid"}
        )

        results = remove_ids(self.fact_obj.www_ultimes_factures(self.cursor, self.uid, vat_name))

        self.assertEqual(len(results), 2)
        self.assertEqual(
            results[0],
            {
                "polissa_id": 1,
                "number": u"FE0002",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-03-18",
                "data_final": "2017-04-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[1],
            {
                "polissa_id": 1,
                "number": u"FE0001",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-02-18",
                "data_final": "2017-03-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )

    def test_www_ultimes_factures__2ok_1draft_ok(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-15")
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, "2017-02-15", 8000)
        self.create_measure(meter_id, "2017-03-15", 8600)
        self.create_measure(meter_id, "2017-04-15", 9000)
        self.create_measure(meter_id, "2017-05-15", 9350)
        self.create_invoice(
            pol_id, meter_id, "2017-02-18", "2017-03-17", "FE0001", {"state": "paid"}
        )
        self.create_invoice(
            pol_id, meter_id, "2017-03-18", "2017-04-17", "FE0002", {"state": "paid"}
        )
        self.create_invoice(
            pol_id, meter_id, "2017-04-10", "2017-05-10", "FE0003", {"state": "draft"}
        )

        results = remove_ids(self.fact_obj.www_ultimes_factures(self.cursor, self.uid, vat_name))

        self.assertEqual(len(results), 2)
        self.assertEqual(
            results[0],
            {
                "polissa_id": 1,
                "number": u"FE0002",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-03-18",
                "data_final": "2017-04-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[1],
            {
                "polissa_id": 1,
                "number": u"FE0001",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-02-18",
                "data_final": "2017-03-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )

    def test_www_ultimes_factures__3ok_ok(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-15")
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, "2017-02-15", 8000)
        self.create_measure(meter_id, "2017-03-15", 8600)
        self.create_measure(meter_id, "2017-04-15", 9000)
        self.create_measure(meter_id, "2017-05-15", 9350)
        self.create_invoice(
            pol_id, meter_id, "2017-02-18", "2017-03-17", "FE0001", {"state": "paid"}
        )
        self.create_invoice(
            pol_id, meter_id, "2017-03-18", "2017-04-17", "FE0002", {"state": "paid"}
        )
        self.create_invoice(
            pol_id, meter_id, "2017-04-18", "2017-05-17", "FE0003", {"state": "paid"}
        )

        results = remove_ids(self.fact_obj.www_ultimes_factures(self.cursor, self.uid, vat_name))

        self.assertEqual(len(results), 3)
        self.assertEqual(
            results[0],
            {
                "polissa_id": 1,
                "number": u"FE0003",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-04-18",
                "data_final": "2017-05-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[1],
            {
                "polissa_id": 1,
                "number": u"FE0002",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-03-18",
                "data_final": "2017-04-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[2],
            {
                "polissa_id": 1,
                "number": u"FE0001",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-02-18",
                "data_final": "2017-03-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )

    def test_www_ultimes_factures__3ok_and_1ab_ok(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-15")
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, "2017-02-15", 8000)
        self.create_measure(meter_id, "2017-03-15", 8600)
        self.create_measure(meter_id, "2017-04-15", 9000)
        self.create_measure(meter_id, "2017-05-15", 9350)
        self.create_invoice(
            pol_id, meter_id, "2017-02-18", "2017-03-17", "FE0001", {"state": "paid"}
        )
        self.create_invoice(
            pol_id, meter_id, "2017-03-18", "2017-04-17", "FE0002", {"state": "paid"}
        )
        inv3_id = self.create_invoice(
            pol_id, meter_id, "2017-04-18", "2017-05-17", "FE0003", {"state": "paid"}
        )
        self.create_invoice_ab(pol_id, meter_id, inv3_id, {"state": "paid"})

        results = remove_ids(self.fact_obj.www_ultimes_factures(self.cursor, self.uid, vat_name))

        self.assertEqual(len(results), 4)
        self.assertEqual(
            results[0],
            {
                "polissa_id": 1,
                "number": u"AB-FE0003",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-04-18",
                "data_final": "2017-05-17",
                "estat_pagament": "PAGADA",
                "tipus": "ABONADORA",
            },
        )
        self.assertEqual(
            results[1],
            {
                "polissa_id": 1,
                "number": u"FE0003",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-04-18",
                "data_final": "2017-05-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[2],
            {
                "polissa_id": 1,
                "number": u"FE0002",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-03-18",
                "data_final": "2017-04-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[3],
            {
                "polissa_id": 1,
                "number": u"FE0001",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-02-18",
                "data_final": "2017-03-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )

    def test_www_ultimes_factures__3ok_and_1ab_1re_ok(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-15")
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, "2017-02-15", 8000)
        self.create_measure(meter_id, "2017-03-15", 8600)
        self.create_measure(meter_id, "2017-04-15", 9000)
        self.create_measure(meter_id, "2017-05-15", 9350)
        self.create_invoice(
            pol_id, meter_id, "2017-02-18", "2017-03-17", "FE0001", {"state": "paid"}
        )
        self.create_invoice(
            pol_id, meter_id, "2017-03-18", "2017-04-17", "FE0002", {"state": "paid"}
        )
        inv3_id = self.create_invoice(
            pol_id, meter_id, "2017-04-18", "2017-05-17", "FE0003", {"state": "paid"}
        )
        self.create_invoice_ab(pol_id, meter_id, inv3_id, {"state": "paid"})
        self.create_invoice_re(pol_id, meter_id, inv3_id, {"state": "paid"})

        results = remove_ids(self.fact_obj.www_ultimes_factures(self.cursor, self.uid, vat_name))

        self.assertEqual(len(results), 5)
        self.assertEqual(
            results[0],
            {
                "polissa_id": 1,
                "number": u"RE-FE0003",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-04-18",
                "data_final": "2017-05-17",
                "estat_pagament": "PAGADA",
                "tipus": "RECTIFICADORA",
            },
        )
        self.assertEqual(
            results[1],
            {
                "polissa_id": 1,
                "number": u"AB-FE0003",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-04-18",
                "data_final": "2017-05-17",
                "estat_pagament": "PAGADA",
                "tipus": "ABONADORA",
            },
        )
        self.assertEqual(
            results[2],
            {
                "polissa_id": 1,
                "number": u"FE0003",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-04-18",
                "data_final": "2017-05-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[3],
            {
                "polissa_id": 1,
                "number": u"FE0002",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-03-18",
                "data_final": "2017-04-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[4],
            {
                "polissa_id": 1,
                "number": u"FE0001",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-02-18",
                "data_final": "2017-03-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )

    def test_www_ultimes_factures__3ok_and_1ab_1re_2_not_visible_ok(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-15")
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, "2017-02-15", 8000)
        self.create_measure(meter_id, "2017-03-15", 8600)
        self.create_measure(meter_id, "2017-04-15", 9000)
        self.create_measure(meter_id, "2017-05-15", 9350)
        self.create_invoice(
            pol_id, meter_id, "2017-02-18", "2017-03-17", "FE0001", {"state": "paid"}
        )
        self.create_invoice(
            pol_id, meter_id, "2017-03-18", "2017-04-17", "FE0002", {"state": "paid"}
        )
        inv3_id = self.create_invoice(
            pol_id,
            meter_id,
            "2017-04-18",
            "2017-05-17",
            "FE0003",
            {"state": "paid", "visible_ov": False},
        )
        self.create_invoice_ab(pol_id, meter_id, inv3_id, {"state": "paid", "visible_ov": False})
        self.create_invoice_re(pol_id, meter_id, inv3_id, {"state": "paid"})

        results = remove_ids(self.fact_obj.www_ultimes_factures(self.cursor, self.uid, vat_name))

        self.assertEqual(len(results), 5)
        self.assertEqual(
            results[0],
            {
                "polissa_id": 1,
                "number": u"RE-FE0003",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-04-18",
                "data_final": "2017-05-17",
                "estat_pagament": "PAGADA",
                "tipus": "RECTIFICADORA",
            },
        )
        self.assertEqual(
            results[1],
            {
                "polissa_id": 1,
                "number": u"AB-FE0003",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-04-18",
                "data_final": "2017-05-17",
                "estat_pagament": "PAGADA",
                "tipus": "ABONADORA",
            },
        )
        self.assertEqual(
            results[2],
            {
                "polissa_id": 1,
                "number": u"FE0003",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-04-18",
                "data_final": "2017-05-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[3],
            {
                "polissa_id": 1,
                "number": u"FE0002",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-03-18",
                "data_final": "2017-04-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[4],
            {
                "polissa_id": 1,
                "number": u"FE0001",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-02-18",
                "data_final": "2017-03-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )

    def test_www_ultimes_factures__3ok_sent_not_paid_ok(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-15")
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, "2017-02-15", 8000)
        self.create_measure(meter_id, "2017-03-15", 8600)
        self.create_measure(meter_id, "2017-04-15", 9000)
        self.create_measure(meter_id, "2017-05-15", 9350)
        self.create_invoice(
            pol_id, meter_id, "2017-02-18", "2017-03-17", "FE0001", {"state": "open"}
        )
        self.create_invoice(
            pol_id, meter_id, "2017-03-18", "2017-04-17", "FE0002", {"state": "open"}
        )
        self.create_invoice(
            pol_id, meter_id, "2017-04-18", "2017-05-17", "FE0003", {"state": "open"}
        )

        results = remove_ids(self.fact_obj.www_ultimes_factures(self.cursor, self.uid, vat_name))

        self.assertEqual(len(results), 3)
        self.assertEqual(
            results[0],
            {
                "polissa_id": 1,
                "number": u"FE0003",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-04-18",
                "data_final": "2017-05-17",
                "estat_pagament": "EN_PROCES",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[1],
            {
                "polissa_id": 1,
                "number": u"FE0002",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-03-18",
                "data_final": "2017-04-17",
                "estat_pagament": "EN_PROCES",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[2],
            {
                "polissa_id": 1,
                "number": u"FE0001",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-02-18",
                "data_final": "2017-03-17",
                "estat_pagament": "EN_PROCES",
                "tipus": "ORDINARIA",
            },
        )

    def test_www_ultimes_factures__3ok_last_sent_not_paid_ok(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-15")
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, "2017-02-15", 8000)
        self.create_measure(meter_id, "2017-03-15", 8600)
        self.create_measure(meter_id, "2017-04-15", 9000)
        self.create_measure(meter_id, "2017-05-15", 9350)
        self.create_invoice(
            pol_id, meter_id, "2017-02-18", "2017-03-17", "FE0001", {"state": "paid"}
        )
        self.create_invoice(
            pol_id, meter_id, "2017-03-18", "2017-04-17", "FE0002", {"state": "paid"}
        )
        self.create_invoice(
            pol_id, meter_id, "2017-04-18", "2017-05-17", "FE0003", {"state": "open"}
        )

        results = remove_ids(self.fact_obj.www_ultimes_factures(self.cursor, self.uid, vat_name))

        self.assertEqual(len(results), 3)
        self.assertEqual(
            results[0],
            {
                "polissa_id": 1,
                "number": u"FE0003",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-04-18",
                "data_final": "2017-05-17",
                "estat_pagament": "EN_PROCES",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[1],
            {
                "polissa_id": 1,
                "number": u"FE0002",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-03-18",
                "data_final": "2017-04-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[2],
            {
                "polissa_id": 1,
                "number": u"FE0001",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-02-18",
                "data_final": "2017-03-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )

    def test_www_ultimes_factures__3ok_last_sent_not_paid_invisible_ok(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-15")
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, "2017-02-15", 8000)
        self.create_measure(meter_id, "2017-03-15", 8600)
        self.create_measure(meter_id, "2017-04-15", 9000)
        self.create_measure(meter_id, "2017-05-15", 9350)
        self.create_invoice(
            pol_id, meter_id, "2017-02-18", "2017-03-17", "FE0001", {"state": "paid"}
        )
        self.create_invoice(
            pol_id, meter_id, "2017-03-18", "2017-04-17", "FE0002", {"state": "open"}
        )
        self.create_invoice(
            pol_id,
            meter_id,
            "2017-04-18",
            "2017-05-17",
            "FE0003",
            {"state": "open", "visible_ov": False},
        )

        results = remove_ids(self.fact_obj.www_ultimes_factures(self.cursor, self.uid, vat_name))

        self.assertEqual(len(results), 3)
        self.assertEqual(
            results[0],
            {
                "polissa_id": 1,
                "number": u"FE0003",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-04-18",
                "data_final": "2017-05-17",
                "estat_pagament": "EN_PROCES",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[1],
            {
                "polissa_id": 1,
                "number": u"FE0002",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-03-18",
                "data_final": "2017-04-17",
                "estat_pagament": "EN_PROCES",
                "tipus": "ORDINARIA",
            },
        )
        self.assertEqual(
            results[2],
            {
                "polissa_id": 1,
                "number": u"FE0001",
                "date_invoice": datetime.today().strftime("%Y-%m-%d"),
                "data_inici": "2017-02-18",
                "data_final": "2017-03-17",
                "estat_pagament": "PAGADA",
                "tipus": "ORDINARIA",
            },
        )

    def test_www_ultimes_factures__AB_negatives_ok(self):
        pol_id = self.get_fixture("giscedata_polissa", "polissa_0001")
        meter_id = self.prepare_contract(pol_id, "2017-01-01", "2017-02-15")
        vat_name = self.get_contract_payer_vat_name(pol_id)
        self.create_measure(meter_id, "2017-02-15", 8000)
        self.create_measure(meter_id, "2017-03-15", 8600)
        self.create_measure(meter_id, "2017-04-15", 9000)
        self.create_measure(meter_id, "2017-05-15", 9350)
        inv1_id = self.create_invoice(
            pol_id, meter_id, "2017-02-18", "2017-03-17", "FE0001", {"state": "paid"}
        )
        inv2_id = self.create_invoice(
            pol_id, meter_id, "2017-03-18", "2017-04-17", "FE0002", {"state": "paid"}
        )
        inv3_id = self.create_invoice(
            pol_id, meter_id, "2017-04-18", "2017-05-17", "FE0003", {"state": "paid"}
        )
        self.create_invoice_ab(pol_id, meter_id, inv1_id, {"state": "paid"})
        self.create_invoice_ab(pol_id, meter_id, inv2_id, {"state": "paid"})
        self.create_invoice_ab(pol_id, meter_id, inv3_id, {"state": "paid"})
        self.create_invoice_re(pol_id, meter_id, inv1_id, {"state": "paid"})
        self.create_invoice_re(pol_id, meter_id, inv2_id, {"state": "paid"})
        self.create_invoice_re(pol_id, meter_id, inv3_id, {"state": "paid"})

        results = self.fact_obj.www_ultimes_factures(self.cursor, self.uid, vat_name)

        self.assertEqual(len(results), 9)

        self.assertEqual(results[0]["tipus"], "RECTIFICADORA")
        self.assertGreater(results[0]["amount_total"], 0)
        self.assertEqual(results[1]["tipus"], "RECTIFICADORA")
        self.assertGreater(results[1]["amount_total"], 0)
        self.assertEqual(results[2]["tipus"], "RECTIFICADORA")
        self.assertGreater(results[2]["amount_total"], 0)

        self.assertEqual(results[3]["tipus"], "ABONADORA")
        self.assertLess(results[3]["amount_total"], 0)
        self.assertEqual(results[4]["tipus"], "ABONADORA")
        self.assertLess(results[4]["amount_total"], 0)
        self.assertEqual(results[5]["tipus"], "ABONADORA")
        self.assertLess(results[5]["amount_total"], 0)

        self.assertEqual(results[6]["tipus"], "ORDINARIA")
        self.assertGreater(results[6]["amount_total"], 0)
        self.assertEqual(results[7]["tipus"], "ORDINARIA")
        self.assertGreater(results[7]["amount_total"], 0)
        self.assertEqual(results[8]["tipus"], "ORDINARIA")
        self.assertGreater(results[8]["amount_total"], 0)

    # ----------------------------------------------------
    # Main cases testing functions for www_estat_pagament
    # ----------------------------------------------------
    def test_www_estat_pagament_ov__cancel_ERROR(self):
        fact_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "cancel"})
        ret_value = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(ret_value, "ERROR")

    def test_www_estat_pagament_ov__draft_ERROR(self):
        fact_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "draft"})
        ret_value = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(ret_value, "ERROR")

    def test_www_estat_pagament_ov__open_correct_EN_PROCES(self):
        fact_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "open"})
        ret_value = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(ret_value, "EN_PROCES")

    def test_www_estat_pagament_ov__open_reclama_NO_PAGADA(self):
        fact_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "open"})
        ps_id = self.get_fixture("som_account_invoice_pending", "reclamacio_en_curs_pending_state")
        self.set_pending_state(fact_id, ps_id)
        ret_value = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(ret_value, "NO_PAGADA")

    def test_www_estat_pagament_ov__open_1f_NO_PAGADA(self):
        fact_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "open"})
        ps_id = self.get_fixture(
            "som_account_invoice_pending", "default_avis_impagament_pending_state"
        )
        self.set_pending_state(fact_id, ps_id)
        ret_value = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(ret_value, "NO_PAGADA")

    def test_www_estat_pagament_ov__open_3f_NO_PAGADA(self):
        fact_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "open"})
        ps_id = self.get_fixture(
            "som_account_invoice_pending", "notificacio_tall_imminent_enviada_pending_state"
        )
        self.set_pending_state(fact_id, ps_id)
        ret_value = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(ret_value, "NO_PAGADA")

    def test_www_estat_pagament_ov__open_4f_NO_PAGADA(self):
        fact_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "open"})
        ps_id = self.get_fixture(
            "som_account_invoice_pending", "esperant_segona_factura_impagada_pending_state"
        )
        self.set_pending_state(fact_id, ps_id)
        ret_value = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(ret_value, "NO_PAGADA")

    def test_www_estat_pagament_ov__open_6f_NO_PAGADA(self):
        fact_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "open"})
        ps_id = self.get_fixture("som_account_invoice_pending", "default_tall_pending_state")
        self.set_pending_state(fact_id, ps_id)
        ret_value = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(ret_value, "NO_PAGADA")

    def test_www_estat_pagament_ov__open_7f_ADV_NO_PAGADA(self):
        fact_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "open"})
        ps_id = self.get_fixture(
            "som_account_invoice_pending", "pendent_traspas_advocats_pending_state"
        )
        self.set_pending_state(fact_id, ps_id)
        ret_value = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(ret_value, "NO_PAGADA")

    def test_www_estat_pagament_ov__open_no_rec_NO_PAGADA(self):
        fact_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "open"})
        ps_id = self.get_fixture("som_account_invoice_pending", "no_reclamable_pending_state")
        self.set_pending_state(fact_id, ps_id)
        ret_value = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(ret_value, "NO_PAGADA")

    def test_www_estat_pagament_ov__open_pact_g_NO_PAGADA(self):
        fact_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "open"})
        ps_id = self.get_fixture("som_account_invoice_pending", "default_pacte_girar_pending_state")
        self.set_pending_state(fact_id, ps_id)
        ret_value = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(ret_value, "NO_PAGADA")

    def test_www_estat_pagament_ov__open_pact_t_NO_PAGADA(self):
        fact_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "open"})
        ps_id = self.get_fixture("som_account_invoice_pending", "pacte_transferencia_pending_state")
        self.set_pending_state(fact_id, ps_id)
        ret_value = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(ret_value, "NO_PAGADA")

    def test_www_estat_pagament_ov__open_pob_NO_PAGADA(self):
        fact_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "open"})
        ps_id = self.get_fixture(
            "som_account_invoice_pending", "pendent_consulta_probresa_pending_state"
        )
        self.set_pending_state(fact_id, ps_id)
        payment_state = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(payment_state, "NO_PAGADA")

    def test_www_estat_pagament_ov__paid_correct_group_move(self):
        fact_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "paid"})
        self.create_dummy_group_move(fact_id)
        payment_state = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(payment_state, "PAGADA")

        self.fact_obj.write(self.cursor, self.uid, fact_id, {"state": "open"})
        ps_id = self.get_fixture(
            "som_account_invoice_pending", "esperant_segona_factura_impagada_pending_state"
        )
        self.set_pending_state(fact_id, ps_id)
        payment_state = self.fact_obj.www_estat_pagament_ov(self.cursor, self.uid, fact_id)
        self.assertEqual(payment_state, "EN_PROCES")
