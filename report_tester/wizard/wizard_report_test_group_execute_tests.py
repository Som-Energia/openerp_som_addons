# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _


class WizardReportTestGroupExecuteTests(osv.osv_memory):
    _name = "wizard.report.test.group.execute.tests"

    def do(self, cursor, uid, ids, context=None):
        info = _("test info")
        self.write(cursor, uid, ids, {"state": "end", "info": info})
        return True

    _columns = {
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
        "info": fields.text("Informació", readonly=True),
    }

    _defaults = {
        "state": lambda *a: "init",
        "info": lambda *a: "",
    }


WizardReportTestGroupExecuteTests()
