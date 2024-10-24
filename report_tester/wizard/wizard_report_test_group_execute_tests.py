# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
import threading
import pooler
from oorq.oorq import JobsPool


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

    def do_async(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        rtg_ids = context.get("active_ids", [])
        rtg_obj = self.pool.get("report.test.group")
        rt_ids = rtg_obj.pre_execute_tests_async(cursor, uid, rtg_ids, context=context)

        gen_thread = threading.Thread(
            target=self.do_async_theaded, args=(cursor, uid, ids, rt_ids, context)
        )
        gen_thread.start()
        msg = _("Executant {} tests per workers.").format(len(rt_ids))
        self.write(cursor, uid, ids, {"state": "end", "info": msg})
        return True

    def do_async_theaded(self, cursor, uid, ids, rt_ids, context=None):
        if context is None:
            context = {}

        rt_obj = self.pool.get("report.test")
        th_cursor = pooler.get_db(cursor.dbname).cursor()
        j_pool = JobsPool()
        for rt_id in rt_ids:
            j_pool.add_job(
                rt_obj.execute_one_test_async(th_cursor, uid, rt_id, context=context)
            )
        j_pool.join()
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
