# -*- coding: utf-8 -*-
from osv import osv
from .utils import get_gkwh_atr_price


class ProductPricelist(osv.osv):
    """Llistes de preus.
    """
    _inherit = 'product.pricelist'

    def get_gkwh_atr_price(self, cursor, uid, polissa_id, period_name, context=None, with_taxes=False):
        pol_obj = self.pool.get('giscedata.polissa')
        polissa = pol_obj.browse(cursor, uid, polissa_id)
        return get_gkwh_atr_price(cursor, uid, polissa, period_name, context, with_taxes)

ProductPricelist()