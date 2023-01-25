# -*- coding: utf-8 -*-
from osv import osv, fields

from giscedata_polissa.giscedata_polissa import TIPO_AUTOCONSUMO_SEL

class GiscedataAtc(osv.osv):

    _name = 'giscedata.atc'
    _inherit = 'giscedata.atc'


    _columns = {
        'tarifa': fields.related('polissa_id', 'llista_preu', 'name',
                                type='char', string='tarifa Comercialitzadora', readonly=True),
        'tipus_autoconsum': fields.related('polissa_id', 'tipus_autoconsum',  type='selection',
                               selection=TIPO_AUTOCONSUMO_SEL, string='tipus autoconsum', readonly=True),
        'te_generation': fields.related('polissa_id', 'te_assignacio_gkwh', type='boolean', string='te generation', readonly=True),
        'pending_state': fields.related('polissa_id', 'pending_state', type='char', string='pending state', readonly=True),
        'polissa_active': fields.related('polissa_id', 'active', type='boolean',  string='polissa activa', readonly=True),
    }

GiscedataAtc()