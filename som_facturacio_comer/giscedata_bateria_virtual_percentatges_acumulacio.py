# -*- coding: utf-8 -*-
"""
Nou modesl de dades per gestionar els percentatges d'acumulacio dels origens de bateria virtual per SOMENERGIA.
"""

from osv import osv, fields
from tools.translate import _


class GiscedataBateriaVirtualPercentatgesAcumulacio(osv.osv):

    _name = 'giscedata.bateria.virtual.percentatges.acumulacio'
    _description = _('Bateria virtual percentatge acumulable')

    _columns = {
        'percentatge': fields.integer('Pecentatge', help=_("Percentatge que acumula la bateria virtual")),
        'data_inici': fields.date(_("Data inici"), required=True),
        'data_fi': fields.date(_("Data fi")),
        'origen_id': fields.many2one('giscedata.bateria.virtual.origen', 'Origen', ondelete='cascade')
    }

    _defaults = {
        'percentatge': lambda *a: 100,
    }


GiscedataBateriaVirtualPercentatgesAcumulacio()