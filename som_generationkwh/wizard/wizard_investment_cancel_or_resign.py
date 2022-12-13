# -*- coding: utf-8 -*-

import random
from osv import osv, fields
from tools.translate import _
import pickle

class WizardInvestmentCancelOrResing(osv.osv_memory):

    _name = 'wizard.generationkwh.investment.cancel.or.resign'
    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
        'invoices':fields.text('test'),
    }

    def do_cancel_or_resign(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz = self.browse(cursor, uid, ids[0], context=context)
        result = ''
        investment_ids = context.get('active_ids', [])
        Investment = self.pool.get('generationkwh.investment')

        all_invoices = []
        for counter,investment_id in enumerate(investment_ids):

            inv_data = self._get_investment_data(cursor,uid,investment_id,context)
            if inv_data[2]: #draft
                try:
                    Investment.cancel(cursor, uid, [investment_id], context)
                    action = "ha estat cancel·lada"
                except Exception as e:
                    action = "ha generat error al cancelar: " + str(e)
            else:
                try:
                    resign_invoices, errors = Investment.resign(cursor, uid,
                                                                [investment_id],
                                                                context)
                    action = "ha estat renunciada"
                    all_invoices.extend(resign_invoices)
                    if len(resign_invoices) > 0:
                        action += "\n\t - S'han donat per pagada la factura "
                        action += "{0} i s'ha creat la factura de renúncia {1}".format(
                            resign_invoices[0],
                            resign_invoices[1]
                            )
                    if len(errors) > 0:
                        action += "\n\t - S'han generat {0} errors de factura:".format(
                            len(errors))
                        for error in errors:
                            action += "\n\t\t · {0}".format(error)
                except Exception as e:
                    action = "ha generat error al renunciar: " + str(e)

            result += "{0}/{1} inversió ( {2} , {3} , {4} ) {5}\n".format(
                counter+1,
                len(investment_ids),
                investment_id,
                inv_data[0],
                inv_data[1],
                action
            )
        wiz.write({ 'info': result,
                    'state': 'done',
                    'invoices' : pickle.dumps(all_invoices)
                  }, context=context)

    def close_and_show(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context)
        invoices = pickle.loads(wiz.invoices)
        return {
            'domain': "[('id','in', %s)]" % str(invoices),
            'name': _('Factures generades'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window'
        }

    def _get_investment_data(self, cursor, uid, investment_id, context=None):
        Investment = self.pool.get('generationkwh.investment')
        inv = Investment.read(cursor, uid, investment_id , [])
        customer_name = inv['member_id'][1]
        investment_name = inv['name']
        investment_draft = inv['draft']
        return (customer_name, investment_name, investment_draft)

    def _default_info(self, cursor, uid, context=None):
        if context is None:
            context = {}

        investment_ids = context.get('active_ids', [])
        result = 'Inversion seleccionades per a cancel·lació o renúncia:\n\n'
        for counter,investment_id in enumerate(investment_ids):
            inv_data = self._get_investment_data(cursor,uid,investment_id,context)
            result += "({0}/{1}) inversió ( {2} , {3} , {4} ) realitzarà l'acció {5}\n".format(
                    counter+1,
                    len(investment_ids),
                    investment_id,
                    inv_data[0],
                    inv_data[1],
                    'cancel·lació' if inv_data[2] else 'renúncia',
                )
        return result

    _defaults = {
        'state': lambda *a: 'init',
        'info': _default_info,
    }

WizardInvestmentCancelOrResing()
# vim: et ts=4 sw=4
