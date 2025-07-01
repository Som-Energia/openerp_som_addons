# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _
from tools import email_send
import traceback
from datetime import datetime, timedelta


class SomAutoreclamaF1cAutomation(osv.osv_memory):

    _name = "som.autoreclama.f1c.automation"

    def get_f1c_candidates_to_reclaim(self, cursor, uid, context=None):
        if not context:
            context = {}
        hours_back = context.get('hours_back', 24)
        last_24_hours = datetime.now() - timedelta(hours=hours_back)
        f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")
        f1_ids = f1_obj.search(cursor, uid, [
            ('data_carrega', '>=', last_24_hours.strftime("%Y-%m-%d %H:%M:%S")),
            ('type_factura', '=', 'C'),
        ])

        return f1_ids

    def reclaim_f1c(self, cursor, uid, f1_ids, context=None):
        atc_obj = self.pool.get("giscedata.atc")
        f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")

        ok_ids = []
        error_ids = []
        msg = u""
        for f1_id in f1_ids:
            f1_name = f1_obj.read(cursor, uid, f1_id, ["name"])["name"]
            try:
                atc_id = atc_obj.create_ATC_R1_010_from_f1_via_wizard(
                    cursor, uid, f1_id, context=context)

                msg += u"F1 {} ha generat cas ATC 010 amb id {}\n\n".format(f1_name, atc_id)
                ok_ids.append(f1_id)
            except Exception as e:
                msg += u"F1 {} no ha pogut generar cas ATC 010 per el motiu:\n".format(f1_name)
                msg += u"  ERROR: {}\n".format(e.message)
                msg += u"{}\n\n".format(traceback.format_exc())
                error_ids.append(f1_id)

        summary = u"Sumari ATC 010 per F1 tipus C\n"
        summary += u"F1's tipus C amb ATC generat : .................... {}\n".format(len(ok_ids))
        summary += u"F1's tipus C que han donat error en generar ATC ....{}\n\n".format(
            len(error_ids))
        return ok_ids, error_ids, summary + msg

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
