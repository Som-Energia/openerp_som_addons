# -*- coding: utf-8 -*-


from osv import osv, fields


class AccountInvoicePendingHistory(osv.osv):
    _name = "account.invoice.pending.history"
    _inherit = "account.invoice.pending.history"

    def _days_to_string(self, cr, uid, ids, field_name, unknow_none, context):
        invoice_pending_history_records = self.read(
            cr, uid, ids, ["id", "days_to_next_state"], context
        )
        res = {}
        for record in invoice_pending_history_records:
            days = record["days_to_next_state"]
            res[record["id"]] = str(days if days is not False else "")
        return res

    def historize(self, cursor, uid, ids, message=""):
        """sets text to observations field"""
        if not isinstance(ids, (tuple, list)):
            ids = [ids]
        for _id in ids:
            old_observations = self.read(cursor, uid, _id, ["observations"])["observations"]
            old_observations = "\n{}".format(old_observations) if old_observations else ""
            data = {"observations": message + old_observations}
            self.write(cursor, uid, _id, data)
        return True

    _columns = {
        "powersms_id": fields.many2one("powersms.smsbox", u"SMS", required=False),
        "powersms_sent_date": fields.date(u"SMS sent date", readonly=True),
        "observations": fields.char(u"Observacions", size=256),
        "days_to_next_state": fields.integer(u"Dies pel següent canvi automàtic", required=False),
        "days_to_next_state_string": fields.function(
            _days_to_string,
            type="char",
            size=128,
            method=True,
            string=u"Dies pel següent canvi automàtic des de la data de canvi",
            help=u"Si aquest camp està buit es faran servir els dies per defecte",
        ),
    }


AccountInvoicePendingHistory()


class GiscedataFacturacioFactura(osv.osv):
    _name = "giscedata.facturacio.factura"
    _inherit = "giscedata.facturacio.factura"

    def powersms_create_callback(self, cursor, uid, ids, vals, context=None):
        """Hook que cridarà el powersms quan es creei un sms
        a partir d'una pòlisssa.
        """
        if context is None:
            context = {}

        hist_obj = self.pool.get("account.invoice.pending.history")
        pending_state_id = context.get("pending_state_id", False)
        origin_ids = context.get("ps_callback_origin_ids", {})
        for f_id in ids:
            inv_id = self.read(cursor, uid, f_id, ["invoice_id"])["invoice_id"][0]
            search_params = [("invoice_id", "=", inv_id)]
            if pending_state_id:
                search_params.append(("pending_state_id", "=", pending_state_id))
            hist_id = hist_obj.search(cursor, uid, search_params)
            if hist_id:
                hist_id = hist_id[0]
                hist_obj.write(cursor, uid, hist_id, {"powersms_id": origin_ids.get(f_id, False)})
        return True

    def powersms_write_callback(self, cursor, uid, ids, vals, context=None):
        """Hook que cridarà el powersms quan es modifiqui un sms."""
        if context is None:
            context = {}

        if "date_sms" in vals and "folder" in vals:
            vals_w = {
                "powersms_sent_date": vals["date_sms"],
            }
            if vals["folder"] == "sent":
                hist_obj = self.pool.get("account.invoice.pending.history")
                origin_ids = context.get("ps_callback_origin_ids", {})
                for f_id in ids:
                    inv_id = self.read(cursor, uid, f_id, ["invoice_id"])["invoice_id"][0]
                    sms_id = origin_ids.get(f_id, False)
                    if sms_id:
                        hist_id = hist_obj.search(
                            cursor, uid, [("invoice_id", "=", inv_id), ("powersms_id", "=", sms_id)]
                        )
                        if hist_id:
                            hist_obj.write(cursor, uid, hist_id, vals_w)
        return True


GiscedataFacturacioFactura()
