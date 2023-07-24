# -*- coding: utf-8 -*-


from osv import osv, fields


class Norma57FileLine(osv.osv):
    _name = "norma57.file.line"
    _inherit = "norma57.file.line"

    def _pending_state(self, cursor, uid, ids, field_name, arg, context=None):
        res = {}
        for record in self.read(cursor, uid, ids, ["resource"]):
            if record["resource"]:
                model_fact, id_fact = record["resource"].split(",")
                id_fact = int(id_fact)
                if model_fact in ("account.invoice", "giscedata.facturacio.factura"):
                    invoice_obj = self.pool.get(model_fact)
                    if invoice_obj:
                        pending_state = invoice_obj.read(cursor, uid, id_fact, ["pending_state"])[
                            "pending_state"
                        ][1]
                        res[record["id"]] = pending_state
        return res

    _columns = {
        "pending_state": fields.function(
            _pending_state, method=True, string="Estat pendent", type="string"
        )
    }


Norma57FileLine()
