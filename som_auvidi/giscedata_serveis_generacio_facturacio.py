# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _


class GiscedataServeiGeneracioFacturacio(osv.osv):
    _name = "giscedata.servei.generacio"
    _inherit = "giscedata.servei.generacio"

    def get_missatge_factura_duplicada(self, cursor, uid, context=None):
        return _("Aquest contracte té AUVI i seria millor fer la factura per lot, si no saps "
                 "com procedir busca ajuda. Si ja l'estas creant per lot vol dir que algu abans "
                 "l'ha creat per factura manual")


GiscedataServeiGeneracioFacturacio()
