# -*- coding: utf-8 -*-
from osv import osv, fields
from osv.osv import except_osv

import datetime

class GiscedataPolissa(osv.osv):
    """Pòlissa per afegir el camp teoric_maximum_consume_GC.
    """
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    _columns = {
        'teoric_maximum_consume_GC': fields.float(
            digits=(8,2),
            string='Teoric maximum consume Grans Contractes',
            help=u"Maximum consum teoric d'un contracte d'autoconsum associat a una validació.")
    }

GiscedataPolissa()

class GiscedataPolissaModcontractual(osv.osv):
    """Modificació Contractual d'una Pòlissa."""
    _name = 'giscedata.polissa.modcontractual'
    _inherit = 'giscedata.polissa.modcontractual'

    _columns = {
        'teoric_maximum_consume_GC': fields.float(digits=(8,2), string='Teoric maximum consume Grans Contractes')
    }


GiscedataPolissaModcontractual()