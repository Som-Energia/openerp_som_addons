# -*- coding: utf-8 -*-
from destral.transaction import Transaction
import mock
from giscedata_switching.tests.common_tests import TestSwitchingImport
from destral.patch import PatchNewCursors


class TestActivacioCn(TestSwitchingImport):
    def setUp(self):
        self.pool = self.openerp.pool
        self.Polissa = self.pool.get("giscedata.polissa")
        self.Switching = self.pool.get("giscedata.switching")
        self.User = self.pool.get("res.users")
        self.Company = self.pool.get("res.company")
        self.ResPartner = self.pool.get("res.partner")
        self.ResConfig = self.openerp.pool.get("res.config")
        self.ResPartnerAddress = self.pool.get("res.partner.address")
        self.C106 = self.openerp.pool.get("giscedata.switching.c1.06")
        self.C206 = self.openerp.pool.get("giscedata.switching.c2.06")
        self.ResConfig = self.openerp.pool.get("res.config")
        self.IrModelData = self.openerp.pool.get("ir.model.data")

    def get_cn_06(self, txn, contract_id, tipus, context=None):
        """ " tipus és 'C1' o 'C2'"""
        if not context:
            context = {}
        uid = txn.user
        cursor = txn.cursor
        self.switch(txn, "distri")
        context["extra_vals"] = {
            "data_alta": "2017-01-31",
            "lot_facturacio": False,
            "data_baixa": False,
        }
        # create step 06
        self.update_polissa_distri(txn)
        self.activar_polissa_CUPS(txn, context=context)
        self.change_polissa_comer(txn)
        step_id = self.create_case_and_step(
            cursor, uid, contract_id, tipus, "06", {"whereiam": "distri"}
        )

        cn06 = None
        if tipus == "C1":
            cn06 = self.C106.browse(cursor, uid, step_id)
        else:
            cn06 = self.C206.browse(cursor, uid, step_id)

        cn06.write({"data_activacio": "2021-11-30"})

        # switch to comer and recalculate whereiam field
        company_id = self.User.read(cursor, uid, uid, ["company_id"])["company_id"][0]
        self.Company.write(cursor, uid, company_id, {"partner_id": 2})
        self.switch(txn, "comer")
        cups_id = self.Switching.read(cursor, uid, cn06.sw_id.id, ["cups_id"])["cups_id"][0]
        self.Switching.write(cursor, uid, cn06.sw_id.id, {"cups_id": cups_id})

        cn = self.Switching.browse(cursor, uid, cn06.sw_id.id, {"browse_reference": True})

        return cn

    @mock.patch("som_polissa_soci.models.res_partner_address.ResPartnerAddress.unsubscribe_partner_in_customers_no_members_lists")  # noqa: E501
    def test_c1_06_baixa_mailchimp_ok(self, mock_function):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            self.ResConfig.set(cursor, uid, "sw_allow_baixa_polissa_from_cn_without_invoice", "1")
            contract_id = self.get_contract_id(txn)
            # remove all other contracts
            old_partner_id = self.Polissa.read(cursor, uid, contract_id, ["titular"])["titular"][0]
            pol_ids = self.Polissa.search(
                cursor, uid, [("id", "!=", contract_id), ("titular", "=", old_partner_id)]
            )
            self.Polissa.write(cursor, uid, pol_ids, {"titular": False})

            c1 = self.get_cn_06(txn, contract_id, "C1")

            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, c1)

            mock_function.assert_called_with(mock.ANY, uid, old_partner_id)

            expected_result = (
                u"[Baixa Mailchimp] S'ha iniciat el procés de baixa "
                u"per l'antic titular (ID %d)" % (old_partner_id)
            )
            history_line_desc = [line["description"] for line in c1.history_line]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))

    @mock.patch("som_polissa_soci.models.res_partner_address.ResPartnerAddress.unsubscribe_partner_in_customers_no_members_lists")  # noqa: E501
    def test_c1_06_baixa_mailchimp_error__more_than_one_contract(self, mock_function):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            self.ResConfig.set(cursor, uid, "sw_allow_baixa_polissa_from_cn_without_invoice", "1")
            contract_id = self.get_contract_id(txn, "polissa_tarifa_018")

            c1 = self.get_cn_06(txn, contract_id, "C1", {"polissa_xml_id": "polissa_tarifa_018"})
            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, c1)

            self.assertTrue(not mock_function.called)

            expected_result = (
                u"[Baixa Mailchimp] No s'ha iniciat el procés de baixa "
                u"perque l'antic titular encara té pòlisses associades"
            )
            history_line_desc = [line["description"] for line in c1.history_line]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))

    @mock.patch("som_polissa_soci.models.res_partner_address.ResPartnerAddress.unsubscribe_partner_in_customers_no_members_lists")  # noqa: E501
    def test_c2_06_baixa_mailchimp_ok(self, mock_mailchimp_function):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            self.ResConfig.set(cursor, uid, "sw_allow_baixa_polissa_from_cn_without_invoice", "1")

            contract_id = self.get_contract_id(txn)
            # remove all other contracts
            old_partner_id = self.Polissa.read(cursor, uid, contract_id, ["titular"])["titular"][0]
            pol_ids = self.Polissa.search(
                cursor, uid, [("id", "!=", contract_id), ("titular", "=", old_partner_id)]
            )
            self.Polissa.write(cursor, uid, pol_ids, {"titular": False})

            c2 = self.get_cn_06(txn, contract_id, "C2")

            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, c2)

            mock_mailchimp_function.assert_called_with(mock.ANY, uid, old_partner_id)

            expected_result = (
                u"[Baixa Mailchimp] S'ha iniciat el procés de baixa "
                u"per l'antic titular (ID %d)" % (old_partner_id)
            )
            history_line_desc = [line["description"] for line in c2.history_line]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))

    @mock.patch("som_polissa_soci.models.res_partner_address.ResPartnerAddress.unsubscribe_partner_in_customers_no_members_lists")  # noqa: E501
    def test_c2_06_baixa_mailchimp_error__more_than_one_contract(self, mock_function):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            self.ResConfig.set(cursor, uid, "sw_allow_baixa_polissa_from_cn_without_invoice", "1")

            contract_id = self.get_contract_id(txn, "polissa_tarifa_018")

            c2 = self.get_cn_06(txn, contract_id, "C2", {"polissa_xml_id": "polissa_tarifa_018"})
            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, c2)

            self.assertTrue(not mock_function.called)

            expected_result = (
                u"[Baixa Mailchimp] No s'ha iniciat el procés de baixa "
                u"perque l'antic titular encara té pòlisses associades"
            )
            history_line_desc = [line["description"] for line in c2.history_line]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))

    @mock.patch("som_polissa_soci.models.res_partner_address.ResPartnerAddress.unsubscribe_partner_in_customers_no_members_lists")  # noqa: E501
    def test_c1_06_baixa_mailchimp_error__active_contract(self, mock_function):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            self.ResConfig.set(cursor, uid, "sw_allow_baixa_polissa_from_cn_without_invoice", "0")

            contract_id = self.get_contract_id(txn)
            # remove all other contracts
            old_partner_id = self.Polissa.read(cursor, uid, contract_id, ["titular"])["titular"][0]
            pol_ids = self.Polissa.search(
                cursor, uid, [("id", "!=", contract_id), ("titular", "=", old_partner_id)]
            )
            self.Polissa.write(cursor, uid, pol_ids, {"titular": False})

            c1 = self.get_cn_06(txn, contract_id, "C1")

            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, c1)

            self.assertTrue(not mock_function.called)

            expected_result = u"[Baixa Mailchimp] No s'ha donat de baixa el titular perquè la pòlissa està activa."  # noqa: E501
            history_line_desc = [line["description"] for line in c1.history_line]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))
