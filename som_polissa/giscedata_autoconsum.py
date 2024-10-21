# -*- coding: utf-8 -*-
from osv import osv, fields


class GiscedataAutoconsumGenerador(osv.osv):
    """Model de generador d'autoconsum."""

    _name = 'giscedata.autoconsum.generador'
    _inherit = 'giscedata.autoconsum.generador'

    _columns = {
        'emmagatzematge': fields.boolean('Te emmagatzematge'),
        'potencia_sortida': fields.float(u'Potència de sortida (KW)'),
        'energia_acumulable': fields.float(u'Energía acumulable'),
    }

    _defaults = {
        'emmagatzematge': lambda *a: False,
        'potencia_sortida': lambda *a: 0.0,
        'energia_acumulable': lambda *a: 0.0,
    }


GiscedataAutoconsumGenerador()
