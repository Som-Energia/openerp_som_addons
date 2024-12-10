# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _


class WizardReportTestExecuteTest(osv.osv_memory):
    _name = "wizard.report.test.execute.test"

    def do(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        rt_obj = self.pool.get("report.test")
        rt_ids = context.get("active_ids", [])
        info = rt_obj.execute_test(cursor, uid, rt_ids, context)
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


WizardReportTestExecuteTest()
