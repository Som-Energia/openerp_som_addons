# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _


class WizardCreateAtc(osv.osv_memory):
    _name = "wizard.create.atc.from.polissa"
    _inherit = "wizard.create.atc.from.polissa"

    def create_atc_case(self, cursor, uid, ids, from_model, context=None):
        atc_obj = self.pool.get("giscedata.atc")
        ret = super(WizardCreateAtc, self).create_atc_case(cursor, uid, ids, from_model, context)
        wizard = self.browse(cursor, uid, ids[0], context)

        cases_ids = wizard.generated_cases

        # Quan és un sol registre, el comportament ja és l'esperat
        if len(cases_ids) > 1:
            atc_obj.write(cursor, uid, cases_ids, {"name": wizard.name})
        return ret

    _defaults = {
        "name": lambda *a: _("Text per defecte"),
    }


WizardCreateAtc()
