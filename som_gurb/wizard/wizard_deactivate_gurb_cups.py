# -*- coding: utf-8 -*-
from osv import osv, fields


class WizardDesactivateGurbCups(osv.osv_memory):
    _name = "wizard.deactivate.gurb.cups"

    def deactivate_cups(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        gurb_cups_obj = self.pool.get("som.gurb.cups")
        gurb_cups_id = context.get("active_id", False)
        wizard = self.browse(cursor, uid, ids[0], context)
        context['ens_ha_avisat'] = wizard.ens_ha_avisat
        gurb_cups_obj.unsubscribe_gurb_cups(cursor, uid, gurb_cups_id, context=context)

        return True

    _columns = {
        'ens_ha_avisat': fields.boolean('Ens ha avisat'),
    }


WizardDesactivateGurbCups()
