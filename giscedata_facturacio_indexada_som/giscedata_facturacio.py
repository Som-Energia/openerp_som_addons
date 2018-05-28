# -*- coding: utf-8 -*-
from osv import osv
from .tarifes import TARIFFS_FACT


class GiscedataFacturacioFacturador(osv.osv):
    _name = 'giscedata.facturacio.facturador'
    _inherit = 'giscedata.facturacio.facturador'

    def get_tarifa_class(self, modcontractual):
        parent = super(GiscedataFacturacioFacturador, self).get_tarifa_class
        if modcontractual.mode_facturacio == 'index':
            return TARIFFS_FACT[modcontractual.tarifa.name]
        else:
            return parent(modcontractual)


GiscedataFacturacioFacturador()
