# -*- coding: utf-8 -*-
from osv import osv, fields


class WizardModel(osv.osv_memory):

    _name = "wizard.model"

    def action_template(self, cursor, uid, ids, context=None):

        if not context:
            return False

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        context.get("active_ids")

        return {"type": "ir.actions.act_window_close"}

    _columns = {
        "template_field": fields.char(
            "Example of field",
            size=64,
            required=True,
            help="La nova contrasenya",
        ),
    }


WizardModel()
