# -*- coding: utf-8 -*-
from osv import osv
from som_extend_facturacio_comer.utils import get_gkwh_atr_price


class ProductPricelist(osv.osv):
    """Llistes de preus.
    """
    _name = 'product.pricelist'
    _inherit = 'product.pricelist'

    def get_gkwh_atr_price(cursor, uid, polissa, period_name, context, with_taxes=False):
        return get_gkwh_atr_price(cursor, uid, polissa, period_name, context, with_taxes)
