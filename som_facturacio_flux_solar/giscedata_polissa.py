# -*- coding: utf-8 -*-
from datetime import datetime

from osv import osv, fields


class GiscedataPolissa(osv.osv):
    """Pòlissa per afegir el camp de soci.
    """
    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def is_autoconsum_amb_excedents(cursor, uid, autoconsumo, context=None):
        if context is None:
            context = {}
        if autoconsumo in ('41', '42', '43'):
            return True
        else:
            return False


GiscedataPolissa()
