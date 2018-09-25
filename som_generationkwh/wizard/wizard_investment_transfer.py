# -*- coding: utf-8 -*-
from datetime import date
from osv import osv, fields
from tools.translate import _
import pickle

class WizardInvestmentTransfer(osv.osv):

    _name = 'wizard.generationkwh.investment.transfer'

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
        'invoices': fields.text(
            'test',
        ),
        'partner_id_alt': fields.many2one(
            'res.partner',
            'Titular',
            domain=[('category_id','=',8)],
            required=True,
        ),
        'iban': fields.many2one(
            'res.partner.bank',
            'IBAN',
            required=True,
        ),        
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': lambda *a: 'Aquesta acció transferirà la inversió.\n'
                           'Condicions:\n'
                           '  - Les inversions han d"estar pagades \n'
    }

    def do_transfer(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        Investment = self.pool.get('generationkwh.investment')
        wiz = self.browse(cursor, uid, ids[0], context)
        investment_ids = context.get('active_ids', [])
        new_partner_id = int(wiz.partner_id_alt.id)
        iban = wiz.iban.iban
        order_date = date.today()

        new_investment_id = Investment.create_from_transfer(cursor, uid, investment_ids[0], new_partner_id, order_date, iban, context=None)
        old = investment.read(investment_ids[0],['name'])
        new = investment.read(new_investment_id,['name'])

        info = "RESULTAT: \n"
        info += "================\n"
        info += "Investment vell: %d" % old['name'] if old else "Error"
        info += "\nInvestment nou: %d" % new['name'] if new else "Error"
        wiz.write(dict(
            info= info,
            state = 'Done',
            ))

        return True


WizardInvestmentTransfer()
# vim: et ts=4 sw=4 
