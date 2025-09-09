# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _
from tools import email_send


class ReportTesterAutomation(osv.osv_memory):

    _name = "report.tester.automation"

    def automation(self, cursor, uid, context=None):
        rtg_obj = self.pool.get("report.test.group")
        params = [('name', 'like', '%post intervenció%')]
        rtg_ids = rtg_obj.search(cursor, uid, params)
        exe_info = rtg_obj.execute_tests(cursor, uid, rtg_ids, context)
        acc_info = rtg_obj.accept_tests(cursor, uid, rtg_ids, context)
        results = rtg_obj.get_active_results(cursor, uid, rtg_ids, context)
        results = list(set(results))
        error = len(results) != 1 or results[0] != 'equals'

        return error, exe_info, acc_info, rtg_ids

    def _cronjob_automation_mail_text(self, cursor, uid, data=None, context=None):
        if not data:
            data = {}
        if not context:
            context = {}

        subject = _(u"Resultat report tester automàtic amb ERROR")
        error, exe_info, acc_info, g_ids = self.automation(cursor, uid, context)
        emails_to = data.get("emails_to", "").split(",")
        emails = []
        for email_to in emails_to:
            if email_to:
                emails.append(email_to.strip())
        emails_to = emails

        if emails_to and error:
            user_obj = self.pool.get("res.users")
            email_from = user_obj.browse(cursor, uid, uid).address_id.email
            msg = u"Ids de grups {}\n".format(g_ids) + u"\n" + exe_info + u"\n" + acc_info
            email_send(email_from, emails_to, subject, msg)

        return not error


ReportTesterAutomation()
