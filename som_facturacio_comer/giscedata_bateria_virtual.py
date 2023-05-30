# -*- coding: utf-8 -*-
"""Modificacions del model giscedata_facturacio_factura per SOMENERGIA.
"""

from osv import osv, fields
from tools.translate import _

STATES_GESTIO_ACUMULACIO = [
    ('estandard', _("Acumular segons saldo d'excedents")),
]

class GiscedataBateriaVirtualOrigen(osv.osv):
    _name = "giscedata.bateria.virtual.origen"
    _inherit = 'giscedata.bateria.virtual.origen'

    _columns = {
        'gestio_descomptes': fields.selection(STATES_GESTIO_ACUMULACIO, 'Gestió dels descomptes'),
        'percentatges_acumulacio': fields.one2many('giscedata.bateria.virtual.percentatges.acumulacio', 'origen_id', 'Percentatges acumulacio'),
    }

    _defaults = {
        'gestio_acumulacio': lambda *a: 'estandard',
    }


GiscedataBateriaVirtualOrigen()