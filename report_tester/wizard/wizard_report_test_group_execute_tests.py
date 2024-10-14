# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _


class WizardReportTestGroupExecuteTests(osv.osv_memory):
    _name = "wizard.report.test.group.execute.tests"

    def do(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        rtg_obj = self.pool.get("report.test.group")
        rtg_ids = context.get("active_ids", [])
        info = rtg_obj.execute_tests(cursor, uid, rtg_ids, context)
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


WizardReportTestGroupExecuteTests()
