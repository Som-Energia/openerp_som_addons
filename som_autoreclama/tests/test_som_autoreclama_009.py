
# -*- coding: utf-8 -*-
import mock
import unittest
from ..models import giscedata_polissa
from test_som_autoreclama_base import SomAutoreclamaBaseTests, today_str


class SomAutoreclama009AutomationTest(SomAutoreclamaBaseTests):

    def test_create_ATC_R1_009_from_polissa_via_wizard__bad_f1(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "C",
        })

        with self.assertRaises(Exception) as context:
            _ = atc_obj.create_ATC_R1_009_from_polissa_via_wizard(
                self.cursor, self.uid, polissa_id, {}
            )

        msg = u"Error en la creació del CAC R1 009, no s'ha trobat F1 adient!!!"
        self.assertTrue(msg in context.exception.message)

    def test_create_ATC_R1_009_from_polissa_via_wizard__no_provider_invoice(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "N",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-01-01",
            "fecha_factura_hasta": "2015-01-31",
            "import_phase": 50,
        })

        with self.assertRaises(Exception) as context:
            _ = atc_obj.create_ATC_R1_009_from_polissa_via_wizard(
                self.cursor, self.uid, polissa_id, {}
            )

        msg = u"Error en la creació del CAC R1 009, l'F1 trobat no té factura de proveïdor id f1"
        self.assertTrue(msg in context.exception.message)

    def test_create_ATC_R1_009_from_polissa_via_wizard__one_ok(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "N",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-01-01",
            "fecha_factura_hasta": "2015-01-31",
            "import_phase": 50,
        })
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
            'payment_mode_id': 4,
        })

        atc_id = atc_obj.create_ATC_R1_009_from_polissa_via_wizard(
            self.cursor, self.uid, polissa_id, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "intercambi")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "009")])
        _, section_id = self.get_object_reference(
            "som_switching", "atc_section_factura"
        )
        tag_id = self.search_in("giscedata.atc.tag", [("name", "ilike", "%Autocac 009")])

        self.assertEqual(atc.name, u"AUTOCAC 009")
        self.assertEqual(atc.canal_id.id, channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id, subtipus_id)
        self.assertEqual(atc.polissa_id.id, polissa_id)
        self.assertEqual(atc.tag.id, tag_id)

        self.assertEqual(atc.tancar_cac_al_finalitzar_r1, True)
        self.assertEqual(atc.state, "pending")
        self.assertEqual(atc.agent_actual, "10")

        model, id = atc.ref.split(",")
        self.assertEqual(model, "giscedata.switching")
        model_obj = self.get_model(model)
        ref = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(ref.proces_id.name, u"R1")
        self.assertEqual(ref.step_id.name, u"01")
        self.assertEqual(ref.section_id.name, u"Switching")
        self.assertEqual(ref.cups_polissa_id.id, polissa_id)
        self.assertEqual(ref.state, u"open")
        self.assertEqual(ref.ref, u"giscedata.atc, {}".format(atc.id))

        model, id = ref.step_ids[0].pas_id.split(",")
        self.assertEqual(model, "giscedata.switching.r1.01")
        model_obj = self.get_model(model)
        pas = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(pas.subtipus_id.id, subtipus_id)
        self.assertEqual(pas.reclamacio_ids[0].num_factura, '1234567890ABCD')

    def test_create_ATC_R1_009_from_polissa_via_wizard__use_last_valid_f1(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 1)
        f1_id = f1_ids[0]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "N",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-01-01",
            "fecha_factura_hasta": "2015-01-31",
            "import_phase": 50,
        })
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
            'payment_mode_id': 4,
        })

        f1_id = f1_ids[1]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "ABCD987654321",
            "type_factura": "N",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-02-01",
            "fecha_factura_hasta": "2015-02-28",
            "import_phase": 40,
        })
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
            'payment_mode_id': 4,
        })

        atc_id = atc_obj.create_ATC_R1_009_from_polissa_via_wizard(
            self.cursor, self.uid, polissa_id, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "intercambi")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "009")])
        _, section_id = self.get_object_reference(
            "som_switching", "atc_section_factura"
        )
        tag_id = self.search_in("giscedata.atc.tag", [("name", "ilike", "%Autocac 009")])

        self.assertEqual(atc.name, u"AUTOCAC 009")
        self.assertEqual(atc.canal_id.id, channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id, subtipus_id)
        self.assertEqual(atc.polissa_id.id, polissa_id)
        self.assertEqual(atc.tag.id, tag_id)

        self.assertEqual(atc.tancar_cac_al_finalitzar_r1, True)
        self.assertEqual(atc.state, "pending")
        self.assertEqual(atc.agent_actual, "10")

        model, id = atc.ref.split(",")
        self.assertEqual(model, "giscedata.switching")
        model_obj = self.get_model(model)
        ref = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(ref.proces_id.name, u"R1")
        self.assertEqual(ref.step_id.name, u"01")
        self.assertEqual(ref.section_id.name, u"Switching")
        self.assertEqual(ref.cups_polissa_id.id, polissa_id)
        self.assertEqual(ref.state, u"open")
        self.assertEqual(ref.ref, u"giscedata.atc, {}".format(atc.id))

        model, id = ref.step_ids[0].pas_id.split(",")
        self.assertEqual(model, "giscedata.switching.r1.01")
        model_obj = self.get_model(model)
        pas = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(pas.subtipus_id.id, subtipus_id)
        self.assertEqual(pas.reclamacio_ids[0].num_factura, 'ABCD987654321')

    def test_create_ATC_R1_009_from_polissa_via_wizard__use_last_valid_f1_complex(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 2)
        f1_id = f1_ids[0]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "R",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-01-01",
            "fecha_factura_hasta": "2015-01-31",
            "import_phase": 50,
        })
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
            'payment_mode_id': 4,
        })

        f1_id = f1_ids[1]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "ABCD987654321",
            "type_factura": "G",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-02-01",
            "fecha_factura_hasta": "2015-02-28",
            "import_phase": 30,
        })
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
            'payment_mode_id': 4,
        })

        f1_id = f1_ids[2]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "FFFJJJJJJJJJJ",
            "type_factura": "N",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-03-01",
            "fecha_factura_hasta": "2015-03-30",
            "import_phase": 20,
        })
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
            'payment_mode_id': 4,
        })

        atc_id = atc_obj.create_ATC_R1_009_from_polissa_via_wizard(
            self.cursor, self.uid, polissa_id, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)

        channel_id = self.search_in("res.partner.canal", [("name", "ilike", "intercambi")])
        subtipus_id = self.search_in("giscedata.subtipus.reclamacio", [("name", "=", "009")])
        _, section_id = self.get_object_reference(
            "som_switching", "atc_section_factura"
        )

        self.assertEqual(atc.name, u"AUTOCAC 009")
        self.assertEqual(atc.canal_id.id, channel_id)
        self.assertEqual(atc.section_id.id, section_id)
        self.assertEqual(atc.subtipus_id.id, subtipus_id)
        self.assertEqual(atc.polissa_id.id, polissa_id)
        self.assertTrue(u"Autocac 009" in atc.tag.name)

        self.assertEqual(atc.tancar_cac_al_finalitzar_r1, True)
        self.assertEqual(atc.state, "pending")
        self.assertEqual(atc.agent_actual, "10")

        model, id = atc.ref.split(",")
        self.assertEqual(model, "giscedata.switching")
        model_obj = self.get_model(model)
        ref = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(ref.proces_id.name, u"R1")
        self.assertEqual(ref.step_id.name, u"01")
        self.assertEqual(ref.section_id.name, u"Switching")
        self.assertEqual(ref.cups_polissa_id.id, polissa_id)
        self.assertEqual(ref.state, u"open")
        self.assertEqual(ref.ref, u"giscedata.atc, {}".format(atc.id))

        model, id = ref.step_ids[0].pas_id.split(",")
        self.assertEqual(model, "giscedata.switching.r1.01")
        model_obj = self.get_model(model)
        pas = model_obj.browse(self.cursor, self.uid, int(id))

        self.assertEqual(pas.subtipus_id.id, subtipus_id)
        self.assertEqual(pas.reclamacio_ids[0].num_factura, 'ABCD987654321')

    def test_create_ATC_R1_009_from_polissa_via_wizard__error_has_a_previous_009(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "R",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-01-01",
            "fecha_factura_hasta": "2015-01-31",
            "import_phase": 50,
        })
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
            'payment_mode_id': 4,
        })

        atc_id = atc_obj.create_ATC_R1_009_from_polissa_via_wizard(
            self.cursor, self.uid, polissa_id, {}
        )

        with self.assertRaises(Exception) as context:
            _ = atc_obj.create_ATC_R1_009_from_polissa_via_wizard(
                self.cursor, self.uid, polissa_id, {}
            )

        msg = u"Error en la creació del CAC R1 009, ja n'hi ha un CAC  009 en estat obert o pendent amb id {}!!!".format(atc_id)  # noqa: E501
        self.assertTrue(msg in context.exception.message)

    def test_create_ATC_R1_009_from_polissa_via_wizard__previous_009(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "R",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-01-01",
            "fecha_factura_hasta": "2015-01-31",
            "import_phase": 50,
        })
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
            'payment_mode_id': 4,
        })

        atc_id = self.build_atc(log_days=60, subtype="009", polissa="polissa_0004")

        with self.assertRaises(Exception) as context:
            _ = atc_obj.create_ATC_R1_009_from_polissa_via_wizard(
                self.cursor, self.uid, polissa_id, {}
            )

        msg = u"Error en la creació del CAC R1 009, ja n'hi ha un CAC  009 en estat obert o pendent amb id {}!!!".format(atc_id)  # noqa: E501
        self.assertTrue(msg in context.exception.message)

    def test_create_ATC_R1_009_from_polissa_via_wizard__previous_036(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "R",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-01-01",
            "fecha_factura_hasta": "2015-01-31",
            "import_phase": 50,
        })
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
            'payment_mode_id': 4,
        })

        atc_id = self.build_atc(log_days=60, subtype="036", polissa="polissa_0004")

        with self.assertRaises(Exception) as context:
            _ = atc_obj.create_ATC_R1_009_from_polissa_via_wizard(
                self.cursor, self.uid, polissa_id, {}
            )

        msg = u"Error en la creació del CAC R1 009, ja n'hi ha un CAC 036 en estat obert o pendent amb id {}!!!".format(atc_id)  # noqa: E501
        self.assertTrue(msg in context.exception.message)

    def test_create_ATC_R1_009_from_polissa_via_wizard__previous_036_closed(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "R",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-01-01",
            "fecha_factura_hasta": "2015-01-31",
            "import_phase": 50,
        })
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
            'payment_mode_id': 4,
        })

        _ = self.build_atc(log_days=60, subtype="036", polissa="polissa_0004",
                           state='done', date_closed='2014-11-10')

        atc_id = atc_obj.create_ATC_R1_009_from_polissa_via_wizard(
            self.cursor, self.uid, polissa_id, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)
        self.assertEqual(atc.name, u"AUTOCAC 009")

    def test_create_ATC_R1_009_from_polissa_via_wizard__tag_one_indexed(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )
        pol_obj.write(self.cursor, self.uid, polissa_id, {'mode_facturacio': 'index'})

        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "R",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-01-01",
            "fecha_factura_hasta": "2015-01-31",
            "import_phase": 50,
        })
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
            'payment_mode_id': 4,
        })

        atc_id = atc_obj.create_ATC_R1_009_from_polissa_via_wizard(
            self.cursor, self.uid, polissa_id, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)

        tag_id = self.get_object_reference('som_autoreclama', 'tag_som_autoreclama_009_GEGC')[1]

        self.assertEqual(atc.name, u"AUTOCAC 009")
        self.assertEqual(atc.polissa_id.id, polissa_id)
        self.assertEqual(atc.tag.id, tag_id)

    def test_create_ATC_R1_009_from_polissa_via_wizard__tag_one_non_20TD(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        tar_obj = self.get_model("giscedata.polissa.tarifa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )

        tar_ids = tar_obj.search(self.cursor, self.uid, [("name", "!=", "2.0TD")])
        pol_obj.write(self.cursor, self.uid, polissa_id, {
            'mode_facturacio': 'atr',
            'tarifa': tar_ids[0],
        })

        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "R",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-01-01",
            "fecha_factura_hasta": "2015-01-31",
            "import_phase": 50,
        })
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
            'payment_mode_id': 4,
        })

        atc_id = atc_obj.create_ATC_R1_009_from_polissa_via_wizard(
            self.cursor, self.uid, polissa_id, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)

        tag_id = self.get_object_reference('som_autoreclama', 'tag_som_autoreclama_009_GEGC')[1]

        self.assertEqual(atc.name, u"AUTOCAC 009")
        self.assertEqual(atc.polissa_id.id, polissa_id)
        self.assertEqual(atc.tag.id, tag_id)

    @unittest.skip(reason="WIP using mock")
    @mock.patch.object(giscedata_polissa.GiscedataPolissa, "autoconsumo")
    def __test_create_ATC_R1_009_from_polissa_via_wizard__tag_two_auto(self, mock_autoconsumo):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        tar_obj = self.get_model("giscedata.polissa.tarifa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        mock_autoconsumo.return_value = 42
        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )

        tar_ids = tar_obj.search(self.cursor, self.uid, [("name", "=", "2.0TD")])
        pol_obj.write(self.cursor, self.uid, polissa_id, {
            'mode_facturacio': 'atr',
            'tarifa': tar_ids[0],
        })

        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "R",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-01-01",
            "fecha_factura_hasta": "2015-01-31",
            "import_phase": 50,
        })
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
            'payment_mode_id': 4,
        })

        atc_id = atc_obj.create_ATC_R1_009_from_polissa_via_wizard(
            self.cursor, self.uid, polissa_id, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)

        tag_id = self.get_object_reference('som_autoreclama', 'tag_som_autoreclama_009_GEA')[1]

        self.assertEqual(atc.name, u"AUTOCAC 009")
        self.assertEqual(atc.polissa_id.id, polissa_id)
        self.assertEqual(atc.tag.id, tag_id)

    def test_create_ATC_R1_009_from_polissa_via_wizard__tag_tree_2_0TD_periods_auto(self):
        atc_obj = self.get_model("giscedata.atc")
        pol_obj = self.get_model("giscedata.polissa")
        tar_obj = self.get_model("giscedata.polissa.tarifa")
        f1_obj = self.get_model("giscedata.facturacio.importacio.linia")
        ff_obj = self.get_model("giscedata.facturacio.importacio.linia.factura")

        _, polissa_id = self.get_object_reference(
            "giscedata_polissa", "polissa_0004"
        )

        tar_ids = tar_obj.search(self.cursor, self.uid, [("name", "=", "2.0TD")])
        pol_obj.write(self.cursor, self.uid, polissa_id, {
            'mode_facturacio': 'atr',
            'tarifa': tar_ids[0],
        })

        pol = pol_obj.browse(self.cursor, self.uid, polissa_id)
        f1_ids = f1_obj.search(self.cursor, self.uid, [("cups_id", "in", [pol.cups.id])])
        self.assertGreater(len(f1_ids), 0)
        f1_id = f1_ids[0]

        f1 = f1_obj.browse(self.cursor, self.uid, f1_id)
        self.assertEqual(f1.cups_id.name, pol.cups.name)

        f1_obj.write(self.cursor, self.uid, f1_id, {
            "invoice_number_text": "1234567890ABCD",
            "type_factura": "R",
            "polissa_id": pol.id,
            "fecha_factura_desde": "2015-01-01",
            "fecha_factura_hasta": "2015-01-31",
            "import_phase": 50,
        })
        ff_obj.create(self.cursor, self.uid, {
            'linia_id': f1_id,
            'tipo_factura': '04',
            'importacio_id': 1,
            'address_invoice_id': pol.direccio_pagament.id,
            'partner_id': pol.titular.id,
            'account_id': 3,
            'polissa_id': polissa_id,
            'tarifa_acces_id': pol.tarifa.id,
            'cups_id': pol.cups.id,
            'factura_id': 3,
            'llista_preu': pol.llista_preu.id,
            'payment_mode_id': 4,
        })

        atc_id = atc_obj.create_ATC_R1_009_from_polissa_via_wizard(
            self.cursor, self.uid, polissa_id, {}
        )

        atc = atc_obj.browse(self.cursor, self.uid, atc_id)

        tag_id = self.get_object_reference('som_autoreclama', 'tag_som_autoreclama_009_GET')[1]

        self.assertEqual(atc.name, u"AUTOCAC 009")
        self.assertEqual(atc.polissa_id.id, polissa_id)
        self.assertEqual(atc.tag.id, tag_id)

    # TODO: test NF readings

    def test_create_polissa__test_now(self):
        pol_obj = self.get_model("giscedata.polissa")

        pol_id = pol_obj.create(self.cursor, self.uid, {
            'name': '0001234',
            'cups': 1,
            'titular': 1,
        })

        initial006_state_id = self.get_object_reference(
            "som_autoreclama", "correct_state_workflow_polissa"
        )[1]

        initial009_state_id = self.get_object_reference(
            "som_autoreclama", "correct_state_workflow_polissa009"
        )[1]

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.name, '0001234')
        self.assertEqual(pol.cups.name, 'ES1234000000000001JN0F')
        self.assertEqual(pol.autoreclama_state.id, initial006_state_id)
        self.assertEqual(pol.autoreclama_state_date, today_str())
        self.assertEqual(pol.autoreclama009_state.id, initial009_state_id)
        self.assertEqual(pol.autoreclama009_state_date, today_str())

    def test_create_polissa__test_other(self):
        pol_obj = self.get_model("giscedata.polissa")
        state006_id = self.get_object_reference(
            "som_autoreclama", "loop_state_workflow_polissa"
        )[1]

        state009_id = self.get_object_reference(
            "som_autoreclama", "disabled_state_workflow_polissa009"
        )[1]

        pol_id = pol_obj.create(self.cursor, self.uid, {
            'name': '0001234',
            'cups': 1,
            'titular': 1,
        }, context={
            'autoreclama_history_initial_state_id': state006_id,
            'autoreclama_history_initial_date': '2022-08-01',
            'autoreclama_009_history_initial_state_id': state009_id,
        })

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.name, '0001234')
        self.assertEqual(pol.cups.name, 'ES1234000000000001JN0F')
        self.assertEqual(pol.autoreclama_state.id, state006_id)
        self.assertEqual(pol.autoreclama_state_date, '2022-08-01')
        self.assertEqual(pol.autoreclama009_state.id, state009_id)
        self.assertEqual(pol.autoreclama009_state_date, '2022-08-01')

    def test__wizard_set_manual_state__2_changes_2_machines(self):
        pol_obj = self.get_model("giscedata.polissa")
        w_obj = self.get_model("wizard.som.autoreclama.set.manual.state")

        correct006_state_id = self.get_object_reference(
            "som_autoreclama", "correct_state_workflow_polissa"
        )[1]
        loop006_state_id = self.get_object_reference(
            "som_autoreclama", "loop_state_workflow_polissa"
        )[1]
        disabled006_state_id = self.get_object_reference(
            "som_autoreclama", "disabled_state_workflow_polissa"
        )[1]

        correct009_state_id = self.get_object_reference(
            "som_autoreclama", "correct_state_workflow_polissa009"
        )[1]
        disabled009_state_id = self.get_object_reference(
            "som_autoreclama", "disabled_state_workflow_polissa009"
        )[1]
        loop009_state_id = self.get_object_reference(
            "som_autoreclama", "loop_state_workflow_polissa009"
        )[1]

        pol_id = pol_obj.create(self.cursor, self.uid, {
            'name': '0001234',
            'cups': 1,
            'titular': 1,
        }, context={
            'autoreclama_history_initial_date': '2022-08-01',
        })

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.name, '0001234')
        self.assertEqual(pol.cups.name, 'ES1234000000000001JN0F')
        self.assertEqual(pol.autoreclama_state.id, correct006_state_id)
        self.assertEqual(pol.autoreclama_state_date, '2022-08-01')
        self.assertEqual(pol.autoreclama009_state.id, correct009_state_id)
        self.assertEqual(pol.autoreclama009_state_date, '2022-08-01')

        ctxt = {'namespace': "polissa", 'active_ids': [pol_id]}
        wiz_id = w_obj.create(self.cursor, self.uid, {}, context=ctxt)
        w_obj.write(self.cursor, self.uid, [wiz_id], {
            'next_state_id': loop006_state_id,
            'change_date': '2022-09-15',
            'attached_atc': 1,
        })
        w_obj.assign_state(self.cursor, self.uid, [wiz_id], context=ctxt)

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.autoreclama_state.id, loop006_state_id)
        self.assertEqual(pol.autoreclama_state_date, '2022-09-15')
        self.assertEqual(pol.autoreclama009_state.id, correct009_state_id)
        self.assertEqual(pol.autoreclama009_state_date, '2022-08-01')

        ctxt = {'namespace': "polissa009", 'active_ids': [pol_id]}
        wiz_id = w_obj.create(self.cursor, self.uid, {}, context=ctxt)
        w_obj.write(self.cursor, self.uid, [wiz_id], {
            'next_state_id': loop009_state_id,
            'change_date': '2022-09-20',
            'attached_atc': 1,
        })
        w_obj.assign_state(self.cursor, self.uid, [wiz_id], context=ctxt)

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.autoreclama_state.id, loop006_state_id)
        self.assertEqual(pol.autoreclama_state_date, '2022-09-15')
        self.assertEqual(pol.autoreclama009_state.id, loop009_state_id)
        self.assertEqual(pol.autoreclama009_state_date, '2022-09-20')

        ctxt = {'namespace': "polissa", 'active_ids': [pol_id]}
        wiz_id = w_obj.create(self.cursor, self.uid, {}, context=ctxt)
        w_obj.write(self.cursor, self.uid, [wiz_id], {
            'next_state_id': disabled006_state_id,
            'change_date': '2022-10-01',
            'attached_atc': 1,
        })
        w_obj.assign_state(self.cursor, self.uid, [wiz_id], context=ctxt)
        ctxt = {'namespace': "polissa009", 'active_ids': [pol_id]}
        wiz_id = w_obj.create(self.cursor, self.uid, {}, context=ctxt)
        w_obj.write(self.cursor, self.uid, [wiz_id], {
            'next_state_id': disabled009_state_id,
            'change_date': '2022-10-01',
            'attached_atc': 1,
        })
        w_obj.assign_state(self.cursor, self.uid, [wiz_id], context=ctxt)

        pol = pol_obj.browse(self.cursor, self.uid, pol_id)
        self.assertEqual(pol.autoreclama_state.id, disabled006_state_id)
        self.assertEqual(pol.autoreclama_state_date, '2022-10-01')
        self.assertEqual(pol.autoreclama009_state.id, disabled009_state_id)
        self.assertEqual(pol.autoreclama009_state_date, '2022-10-01')


class SomAutoreclamaConditions009Test(SomAutoreclamaBaseTests):
    def test_fit_polissa_condition__2_009_in_a_row_yes(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        context = {'days_ago_R1009': 120}
        pol_id = self.build_polissa(f1_date_days_from_today=76)
        atc1_id = self.add_done_009_to_polissa(pol_id, 85)
        atc2_id = self.add_done_009_to_polissa(pol_id, 80)
        self.add_correct_to_history009(pol_id, 85, atc1_id)
        self.add_correct_to_history009(pol_id, 80, atc2_id)

        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", context)
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_bucle_2_009_inarow_review_state_workflow_polissa009"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, True)

    def test_fit_polissa_condition__2_009_in_a_row_no(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        context = {'days_ago_R1009': 120}
        pol_id = self.build_polissa(f1_date_days_from_today=76)

        atc1_id = self.add_done_009_to_polissa(pol_id, 85)
        atc2_id = self.add_done_009_to_polissa(pol_id, 20)
        self.add_correct_to_history009(pol_id, 85, atc1_id)
        self.add_correct_to_history009(pol_id, 20, atc2_id)

        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", context)
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_bucle_2_009_inarow_review_state_workflow_polissa009"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, False)

    def test_fit_polissa_condition__2_009_in_a_row_with_previous_review_state_yes(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        context = {'days_ago_R1009': 120}
        pol_id = self.build_polissa(f1_date_days_from_today=76)
        atc1_id = self.add_done_009_to_polissa(pol_id, 85)
        atc2_id = self.add_done_009_to_polissa(pol_id, 80)
        self.add_review_to_history009(pol_id, 90)
        self.add_correct_to_history009(pol_id, 85, atc1_id)
        self.add_correct_to_history009(pol_id, 80, atc2_id)

        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", context)
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_bucle_2_009_inarow_review_state_workflow_polissa009"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, True)

    def test_fit_polissa_condition__2_009_in_a_row_with_previous_review_state_no(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        context = {'days_ago_R1009': 120}
        pol_id = self.build_polissa(f1_date_days_from_today=76)
        atc1_id = self.add_done_009_to_polissa(pol_id, 85)
        atc2_id = self.add_done_009_to_polissa(pol_id, 80)
        self.add_correct_to_history009(pol_id, 85, atc1_id)
        self.add_review_to_history009(pol_id, 82)
        self.add_correct_to_history009(pol_id, 80, atc2_id)

        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", context)
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_bucle_2_009_inarow_review_state_workflow_polissa009"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, False)

    def test_fit_polissa_condition__cycles_estimate_bucle_state_yes(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")
        pol_id = self.build_polissa(pool_readings=[
            {'date': '2020-01-08', 'origen': '40'},
            {'date': '2020-02-09', 'origen': '40'},
            {'date': '2020-03-08', 'origen': '10'},
            {'date': '2020-04-09', 'origen': '40'},
            {'date': '2020-05-07', 'origen': '40'},
            {'date': '2020-06-09', 'origen': '40'},
            {'date': '2020-07-10', 'origen': '40'},
            {'date': '2020-08-06', 'origen': '40'},
        ])
        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", {})
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_cycles_estimate_correct_state_workflow_polissa009"
        )
        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, False)

    def test_fit_polissa_condition__cycles_estimate_bucle_state_no(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")
        pol_id = self.build_polissa(pool_readings=[
            {'date': '2020-01-08', 'origen': '40'},
            {'date': '2020-02-09', 'origen': '40'},
            {'date': '2020-03-08', 'origen': '40'},
            {'date': '2020-04-09', 'origen': '40'},
            {'date': '2020-05-07', 'origen': '10'},
            {'date': '2020-06-09', 'origen': '40'},
            {'date': '2020-07-10', 'origen': '40'},
            {'date': '2020-08-06', 'origen': '40'},
        ])
        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", {})
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_cycles_estimate_correct_state_workflow_polissa009"
        )
        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, False)

    def test_fit_polissa_condition__cycles_estimate_bucle_state_low_readings_real_no(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")
        pol_id = self.build_polissa(pool_readings=[
            {'date': '2020-06-09', 'origen': '10'},
            {'date': '2020-07-10', 'origen': '10'},
            {'date': '2020-08-06', 'origen': '10'},
        ])
        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", {})
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_cycles_estimate_correct_state_workflow_polissa009"
        )
        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, False)

    def test_fit_polissa_condition__cycles_estimate_bucle_state_low_readings_estimated_no(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")
        pol_id = self.build_polissa(pool_readings=[
            {'date': '2020-06-09', 'origen': 'est'},
            {'date': '2020-07-10', 'origen': '40'},
            {'date': '2020-08-06', 'origen': '40'},
        ])
        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", {})
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_cycles_estimate_correct_state_workflow_polissa009"
        )
        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, False)

    def test_fit_polissa_condition__cycles_estimate_bucle_state_high_readings_mix_no(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")
        pol_id = self.build_polissa(pool_readings=[
            {'date': '2020-01-08', 'origen': '10'},
            {'date': '2020-02-09', 'origen': '20'},
            {'date': '2020-03-08', 'origen': '30'},
            {'date': '2020-04-09', 'origen': '10'},
            {'date': '2020-05-07', 'origen': 'est'},
            {'date': '2020-06-09', 'origen': '30'},
            {'date': '2020-07-10', 'origen': '10'},
            {'date': '2020-08-06', 'origen': '20'},
            {'date': '2020-09-06', 'origen': 'est'},
            {'date': '2020-10-05', 'origen': '10'},
            {'date': '2020-11-07', 'origen': 'est'},
            {'date': '2020-12-08', 'origen': '30'},
        ])
        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", {})
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_cycles_estimate_correct_state_workflow_polissa009"
        )
        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, False)

    def test_fit_polissa_condition__loop_to_correct_yes_far(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")
        pol_id = self.build_polissa(pool_readings=[
            {'date': '2020-01-08', 'origen': 'est'},
            {'date': '2020-02-09', 'origen': 'est'},
            {'date': '2020-03-08', 'origen': 'est'},
            {'date': '2020-04-09', 'origen': 'est'},
            {'date': '2020-05-07', 'origen': 'est'},
            {'date': '2020-06-09', 'origen': 'est'},
            {'date': '2020-07-10', 'origen': 'est'},
            {'date': '2020-08-06', 'origen': 'real'},
            {'date': '2020-09-06', 'origen': 'est'},
            {'date': '2020-10-05', 'origen': 'est'},
            {'date': '2020-11-07', 'origen': 'est'},
            {'date': '2020-12-08', 'origen': 'est'},
        ])
        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", {})
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_loop_to_correct_state_workflow_polissa009"
        )
        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, True)
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_revisar_to_correct_state_workflow_polissa009"
        )
        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, True)

    def test_fit_polissa_condition__loop_to_correct_yes_near(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")
        pol_id = self.build_polissa(pool_readings=[
            {'date': '2020-01-08', 'origen': 'est'},
            {'date': '2020-02-09', 'origen': 'est'},
            {'date': '2020-03-08', 'origen': 'est'},
            {'date': '2020-04-09', 'origen': 'est'},
            {'date': '2020-05-07', 'origen': 'est'},
            {'date': '2020-06-09', 'origen': 'est'},
            {'date': '2020-07-10', 'origen': 'est'},
            {'date': '2020-08-06', 'origen': 'est'},
            {'date': '2020-09-06', 'origen': 'est'},
            {'date': '2020-10-05', 'origen': 'est'},
            {'date': '2020-11-07', 'origen': '10'},
            {'date': '2020-12-08', 'origen': 'est'},
        ])
        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", {})
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_loop_to_correct_state_workflow_polissa009"
        )
        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, True)
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_revisar_to_correct_state_workflow_polissa009"
        )
        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, True)

    def test_fit_polissa_condition__loop_to_correct_yes_now(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")
        pol_id = self.build_polissa(pool_readings=[
            {'date': '2020-01-08', 'origen': 'est'},
            {'date': '2020-02-09', 'origen': 'est'},
            {'date': '2020-03-08', 'origen': 'est'},
            {'date': '2020-04-09', 'origen': 'est'},
            {'date': '2020-05-07', 'origen': 'est'},
            {'date': '2020-06-09', 'origen': 'est'},
            {'date': '2020-07-10', 'origen': 'est'},
            {'date': '2020-08-06', 'origen': 'est'},
            {'date': '2020-09-06', 'origen': 'est'},
            {'date': '2020-10-05', 'origen': 'est'},
            {'date': '2020-11-07', 'origen': 'est'},
            {'date': '2020-12-08', 'origen': 'real'},
        ])
        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", {})
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_loop_to_correct_state_workflow_polissa009"
        )
        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, True)
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_revisar_to_correct_state_workflow_polissa009"
        )
        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, True)

    def test_fit_polissa_condition__loop_to_correct_no(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")
        pol_id = self.build_polissa(pool_readings=[
            {'date': '2020-01-08', 'origen': 'est'},
            {'date': '2020-02-09', 'origen': 'est'},
            {'date': '2020-03-08', 'origen': 'est'},
            {'date': '2020-04-09', 'origen': 'est'},
            {'date': '2020-05-07', 'origen': 'est'},
            {'date': '2020-06-09', 'origen': 'est'},
            {'date': '2020-07-10', 'origen': 'real'},
            {'date': '2020-08-06', 'origen': 'est'},
            {'date': '2020-09-06', 'origen': 'est'},
            {'date': '2020-10-05', 'origen': 'est'},
            {'date': '2020-11-07', 'origen': 'est'},
            {'date': '2020-12-08', 'origen': 'est'},
        ])
        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", {})
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_loop_to_correct_state_workflow_polissa009"
        )
        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_revisar_to_correct_state_workflow_polissa009"
        )
        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, False)

    def test_fit_polissa_condition__cac009_closed_yes(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        context = {'days_ago_R1009': 120}
        pol_id = self.build_polissa(f1_date_days_from_today=76)
        atc1_id = self.add_done_009_to_polissa(pol_id, 30)
        self.add_correct_to_history009(pol_id, 30, atc1_id)

        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", context)
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_CACR1009_closed_loop_state_workflow_polissa009"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, True)

    def test_fit_polissa_condition__cac009_closed_yes_near(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        context = {'days_ago_R1009': 120}
        pol_id = self.build_polissa(f1_date_days_from_today=76)
        atc1_id = self.add_done_009_to_polissa(pol_id, 30)
        self.add_correct_to_history009(pol_id, 21, atc1_id)

        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", context)
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_CACR1009_closed_loop_state_workflow_polissa009"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, True)

    def test_fit_polissa_condition__cac009_closed_no(self):
        polissa_obj = self.get_model("giscedata.polissa")
        cond_obj = self.get_model("som.autoreclama.state.condition")

        context = {'days_ago_R1009': 120}
        pol_id = self.build_polissa(f1_date_days_from_today=76)

        atc1_id = self.add_done_009_to_polissa(pol_id, 20)
        self.add_correct_to_history009(pol_id, 20, atc1_id)

        pol_data = polissa_obj.get_autoreclama_data(
            self.cursor, self.uid, pol_id, "polissa009", context)
        _, cond_id = self.get_object_reference(
            "som_autoreclama",
            "conditions_CACR1009_closed_loop_state_workflow_polissa009"
        )

        ok = cond_obj.fit_condition(self.cursor, self.uid, cond_id, pol_data, "polissa009", {})
        self.assertEqual(ok, False)
