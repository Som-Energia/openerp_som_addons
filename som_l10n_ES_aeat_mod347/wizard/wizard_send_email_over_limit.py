# -*- coding: utf-8 -*-
from tools.translate import _
from osv import osv, fields


class SendEmailOverLimitWizard(osv.osv_memory):
    """Wizard per l'enviament del model 347"""

    _name = "send.email.over.limit.wizard"

    def _get_fiscal_year(self, cursor, uid, context={}):
        active_id = context.get("active_id")
        report_obj = self.pool.get("l10n.es.aeat.mod347.report")
        report = report_obj.browse(cursor, uid, active_id)
        return report.fiscalyear_id.name

    def _get_calculation_date(self, cursor, uid, context={}):
        active_id = context.get("active_id")
        report_obj = self.pool.get("l10n.es.aeat.mod347.report")
        report = report_obj.browse(cursor, uid, active_id)
        return report.calculation_date

    def send_email_to_partner_records(self, cursor, uid, ids, context=None):
        active_id = context.get("active_id")
        report_obj = self.pool.get("l10n.es.aeat.mod347.report")
        ret_value = report_obj.send_email_clients_import_over_limit(
            cursor, uid, [active_id], context
        )

        if ret_value:
            self.write(cursor, uid, ids, {"state": "ok"})
        else:
            self.write(cursor, uid, ids, {"state": "error"})

    _columns = {
        "state": fields.selection(
            [("init", "Init"), ("ok", "Ok"), ("error", "Error")],
            string="Progress State",
            translate=False,
        ),
        "fiscal_year": fields.char("Any fiscal", size=256, readonly=True),
        "calculation_date": fields.char("Data de càlcul", size=256, readonly=True),
    }

    _defaults = {
        "state": "init",
        "fiscal_year": _get_fiscal_year,
        "calculation_date": _get_calculation_date,
    }


SendEmailOverLimitWizard()
