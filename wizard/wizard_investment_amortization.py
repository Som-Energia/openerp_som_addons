# -*- coding: utf-8 -*-
from __future__ import division
from osv import osv, fields
from tools.translate import _
from datetime import datetime, timedelta
from calendar import isleap
import netsvc
from som_generationkwh import investment
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
        'date_end': lambda *a: str(datetime.today()+timedelta(days=6)),
    }

    def preview(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context)

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

        # TODO: delete this code when amortize_one gets producction ready
        amortized_invoice_ids, amortized_invoice_errors = Investment.amortize(cursor, uid, current_date, None, context)

        """
        # Check before uncomment!
        # TODO: use this code when amortize_one gets producction ready to control errors
        pending_amortizations = Investment.pending_amortizations(cursor, uid, current_date)
        for pending_amortization in pending_amortizations:
            try:
                amortized_invoice_id = Investment.amortize_one(cursor, uid, pending_amortization, context)
                amortized_invoice_ids.append(amortized_invoice_id)
            except Exception,e: # write specific exception catch code
                amortized_invoice_errors.append((pending_amortization,str(e)))
        """

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
