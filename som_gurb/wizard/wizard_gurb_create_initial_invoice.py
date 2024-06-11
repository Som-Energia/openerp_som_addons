# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class WizardGurbCreateInitialInvoice(osv.osv_memory):

    _name = "wizard.gurb.create.initial.invoice"

    def _get_default_info(self, cursor, uid, context=None):
        if context is None:
            context = {}
        gurb_cups_ids = context.get("active_ids", [])
        return _(u"Es crearan {} factures d'inscripció.".format(len(gurb_cups_ids)))

    def get_created_invoices(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz_br = self.browse(cursor, uid, ids[0], context=context)

        invoice_ids = list(set(wiz_br.invoice_ids))

        res = {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': "[('id', 'in', %s)]" % invoice_ids,
        }

        return res

    def create_initial_invoices(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        gurb_cups_o = self.pool.get("som.gurb.cups")
        gurb_cups_ids = context.get("active_ids", [])
        wiz_br = self.browse(cursor, uid, ids[0], context=context)

        if not gurb_cups_ids:
            raise osv.except_osv("Error", _("No s'han seleccionat IDs"))

        invoice_ids, errors = gurb_cups_o.create_initial_invoices(cursor, uid, gurb_cups_ids)

        errors = "\n".join(errors) if errors else "No hi ha hagut errors."
        res = "S'han creat {} factures d'inscripció.".format(len(invoice_ids))

        wiz_br.write(
            {
                "state": "end",
                "info": res,
                "errors": errors,
                "invoice_ids": invoice_ids
            },
            context=context,
        )

    _columns = {
        "state": fields.selection([("init", "Init"), ("end", "End")], "State"),
        "invoice_ids": fields.text("IDs de les factures"),
        "info": fields.text("Informació"),
        "errors": fields.text("Errors"),
    }

    _defaults = {
        "state": lambda *a: "init",
        "info": _get_default_info,
    }


WizardGurbCreateInitialInvoice()
