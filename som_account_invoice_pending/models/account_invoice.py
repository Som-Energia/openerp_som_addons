# -*- coding: utf-8 -*-
from osv import osv
from datetime import date
from oorq.decorators import job
from tools import config


class AccountInvoice(osv.osv):

    _name = "account.invoice"
    _inherit = "account.invoice"

    def set_pending(self, cursor, uid, ids, pending_id, context=None):
        res = super(AccountInvoice, self).set_pending(
            cursor, uid, ids, pending_id, context
        )

        ir_model_data = self.pool.get("ir.model.data")
        perdues_fact_df = ir_model_data.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "perdues_fact_default_pending_state"
        )[1]

        perdues_fact_bs = ir_model_data.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "perdues_fact_bo_social_pending_state"
        )[1]

        fue_bs = ir_model_data.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "fue_bo_social_pending_state"
        )[1]

        fue_df = ir_model_data.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "fue_default_pending_state"
        )[1]

        r1_bs = ir_model_data.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "reclamacio_en_curs_pending_state"
        )[1]

        r1_df = ir_model_data.get_object_reference(
            cursor, uid,
            "som_account_invoice_pending",
            "default_reclamacio_en_curs_pending_state"
        )[1]

        if pending_id in (perdues_fact_df, perdues_fact_bs, fue_bs, fue_df, r1_bs, r1_df):
            pt_obj = self.pool.get("payment.type")
            no_remesa_ids = pt_obj.search(
                cursor, uid,
                [('code', '=', 'NO_REMESA')],
                context=context
            )

            pending_type = {
                perdues_fact_df: u"Pèrdues",
                perdues_fact_bs: u"Pèrdues",
                fue_bs: u"FUE",
                fue_df: u"FUE",
                r1_bs: u"R1 Reclamació",
                r1_df: u"R1 Reclamació",
            }

            today_str = date.today().strftime("%Y-%m-%d")
            log_text = u"{} - Factura - {}".format(
                today_str,
                pending_type.get(pending_id, u"Error")
            )

            for invoice_id in ids:
                inv_data = self.read(
                    cursor, uid,
                    invoice_id, ['comment'],
                    context=context
                )

                if 'comment' in inv_data and inv_data['comment']:
                    comment = log_text + "\n" + inv_data['comment']
                else:
                    comment = log_text
                to_write = {
                    'comment': comment
                }
                if len(no_remesa_ids) == 1:
                    to_write['payment_type'] = no_remesa_ids[0]

                self.write(
                    cursor, uid,
                    invoice_id, to_write,
                    context=context
                )

        return res

    def mail_unpaid_apo_invoice(self, cursor, uid, ids, fact_ids, context=None):
        """Enviament individual"""
        ir_mod_dat = self.pool.get("ir.model.data")

        tmpl = ir_mod_dat._get_obj(
            cursor, uid, "som_account_invoice_pending", "email_interessos_aportacions_retornat"
        )
        ctx = context.copy()

        ctx.update(
            {
                "state": "single",
                "priority": "0",
                "from": tmpl.enforce_from_account.id,
                "template_id": tmpl.id,
                "src_model": "account.invoice",
                "type": "in_invoice",
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

    def action_mail_unpaid_apo_invoice(self, cursor, uid, ids, context=None):
        email_wizard_obj = self.pool.get("poweremail.send.wizard")

        wiz_vals = {
            "state": context["state"],
            "priority": context["priority"],
            "from": context["from"],
        }
        pe_wiz = email_wizard_obj.create(cursor, uid, wiz_vals, context=context)
        return email_wizard_obj.send_mail(cursor, uid, [pe_wiz], context=context)

    @job(queue=config.get("poweremail_render_queue", "poweremail"))
    def action_mail_unpaid_apo_invoice_async(self, cursor, uid, id, context=None):
        self.action_mail_unpaid_apo_invoice(cursor, uid, id, context)

    def unpay(self, cursor, uid, ids, amount, pay_account_id, period_id,
              pay_journal_id, context=None, name=''):

        res = super(AccountInvoice, self).unpay(
            cursor, uid, ids, amount, pay_account_id, period_id, pay_journal_id,
            context, name
        )
        invoice_id = ids[0] if ids else None
        if self.is_interest_payment(cursor, uid, invoice_id):
            # Send email notification for APO invoices
            self.mail_unpaid_apo_invoice(
                cursor, uid, ids, [invoice_id], context=context
            )

        return res


AccountInvoice()
