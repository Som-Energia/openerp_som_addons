# -*- encoding: utf-8 -*-

from datetime import date
from osv import osv, fields
from tools.translate import _

class WizardContractSignSignaturit(osv.osv_memory):

    _name = 'wizard.generationkwh.sign.signaturit'

    def start_request(self, cursor, uid, ids, context=None):
        """ Do selected action"""
        if context is None:
            context = {}
        wiz = self.browse(cursor, uid, ids[0], context=context)
        #Buscar si totes estan pendents de notificar


        if False:
            #No notificaré cap:
            print("No notifico cap!")
            self.write(cursor, uid, ids, {
                'state': 'failed',
                'failed_records': "\n".join(['GWH0001', 'GWH0002', 'GWH0003', 'GWH0004'] * 3)
            })
        else:
            #Notificaré totes:
            print("Notifico totes!")
            self.write(cursor, uid, ids, {'state': 'done'})

    def _own_generationkwh_num(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}
        wiz = self.browse(cursor, uid, ids, context=context)
        return "\n".join(['GWH0001', 'GWH0002', 'GWH0003', 'GWH0004'] * 3)

    _columns = {
        'state': fields.char('State', size=16),
        'info': fields.text('Info'),
        'failed_records': fields.text()
    }
    _defaults = {
        'state': lambda *a: 'init',
        'info': _own_generationkwh_num,
    }

WizardContractSignSignaturit()