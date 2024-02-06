# -*- coding: utf-8 -*-
from osv import osv


class ProductPricelist(osv.osv):
    """Llistes de preus.
    """
    _name = 'product.pricelist'
    _inherit = 'product.pricelist'

    def get_atr_price(self, cursor, uid, ids, tipus, product_id, fiscal_position_id,
                      with_taxes=False, direccio_pagament=None, titular=None, context=None):
        afp_obj = self.pool.get('account.fiscal.position')
        fiscal_position = afp_obj.browse(cursor, uid, fiscal_position_id)
        return super(ProductPricelist, self).get_atr_price(
            cursor, uid, ids, tipus, product_id, fiscal_position, with_taxes, direccio_pagament,
            titular, context)
