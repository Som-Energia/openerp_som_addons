# -*- coding: utf-8 -*-

from osv import osv
from tools.translate import _


class WizardReportTestViewAttached(osv.osv_memory):
    _name = "wizard.report.test.view.attached"

    def view_attached(self, cursor, uid, ids, context=None):
        if not context:
            context = {}

        rt_ids = context.get("active_ids", [])
        if not rt_ids:
            return False

        att_obj = self.pool.get("ir.attachment")
        att_ids = att_obj.search(cursor, uid, [
            ('res_model', '=', 'report.test'),
            ('res_id', 'in', rt_ids),
        ])

        return {
            "domain": "[('id','in', {0})]".format(str(att_ids)),
            "name": _("Fitxers de diferències"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "ir.attachment",
            "type": "ir.actions.act_window",
        }

    _columns = {
    }

    _defaults = {
    }


WizardReportTestViewAttached()
