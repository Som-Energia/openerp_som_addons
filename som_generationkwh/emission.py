# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from tools import config
import netsvc
import generationkwh.investmentmodel as gkwh

def field_function(ff_func):
    def string_key(*args, **kwargs):
        res = ff_func(*args, **kwargs)
        ctx = kwargs.get('context', None)
        if ctx or ctx is None:
            return res

        if not ctx.get('xmlrpc', False):
            return res

        return dict([(str(key), value) for key, value in res.tuples])

    return string_key

class GenerationkwhEmission(osv.osv):

    _name = 'generationkwh.emission'
    _order = 'name DESC'

    def _ff_investments(self, cursor, uid, ids, field_names, args,
                        context=None):
        """ Check's if a member any gkwh investment"""
        invest_obj = self.pool.get('generationkwh.investment')

        if context is None:
            context = {}

        if not isinstance(ids, (tuple, list)):
            ids = [ids]

        init_dict = dict([(f, False) for f in field_names])
        res = {}.fromkeys(ids, {})
        for k in res.keys():
            res[k] = init_dict.copy()

        for emission_id in ids:
            investment_ids = invest_obj.search(cursor, uid, [('emission_id', '=', emission_id)])
            amount = 0
            for investment_id in investment_ids:
                investment_data = invest_obj.read(cursor, uid, investment_id, ['nshares', 'amortized_amount'])
                amount = amount + investment_data['nshares'] * gkwh.shareValue - investment_data['amortized_amount']
            res[emission_id] = {'current_total_amount_invested': int(amount)}

        return res

    '''
    Field inspired in generationkwh/investmentmodel.py
    That fields are not imported here:
        waitDaysBeforeDivest = 30 #no allow divest before 30 deays from payment_date
        irpfTaxValue = 0.19
        creditorCode = 'ES24000F55091367'
        shareValue = 100
    '''
    _columns = {
        'name': fields.char(
            "Nom", size=50, required=False, unique=True,
            help="Nom de la campanya d'inversió",),
        'code': fields.char(
            "Codi emissió", size=50, unique=True,
            help="Codi de la campanya d'inversió",),
        'start_date': fields.date(
            "Data d'inici", required=True,
            help="Quin dia es va començar l'emissió",),
        'amount_emission': fields.integer(
            "Import de l'emissió", required=False,
            help="Total de l'emissió en €. Si es deixa buit, és il.limitada",),
        'state': fields.selection([
            ('draft', 'Esborrany'), ('open', 'Oberta'),
            ('done', 'Realitzat'), ('cancel', 'Cancelat'),
            ], 'Emission State', readonly=True, help="Gives the state of the emission. Only emission in open state accepts new investments.", select=True),
        'type': fields.selection([
            ('genkwh', 'GenerationkWh'), ('tit', 'Títols'),
            ('apo', 'Aportacions'), ('other', 'Other'), #When not implementet yet
            ], 'Emission Type', help="Type of the emission.",
            select=True, required=False),
        'grace_period': fields.integer(
            "Periode de carència", required=False,
            help="Període de carència en anys, abans de fer la primera amortització",),
        'expiration_years': fields.integer(
            "Duració prèstec", required=False,
            help="Anys que dura el prèstec",),
        'waiting_days': fields.integer(
            "Dies per activació GKWH", required=False,
            help="Nombre de dies que passen perquè es comencin a repartir kwh",),
        'mandate_name': fields.char(
            "Nom de mandato", size=50, required=False,
            help="Motiu pel qual es podra fer servir el mandato",),
        'journal_id': fields.many2one('account.journal', "Diari",
            domain="[('type','=','cash')]", required=True,
             help="Diari on es comptabilitzaràn les inversions"),
        'investment_product_id': fields.many2one('product.product',
            'Producte factura inversió', required=True,
            help="Producte de la línia del capital dins la factura de la inversió"),
        'amortization_product_id': fields.many2one('product.product',
            'Producte factura amortizació', help="Producte de la línia de l'amortització dins la factura de la inversió"),
        'irpf_product_id': fields.many2one('product.product',
            'Producte factura IRPF', help="Producte de la línia IRPF dins la factura de la inversió"),
        'investment_payment_mode_id': fields.many2one('payment.mode',
            'Mode pagament inversió', required=True),
        'amortization_payment_mode_id': fields.many2one('payment.mode',
            'Mode pagament amortització' ),
        'bridge_account_payments_id': fields.many2one('account.account',
            'Compte pont per conciliar moviments'),
        'limited_period_end_date': fields.date(
            "Data final limit inversió per la campanya"),
        'limited_period_amount': fields.integer(
            "Import limit inversió per la campanya",
            help="Limit en € en aportacions per persona",),
        'end_date': fields.date(
            "Data final campanya",
            help="Dia en que es tanca la campanya. Si es deixa buit, és il·limitada",),
        'current_total_amount_invested': fields.function(
            _ff_investments, string='Total invertit',
            type='integer', method=True,
            multi='investments', store=True,
        )}

    _defaults = {
        'state' : lambda *a: 'draft',
        'grace_period': lambda *a: 0,
        'expiration_years': lambda *a: 0,
        'waiting_days': lambda *a: 0,
    }

    def set_to_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state':'draft'})
        return True

    def action_open(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'open',})
        return True

    def set_done(self, cr, uid, ids, *args):
        self.write(cr,uid,ids,{'state': 'done',})
        return True

    def cancel(self, cr, uid, ids, *args):
        self.write(cr,uid,ids,{'state': 'cancel',})
        return True

    def current_interest(self, cr, uid):
        cfg_obj = self.pool.get('res.config')
        current_interest = float(
            cfg_obj.get(cr, uid, 'som_aportacions_interest', '0')
        )
        return current_interest

GenerationkwhEmission()

# vim: et ts=4 sw=4
