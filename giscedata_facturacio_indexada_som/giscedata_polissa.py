# -*- coding: utf-8 -*-
from osv import osv, fields


class GiscedataPolissa(osv.osv):
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    _columns = {
        'coeficient_h': fields.float(
            u'Coeficient H €/MWh',
            digits=(4, 2),
            readonly=True,
            states={
                'esborrany': [('readonly', False)],
                'validar': [('readonly', False), ('required', True)],
                'modcontractual': [('readonly', False), ('required', True)]
            }
        )
    }

    _defaults = {
        'coeficient_h': lambda *a: 0.0
    }


GiscedataPolissa()


class GiscedataPolissaModcontractual(osv.osv):
    _name = 'giscedata.polissa.modcontractual'
    _inherit = 'giscedata.polissa.modcontractual'

    _columns = {
        'coeficient_h': fields.float(
            u'Coeficient H €/MWh',
            digits=(4, 2)
        ),
    }

    _defaults = {
        'coeficient_h': lambda *a: 0.0
    }


GiscedataPolissaModcontractual()
