# -*- coding: utf-8 -*-
from osv import fields, osv


_tipus_tarifes_lead = [
    ('tarifa_existent', 'Tarifa existent (ATR o Fixa)'),
    ('tarifa_provisional', 'Tarifa ATR provisional'),
]

class GiscedataCrmLead(osv.OsvInherits):

    _inherit = "giscedata.crm.lead"

    def contract_pdf(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        context['lead'] = True

        return super(GiscedataCrmLead, self).contract_pdf(cursor, uid, ids, context=context)

    _columns = {
        'tipus_tarifa_lead': fields.selection(
            _tipus_tarifes_lead, 'Tipus de tarifa del contracte'
        ),
        'preu_fix_energia_p1': fields.float('Preu Fix Energia P1', digits=(16, 4)),
        'preu_fix_energia_p2': fields.float('Preu Fix Energia P2', digits=(16, 4)),
        'preu_fix_energia_p3': fields.float('Preu Fix Energia P3', digits=(16, 4)),
        'preu_fix_energia_p4': fields.float('Preu Fix Energia P4', digits=(16, 4)),
        'preu_fix_energia_p5': fields.float('Preu Fix Energia P5', digits=(16, 4)),
        'preu_fix_energia_p6': fields.float('Preu Fix Energia P6', digits=(16, 4)),
        'preu_fix_potencia_p1': fields.float('Preu Fix Potència P1', digits=(16, 4)),
        'preu_fix_potencia_p2': fields.float('Preu Fix Potència P2', digits=(16, 4)),
        'preu_fix_potencia_p3': fields.float('Preu Fix Potència P3', digits=(16, 4)),
        'preu_fix_potencia_p4': fields.float('Preu Fix Potència P4', digits=(16, 4)),
        'preu_fix_potencia_p5': fields.float('Preu Fix Potència P5', digits=(16, 4)),
        'preu_fix_potencia_p6': fields.float('Preu Fix Potència P6', digits=(16, 4)),
    }

    _defaults = {
        'tipus_tarifa_lead': lambda*a: 'tarifa_existent',
    }

GiscedataCrmLead()
