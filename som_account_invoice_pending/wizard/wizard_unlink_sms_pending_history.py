# -*- coding: utf-8 -*-

from osv import osv, fields


class WizardUnlinkSMSPendingHistory(osv.osv_memory):
    _name = "wizard.unlink.sms.pending.history"

    def unlink_sms_pending_history(self, cursor, uid, ids, context=None):

        sms_ids = context.get("active_ids", [])
        if not sms_ids:
            raise osv.except_osv("Error", "No s'ha seleccionat cap element")

        psms_box_obj = self.pool.get("powersms.smsbox")
        sms_info = psms_box_obj.read(cursor, uid, sms_ids, ["reference"])
        for info in sms_info:
            if not info["reference"] or ("giscedata.facturacio.factura" not in info["reference"]):
                raise osv.except_osv("Error", "S'ha seleccionat algun SMS que no és de factura")

        aiph_obj = self.pool.get("account.invoice.pending.history")
        aiph_ids = aiph_obj.search(cursor, uid, [("powersms_id", "in", sms_ids)])
        if aiph_ids:
            aiph_obj.write(
                cursor, uid, aiph_ids, {"powersms_id": False, "powersms_sent_date": False}
            )
        psms_box_obj.unlink(cursor, uid, sms_ids)
        self.write(cursor, uid, ids, {"state": "finished"})

    _columns = {
        "state": fields.char("State", size=16),
    }
    _defaults = {
        "state": lambda *a: "init",
    }


WizardUnlinkSMSPendingHistory()
