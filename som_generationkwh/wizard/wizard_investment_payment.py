# -*- coding: utf-8 -*-

from datetime import date

from osv import osv, fields
from tools.translate import _


class WizardInvestmentPayment(osv.osv):

    _name = 'wizard.generationkwh.investment.payment'

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': lambda *a: 'Hola Bon dia. Amb aquesta acció crearem les factures per les inversions inicials',
    }


    def do_payment(self, cursor,uid, ids, context=None):
        Investment = self.pool.get('generationkwh.investment')

        wiz = self.browse(cursor, uid, ids[0], context)
        inv_ids = context.get('active_ids', [])
        Investment.create_initial_invoice(cursor,uid, inv_ids[0])
        #TODO: open_invoice
        wiz.write(dict(
            info=
                "TODO: invoices draft \n"
                "TODO: invoices_opnened \n"
                "TODO: create payment_order \n"
                "TODO: invoices in payment_order \n"
                "TODO: log",
            state = 'Done',
            ))
        return True

WizardInvestmentPayment()