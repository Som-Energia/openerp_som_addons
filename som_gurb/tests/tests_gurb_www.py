# -*- coding: utf-8 -*-

import mock
from tests_gurb_base import TestsGurbBase


class TestsGurbWww(TestsGurbBase):

    _start_signature_fnc = (
        "giscedata_signatura_documents_signaturit.giscedata_signatura_documents."
        "GiscedataSignaturaProcess.start"
    )
    _update_signature_fnc = (
        "giscedata_signatura_documents_signaturit.giscedata_signatura_documents."
        "GiscedataSignaturaProcess.update"
    )
    _www_signature_fnc = "som_gurb.www.som_gurb_www.SomGurbWww._get_signature_url"

    def test_get_info_gurb__bad_gurb_code(self):
        gurb_www_o = self.openerp.pool.get("som.gurb.www")

        bad_gurb_name = "erroneus_code"
        result = gurb_www_o.get_info_gurb(
            self.cursor, self.uid,
            bad_gurb_name,
            "2.0TD"
        )

        msg = u"Cap Gurb Group amb el codi {}".format(bad_gurb_name)
        self.assertEqual(result["error"], msg)
        self.assertEqual(result["code"], "BadGurbCode")

    def test_get_info_gurb__unsuported_access_tariff(self):
        gurb_www_o = self.openerp.pool.get("som.gurb.www")

        bad_access_tariff = "6.1TD"
        result = gurb_www_o.get_info_gurb(
            self.cursor, self.uid,
            'G001',
            bad_access_tariff
        )

        msg = u"Tarifa d'accés no suportada '{}'".format(bad_access_tariff)
        self.assertEqual(result["error"], msg)
        self.assertEqual(result["code"], "UnsuportedAccessTariff")

    def test_get_info_gurb__available_betas(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_www_o = self.openerp.pool.get("som.gurb.www")
        gurb_cups_o = self.openerp.pool.get("som.gurb.cups")

        # GURB CUPS must be active
        gurb_cups_id_1 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0001"
        )[1]
        gurb_cups_id_2 = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cups_0002"
        )[1]
        gurb_cups_o.write(self.cursor, self.uid, gurb_cups_id_1, {"state": "active"})
        gurb_cups_o.write(self.cursor, self.uid, gurb_cups_id_2, {"state": "active"})

        result = gurb_www_o.get_info_gurb(
            self.cursor, self.uid,
            'G001',
            "2.0TD"
        )

        self.assertEqual(result["available_betas"], [x / 10.0 for x in range(5, 25, 5)])

    def test_get_info_gurb__surplus_comensation(self):
        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_www_o = self.openerp.pool.get("som.gurb.www")
        gurb_cau_o = self.openerp.pool.get("som.gurb.cau")

        gurb_cau_id = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_cau_0001"
        )[1]
        gurb_cau_o.write(self.cursor, self.uid, gurb_cau_id, {"has_compensation": True})

        result = gurb_www_o.get_info_gurb(
            self.cursor, self.uid,
            'G001',
            "2.0TD"
        )

        self.assertTrue(result["surplus_compensation"])

    def test_get_info_gurb__quotas(self):
        gurb_www_o = self.openerp.pool.get("som.gurb.www")

        result = gurb_www_o.get_info_gurb(
            self.cursor, self.uid,
            'G001',
            "2.0TD"
        )

        self.assertEqual(result["initial_quota"], 3.75)
        self.assertEqual(result["quota"], 5)

        result = gurb_www_o.get_info_gurb(
            self.cursor, self.uid,
            'G001',
            "3.0TD"
        )
        self.assertEqual(result["quota"], 4)

    def test__check_coordinates_2km_validation__inside2km(self):
        gurb_www_obj = self.get_model("som.gurb.www")

        gurb_code = "G001"
        result = gurb_www_obj.check_coordinates_2km_validation(
            self.cursor, self.uid, -3.064674264239092, 37.35812464702857, gurb_code
        )

        self.assertTrue(result)

    def test__check_coordinates_2km_validation__outside2km(self):
        gurb_www_obj = self.get_model("som.gurb.www")

        gurb_code = "G001"
        result = gurb_www_obj.check_coordinates_2km_validation(
            self.cursor, self.uid, 37.35812464702857, -3.064674264239092, gurb_code
        )

        self.assertFalse(result)

    @mock.patch(_start_signature_fnc, return_value=True)
    def test_create_new_gurb_cups_on_draft_contract(self, start_mock):
        gurb_www_obj = self.get_model("som.gurb.www")

        form_payload = {
            "gurb_code": "G001",
            "access_tariff": "2.0TD",
            "cups": "ES0021126262693495FV",
            "beta": 2.0,
        }
        result = gurb_www_obj.create_new_gurb_cups(
            self.cursor, self.uid, form_payload
        )

        self.assertTrue(result["success"])

    @mock.patch(_www_signature_fnc)
    def test_create_new_gurb_cups_on_active_contract(self, helper_mock):
        helper_mock.return_value = "https://signaturit.com/signing/abcdefg1234567"

        gurb_www_obj = self.get_model("som.gurb.www")
        imd_obj = self.openerp.pool.get("ir.model.data")
        res_partner_obj = self.openerp.pool.get("res.partner")

        titular_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_polissa", "res_partner_domestic"
        )[1]
        res_partner_obj.write(self.cursor, self.uid, titular_id, {"lang": "en_US"})

        self.activar_polissa_CUPS()
        form_payload = {
            "gurb_code": "G001",
            "access_tariff": "2.0TD",
            "cups": "ES0021126262693495FV",
            "beta": 2.0,
        }

        result = gurb_www_obj.create_new_gurb_cups(
            self.cursor, self.uid, form_payload
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["signature_url"], "https://signaturit.com/signing/abcdefg1234567")
        self.assertTrue(helper_mock.called)

    def test_private_fnc_get_cups_id(self):
        gurb_www_obj = self.get_model("som.gurb.www")
        imd_o = self.openerp.pool.get("ir.model.data")

        gurb_cups_id = imd_o.get_object_reference(
            self.cursor, self.uid, "giscedata_cups", "cups_tarifa_018"
        )[1]

        fnc_gurb_cups_id = gurb_www_obj._get_cups_id(
            self.cursor, self.uid, "ES0021126262693495FV"
        )

        self.assertEqual(gurb_cups_id, fnc_gurb_cups_id)

        fnc_gurb_cups_id = gurb_www_obj._get_cups_id(
            self.cursor, self.uid, "Nye he he he"
        )
        self.assertFalse(fnc_gurb_cups_id)
        fnc_gurb_cups_id = gurb_www_obj._get_cups_id(
            self.cursor, self.uid, "ES0396705156982945JF"
        )
        self.assertIsNone(fnc_gurb_cups_id)

    def test_get_prioritary_gurb_cau_id_no_capacity(self):
        gurb_group_o = self.openerp.pool.get("som.gurb.group")
        imd_o = self.openerp.pool.get("ir.model.data")
        gurb_group_id = imd_o.get_object_reference(
            self.cursor, self.uid, "som_gurb", "gurb_group_0001"
        )[1]
        beta = 100000
        result = gurb_group_o.get_prioritary_gurb_cau_id(self.cursor, self.uid, gurb_group_id, beta)
        self.assertFalse(result)

    def test_create_new_gurb_cups_bad_beta(self):
        gurb_www_obj = self.get_model("som.gurb.www")
        form_payload = {
            "gurb_code": "G001",
            "access_tariff": "2.0TD",
            "cups": "ES0021000000000001",
            "beta": 0,
        }
        result = gurb_www_obj.create_new_gurb_cups(self.cursor, self.uid, form_payload)
        self.assertEqual(result["code"], "BadBeta")

    @mock.patch(_start_signature_fnc, return_value=True)
    @mock.patch(_update_signature_fnc, return_value=True)
    def test_activate_gurb_cups_lead(self, start_mock, update_mock):
        gurb_www_obj = self.get_model("som.gurb.www")
        gurb_cups_obj = self.get_model("som.gurb.cups")
        sign_docs_obj = self.get_model("giscedata.signatura.documents")
        sign_process_obj = self.get_model("giscedata.signatura.process")

        form_payload = {
            "gurb_code": "G001",
            "access_tariff": "2.0TD",
            "cups": "ES0021126262693495FV",
            "beta": 2.0,
        }
        gurb_cups_id = gurb_www_obj.create_new_gurb_cups(
            self.cursor, self.uid, form_payload
        )["gurb_cups_id"]
        search_vals = [("model", "=", "som.gurb.cups,{}".format(gurb_cups_id))]
        doc_id = sign_docs_obj.search(self.cursor, self.uid, search_vals, limit=1)[0]
        process_id = sign_docs_obj.browse(self.cursor, self.uid, doc_id).process_id.id
        sign_process_obj.write(self.cursor, self.uid, [process_id], {'status': 'completed'})
        result = gurb_www_obj.activate_gurb_cups_lead(self.cursor, self.uid, gurb_cups_id)

        gurb_cups_br = gurb_cups_obj.browse(self.cursor, self.uid, gurb_cups_id)
        self.assertEqual(gurb_cups_br.state, "comming_registration")
        self.assertTrue(result["success"])

    @mock.patch(_start_signature_fnc, return_value=True)
    @mock.patch(_update_signature_fnc, return_value=True)
    def test_activate_gurb_cups_lead_fail_state(self, start_mock, update_mock):
        gurb_www_obj = self.get_model("som.gurb.www")
        gurb_cups_obj = self.get_model("som.gurb.cups")

        form_payload = {
            "gurb_code": "G001",
            "access_tariff": "2.0TD",
            "cups": "ES0021126262693495FV",
            "beta": 2.0,
        }
        gurb_cups_id = gurb_www_obj.create_new_gurb_cups(
            self.cursor, self.uid, form_payload
        )["gurb_cups_id"]
        gurb_cups_obj.send_signal(self.cursor, self.uid, [gurb_cups_id], "button_create_cups")
        result = gurb_www_obj.activate_gurb_cups_lead(self.cursor, self.uid, gurb_cups_id)

        self.assertEqual(result["code"], "GurbCupsNotDraft")

    @mock.patch(_start_signature_fnc, return_value=True)
    @mock.patch(_update_signature_fnc, return_value=True)
    def test_activate_gurb_cups_lead_fail_sign(self, start_mock, update_mock):
        gurb_www_obj = self.get_model("som.gurb.www")
        gurb_cups_obj = self.get_model("som.gurb.cups")

        form_payload = {
            "gurb_code": "G001",
            "access_tariff": "2.0TD",
            "cups": "ES0021126262693495FV",
            "beta": 2.0,
        }
        gurb_cups_id = gurb_www_obj.create_new_gurb_cups(
            self.cursor, self.uid, form_payload
        )["gurb_cups_id"]
        result = gurb_www_obj.activate_gurb_cups_lead(self.cursor, self.uid, gurb_cups_id)

        gurb_cups_br = gurb_cups_obj.browse(self.cursor, self.uid, gurb_cups_id)
        self.assertEqual(gurb_cups_br.state, "draft")
        self.assertEqual(result["code"], "SignatureNotCompleted")
