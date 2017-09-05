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
        wiz = self.browse(cursor, uid, ids[0], context=context)

        partner_id = int(wiz.partner_id_alt.id)
        amount_in_e = float(wiz.amount_in_euros)
        ip = str(wiz.ip)
        iban = str(wiz.iban)

        start = datetime.now()

        investment_id = Investment.create_from_form(cursor, uid,
            partner_id, wiz.order_date, amount_in_e, ip, iban,
            context)

        end = datetime.now()

        result = ""
        result += "Creació: \t\t{}\n".format(end - start)

        result += "\n"
        if investment_id:
            result += "Inversió creada\n"
        else:
            result += "Error en creació\n"

        result += "\n"
        result += "Dades d'entrada\n"
        result += "Partner_id : \t{}\n".format(partner_id)
        result += "Order date : \t{}\n".format(wiz.order_date)
        result += "Amount : \t\t{}\n".format(amount_in_e)
        result += "IP : \t\t\t\t{}\n".format(ip)
        result += "IBAN : \t\t\t{}\n".format(iban)

        wiz.write({'info': result , 'state': 'done'}, context=context)

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
        'partner_id_alt': fields.many2one(
            'res.partner',
            'Titular',
            domain=[('category_id','=',8)],
            required=True,
            ),
        'amount_in_euros': fields.float(
            'Quantitat aportada',
            required=True,
            ),
        'ip': fields.char("Ip d'origen",size=16,required=True),
        'iban': fields.char('Compte iban',size=35,required=True),
        'order_date': fields.date(
            'Data de comanda',
            required=True
        ),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': lambda *a: '',
        'order_date': lambda *a: str(datetime.today()+timedelta(days=6)),
        'amount_in_euros': lambda *a: 0.0,
        'ip': lambda *a: "0.0.0.0",
        'iban': lambda *a: ""
    }

WizardInvestmentCreation()
