# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

STATES = [
    ("init", "Estat Inicial"),
    ("finished", "Estat Final"),
]


class WizardCreateEnviamentsFromObject(osv.osv_memory):
    _name = "wizard.infoenergia.create.enviaments.from.object"

    def create_enviaments(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context=context)
        lot_obj = self.pool.get("som.infoenergia.lot.enviament")
        lot_id = wiz.read(["lot_enviament"])[0]["lot_enviament"]
        if not lot_id:
            raise osv.except_osv("ERROR", "S'ha de seleccionar un lot d'enviament")

        pol_ids = context.get("active_ids", [])
        wiz.write({"state": "finished"})
        del context["active_ids"]
        lot_obj.create_enviaments_from_object_list(cursor, uid, lot_id, pol_ids, context)

    _columns = {
        "state": fields.selection(
            STATES, _(u"Estat del wizard de creació d'enviaments a partir de pòlisses")
        ),
        "lot_enviament": fields.many2one(
            "som.infoenergia.lot.enviament",
            "Lot Enviament",
            help=_(u"Lot Enviament on s'afegeixen les pòlisses"),
        ),
    }

    _defaults = {
        "state": "init",
    }


WizardCreateEnviamentsFromObject()
