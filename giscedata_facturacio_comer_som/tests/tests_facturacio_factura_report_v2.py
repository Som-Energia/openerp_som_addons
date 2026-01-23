# -*- coding: utf-8 -*-

from destral import testing
from destral.transaction import Transaction


class Tests_FacturacioFacturaReportV2_base(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user

        self.rv2_obj = self.model("giscedata.facturacio.factura.report.v2")
        self.rsom_obj = self.model("giscedata.facturacio.factura.report")
        self.factura_obj = self.model("giscedata.facturacio.factura")
        self.pol_obj = self.model("giscedata.polissa")
        self.mod_obj = self.model("giscedata.polissa.modcontractual")
        self.rep_obj = self.model("giscedata.facturacio.factura.repartiment")
        self.repl_oj = self.model("giscedata.facturacio.factura.repartiment.linia")
        self.mix_obj = self.model("giscedata.facturacio.factura.mix.energetic")
        self.mixl_obj = self.model("giscedata.facturacio.factura.mix.energetic.linia")

        self.setup_langs()
        self.maxDiff = None

    def tearDown(self):
        self.txn.stop()

    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def get_fixture(self, model, reference):
        imd_obj = self.model("ir.model.data")
        return imd_obj.get_object_reference(self.txn.cursor, self.txn.user, model, reference)[1]

    def setup_langs(self):
        lang_obj = self.model("res.lang")
        lang_obj.create(self.cursor, self.uid, {"name": "cas", "code": "es_ES"})
        lang_obj.create(self.cursor, self.uid, {"name": "cat", "code": "ca_ES"})

    def setup_polissa(self, factura_id):
        fact = self.factura_obj.browse(self.cursor, self.uid, factura_id)
        self.mod_obj.create(self.cursor, self.uid, {
            "polissa_id": fact.polissa_id.id,
            "tarifa": fact.polissa_id.tarifa.id,
            "data_inici": "2016-01-01",
            "data_final": "2024-01-01",
            "cups": fact.polissa_id.cups.id,
            "tipus": 'mod',
            "name": '1',
            "tensio_normalitzada": 1,
            "potencia": 1,
            "tensio": 220,
            "tipus_subseccio": '00',
            "distribuidora": 1,
            "tipo_pago": 1,
            "notificacio": 'titular',
            "trafo": 0.0,
            "facturacio": 2,
            "facturacio_potencia": 'icp',
            "potencies_periode": 'P1: 3.4 P2: 3.4',
            "titular": fact.polissa_id.titular.id,
            "pagador": fact.polissa_id.titular.id,
        })
        self.factura_obj.write(self.cursor, self.uid, factura_id, {
            "address_contact_id": fact.polissa_id.direccio_pagament.id,
        })

        rep_id = self.rep_obj.create(self.cursor, self.uid, {
            "num_boe": "test",
            "data_inici": "2016-01-01",
            "data_final": "2024-01-01",
        })
        self.repl_oj.create(self.cursor, self.uid, {
            "repartiment_id": rep_id,
            "codi": "r",
            "percentatge": 20.0,
        })
        self.repl_oj.create(self.cursor, self.uid, {
            "repartiment_id": rep_id,
            "codi": "d",
            "percentatge": 20.0,
        })
        self.repl_oj.create(self.cursor, self.uid, {
            "repartiment_id": rep_id,
            "codi": "s",
            "percentatge": 40.0,
        })
        self.repl_oj.create(self.cursor, self.uid, {
            "repartiment_id": rep_id,
            "codi": "a",
            "percentatge": 20.0,
        })
        mix_id = self.mix_obj.create(self.cursor, self.uid, {
            "name": "test",
            "entitat": "comer",
            "inici": "2016-01-01",
            "final": "2024-01-01",
        })
        self.mixl_obj.create(self.cursor, self.uid, {
            'name': 'renovable',
            'mix_id': mix_id,
            'percentatge': 100.0,
        })

        mix_id = self.mix_obj.create(self.cursor, self.uid, {
            "name": "test",
            "entitat": "estatal",
            "inici": "2016-01-01",
            "final": "2024-01-01",
        })
        self.mixl_obj.create(self.cursor, self.uid, {
            'name': 'nuclear',
            'mix_id': mix_id,
            'percentatge': 100.0,
        })
        fact.lectures_energia_ids[0].write({"name": '2.0TD (P1)'})
        fact.partner_id.write({'lang': 'ca_ES'})
        fact.write({'date_due': '2024-12-31'})
        fact.polissa_id.titular.write({'vat': 'ES11111111H'})


class Tests_FacturacioFacturaReportV2(Tests_FacturacioFacturaReportV2_base):
    def test__get_data__returns_something(self):
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.setup_polissa(f_id)

        rv2_data = self.rv2_obj.get_data(self.cursor, self.uid, f_id, context={})
        som_data = self.rsom_obj.get_components_data_dict(
            self.cursor, self.uid, f_id, context={}
        )

        self.assertTrue("components_som" in rv2_data)

        def normalize_nested(d):
            new_dict = {}
            for k, v in d.iteritems():
                if isinstance(v, dict):
                    new_dict[k] = normalize_nested(v)
                else:
                    new_dict[k] = False if v == '' else v
            return new_dict

        for component_name in rv2_data["components_som"].keys():
            self.assertEqual(
                normalize_nested(rv2_data["components_som"][component_name]),
                normalize_nested(som_data[component_name]),
            )

    def test__get_data_factura_som__denies_legacy_components(self):
        legacy_components = [
            'amount_destination',
            'contract_data',
            'emergency_complaints',
            'energy_consumption_graphic',
            'invoice_details_comments',
            'invoice_details_energy',
            'invoice_details_generation',
            'invoice_details_other_concepts',
            'invoice_details_power',
            'invoice_details_reactive',
            'invoice_details_tec271',
            'invoice_summary',
            'maximeter_readings_table',
            'meters',
            'reactive_readings_table',
            'readings_6x',
            'readings_g_table',
            'readings_table',
            'readings_text',
            'cnmc_comparator_qr_link',
        ]
        f_id = self.get_fixture("giscedata_facturacio", "factura_0001")
        self.setup_polissa(f_id)
        rv2_data = self.rv2_obj.get_data(
            self.cursor, self.uid, f_id, context={}
        )
        self.assertFalse(set(legacy_components) & set(rv2_data['components_som'].keys()))
