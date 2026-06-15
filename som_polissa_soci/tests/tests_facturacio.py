# -*- coding: utf-8 -*-
from destral import testing
import json


class TestsFacturacioDonatiu(testing.OOTestCaseWithCursor):
    def get_object_id(self, module, obj_ref):
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        irmd_o = pool.get("ir.model.data")
        object_id = irmd_o.get_object_reference(cursor, uid, module, obj_ref)[1]
        return object_id

    def test_add_donatiu_line(self):
        """
        Comprova que s'afegeix una línia de donatiu (DN01) a la factura
        quan la pòlissa té el donatiu activat.

        @return:
        """
        cursor, uid, pool = (self.txn.cursor, self.txn.user, self.openerp.pool)
        polissa_o = pool.get("giscedata.polissa")
        wiz_o = pool.get("wizard.manual.invoice")
        linia_factura_o = pool.get("giscedata.facturacio.factura.linia")

        polissa_id = self.get_object_id("giscedata_polissa", "polissa_0001")
        journal_id = self.get_object_id("giscedata_facturacio", "facturacio_journal_energia")
        partner_id = self.get_object_id("base", "res_partner_agrolait")
        product_dn01_id = self.get_object_id("som_polissa_soci", "dona_DN01")

        data_lectura_inici = "2016-02-02"
        data_lectura_final = "2016-03-03"

        polissa_wv = {
            "soci": partner_id,
            "data_ultima_lectura": data_lectura_inici,
            "donatiu": True,
        }
        polissa_o.write(cursor, uid, polissa_id, polissa_wv)

        polissa_o.send_signal(cursor, uid, [polissa_id], ["validar", "contracte"])

        wiz_cv = {
            "polissa_id": polissa_id,
            "journal_id": journal_id,
            "date_start": data_lectura_inici,
            "date_end": data_lectura_final,
        }
        wiz_id = wiz_o.create(cursor, uid, wiz_cv)
        wiz_o.action_manual_invoice(cursor, uid, [wiz_id])
        wiz_o = wiz_o.browse(cursor, uid, wiz_id)

        invoice_id = json.loads(wiz_o.invoice_ids)[0]
        dmn = [("factura_id", "=", invoice_id), ("product_id", "=", product_dn01_id)]
        linia_dn01_ids = linia_factura_o.search(cursor, uid, dmn)

        self.assertEqual(len(linia_dn01_ids), 1)

        linia_factura_v = linia_factura_o.read(
            cursor, uid, linia_dn01_ids[0], ["price_unit", "quantity"])
        self.assertEqual(linia_factura_v["price_unit"], 0.01)
