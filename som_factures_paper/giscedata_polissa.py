# -*- coding: utf-8 -*-
from osv import osv, fields

class GiscedataPolissa(osv.osv):
    """Pòlissa per afegir els camps de necessita rebut amb la factura en paper i observacions.
    """
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'


    _columns = {
        'postal_rebut': fields.boolean(string=u"Adjuntar rebut C. postal"),
        'postal_observacions': fields.char(string=u"Observacions C. postal", size=170)
    }

    _defaults = {
        'postal_rebut': lambda *a: False
    }

GiscedataPolissa()

