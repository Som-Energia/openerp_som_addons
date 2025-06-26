# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _
from tools import email_send
import traceback
from datetime import datetime, timedelta, date


class SomAutoreclamaF1cAutomation(osv.osv_memory):

    _name = "som.autoreclama.f1c.automation"

    def get_f1c_candidates_to_reclaim(self, cursor, uid, context=None):
        last_24_hours = datetime.now() - timedelta(hours=24)
        f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")
        f1_ids = f1_obj.search(cursor, uid, [
            ('data_carrega', '>=', last_24_hours.strftime("%Y-%m-%d")),
            ('type_factura', '=', 'C'),
            ('user_observations', 'not ilike', '%Generat cas atc r1 010 automàtic amb id%'),
        ])
        # remove the sent ones (comment)
        return f1_ids

    def reclaim_f1c(self, cursor, uid, f1_ids, context=None):
        atc_obj = self.pool.get("giscedata.atc")
        f1_obj = self.pool.get("giscedata.facturacio.importacio.linia")

        tag = u"Generat cas atc r1 010 automàtic amb id"
        today = date.today().strptime("%Y-%m-%d")

        ok_ids = []
        error_ids = []
        msg = u""
        for f1_id in f1_ids:
            try:
                atc_id = atc_obj.create_ATC_R1_010_from_f1_via_wizard(
                    cursor, uid, f1_id, context=context)

                data = f1_obj.read(
                    cursor, uid, f1_id, ["user_observations", "name"])
                observations = data["user_observations"] or u""
                f1_name = data["name"]
                line = u"{} {} {}".format(today, tag, atc_id)
                new_observations = u"{}\n{}".format(line, observations)
                f1_obj.write(cursor, uid, f1_id, {"user_observations": new_observations})
                msg += u"F1 {} ha generat cas ATC 010 amb id {}\n\n".format(f1_name, f1_id)
                ok_ids.append(atc_id)
            except Exception:
                msg += u"F1 {} no ha pogut generar cas ATC 010 per el motiu:\n".format(f1_name)
                msg += u"{}\n\n".format(traceback.format_exc())
                error_ids.append(f1_ids)

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
