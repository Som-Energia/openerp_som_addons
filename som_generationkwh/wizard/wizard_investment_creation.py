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

        action = wiz.action

    def _default_action(self, cursor, uid, context=None):
        """Gets wizard action from context"""



    def _default_info(self, cursor, uid, context=None):
        """Fills wizard info field depending on action/investments selected"""
        action = self._default_action(cursor, uid, context=context)

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
        'action': fields.selection([
            ('activate', 'Activa'),
            ('deactivate', 'Desactiva')
            ],
            string='Action'
        )
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': _default_info,
        'action': _default_action,
    }

WizardInvestmentCreation()
