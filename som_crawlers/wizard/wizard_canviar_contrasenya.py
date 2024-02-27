# -*- coding: utf-8 -*-
from osv import osv, fields


class WizardCanviarContrasenya(osv.osv_memory):

    _name = "wizard.canviar.contrasenya"

    def canviar_contrasenya(self, cursor, uid, ids, context=None):

        if not context:
            return False

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        active_ids = context.get("active_ids")

        conf_obj = self.pool.get("som.crawlers.config")
        wizard = self.browse(cursor, uid, ids[0])
        for id in active_ids:
            conf_obj.canviar_contrasenya(cursor, uid, id, wizard.contrasenya, context=context)

        return {"type": "ir.actions.act_window_close"}

    _columns = {
        "contrasenya": fields.char(
            "Contrasenya",
            size=64,
            required=True,
            help="La nova contrasenya",
        ),
    }


WizardCanviarContrasenya()
