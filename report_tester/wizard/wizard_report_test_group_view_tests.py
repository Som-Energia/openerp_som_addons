# -*- coding: utf-8 -*-

from osv import osv
from tools.translate import _


class WizardReportTestGroupViewTests(osv.osv_memory):
    _name = "wizard.report.test.group.view.tests"

    def view_all_test(self, cursor, uid, ids, context=None):
        if not context:
            context = {}

        rtg_ids = context.get("active_ids", [])
        if not rtg_ids:
            return False

        rt_obj = self.pool.get("report.test")
        rt_ids = rt_obj.search(cursor, uid, [
            ("group_id", "in", rtg_ids),
        ])

        return {
            "domain": "[('id','in', {0})]".format(str(rt_ids)),
            "name": _("Tots els tests"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "report.test",
            "type": "ir.actions.act_window",
        }

    def view_error_test(self, cursor, uid, ids, context=None):
        if not context:
            context = {}

        rtg_ids = context.get("active_ids", [])
        if not rtg_ids:
            return False

        rt_obj = self.pool.get("report.test")
        rt_ids = rt_obj.search(cursor, uid, [
            ("group_id", "in", rtg_ids),
            ("result", "not in", ["equals", "differents"]),
        ])

        return {
            "domain": "[('id','in', {0})]".format(str(rt_ids)),
            "name": _("Tests amb Errors"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "report.test",
            "type": "ir.actions.act_window",
        }

    def view_diffs(self, cursor, uid, ids, context=None):
        if not context:
            context = {}

        rtg_ids = context.get("active_ids", [])
        if not rtg_ids:
            return False

        rt_obj = self.pool.get("report.test")
        rt_ids = rt_obj.search(cursor, uid, [
            ("group_id", "in", rtg_ids),
            ("result", "=", "differents"),
        ])

        return {
            "domain": "[('id','in', {0})]".format(str(rt_ids)),
            "name": _("Tests amb diferències"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "report.test",
            "type": "ir.actions.act_window",
        }

    def view_attach_diffs(self, cursor, uid, ids, context=None):
        if not context:
            context = {}

        rtg_ids = context.get("active_ids", [])
        if not rtg_ids:
            return False

        rt_obj = self.pool.get("report.test")
        rt_ids = rt_obj.search(cursor, uid, [
            ("group_id", "in", rtg_ids),
            ("result", "=", "differents"),
        ])

        att_obj = self.pool.get("ir.attachment")
        att_ids = att_obj.search(cursor, uid, [
            ('name', '=', "diff.pdf"),
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


WizardReportTestGroupViewTests()
