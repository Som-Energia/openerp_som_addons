# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from datetime import date
import mock


def get_today_str():
    return date.today().strftime("%Y-%m-%d")


def split_first(message, sepparator='\n'):
    if sepparator not in message:
        return message, False

    idx = message.index(sepparator)
    return message[:idx], message[idx + 1:]


class TestAccountInvoiceSetPendingAutomations(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    def getref(self, module, reference):
        IrModelData = self.pool.get("ir.model.data")
        return IrModelData.get_object_reference(
            self.cursor, self.uid,
            module, reference
        )[1]

    def read_one(self, model_obj, model_id, field):
        data = model_obj.read(self.cursor, self.uid, model_id, [field])
        if field in data:
            return data[field]
        return None

    def write_one(self, model_obj, model_id, field, value):
        data = {
            field: value
        }
        model_obj.write(self.cursor, self.uid, model_id, data)

    def _load_data_unpaid_invoices(self, invoice_semid_list=[]):
        imd_obj = self.pool.get("ir.model.data")
        inv_obj = self.pool.get("account.invoice")
        fact_obj = self.pool.get("giscedata.facturacio.factura")

        facts = []
        invos = []

        contract_name = ""
        for index, res_id in enumerate(invoice_semid_list, start=1):
            fact_id = imd_obj.get_object_reference(
                self.cursor, self.uid, "giscedata_facturacio", "factura_000" + str(index)
            )[1]
            invoice_id = fact_obj.read(
                self.cursor, self.uid, fact_id, ["invoice_id"]
            )["invoice_id"][0]

            if index == 1:
                contract_name = inv_obj.read(
                    self.cursor, self.uid,
                    invoice_id, ["name"]
                )["name"]

            inv_obj.write(
                self.cursor, self.uid,
                invoice_id,
                {
                    "name": contract_name,
                },
            )
            inv_obj.set_pending(
                self.cursor, self.uid,
                [invoice_id], res_id
            )
            invos.append(invoice_id)
            facts.append(fact_id)
        return facts, invos

    def create_no_remesable(self):
        pt_obj = self.pool.get("payment.type")
        no_remesa_ids = pt_obj.search(
            self.cursor, self.uid,
            [('code', '=', 'NO_REMESA')]
        )
        if no_remesa_ids:
            return no_remesa_ids[0]

        return pt_obj.create(
            self.cursor, self.uid,
            {
                'name': u'No remesables',
                'code': 'NO_REMESA',
                'note': u"Factures que no s'han de remesar",
            }
        )

    def test_set_pending_FUE__one_invoice(self):
        fue_bs_state_id = self.getref(
            "som_account_invoice_pending", "fue_bo_social_pending_state"
        )
        fue_df_state_id = self.getref(
            "som_account_invoice_pending", "fue_default_pending_state"
        )
        corr_state_id = self.getref(
            "account_invoice_pending", "default_invoice_pending_state"
        )

        fact_ids, inv_ids = self._load_data_unpaid_invoices(
            [corr_state_id, corr_state_id]
        )

        no_remesa_pt_id = self.create_no_remesable()

        inv_obj = self.pool.get("account.invoice")
        fact_obj = self.pool.get("giscedata.facturacio.factura")

        self.write_one(fact_obj, fact_ids[0], 'comment', u"2024-02-30 BlaBLaBLa")
        previous_comment_1 = self.read_one(fact_obj, fact_ids[0], 'comment')
        previous_comment_2 = self.read_one(fact_obj, fact_ids[1], 'comment')

        inv_obj.set_pending(self.cursor, self.uid, [inv_ids[0]], fue_bs_state_id)
        inv_obj.set_pending(self.cursor, self.uid, [inv_ids[1]], fue_df_state_id)

        f_data = fact_obj.browse(self.cursor, self.uid, fact_ids[0])
        self.assertEqual(f_data.pending_state.id, fue_bs_state_id)
        self.assertEqual(f_data.payment_type.id, no_remesa_pt_id)
        new_comment, old_comment = split_first(f_data.comment)
        expected_comment = u'{} - Factura - FUE'.format(get_today_str())
        self.assertEqual(new_comment, expected_comment)
        self.assertEqual(old_comment, previous_comment_1)

        f_data = fact_obj.browse(self.cursor, self.uid, fact_ids[1])
        self.assertEqual(f_data.pending_state.id, fue_df_state_id)
        self.assertEqual(f_data.payment_type.id, no_remesa_pt_id)
        new_comment, old_comment = split_first(f_data.comment)
        expected_comment = u'{} - Factura - FUE'.format(get_today_str())
        self.assertEqual(new_comment, expected_comment)
        self.assertEqual(old_comment, previous_comment_2)

    def test_set_pending_R1__one_invoice(self):
        r1_bs_state_id = self.getref(
            "som_account_invoice_pending", "reclamacio_en_curs_pending_state"
        )
        r1_df_state_id = self.getref(
            "som_account_invoice_pending", "default_reclamacio_en_curs_pending_state"
        )
        corr_state_id = self.getref(
            "account_invoice_pending", "default_invoice_pending_state"
        )

        fact_ids, inv_ids = self._load_data_unpaid_invoices(
            [corr_state_id, corr_state_id]
        )

        no_remesa_pt_id = self.create_no_remesable()

        inv_obj = self.pool.get("account.invoice")
        fact_obj = self.pool.get("giscedata.facturacio.factura")

        self.write_one(fact_obj, fact_ids[0], 'comment', u"2021-02-15 BlaBLaBLa")
        self.write_one(
            fact_obj, fact_ids[0], 'comment',
            u"2022-04-12 BlaBLaBLa\n2021-05-12 test multiline"
        )
        previous_comment_1 = self.read_one(fact_obj, fact_ids[0], 'comment')
        previous_comment_2 = self.read_one(fact_obj, fact_ids[1], 'comment')

        inv_obj.set_pending(self.cursor, self.uid, [inv_ids[0]], r1_bs_state_id)
        inv_obj.set_pending(self.cursor, self.uid, [inv_ids[1]], r1_df_state_id)

        f_data = fact_obj.browse(self.cursor, self.uid, fact_ids[0])
        self.assertEqual(f_data.pending_state.id, r1_bs_state_id)
        self.assertEqual(f_data.payment_type.id, no_remesa_pt_id)
        new_comment, old_comment = split_first(f_data.comment)
        expected_comment = u'{} - Factura - R1 Reclamació'.format(get_today_str())
        self.assertEqual(new_comment, expected_comment)
        self.assertEqual(old_comment, previous_comment_1)

        f_data = fact_obj.browse(self.cursor, self.uid, fact_ids[1])
        self.assertEqual(f_data.pending_state.id, r1_df_state_id)
        self.assertEqual(f_data.payment_type.id, no_remesa_pt_id)
        new_comment, old_comment = split_first(f_data.comment)
        expected_comment = u'{} - Factura - R1 Reclamació'.format(get_today_str())
        self.assertEqual(new_comment, expected_comment)
        self.assertEqual(old_comment, previous_comment_2)

    def test_set_pending_PERDU__one_invoice(self):
        perd_bs_state_id = self.getref(
            "som_account_invoice_pending", "perdues_fact_bo_social_pending_state"
        )
        perd_df_state_id = self.getref(
            "som_account_invoice_pending", "perdues_fact_default_pending_state"
        )
        corr_state_id = self.getref(
            "account_invoice_pending", "default_invoice_pending_state"
        )

        fact_ids, inv_ids = self._load_data_unpaid_invoices(
            [corr_state_id, corr_state_id]
        )

        no_remesa_pt_id = self.create_no_remesable()

        inv_obj = self.pool.get("account.invoice")
        fact_obj = self.pool.get("giscedata.facturacio.factura")

        self.write_one(fact_obj, fact_ids[0], 'comment', u"2024-05-30 BlaBLaBLa")
        self.write_one(fact_obj, fact_ids[1], 'comment', u"1999-01-31 ????!")
        previous_comment_1 = self.read_one(fact_obj, fact_ids[0], 'comment')
        previous_comment_2 = self.read_one(fact_obj, fact_ids[1], 'comment')

        inv_obj.set_pending(self.cursor, self.uid, [inv_ids[0]], perd_bs_state_id)
        inv_obj.set_pending(self.cursor, self.uid, [inv_ids[1]], perd_df_state_id)

        f_data = fact_obj.browse(self.cursor, self.uid, fact_ids[0])
        self.assertEqual(f_data.pending_state.id, perd_bs_state_id)
        self.assertEqual(f_data.payment_type.id, no_remesa_pt_id)
        new_comment, old_comment = split_first(f_data.comment)
        expected_comment = u'{} - Factura - Pèrdues'.format(get_today_str())
        self.assertEqual(new_comment, expected_comment)
        self.assertEqual(old_comment, previous_comment_1)

        f_data = fact_obj.browse(self.cursor, self.uid, fact_ids[1])
        self.assertEqual(f_data.pending_state.id, perd_df_state_id)
        self.assertEqual(f_data.payment_type.id, no_remesa_pt_id)
        new_comment, old_comment = split_first(f_data.comment)
        expected_comment = u'{} - Factura - Pèrdues'.format(get_today_str())
        self.assertEqual(new_comment, expected_comment)
        self.assertEqual(old_comment, previous_comment_2)

    def test_set_pending_various__set_of_invoices(self):
        fue_bs_state_id = self.getref(
            "som_account_invoice_pending", "fue_bo_social_pending_state"
        )
        fue_df_state_id = self.getref(
            "som_account_invoice_pending", "fue_default_pending_state"
        )
        r1_bs_state_id = self.getref(
            "som_account_invoice_pending", "reclamacio_en_curs_pending_state"
        )
        r1_df_state_id = self.getref(
            "som_account_invoice_pending", "default_reclamacio_en_curs_pending_state"
        )
        perd_bs_state_id = self.getref(
            "som_account_invoice_pending", "perdues_fact_bo_social_pending_state"
        )
        perd_df_state_id = self.getref(
            "som_account_invoice_pending", "perdues_fact_default_pending_state"
        )
        corr_state_id = self.getref(
            "account_invoice_pending", "default_invoice_pending_state"
        )
        extra_df_state_id = self.getref(
            "som_account_invoice_pending", "fracc_manual_default_pending_state"
        )

        fact_ids, inv_ids = self._load_data_unpaid_invoices(
            [
                corr_state_id,
                corr_state_id,
                corr_state_id,
                corr_state_id,
                corr_state_id,
                corr_state_id,
                corr_state_id,
                corr_state_id,
            ]
        )

        no_remesa_pt_id = self.create_no_remesable()

        inv_obj = self.pool.get("account.invoice")
        fact_obj = self.pool.get("giscedata.facturacio.factura")

        self.write_one(fact_obj, fact_ids[0], 'comment', u"2021-04-20 BlaBLaBLa...")
        self.write_one(fact_obj, fact_ids[1], 'comment', u"2022-07-22 BlaBLaBLa!!!")
        self.write_one(fact_obj, fact_ids[2], 'comment', u"2023-05-15 BlaBLaBLa???")
        self.write_one(fact_obj, fact_ids[3], 'comment', u"2024-03-10 BlaBLaBLa¿¿¿")
        self.write_one(fact_obj, fact_ids[4], 'comment', u"2011-10-09 BlaBLaBLa***")
        self.write_one(fact_obj, fact_ids[5], 'comment', u"2012-11-03 BlaBLaBLaZZZ")
        self.write_one(fact_obj, fact_ids[6], 'comment', u"2013-12-30 BlaBLaBLa+++")
        self.write_one(fact_obj, fact_ids[7], 'comment', u"2014-06-05 BlaBLaBLa---")

        previous_comment = []
        previous_comment.append(self.read_one(fact_obj, fact_ids[0], 'comment'))
        previous_comment.append(self.read_one(fact_obj, fact_ids[1], 'comment'))
        previous_comment.append(self.read_one(fact_obj, fact_ids[2], 'comment'))
        previous_comment.append(self.read_one(fact_obj, fact_ids[3], 'comment'))
        previous_comment.append(self.read_one(fact_obj, fact_ids[4], 'comment'))
        previous_comment.append(self.read_one(fact_obj, fact_ids[5], 'comment'))
        previous_comment.append(self.read_one(fact_obj, fact_ids[6], 'comment'))
        previous_comment.append(self.read_one(fact_obj, fact_ids[7], 'comment'))

        previous_payment_type_6 = self.read_one(fact_obj, fact_ids[6], 'payment_type')[0]
        previous_payment_type_7 = self.read_one(fact_obj, fact_ids[7], 'payment_type')[0]

        inv_obj.set_pending(self.cursor, self.uid, [inv_ids[0]], fue_bs_state_id)
        inv_obj.set_pending(self.cursor, self.uid, [inv_ids[1]], fue_df_state_id)
        inv_obj.set_pending(self.cursor, self.uid, [inv_ids[2]], r1_bs_state_id)
        inv_obj.set_pending(self.cursor, self.uid, [inv_ids[3]], r1_df_state_id)
        inv_obj.set_pending(self.cursor, self.uid, [inv_ids[4]], perd_bs_state_id)
        inv_obj.set_pending(self.cursor, self.uid, [inv_ids[5]], perd_df_state_id)
        inv_obj.set_pending(self.cursor, self.uid, [inv_ids[6]], corr_state_id)
        inv_obj.set_pending(self.cursor, self.uid, [inv_ids[7]], extra_df_state_id)

        idx = 0
        f_data = fact_obj.browse(self.cursor, self.uid, fact_ids[idx])
        self.assertEqual(f_data.pending_state.id, fue_bs_state_id)
        self.assertEqual(f_data.payment_type.id, no_remesa_pt_id)
        new_comment, old_comment = split_first(f_data.comment)
        expected_comment = u'{} - Factura - FUE'.format(get_today_str())
        self.assertEqual(new_comment, expected_comment)
        self.assertEqual(old_comment, previous_comment[idx])

        idx = 1
        f_data = fact_obj.browse(self.cursor, self.uid, fact_ids[idx])
        self.assertEqual(f_data.pending_state.id, fue_df_state_id)
        self.assertEqual(f_data.payment_type.id, no_remesa_pt_id)
        new_comment, old_comment = split_first(f_data.comment)
        expected_comment = u'{} - Factura - FUE'.format(get_today_str())
        self.assertEqual(new_comment, expected_comment)
        self.assertEqual(old_comment, previous_comment[idx])

        idx = 2
        f_data = fact_obj.browse(self.cursor, self.uid, fact_ids[idx])
        self.assertEqual(f_data.pending_state.id, r1_bs_state_id)
        self.assertEqual(f_data.payment_type.id, no_remesa_pt_id)
        new_comment, old_comment = split_first(f_data.comment)
        expected_comment = u'{} - Factura - R1 Reclamació'.format(get_today_str())
        self.assertEqual(new_comment, expected_comment)
        self.assertEqual(old_comment, previous_comment[idx])

        idx = 3
        f_data = fact_obj.browse(self.cursor, self.uid, fact_ids[idx])
        self.assertEqual(f_data.pending_state.id, r1_df_state_id)
        self.assertEqual(f_data.payment_type.id, no_remesa_pt_id)
        new_comment, old_comment = split_first(f_data.comment)
        expected_comment = u'{} - Factura - R1 Reclamació'.format(get_today_str())
        self.assertEqual(new_comment, expected_comment)
        self.assertEqual(old_comment, previous_comment[idx])

        idx = 4
        f_data = fact_obj.browse(self.cursor, self.uid, fact_ids[idx])
        self.assertEqual(f_data.pending_state.id, perd_bs_state_id)
        self.assertEqual(f_data.payment_type.id, no_remesa_pt_id)
        new_comment, old_comment = split_first(f_data.comment)
        expected_comment = u'{} - Factura - Pèrdues'.format(get_today_str())
        self.assertEqual(new_comment, expected_comment)
        self.assertEqual(old_comment, previous_comment[idx])

        idx = 5
        f_data = fact_obj.browse(self.cursor, self.uid, fact_ids[idx])
        self.assertEqual(f_data.pending_state.id, perd_df_state_id)
        self.assertEqual(f_data.payment_type.id, no_remesa_pt_id)
        new_comment, old_comment = split_first(f_data.comment)
        expected_comment = u'{} - Factura - Pèrdues'.format(get_today_str())
        self.assertEqual(new_comment, expected_comment)
        self.assertEqual(old_comment, previous_comment[idx])

        idx = 6
        f_data = fact_obj.browse(self.cursor, self.uid, fact_ids[idx])
        self.assertEqual(f_data.pending_state.id, corr_state_id)
        self.assertEqual(f_data.payment_type.id, previous_payment_type_6)
        self.assertEqual(f_data.comment, previous_comment[idx])

        idx = 7
        f_data = fact_obj.browse(self.cursor, self.uid, fact_ids[idx])
        self.assertEqual(f_data.pending_state.id, extra_df_state_id)
        self.assertEqual(f_data.payment_type.id, previous_payment_type_7)
        self.assertEqual(f_data.comment, previous_comment[idx])


class TestAccountInvoiceProviderUnpaidAutomations(testing.OOTestCase):
    def setUp(self):
        self.txn = Transaction().start(self.database)

        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.pool = self.openerp.pool

    def tearDown(self):
        self.txn.stop()

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test_no_send_mail_when_unpaid_no_apo(self, mocked_send_mail):
        ai_obj = self.pool.get("account.invoice")
        ai_id = ai_obj.search(self.cursor, self.uid, [('name', '=', 'PURCHASE-SMOKE-TEST-1')])[0]

        wiz_o = self.pool.get("wizard.unpay")
        context = {"active_ids": [ai_id], "active_id": ai_id, "model": "account.invoice"}

        values = {
            "pay_journal_id": 47,
            "pay_account_id": 1718,
            "date": date.today().strftime("%Y-%m-%d"),
        }
        wiz_id = wiz_o.create(self.cursor, self.uid, values, context=context)
        wiz_o.unpay(self.cursor, self.uid, [wiz_id], context=context)

        mocked_send_mail.assert_not_called()

    @mock.patch("poweremail.poweremail_send_wizard.poweremail_send_wizard.send_mail")
    def test_send_mail_when_unpaid_apo(self, mocked_send_mail):

        ai_obj = self.pool.get("account.invoice")
        ai_id = ai_obj.search(self.cursor, self.uid, [('name', '=', 'PURCHASE-SMOKE-TEST-1')])[0]

        IrModel = self.pool.get("ir.model.data")
        journal_id = IrModel.get_object_reference(
            self.cursor, self.uid, "som_generationkwh", "apo_journal"
        )[1]
        payment_type_id = IrModel.get_object_reference(
            self.cursor, self.uid, "account_payment", "payment_type_demo"
        )[1]

        ai_obj.write(self.cursor, self.uid, ai_id, {
                     "journal_id": journal_id, "payment_type": payment_type_id, "name": 'APO_001'})
        wiz_o = self.pool.get("wizard.unpay")
        context = {"active_ids": [ai_id], "active_id": ai_id, "model": "account.invoice"}

        values = {
            "pay_journal_id": 47,
            "pay_account_id": 1718,
            "date": date.today().strftime("%Y-%m-%d"),
        }
        wiz_id = wiz_o.create(self.cursor, self.uid, values, context=context)
        wiz_o.unpay(self.cursor, self.uid, [wiz_id], context=context)

        mocked_send_mail.assert_called_once()

        # template_id = IrModel.get_object_reference(
        #     self.cursor, self.uid, "som_account_invoice_pending",
        #     "email_interessos_aportacions_retornat"
        # )[1]
        # account_obj = self.pool.get("poweremail.core_accounts")
        # email_from = account_obj.search(
        #     self.cursor, self.uid, [("email_id", "=", "aporta@somenergia.coop")]
        # )[0]
        # expected_ctx = {
        #     'unpay_move_pending_state': 1,
        #     'from': email_from,
        #     'journal_id': 47,
        #     'priority': '0',
        #     'src_model': 'account.invoice',
        #     'state': 'single',
        #     'period_id': 5,
        #     'use_account_id': False,
        #     'date_p': '2025-05-28',
        #     'src_rec_ids': [ai_id],
        #     'model': 'account.invoice',
        #     'active_ids': [ai_id],
        #     'type': 'in_invoice',
        #     'template_id': template_id,
        #     'active_id': ai_id,
        # }
        # mocked_send_mail.assert_called_with(self.cursor, self.uid, [1], context = expected_ctx)


# vim: et ts=4 sw=4
