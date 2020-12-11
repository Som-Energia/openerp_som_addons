# -*- coding: utf-8 -*-
from osv import fields, osv
from .tarifes import TarifaPoolSOM

from tools.translate import _


class ProductPriceList(osv.osv):

    _name = "product.pricelist"
    _inherit = "product.pricelist"

    def _pricelist_type_get(self, cursor, uid, context={}):
        # Dummy TarifaPoolSOM to get available indexed formulas
        selection = []
        formulas = TarifaPoolSOM({}, {}, '2020-08-01', '2020-08-31').get_available_indexed_formulas()
        for key in formulas:
            selection.append((key, key))
        return selection

    _columns = {
        'indexed_formula': fields.selection(_pricelist_type_get, _('Fòrmula indexada'),
                                            required=True)
    }

    _defaults = {
        'indexed_formula': lambda *a: 'Indexada'
    }


ProductPriceList()
