from osv import osv, fields

# -*- coding: utf-8 -*-
from tools.translate import _


class wizard_comment_to_F1(osv.osv_memory):

    _name = "wizard.comment.to.F1"

    def modify_text_F1(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context=context)
        if not wiz.comment and wiz.option != "eliminar":
            raise osv.except_osv(_("Error"), _("No s'ha omplert el camp comentari"))

        active_ids = context.get("active_ids", [])

        model = self.pool.get("giscedata.facturacio.importacio.linia")

        if wiz.option == "eliminar":
            model.write(cursor, uid, active_ids, {"user_observations": ""})
        elif wiz.option == "substituir":
            model.write(cursor, uid, active_ids, {"user_observations": wiz.comment})
        elif wiz.option == "afegir":
            for inv_id in active_ids:
                old_comment = model.read(cursor, uid, inv_id, ["user_observations"])[
                    "user_observations"
                ]
                old_comment = old_comment if old_comment else ""
                new_comment = wiz.comment + "\n"
                model.write(cursor, uid, inv_id, {"user_observations": new_comment + old_comment})
        return {}

    _columns = {
        "comment": fields.text(_(u"Comentari"), readonly=False),
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


wizard_comment_to_F1()
