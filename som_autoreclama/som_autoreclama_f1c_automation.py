# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _
from tools import email_send


class SomAutoreclamaF1cAutomation(osv.osv_memory):

    _name = "som.autoreclama.f1c.automation"

    def get_f1c_candidates_to_reclaim(self, cursor, uid, context=None):
        # search the 24H ++ f1 c type
        # remove the sent ones (comment)
        return []

    def reclaim_f1c(self, cursor, uid, f1_ids, context=None):
        # for each one
        # call create_ATC_R1_010_from_f1_via_wizard
        # mark de f1 with the comment
        # build the message
        pass

    def automation(self, cursor, uid, context=None):
        f1_ids = self.get_f1c_candidates_to_reclaim(cursor, uid, context)
        _, _, msg = self.reclaim_f1c(cursor, uid, f1_ids, context=context)
        return msg

    def _cronjob_f1c_automation_mail_text(self, cursor, uid, data=None, context=None):
        if not data:
            data = {}
        if not context:
            context = {}

        subject = _(u"Resultat accions d'automatització de resposta als F1 tipus C")
        msg = self.automation(cursor, uid, context)
        emails_to = data.get("emails_to", "").split(",")
        emails = []
        for email_to in emails_to:
            if email_to:
                emails.append(email_to.strip())
        emails_to = emails

        if emails_to:
            user_obj = self.pool.get("res.users")
            email_from = user_obj.browse(cursor, uid, uid).address_id.email
            email_send(email_from, emails_to, subject, msg)

        return True


SomAutoreclamaF1cAutomation()
