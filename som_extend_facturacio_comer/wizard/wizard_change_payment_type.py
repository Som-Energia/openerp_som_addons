# -*- encoding: utf-8 -*-
from osv import osv, fields


class WizardChangePaymentType(osv.osv_memory):

    _name = "wizard.change.payment.type"

    def _get_default_model(self, cursor, uid, context=None):
        if context is None:
            context = {}

        return context.get("model")

    def action_change_payment_type(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz = self.browse(cursor, uid, ids[0])

        selected_ids = context.get("active_ids", [])
        model = context.get("model")

        model_obj = self.pool.get(model)
        vals = {}

        if wiz.payment_type:
            vals.update({"payment_type": wiz.payment_type.id})
        if wiz.payment_mode:
            vals.update({"payment_mode_id": wiz.payment_mode.id})

        model_obj.write(cursor, uid, selected_ids, vals)

        wiz.write({"state": "end"})

    _columns = {
        "state": fields.selection([("init", "Initial"), ("end", "End")], "State"),
        "model": fields.char("Model de dades", size=32),
        "payment_type": fields.many2one("payment.type", "Tipus de pagament"),
        "payment_mode": fields.many2one("payment.mode", "Mode de pagament"),
    }

    _defaults = {"state": lambda *a: "init", "model": _get_default_model}


WizardChangePaymentType()
