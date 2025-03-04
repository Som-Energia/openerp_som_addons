# -*- coding: utf-8 -*-
from osv import osv


class WizardDesactivateGurbCups(osv.osv_memory):
    _name = "wizard.deactivate.gurb.cups"

    def deactivate_cups(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        gurb_cups_obj = self.pool.get("som.gurb.cups")
        gurb_cups_id = context.get("active_id", False)
        gurb_cups_obj.unsubscribe_gurb_cups(cursor, uid, gurb_cups_id, context=context)

        return True


WizardDesactivateGurbCups()
