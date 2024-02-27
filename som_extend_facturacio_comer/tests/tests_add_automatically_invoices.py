# -*- coding: utf-8 -*-
from destral import testing
from destral.transaction import Transaction


class AddAutomaticallyInvoicesToPaymentOrder(testing.OOTestCase):
    def test_add_invoice(self):
        """
        Comproba que la funció que afegeix automáticament factures a les remeses
        ho fa correctament amb una remesa ja existent.
        :return: True
        """
        irmd_o = self.openerp.pool.get("ir.model.data")
        payment_order_o = self.openerp.pool.get("payment.order")
        invoice_o = self.openerp.pool.get("account.invoice")
        factura_o = self.openerp.pool.get("giscedata.facturacio.factura")
        imd_obj = self.openerp.pool.get("ir.model.data")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            mode_pagamet_id = irmd_o.get_object_reference(
                cursor, uid, "som_extend_facturacio_comer", "payment_mode_remesa_automatica"
            )[1]

            remesa_cv = {"mode": mode_pagamet_id, "date_prefered": "fixed", "type": "receivable"}
            payment_order_id = payment_order_o.create(cursor, uid, remesa_cv)
            due_date = "2016-11-21"
            dmn = [
                ("date_due", "=", due_date),
                ("state", "in", ("draft", "open")),
                ("type", "like", "out_%"),
                ("payment_order_id", "=", False),
                ("invoice_id.residual", "!=", 0.0),
            ]
            factura_ids = factura_o.search(cursor, uid, dmn)
            factura_o.invoice_open(cursor, uid, factura_ids)
            invoice_vals = factura_o.read(cursor, uid, factura_ids, ["invoice_id"])
            invoice_ids = [x["invoice_id"][0] for x in invoice_vals]

            df_process_id = imd_obj.get_object_reference(
                cursor, uid, "account_invoice_pending", "default_pending_state_process"
            )[1]

            correct_state = invoice_o._get_default_pending(
                cursor,
                uid,
                process_id=df_process_id,
            )
            invoice_o.set_pending(cursor, uid, invoice_ids, correct_state)

            res = payment_order_o.add_invoices_to_payment_order(
                cursor, uid, mode_pagamet_id, due_date
            )
            n_factures_added = res[0]
            payment_order_affected = res[1]
            payment_order_created = res[2]

            self.assertEqual(n_factures_added, len(factura_ids))
            factura_vs = factura_o.read(cursor, uid, factura_ids, ["payment_order_id"])
            for factura_v in factura_vs:
                self.assertEqual(payment_order_affected, factura_v["payment_order_id"][0])

            self.assertEqual(payment_order_affected, payment_order_id)
            self.assertFalse(payment_order_created)

        return True

    def test_add_invoice_creating_payment_order(self):
        """
        Comproba que la funció que afegeix automáticament factures a les remeses
        ho fa correctament sense cap remesa coincident (crea una de nova).
        :return: True
        """
        irmd_o = self.openerp.pool.get("ir.model.data")
        payment_order_o = self.openerp.pool.get("payment.order")
        factura_o = self.openerp.pool.get("giscedata.facturacio.factura")

        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user

            mode_pagamet_id = irmd_o.get_object_reference(
                cursor, uid, "som_extend_facturacio_comer", "payment_mode_remesa_automatica"
            )[1]

            due_date = "2016-11-21"
            dmn = [
                ("date_due", "=", due_date),
                ("state", "in", ("draft", "open")),
                ("type", "like", "out_%"),
                ("payment_order_id", "=", False),
                ("invoice_id.residual", "!=", 0.0),
            ]
            factura_ids = factura_o.search(cursor, uid, dmn)
            factura_o.invoice_open(cursor, uid, factura_ids)
            res = payment_order_o.add_invoices_to_payment_order(
                cursor, uid, mode_pagamet_id, due_date
            )
            n_factures_added = res[0]
            payment_order_affected = res[1]
            payment_order_created = res[2]

            self.assertEqual(n_factures_added, len(factura_ids))
            factura_vs = factura_o.read(cursor, uid, factura_ids, ["payment_order_id"])
            for factura_v in factura_vs:
                self.assertEqual(payment_order_affected, factura_v["payment_order_id"][0])
            self.assertTrue(payment_order_created)

        return True
