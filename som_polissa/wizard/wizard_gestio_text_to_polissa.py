# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


CAMPS = [
    ("info_gestio_endarrerida", "Gest. Endarrerida"),
    ("info_gestions_massives", "Gest. Massives"),
]


class WizardGestioTextToPolissa(osv.osv_memory):

    _name = "wizard.gestio.text.to.polissa"

    def get_polisses_ids(self, cursor, uid, ids, context=None):
        active_ids = context.get("active_ids")
        model = context.get("from_model", "giscedata.polissa")

        if model == "giscedata.polissa":
            return active_ids

        model_obj = self.pool.get(model)
        if model == "giscedata.facturacio.contracte_lot":
            pol_ids = model_obj.read(cursor, uid, active_ids, ["polissa_id"])
            return [p["polissa_id"][0] for p in pol_ids]

    def modify_gestio_to_polissa(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context=context)
        if not wiz.comment and wiz.option != "eliminar":
            raise osv.except_osv(_("Error"), _("No s'ha omplert el camp comentari"))

        pol_ids = self.get_polisses_ids(cursor, uid, ids, context)
        pol_obj = self.pool.get("giscedata.polissa")

        if wiz.option == "eliminar":
            pol_obj.write(cursor, uid, pol_ids, {wiz.field_to_write: ""})
        elif wiz.option == "substituir":
            pol_obj.write(cursor, uid, pol_ids, {wiz.field_to_write: wiz.comment})
        elif wiz.option == "afegir":
            for _id in pol_ids:
                old_comment = pol_obj.read(cursor, uid, _id, [wiz.field_to_write])[
                    wiz.field_to_write
                ]
                old_comment = old_comment if old_comment else ""
                new_comment = wiz.comment + "\n"
                pol_obj.write(cursor, uid, _id, {wiz.field_to_write: new_comment + old_comment})

        return {}

    _columns = {
        "comment": fields.text(_(u"Afegir text gestió"), readonly=False),
        "field_to_write": fields.selection(CAMPS, _(u"Camp"), readonly=False),
        "option": fields.selection(
            [
                ("afegir", "Afegir"),
                ("substituir", "Substituir"),
                ("eliminar", "Eliminar"),
            ],
            "Accio",
            required=True,
        ),
    }

    _defaults = {
        "option": lambda *a: "afegir",
    }


WizardGestioTextToPolissa()
