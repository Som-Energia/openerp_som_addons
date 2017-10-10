# -*- coding: utf-8 -*-

import random
from osv import osv, fields
from tools.translate import _


class WizardInvestmentCancelOrResing(osv.osv):

    _name = 'wizard.generationkwh.investment.cancel.or.resign'
    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
    }

    def do_cancel_or_resign(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz = self.browse(cursor, uid, ids[0], context=context)
        result = ''
        investment_ids = context.get('active_ids', [])

        for counter,investment_id in enumerate(investment_ids):
            # TODO: 
            # cancel or resign this investment
            # detect action to be executed [cancel] [resign] [error-none]
            # execute The action : call to cancel or resign functions
            inv_names = self._get_investment_names(cursor,uid,investment_id,context)
            result += "{0}/{1} Acció {2} realitzada per ( {3} , {4} , {5} )\n".format(
                    counter+1,
                    len(investment_ids),
                    random.choice(['cancel·lació','renúncia']),
                    investment_id,
                    inv_names[0],
                    inv_names[1]
                )

        wiz.write({'info': result , 'state': 'done'}, context=context)

    def _get_investment_names(self, cursor, uid, investment_id, context=None):
        Investment = self.pool.get('generationkwh.investment')
        inv = Investment.read(cursor, uid, investment_id , [])
        customer_name = inv['member_id'][1]
        investment_name = inv['name']
        return (customer_name, investment_name)

    def _default_info(self, cursor, uid, context=None):
        if context is None:
            context = {}

        investment_ids = context.get('active_ids', [])
        result = 'Inversion seleccionades per a cancel·lació o renúncia:\n\n'
        for counter,investment_id in enumerate(investment_ids):
            inv_names = self._get_investment_names(cursor,uid,investment_id,context)
            result += "({0}/{1}) inversió ( {2} , {3} , {4} ) realitzarà l'acció {5}\n".format(
                    counter+1,
                    len(investment_ids),
                    investment_id,
                    inv_names[0],
                    inv_names[1],
                    random.choice(['cancel·lació','renúncia','no cancelable']),
                )
        return result

    _defaults = {
        'state': lambda *a: 'init',
        'info': _default_info,
    }

WizardInvestmentCancelOrResing()
# vim: et ts=4 sw=4
