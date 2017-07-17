# -*- coding: utf-8 -*-
from __future__ import division
from osv import osv, fields
from tools.translate import _
from datetime import datetime, timedelta
from calendar import isleap
import netsvc
from som_generationkwh import investment

class WizardInvestmentAmortization(osv.osv_memory):
    """Assistent per amortitzar la inversió.
    """
    _name = 'wizard.generationkwh.investment.amortization'
    _columns = {
        'date_end': fields.date(
            'Data final',
            required=True
        ),
        'err': fields.text(
            'Missatges d\'error',
            readonly=True,
        ),
        'output': fields.text(
            'Missatges d\'error',
            readonly=True,
        ),
        'state': fields.char(
            'Estat',
            50
        ),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'date_end': lambda *a: str(datetime.today()+timedelta(days=6)),
    }

    def preview(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context)
        context.update(pre_calc=True)
	
        Investment = self.pool.get('generationkwh.investment')
        current_date =  wiz.date_end
        pending_amortizations = Investment.pending_amortizations(cursor, uid, current_date)

        total = 0
        for p in pending_amortizations:
            total = total + p[4]
        
        wiz.write(dict(
            output=
                '- Amortitzacions pendents: {pending}\n\n'
                '- Import total: {pending_amount} €\n'
                .format(
                    pending = len(pending_amortizations),
                    pending_amount = total,

                ),
            state='pre_calc',
            err='soc un error'
            ))

    def generate(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context)
        #Invoice = self.pool.get('account.invoice')
        #invoice_ids = Invoice.search(cursor,uid,[
        #        ('name','like', "%AMOR%"),
        #        ])
        current_date = wiz.date_end
        Investment = self.pool.get('generationkwh.investment')
        invoice_ids = Investment.amortize(cursor, uid, current_date, context)

        return {
            'domain': "[('id','in', %s)]" % str(invoice_ids),
            'name': _('Factures generades'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window'
        }

WizardInvestmentAmortization()
# vim: et ts=4 sw=4 
