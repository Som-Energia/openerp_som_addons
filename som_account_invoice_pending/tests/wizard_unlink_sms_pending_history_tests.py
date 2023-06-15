# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction
from osv.osv import except_osv


class TestWizardUnlinkSMSPendingHistory(testing.OOTestCase):
    def setUp(self):
        self.pool = self.openerp.pool

    def _load_data_unpaid_invoice(self, cursor, uid):
        imd_obj = self.pool.get("ir.model.data")
        rpa_obj = self.pool.get("res.partner.address")
        self.inv_obj = self.pool.get("account.invoice")
        self.fact_obj = self.pool.get("giscedata.facturacio.factura")

        waiting_48h_def = imd_obj.get_object_reference(
            cursor,
            uid,
            "som_account_invoice_pending",
            "default_pendent_notificacio_tall_imminent_pending_state",
        )[1]
        self.fact_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio", "factura_0001"
        )[1]
        titular_id = self.fact_obj.browse(cursor, uid, self.fact_id).partner_id.id
        address_id = rpa_obj.search(cursor, uid, [("partner_id", "=", titular_id)])
        rpa_obj.write(cursor, uid, address_id, {"mobile": "600000000"})

        self.account_id = imd_obj.get_object_reference(
            cursor, uid, "som_account_invoice_pending", "cobraments_mail_account"
        )[1]

        invoice_id = self.fact_obj.read(cursor, uid, self.fact_id, ["invoice_id"])["invoice_id"][0]
        self.inv_obj.set_pending(cursor, uid, [invoice_id], waiting_48h_def)

    def test__unlink_sms_pending_history__ok(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            wiz_obj = self.pool.get("wizard.unlink.sms.pending.history")

            self._load_data_unpaid_invoice(cursor, uid)
            pending_obj = self.pool.get("update.pending.states")

            pending_obj.update_waiting_for_48h(cursor, uid)

            psms_obj = self.pool.get("powersms.smsbox")
            sms_to_send = psms_obj.search(
                cursor,
                uid,
                [
                    ("psms_from", "like", "Info"),
                    ("psms_body_text", "ilike", "%CORTE LUZ POR IMPAGO EN 48h%"),
                ],
            )[0]
            self.assertTrue(sms_to_send)

            factura = self.fact_obj.browse(cursor, uid, self.fact_id)
            aiph = factura.pending_history_ids[1]
            self.assertEqual(aiph.powersms_id.id, sms_to_send)
            aiph = factura.pending_history_ids[1].powersms_sent_date = "2020-01-01"

            context = {"active_id": sms_to_send, "active_ids": [sms_to_send]}
            wiz_id = wiz_obj.create(cursor, uid, {}, context)
            wiz_obj.unlink_sms_pending_history(cursor, uid, [wiz_id], context)

            factura = self.fact_obj.browse(cursor, uid, self.fact_id)
            aiph = factura.pending_history_ids[1]
            self.assertEqual(aiph.powersms_id.id, False)
            self.assertEqual(factura.pending_history_ids[1].powersms_sent_date, False)
            self.assertFalse(psms_obj.search(cursor, uid, [("id", "=", sms_to_send)]))

    def test__unlink_sms_pending_history__not_factura_reference(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            imd_obj = self.pool.get("ir.model.data")

            p_addres_sms = imd_obj.get_object_reference(cursor, uid, "powersms", "sms_outbox_001")[
                1
            ]
            psms_obj = self.pool.get("powersms.smsbox")
            psms_obj.write(cursor, uid, [p_addres_sms], {"reference": "res.partner.address,1"})
            wiz_obj = self.pool.get("wizard.unlink.sms.pending.history")

            context = {"active_id": p_addres_sms, "active_ids": [p_addres_sms]}
            wiz_id = wiz_obj.create(cursor, uid, {}, context)

            with self.assertRaises(except_osv) as error:
                wiz_obj.unlink_sms_pending_history(cursor, uid, [wiz_id], context)
            self.assertEqual(
                error.exception.message,
                "warning -- Error\n\nS'ha seleccionat algun SMS que no és de factura",
            )
            self.assertTrue(psms_obj.search(cursor, uid, [("id", "=", p_addres_sms)]))

    def test__unlink_sms_pending_history__factura_without_pending_history(self):
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            imd_obj = self.pool.get("ir.model.data")
            fact_obj = self.pool.get("giscedata.facturacio.factura")
            p_addres_sms = imd_obj.get_object_reference(cursor, uid, "powersms", "sms_outbox_001")[
                1
            ]
            psms_obj = self.pool.get("powersms.smsbox")
            fact_id = imd_obj.get_object_reference(
                cursor, uid, "giscedata_facturacio", "factura_0001"
            )[1]
            psms_obj.write(
                cursor,
                uid,
                [p_addres_sms],
                {"reference": "giscedata.facturacio.factura,{}".format(fact_id)},
            )
            factura = fact_obj.browse(cursor, uid, fact_id)
            aiph = factura.pending_history_ids
            self.assertFalse(aiph)
            wiz_obj = self.pool.get("wizard.unlink.sms.pending.history")

            context = {"active_id": p_addres_sms, "active_ids": [p_addres_sms]}
            wiz_id = wiz_obj.create(cursor, uid, {}, context)
            wiz_obj.unlink_sms_pending_history(cursor, uid, [wiz_id], context)

            self.assertFalse(psms_obj.search(cursor, uid, [("id", "=", p_addres_sms)]))
