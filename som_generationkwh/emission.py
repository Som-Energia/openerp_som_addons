# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from tools import config
import netsvc


class GenerationkwhEmission(osv.osv):

    _name = 'generationkwh.emission'
    _order = 'name DESC'

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
            'Producte factura amortizació', required=True, help="Producte de la línia de l'amortització dins la factura de la inversió"),
        'irpf_product_id': fields.many2one('product.product',
            'Producte factura IRPF', required=True, help="Producte de la línia IRPF dins la factura de la inversió"),
        'investment_payment_mode_id': fields.many2one('payment.mode',
            'Mode pagament inversió', required=True),
        'amortization_payment_mode_id': fields.many2one('payment.mode',
            'Mode pagament amortització', required=True),
        'bridge_account_payments_id': fields.many2one('account.account',
            'Compte pont per conciliar moviments', required=True),

   }

    _defaults = {
        'state' : lambda *a: 'draft',
        'grace_period': lambda *a: 0,
        'expiration_years': lambda *a: 0,
    }

    def set_to_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state':'draft'})
        return True

    def action_open(self, cr, uid, ids, *args):
        self.write(cr,uid,ids,{'state': 'open',})
        return True

    def set_done(self, cr, uid, ids, *args):
        self.write(cr,uid,ids,{'state': 'done',})
        return True

    def cancel(self, cr, uid, ids, *args):
        self.write(cr,uid,ids,{'state': 'cancel',})
        return True

GenerationkwhEmission()

# vim: et ts=4 sw=4
