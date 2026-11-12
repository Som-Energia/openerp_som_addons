# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _


class WizardReportTestGroupAcceptTests(osv.osv_memory):
    _name = "wizard.report.test.group.accept.tests"

    def do(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        rtg_obj = self.pool.get("report.test.group")
        rtg_ids = context.get("active_ids", [])
        info = rtg_obj.accept_tests(cursor, uid, rtg_ids, context)
        self.write(cursor, uid, ids, {"state": "end", "info": info})
        return True

    _columns = {
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
        "info": fields.text(_("Informació"), readonly=True),
    }

    _defaults = {
        "state": lambda *a: "init",
        "info": lambda *a: "",
    }


WizardReportTestGroupAcceptTests()
