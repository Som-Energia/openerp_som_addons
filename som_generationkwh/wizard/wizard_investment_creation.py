# -*- coding: utf-8 -*-

from datetime import date,datetime,timedelta

from osv import osv, fields
from tools.translate import _


class WizardInvestmentCreation(osv.osv_memory):

    _name = 'wizard.generationkwh.investment.creation'

    def do_create(self, cursor, uid, ids, context=None):
        """ Do selected action"""
        if context is None:
            context = {}
        Investment = self.pool.get('generationkwh.investment')
        Emission = self.pool.get('generationkwh.emission')
        wiz = self.browse(cursor, uid, ids[0], context=context)

        partner_id = int(wiz.partner_id_alt.id)
        amount_in_e = float(wiz.amount_in_euros)
        ip = str(wiz.ip)
        iban = str(wiz.iban)
        emission_id = int(wiz.emission_id.id)
        investment_id = []
        creation_errors = ''

        start = datetime.now()

        try:
            emission_code = Emission.read(cursor, uid, emission_id, ['code'])['code']
            #Compatibility 'emissio_apo'
            investment_id = Investment.create_from_form(cursor, uid,
                   partner_id, wiz.order_date, amount_in_e, ip, iban, emission_code,
                context)
        except Exception as e:
            creation_errors = str(e)

        end = datetime.now()

        result = ""
        result += "Creació: \t\t{}\n".format(end - start)

        result += "\n"
        if investment_id:
            next_state = 'done'
            new_invest = Investment.read(cursor, uid, investment_id, ['name'])
            result += "Inversió creada amb nom: {} - id: {}\n".format(
                    new_invest['name'],
                    investment_id
                )
        else:
            next_state = 'init'
            result += "Error en creació:\t"+ creation_errors +"\n"

        result += "\n"
        result += "Dades d'entrada\n"
        result += "Partner_id : \t{}\n".format(partner_id)
        result += "Order date : \t{}\n".format(wiz.order_date)
        result += "Amount : \t\t{}\n".format(amount_in_e)
        result += "IP : \t\t\t\t{}\n".format(ip)
        result += "IBAN : \t\t\t{}\n".format(iban)
        result += "Emission : \t\t\t{}\n".format(emission_id)

        wiz.write({'info': result , 'state': next_state}, context=context)

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
        'partner_id_alt': fields.many2one(
            'res.partner',
            'Titular',
            domain=[('category_id.name','=','Soci')],
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
        'emission_id': fields.many2one(
            'generationkwh.emission',
            'Emissió',
            domain=[],
            required=True,
            ),
    }

    _defaults = {
        'state': lambda *a: 'init',
        'info': lambda *a: '',
        'order_date': lambda *a: str(datetime.today()),
        'amount_in_euros': lambda *a: 0.0,
        'ip': lambda *a: "0.0.0.0",
        'iban': lambda *a: ""
    }

WizardInvestmentCreation()
