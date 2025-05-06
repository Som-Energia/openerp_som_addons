# -*- coding: utf-8 -*-

from osv import osv
from tools.translate import _


class WizardReportTestGroupViewTests(osv.osv_memory):
    _name = "wizard.report.test.group.view.tests"

    def get_all_test(self, cursor, uid, context):
        if not context:
            context = {}

        rtg_ids = context.get("active_ids", [])
        if not rtg_ids:
            return []

        rt_obj = self.pool.get("report.test")
        rt_ids = rt_obj.search(cursor, uid, [
            ("group_id", "in", rtg_ids),
        ])
        return rt_ids

    def view_all_test(self, cursor, uid, ids, context=None):
        rt_ids = self.get_all_test(cursor, uid, context)
        return {
            "domain": "[('id','in', {0})]".format(str(rt_ids)),
            "name": _("Tots els tests"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "report.test",
            "type": "ir.actions.act_window",
        }

    def view_attach_all_test(self, cursor, uid, ids, context=None):
        rt_ids = self.get_all_test(cursor, uid, context)
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

    def get_error_test(self, cursor, uid, context):
        if not context:
            context = {}

        rtg_ids = context.get("active_ids", [])
        if not rtg_ids:
            return []

        rt_obj = self.pool.get("report.test")
        rt_ids = rt_obj.search(cursor, uid, [
            ("group_id", "in", rtg_ids),
            ("result", "not in", ["equals", "differents"]),
        ])
        return rt_ids

    def view_error_test(self, cursor, uid, ids, context=None):
        rt_ids = self.get_error_test(cursor, uid, context)
        return {
            "domain": "[('id','in', {0})]".format(str(rt_ids)),
            "name": _("Tests amb Errors"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "report.test",
            "type": "ir.actions.act_window",
        }

    def view_attach_error_test(self, cursor, uid, ids, context=None):
        rt_ids = self.get_error_test(cursor, uid, context)
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

    def get_diff_test(self, cursor, uid, context):
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
        return rt_ids

    def view_diffs(self, cursor, uid, ids, context=None):
        rt_ids = self.get_diff_test(cursor, uid, context)
        return {
            "domain": "[('id','in', {0})]".format(str(rt_ids)),
            "name": _("Tests amb diferències"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "report.test",
            "type": "ir.actions.act_window",
        }

    def view_attach_diffs(self, cursor, uid, ids, context=None):
        rt_ids = self.get_diff_test(cursor, uid, context)
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

    def delete_all_attachs(self, cursor, uid, ids, context=None):
        rt_ids = self.get_all_test(cursor, uid, context)
        att_obj = self.pool.get("ir.attachment")
        att_ids = att_obj.search(cursor, uid, [
            ('res_model', '=', 'report.test'),
            ('res_id', 'in', rt_ids),
        ])
        if att_ids:
            att_obj.unlink(cursor, uid, att_ids)
        return True

    _columns = {
    }

    _defaults = {
    }


WizardReportTestGroupViewTests()
