# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

AVAILABLE_STATES = [
    ("init", "Init"),
    ("category_specified", "categoria seleccionada"),
    ("done", "Done"),
]


class WizardMassiveCategoryToPolissa(osv.osv_memory):

    _name = "wizard.massive.category.to.polissa"

    def onchange_category(self, cursor, uid, ids, category_id):
        res = {"value": {"state": "init"}}
        if category_id:
            res = {"value": {"state": "category_specified"}}
        return res

    def action_assignar_categoria(self, cursor, uid, ids, context=None):
        return self.action_gestionar_categoria(cursor, uid, ids, True, context)

    def action_desassignar_categoria(self, cursor, uid, ids, context=None):
        return self.action_gestionar_categoria(cursor, uid, ids, False, context)

    def action_gestionar_categoria(self, cursor, uid, ids, afegir, context=None):
        active_ids = context.get("active_ids", [])

        if not active_ids:
            return {}

        pol_obj = self.pool.get("giscedata.polissa")

        info = u""
        modified = 0
        not_modified = 0
        wiz_vals = self.read(cursor, uid, ids)[0]
        category_id = wiz_vals.get("category", False)
        if not category_id:
            info += _(u"Categoria incorrecta seleccionada!")

        for active_id in active_ids:
            pol_data = pol_obj.read(cursor, uid, active_id, ["name", "category_id"])
            category_list = pol_data["category_id"]
            pol_name = pol_data["name"]

            if afegir:
                if category_id not in category_list:
                    pol_obj.write(cursor, uid, active_id, {"category_id": [(4, category_id)]})
                    info += _(u"Afegida categoria seleccionada a la pòlissa {}\n".format(pol_name))
                    modified += 1
                else:
                    info += _(u"Polissa {} ja té la categoria seleccionada\n".format(pol_name))
                    not_modified += 1
            else:
                if category_id in category_list:
                    pol_obj.write(cursor, uid, active_id, {"category_id": [(3, category_id)]})
                    info += _(u"Treta categoria seleccionada a la pòlissa {}\n".format(pol_name))
                    modified += 1
                else:
                    info += _(
                        u"Polissa {} ja no tenia la categoria seleccionada\n".format(pol_name)
                    )
                    not_modified += 1

        info += _(u"\n\nPolisses modificades {}\n".format(modified))
        info += _(u"Polisses no modificades {}\n".format(not_modified))

        self.write(cursor, uid, ids, {"state": "done", "info": info})
        return

    _columns = {
        "category": fields.many2one("giscedata.polissa.category", "Categories disponibles"),
        "state": fields.selection(selection=AVAILABLE_STATES, string="Estat"),
        "info": fields.text("Info"),
    }


WizardMassiveCategoryToPolissa()
