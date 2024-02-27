# -*- coding: utf-8 -*-

from osv import osv
from ast import literal_eval
from oorq.decorators import job
from tools import config


class WizardPayInvoice(osv.osv_memory):

    _name = "facturacio.pay.invoice"
    _inherit = "facturacio.pay.invoice"

    def action_pay_and_reconcile(self, cursor, uid, ids, context=None):
        """Enviament d'un avís en donar per pagades factures amb un estat pendent concret"""
        if not context:
            context = {}

        if isinstance(ids, list) or isinstance(ids, tuple):
            ids = ids[0]

        ir_md_obj = self.pool.get("ir.model.data")
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        fact_id = context.get("active_id", False)
        factura = fact_obj.browse(cursor, uid, fact_id)
        tpv_journal = ir_md_obj.get_object_reference(
            cursor, uid, "som_account_invoice_pending", "tpv_journal"
        )[1]
        wiz = self.browse(cursor, uid, ids)

        cfg_obj = self.pool.get("res.config")
        pay_alert_conf = cfg_obj.get(cursor, uid, "pay_alert_pending_states_som", "[]")

        if (
            factura.pending_state.id in literal_eval(pay_alert_conf)
            and wiz.journal_id.id == tpv_journal
        ):
            self.mail_avis_cobraments(cursor, uid, ids, [fact_id], context)

        super(WizardPayInvoice, self).action_pay_and_reconcile(cursor, uid, ids, context)

        wiz = self.browse(cursor, uid, ids)
        old_comment = factura.comment if factura.comment else ""
        new_comment = wiz.comment or "" + "\n"
        fact_obj.write(cursor, uid, fact_id, {"comment": new_comment + old_comment})

    def mail_avis_cobraments(self, cursor, uid, ids, fact_ids, context=None):
        """Enviament individual"""
        ir_mod_dat = self.pool.get("ir.model.data")

        tmpl = ir_mod_dat._get_obj(
            cursor, uid, "som_account_invoice_pending", "tpv_pay_alert_template_som"
        )
        ctx = context.copy()

        ctx.update(
            {
                "state": "single",
                "priority": "0",
                "from": tmpl.enforce_from_account.id,
                "template_id": tmpl.id,
                "src_model": "giscedata.facturacio.factura",
                "type": "out_invoice",
            }
        )

        for fact_id in fact_ids:
            ctx.update(
                {
                    "src_rec_ids": [fact_id],
                    "active_ids": [fact_id],
                }
            )
            self.action_mail_avis_cobraments_async(cursor, uid, ids, ctx)

    def action_mail_avis_cobraments(self, cursor, uid, ids, context=None):
        email_wizard_obj = self.pool.get("poweremail.send.wizard")

        wiz_vals = {
            "state": context["state"],
            "priority": context["priority"],
            "from": context["from"],
        }
        pe_wiz = email_wizard_obj.create(cursor, uid, wiz_vals, context=context)
        return email_wizard_obj.send_mail(cursor, uid, [pe_wiz], context=context)

    @job(queue=config.get("poweremail_render_queue", "poweremail"))
    def action_mail_avis_cobraments_async(self, cursor, uid, id, context=None):
        self.action_mail_avis_cobraments(cursor, uid, id, context)


WizardPayInvoice()
