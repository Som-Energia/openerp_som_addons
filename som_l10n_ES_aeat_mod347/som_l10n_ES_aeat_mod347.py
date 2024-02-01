# -*- coding: utf-8 -*-
import logging
from osv import fields, osv


class SomL10nEsAeatMod347Report(osv.osv):

    _name = "l10n.es.aeat.mod347.report"
    _inherit = "l10n.es.aeat.mod347.report"

    def send_email_clients_import_over_limit(self, cursor, uid, report_ids, context=None):
        """
        Send email to the clients from report l10n.es.aeat.mod347.report.
        This report includes clients and providers with an annual invoice total over an specific limit.
        """
        if len(report_ids) != 1:
            return False
        else:
            report_id = report_ids[0]

        report_obj = self.pool.get("l10n.es.aeat.mod347.report")
        partner_record_obj = self.pool.get("l10n.es.aeat.mod347.partner_record")

        if not context:
            context = {}

        report = report_obj.read(cursor, uid, report_id)
        partner_record_ids = partner_record_obj.search(
            cursor, uid, [("report_id", "=", report_id), ("operation_key", "=", "B")]
        )

        if not report or report.get("state") != "calculated" or len(partner_record_ids) == 0:
            return False

        email_params = SomL10nEsAeatMod347Helper.get_email_params(cursor, uid, self)

        for partner_record_id in partner_record_ids:
            SomL10nEsAeatMod347Helper.send_email(cursor, uid, self, partner_record_id, email_params)

        return True


SomL10nEsAeatMod347Report()


class SomL10nEsAeatMod347Partner(osv.osv):

    _name = "l10n.es.aeat.mod347.partner_record"
    _inherit = "l10n.es.aeat.mod347.partner_record"

    def send_annual_import_summary_email(self, cursor, uid, partner_record_ids, context=None):
        """
        Send email to the clients from partner_record l10n.es.aeat.mod347.partner_record.
        This report includes an annual invoice total over an specific limit.
        """
        if len(partner_record_ids) == 0:
            return False

        report_obj = self.pool.get("l10n.es.aeat.mod347.report")
        partner_record_obj = self.pool.get("l10n.es.aeat.mod347.partner_record")

        if not context:
            context = {}

        report_id = partner_record_obj.read(cursor, uid, partner_record_ids[0], ["report_id"]).get(
            "report_id", [None]
        )[0]
        report = report_obj.read(cursor, uid, report_id)
        if not report or report.get("state") != "calculated" or len(partner_record_ids) == 0:
            return False

        email_params = SomL10nEsAeatMod347Helper.get_email_params(cursor, uid, self)

        for partner_record_id in partner_record_ids:
            SomL10nEsAeatMod347Helper.send_email(cursor, uid, self, partner_record_id, email_params)

        return True


SomL10nEsAeatMod347Partner()


class SomL10nEsAeatMod347Helper:
    @staticmethod
    def get_email_params(cursor, uid, _object):
        """
        Return email from poweremail template
        """
        ir_model_data = _object.pool.get("ir.model.data")

        template_id = ir_model_data.get_object_reference(
            cursor, uid, "som_l10n_ES_aeat_mod347", "email_model_347_resum"
        )[1]

        email_from = ir_model_data.get_object_reference(
            cursor, uid, "base_extended_som", "info_energia_from_email"
        )[1]

        email_params = dict({"email_from": email_from, "template_id": template_id})

        return email_params

    @staticmethod
    def send_email(cursor, uid, _object, partner_record_id, email_params):
        logger = logging.getLogger("openerp.poweremail")

        try:
            wiz_send_obj = _object.pool.get("poweremail.send.wizard")
            ctx = {
                "active_ids": [partner_record_id],
                "active_id": partner_record_id,
                "template_id": email_params["template_id"],
                "src_model": "l10n.es.aeat.mod347.partner_record",
                "src_rec_ids": [partner_record_id],
                "from": email_params["email_from"],
                "state": "single",
                "priority": "0",
            }

            params = {"state": "single", "priority": "0", "from": ctx["from"]}
            wiz_id = wiz_send_obj.create(cursor, uid, params, ctx)
            return wiz_send_obj.send_mail(cursor, uid, [wiz_id], ctx)

        except Exception as e:
            logger.info(
                "ERROR sending email to invoice {partner_record_id}: {exc}".format(
                    partner_record_id=partner_record_id, exc=e
                )
            )
            return -1
