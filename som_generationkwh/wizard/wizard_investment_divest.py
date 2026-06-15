# -*- coding: utf-8 -*-

from datetime import date
from osv import osv, fields
from tools.translate import _
import pickle

class WizardInvestmentDivest(osv.osv_memory):

    _name = 'wizard.generationkwh.investment.divest'

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
        'invoices': fields.text(
            'test',
        ),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': lambda *a: 'Aquesta acció crearà la factura de desinversió,'
                           'les obrirà i les posarà dintre de'
                           ' la remesa \n Condicions:\n'
                           '  - Les inversions han d"estar pagades des de fa X dies  \n'
                           '  - Han de tenir bank associat a la persona sòcia \n'
    }


    def do_payment(self, cursor,uid, ids, context=None):
        Investment = self.pool.get('generationkwh.investment')
        Invoice = self.pool.get('account.invoice')

        wiz = self.browse(cursor, uid, ids[0], context)
        investment_ids = context.get('active_ids', [])

        invoice_ids, errors = Investment.divest(cursor, uid, investment_ids)

        info = "RESULTAT: \n"
        info += "================\n"
        if not invoice_ids:
            info+= "No s'han generat factures\n"
        else:
            info += "\nFACTURES GENERADES: \n"
            for invoice_id in invoice_ids:
                invoice = Invoice.read(cursor, uid, invoice_id)
                info+= " - " + str(invoice['name']) + "\n"

        if errors:
            info +=  "\nERRORS DURANT EL PROCÉS: \n"
            for error in errors:
                info+= " -  " + str(error) + "\n"

        wiz.write(dict(
            info= info,
            state = 'Done',
            invoices = pickle.dumps(invoice_ids),
            ))
        return True

    def show_invoices(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context)
        invoice_ids = pickle.loads(wiz.invoices)
        return {
            'domain': "[('id','in', %s)]" % str(invoice_ids),
            'name': _('Factures generades'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window'
        }

    def show_payment_order(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context)
        invoice_ids = pickle.loads(wiz.invoices)

        AccountInvoice = self.pool.get('account.invoice')
        PaymentOrder = self.pool.get('payment.order')
        PaymentLine = self.pool.get('payment.line')

        payment_order_id = 0
        if invoice_ids:
            invoice = AccountInvoice.read(cursor, uid, invoice_ids[0])
            lines = PaymentLine.search(cursor, uid, [('communication','ilike',invoice['name'])])
            line = PaymentLine.read(cursor, uid, lines[0])
            payment_order_id = line['order_id'][0]

        return {
            'domain': "[('id','=', %s)]" % str(payment_order_id),
            'name': _('Ordre de pagament'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'payment.order',
            'type': 'ir.actions.act_window',
        }

WizardInvestmentDivest()
# vim: et ts=4 sw=4 
