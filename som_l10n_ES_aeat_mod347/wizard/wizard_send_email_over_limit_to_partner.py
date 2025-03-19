# -*- coding: utf-8 -*-
from osv import osv, fields


class SendEmailOverLimitWizard(osv.osv_memory):
    """Wizard per l'enviament del model 347"""

    _name = "send.email.over.limit.partner.wizard"

    def _get_fiscal_year(self, cursor, uid, context={}):
        active_ids = context.get("active_ids")
        active_id = active_ids[0]
        partner_record_obj = self.pool.get("l10n.es.aeat.mod347.partner_record")
        partner_record = partner_record_obj.browse(cursor, uid, active_id)
        return partner_record.report_id.fiscalyear_id.name

    def _get_calculation_date(self, cursor, uid, context={}):
        active_ids = context.get("active_ids")
        active_id = active_ids[0]
        partner_record_obj = self.pool.get("l10n.es.aeat.mod347.partner_record")
        partner_record = partner_record_obj.browse(cursor, uid, active_id)
        return partner_record.report_id.calculation_date

    def _get_partner_list(self, cursor, uid, context={}):
        active_ids = context.get("active_ids")
        partner_record_obj = self.pool.get("l10n.es.aeat.mod347.partner_record")
        res_partner_obj = self.pool.get("res.partner")
        partner_record_list = []
        for id in active_ids:
            partner = partner_record_obj.read(cursor, uid, id, ["partner_vat", "partner_id"])
            NIF = partner["partner_vat"]
            partner_id = partner["partner_id"]
            name = res_partner_obj.read(cursor, uid, partner_id[0], ["name"])["name"]
            partner_record_list.append(NIF + " - " + name)
        return "\n".join([partner for partner in partner_record_list])  # noqa: F812

    def send_email_to_partner_records(self, cursor, uid, ids, context=None):
        active_ids = context.get("active_ids")
        partner_record_obj = self.pool.get("l10n.es.aeat.mod347.partner_record")
        ret_value = partner_record_obj.send_annual_import_summary_email(
            cursor, uid, active_ids, context
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
        "info": fields.text("Info"),
    }

    _defaults = {
        "state": "init",
        "fiscal_year": _get_fiscal_year,
        "calculation_date": _get_calculation_date,
        "info": _get_partner_list,
    }


SendEmailOverLimitWizard()
