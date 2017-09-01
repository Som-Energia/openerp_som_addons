# -*- coding: utf-8 -*-

from datetime import date,datetime,timedelta

from osv import osv, fields
from tools.translate import _


class WizardInvestmentCreation(osv.osv):

    _name = 'wizard.generationkwh.investment.creation'

    def do_create(self, cursor, uid, ids, context=None):
        """ Do selected action"""
        if context is None:
            context = {}

        Investment = self.pool.get('generationkwh.investment')
        Member = self.pool.get('somenergia.soci')

        wiz = self.browse(cursor, uid, ids[0], context=context)

        result = wiz.ip

        wiz.write({'info': result , 'state': 'done'}, context=context)

    def _default_info(self, cursor, uid, context=None):
        if context is None:
            context = {}
        return 'testing'

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
        'amount_in_euros': fields.float('quantitat aportada'),
        'ip': fields.char("ip d'origen",size=16),
        'iban': fields.text('compte iban'),
        'order_date': fields.date(
            'data de comanda',
            required=True
        ),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': _default_info,
        'order_date': lambda *a: str(datetime.today()+timedelta(days=6)),
        'amount_in_euros': lambda *a: 0.0,
        'ip': lambda *a: "127.0.0.1",
        'iban': lambda *A: ""
    }

WizardInvestmentCreation()
