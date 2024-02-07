# -*- coding: utf-8 -*-
from osv import osv
from giscedata_facturacio.report.utils import get_atr_price


class ProductPricelist(osv.osv):
    """Llistes de preus.
    """
    _name = 'product.pricelist'
    _inherit = 'product.pricelist'

    def get_atr_price_from_pricelist(
            self, cursor, uid, ids, tipus, product_id, fiscal_position_id, with_taxes=False,
            direccio_pagament=None, titular=None, context=None):
        afp_obj = self.pool.get('account.fiscal.position')
        fiscal_position = afp_obj.browse(cursor, uid, fiscal_position_id)
        return super(ProductPricelist, self).get_atr_price(
            cursor, uid, ids, tipus, product_id, fiscal_position, with_taxes, direccio_pagament,
            titular, context)

    def get_atr_price_from_report(
            self, cursor, uid, polissa, period_name, tipus, context, with_taxes=False):
        return get_atr_price(cursor, uid, polissa, period_name, tipus, context, with_taxes)


ProductPricelist()
