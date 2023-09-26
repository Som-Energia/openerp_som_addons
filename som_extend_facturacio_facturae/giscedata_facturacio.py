# -*- coding: utf-8 -*-

from __future__ import absolute_import

from osv import osv, fields
from tools.translate import _


class GiscedataFacturacioFactura(osv.osv):
    """Extend bill information available."""

    _name = "giscedata.facturacio.factura"
    _inherit = "giscedata.facturacio.factura"

    _columns = {"has_facturae": fields.boolean(_(u"Facturae"))}


GiscedataFacturacioFactura()
