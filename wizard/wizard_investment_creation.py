# -*- coding: utf-8 -*-

from datetime import date

from osv import osv, fields
from tools.translate import _


class WizardInvestmentCreation(osv.osv):

    _name = 'wizard.generationkwh.investment.creation'

    def do_action(self, cursor, uid, ids, context=None):
        """ Do selected action"""
        if context is None:
            context = {}

        Investment = self.pool.get('generationkwh.investment')
        Member = self.pool.get('somenergia.soci')

        wiz = self.browse(cursor, uid, ids[0], context=context)
        result = 'testing'
        wiz.write({'info': result , 'state': 'done'}, context=context)

    def _default_info(self, cursor, uid, context=None):
        if context is None:
            context = {}
        return 'testing'

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': _default_info,
    }

WizardInvestmentCreation()
