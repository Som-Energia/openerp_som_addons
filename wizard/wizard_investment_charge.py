# -*- coding: utf-8 -*-

from datetime import date

from osv import osv, fields
from tools.translate import _


class WizardInvestmentCharge(osv.osv):

    _name = 'wizard.generationkwh.investment.charge'

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': lambda *a: 'Hola Bon dia. Amb aquesta acció crearem les factures per les inversions inicials',
    }


    def do_charge(self, cursor,uid, ids, context=None):
        Investment = self.pool.get('generationkwh.investment')

        wiz = self.browse(cursor, uid, ids[0], context)
        inv_ids = context.get('active_ids', [])
        Investment.charge(cursor, uid, inv_ids, str(date.today()))
        wiz.write(dict(
            info="Data de compra i última data efectiva farcides\n Log completat",
            state = 'Done',
            ))
        return True

WizardInvestmentCharge()