# -*- coding: utf-8 -*-
from osv import osv, fields


class WizardCanviarUsuari(osv.osv_memory):

    _name = "wizard.canviar.usuari"

    def canviar_usuari(self, cursor, uid, ids, context=None):

        if not context:
            return False

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        active_ids = context.get("active_ids")

        conf_obj = self.pool.get("som.crawlers.config")
        wizard = self.browse(cursor, uid, ids[0])
        for id in active_ids:
            conf_obj.canviar_usuari(cursor, uid, id, wizard.usuari, context=context)

        return {"type": "ir.actions.act_window_close"}

    _columns = {
        "usuari": fields.char(
            "Usuari",
            size=64,
            required=True,
            help="El nou nom d'usuari",
        ),
    }


WizardCanviarUsuari()
