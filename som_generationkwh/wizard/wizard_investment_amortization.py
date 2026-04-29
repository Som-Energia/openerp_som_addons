# -*- coding: utf-8 -*-
from __future__ import division
from datetime import date, datetime, timedelta
from osv import osv, fields
from tools.translate import _
import netsvc
from som_generationkwh import investment
from generationkwh.isodates import isodate
import pickle

class WizardInvestmentAmortization(osv.osv_memory):
    """Assistent per amortitzar la inversió.
    """

    _name = 'wizard.generationkwh.investment.amortization'

    _columns = {
        'date_end': fields.date(
            'Data final',
            required=True
        ),
        'errors': fields.text(
            'Missatges d\'error',
            readonly=True,
        ),
        'output': fields.text(
            'Missatges d\'error',
            readonly=True,
        ),
        'results':fields.text(
            'resultats',
            readonly=True,
        ),
        'validation':fields.text(
            '',
            readonly=True,
        ),
        'state': fields.char(
            'Estat',
            50
        ),
        'amortizeds':fields.text(
            'test',
        ),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'date_end': lambda *a: str(datetime.today()),
    }

    def preview(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context)
        Investment = self.pool.get('generationkwh.investment')
        current_date =  wiz.date_end
        investment_ids = context.get('active_ids', [])
        if context.get('search_all'):
            investment_ids = Investment.search(cursor, uid, [('active', '=', True),('emission_id.type','=','genkwh')])

        limit_date = date.today() + timedelta(days=31)
        if isodate(current_date) > limit_date:
            wiz.write(dict(
                validation=
                    'Data no permesa, ha de ser inferior a {limit} per poder amortitzar.\n'
                    .format(
                        limit = limit_date,
                    ),
                state='init',
                ))
        else:
            nAmortizations, totalAmount = Investment.pending_amortization_summary(cursor, uid, current_date, investment_ids)

            wiz.write(dict(
                output=
                    '- Amortitzacions pendents: {pending}\n\n'
                    '- Import total: {pending_amount} €\n'
                    .format(
                        pending = nAmortizations,
                        pending_amount = totalAmount,
                    ),
                state='pre_calc',
                ))

    def generate(self, cursor, uid, ids, context=None):
    
        def generate_error_string(errors):
            print errors
            if not errors:
                return ""
            result = "Les següents {} inversions no s'han pogut amortitzar:\n\n".format(len(errors))
            for error in errors:
                result += "- "+str(error)
            return result

        wiz = self.browse(cursor, uid, ids[0], context)
        current_date = wiz.date_end

        Investment = self.pool.get('generationkwh.investment')

        amortized_invoice_ids = []
        amortized_invoice_errors = []
        investment_ids = context.get('active_ids', [])
        if context.get('search_all'):
            investment_ids = Investment.search(cursor, uid, [('active', '=', True),('emission_id.type','=','genkwh')])

        amortized_invoice_ids, amortized_invoice_errors = Investment.amortize(cursor, uid, current_date, investment_ids, context)

        wiz.write(dict(
            results= "{} inversions amortitzades.\n".format(len(amortized_invoice_ids)),
            errors=generate_error_string(amortized_invoice_errors),
            amortizeds = pickle.dumps(amortized_invoice_ids),
            state='close',
            ))

    def close_and_show(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context)
        amortized_ids = pickle.loads(wiz.amortizeds)
        return {
            'domain': "[('id','in', %s)]" % str(amortized_ids),
            'name': _('Factures generades'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window'
        }

    def show_payment_order(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context)
        amortized_ids = pickle.loads(wiz.amortizeds)

        AccountInvoice = self.pool.get('account.invoice')
        PaymentOrder = self.pool.get('payment.order')
        PaymentLine = self.pool.get('payment.line')

        payment_order_id = 0
        if amortized_ids:
            invoice = AccountInvoice.read(cursor, uid, amortized_ids[0])
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

WizardInvestmentAmortization()
# vim: et ts=4 sw=4 
