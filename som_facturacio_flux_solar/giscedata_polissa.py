# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class GiscedataPolissa(osv.osv):

    _name = "giscedata.polissa"
    _inherit = 'giscedata.polissa'

    def get_auto_bat_name(self, cursor, uid, polissa_id, polissa_name, context=None):
        if context is None:
            context = {}
        return "FS" + str(polissa_name)


GiscedataPolissa()
