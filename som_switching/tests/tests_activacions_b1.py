# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
import mock
from osv import osv
from giscedata_switching.tests.common_tests import TestSwitchingImport
from destral.patch import PatchNewCursors

class TestActivacioB1(TestSwitchingImport):

    def setUp(self):
        self.pool = self.openerp.pool
        self.Polissa = self.pool.get('giscedata.polissa')
        self.Switching = self.pool.get('giscedata.switching')
        self.User = self.pool.get('res.users')
        self.Company = self.pool.get('res.company')
        self.ResPartner = self.pool.get('res.partner')
        self.ResConfig = self.openerp.pool.get('res.config')
        self.ResPartnerAddress = self.pool.get('res.partner.address')
        self.B101 = self.openerp.pool.get('giscedata.switching.b1.01')
        self.ResConfig = self.openerp.pool.get('res.config')
        self.IrModelData = self.openerp.pool.get('ir.model.data')

    def get_b1_01(self, txn, contract_id):
        uid = txn.user
        cursor = txn.cursor
        self.switch(txn, 'comer')

        # create step 01
        self.change_polissa_comer(txn)
        self.update_polissa_distri(txn)
        self.activar_polissa_CUPS(txn)
        step_id = self.create_case_and_step(
            cursor, uid, contract_id, 'B1', '01'
        )

        sw_id = self.B101.read(cursor, uid, step_id, ['sw_id'])['sw_id'][0]
        return self.Switching.browse(cursor, uid, sw_id, {"browse_reference": True})


    def get_b1_02(self, txn, contract_id):
        uid = txn.user
        cursor = txn.cursor
        b1 = self.get_b1_01(txn, contract_id)

        self.create_step(
            cursor, uid, b1, 'B1', '02', context=None
        )
        b1 = self.Switching.browse(cursor, uid, b1.id, {"browse_reference": True})
        b102 = b1.step_ids[-1].pas_id
        b102.write({"data_activacio": "2016-08-01"})

        return b1

    def get_b1_05(self, txn, contract_id):
        uid = txn.user
        cursor = txn.cursor
        b1 = self.get_b1_02(txn, contract_id)
        self.create_step(
            cursor, uid, b1, 'B1', '05', context=None
        )
        b1 = self.Switching.browse(cursor, uid, b1.id, {"browse_reference": True})
        b105 = b1.step_ids[-1].pas_id
        b105.write({"data_activacio": "2016-08-05"})

        return b1

    @mock.patch("som_polissa_soci.res_partner.ResPartner.arxiva_client_mailchimp_async")
    def test_b1_05_baixa_mailchimp_ok(self, mock_function):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            self.ResConfig.set(cursor, uid, 'sw_allow_baixa_polissa_from_cn_without_invoice', '1')

            contract_id = self.get_contract_id(txn)
            # remove all other contracts
            old_partner_id = self.Polissa.read(cursor, uid, contract_id, ['titular'])['titular'][0]
            pol_ids = self.Polissa.search(cursor, uid,
                [('id', '!=', contract_id), ('titular', '=', old_partner_id)])
            self.Polissa.write(cursor, uid, pol_ids, {'titular': False})

            b1 = self.get_b1_05(txn, contract_id)

            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, b1)

            mock_function.assert_called_with(mock.ANY, uid, old_partner_id)

            expected_result = u"[Baixa Mailchimp] S'ha iniciat el procés de baixa " \
                u"per l'antic titular (ID %d)" % (old_partner_id)
            history_line_desc = [
                l['description'] for l in b1.history_line
            ]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))


    @mock.patch("som_polissa_soci.res_partner.ResPartner.arxiva_client_mailchimp_async")
    def test_b1_05_baixa_mailchimp_error__more_than_one_contract(self, mock_function):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            self.ResConfig.set(cursor, uid, 'sw_allow_baixa_polissa_from_cn_without_invoice', '1')

            contract_id = self.get_contract_id(txn)

            b1 = self.get_b1_05(txn, contract_id)
            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, b1)

            self.assertTrue(not mock_function.called)

            expected_result = u"[Baixa Mailchimp] No s'ha iniciat el procés de baixa " \
                u"perque l'antic titular encara té pòlisses associades"
            history_line_desc = [
                l['description'] for l in b1.history_line
            ]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))

    @mock.patch("som_polissa_soci.res_partner.ResPartner.arxiva_client_mailchimp_async")
    def test_b1_05_baixa_mailchimp_error__active_contract(self, mock_function):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            self.ResConfig.set(cursor, uid, 'sw_allow_baixa_polissa_from_cn_without_invoice', '0')

            contract_id = self.get_contract_id(txn)
            # remove all other contracts
            old_partner_id = self.Polissa.read(cursor, uid, contract_id, ['titular'])['titular'][0]
            pol_ids = self.Polissa.search(cursor, uid,
                [('id', '!=', contract_id), ('titular', '=', old_partner_id)])
            self.Polissa.write(cursor, uid, pol_ids, {'titular': False})

            b1 = self.get_b1_05(txn, contract_id)

            with PatchNewCursors():
                self.Switching.activa_cas_atr(cursor, uid, b1)

            self.assertTrue(not mock_function.called)

            expected_result = u"[Baixa Mailchimp] No s\'ha donat de baixa el titular perquè la pòlissa està activa."
            history_line_desc = [
                l['description'] for l in b1.history_line
            ]
            self.assertTrue(any([expected_result in desc for desc in history_line_desc]))
