# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _


class WizardUpdateInvoiceOVCheckBox(osv.osv_memory):
    """Assistent per generar un llistat de Socis en CSV"""

    _name = "wizard.update.ov.check"

    def _default_info(self, cursor, uid, context=None):
        fact_ids = context.get("active_ids", False)
        return _(u"S'actualitzara el camp per {} factures".format(len(fact_ids)))

    def update_check_ov_box(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        fact_ids = context.get("active_ids", False)

        if not fact_ids:
            raise osv.except_osv(u"Error", u"No s'han seleccionat facturas")

        action = self.read(cursor, uid, ids, ["action"])[0]["action"]

        fact_obj = self.pool.get("giscedata.facturacio.factura")

        action = False if action == "desmarcar" else True

        fact_obj.write(cursor, uid, fact_ids, {"visible_ov": action}, context=context)

        self.write(
            cursor,
            uid,
            ids,
            {
                "info": _(u"S'han actualitzar correctament les {} factures".format(len(fact_ids))),
                "state": "end",
            },
            context=context,
        )

    _columns = {
        "action": fields.selection([("marcar", "Visible"), ("desmarcar", "No visible")], "Accio"),
        "info": fields.text("Info"),
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
    }

    _defaults = {
        "action": lambda *a: "desmarcar",
        "info": _default_info,
        "state": lambda *a: "init",
    }


WizardUpdateInvoiceOVCheckBox()
