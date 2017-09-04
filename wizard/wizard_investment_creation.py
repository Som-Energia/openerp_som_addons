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

        partner_id  = int(wiz.partner_id)
        amount_in_e = float(wiz.amount_in_euros)
        ip = str(wiz.ip)
        iban = str(wiz.iban)

        Investment.create_from_form(cursor, uid,
            partner_id, wiz.order_date, amount_in_e, ip, iban,
            context)

        result = "Partner_id : \t{}\n".format(wiz.partner_id)
        result += "Order date: \t{}\n".format(wiz.order_date)
        result += "Amount: \t\t{}\n".format(wiz.amount_in_euros)
        result += "IP \t\t\t\t{}\n".format(wiz.ip)
        result += "IBAN : \t\t\t{}".format(wiz.iban)
        result += "Inversió creada"
        wiz.write({'info': result , 'state': 'done'}, context=context)

    def _default_info(self, cursor, uid, context=None):
        if context is None:
            context = {}
        return 'testing'

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
        'partner_id': fields.integer('partner_id'),
        'amount_in_euros': fields.float('quantitat aportada'),
        'ip': fields.char("ip d'origen",size=16),
        'iban': fields.char('compte iban',size=35),
        'order_date': fields.date(
            'data de comanda',
            required=True
        ),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': _default_info,
        'partner_id': lambda *a: 0,
        'order_date': lambda *a: str(datetime.today()+timedelta(days=6)),
        'amount_in_euros': lambda *a: 0.0,
        'ip': lambda *a: "127.0.0.1",
        'iban': lambda *a: ""
    }

WizardInvestmentCreation()
