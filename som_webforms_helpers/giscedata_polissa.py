# -*- coding: utf-8 -*-

from osv import osv, fields
from giscedata_facturacio.report.utils import get_atr_price, get_comming_atr_price


class GiscedataPolissa(osv.osv):

    _name = 'giscedata.polissa'
    _inherit = 'giscedata.polissa'

    def get_comming_atr_price(self, cursor, uid, ids, context):
        pol = self.browse(cursor, uid, ids)[0]
        return get_comming_atr_price(cursor, uid, pol, context)

    def get_atr_price(self, cursor, uid, ids, pname, tipus, context, with_taxes=False):
        pol = self.browse(cursor, uid, ids)[0]
        return get_atr_price(cursor, uid, pol, pname, tipus, context, with_taxes)

GiscedataPolissa()
