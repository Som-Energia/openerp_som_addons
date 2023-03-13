# -*- coding: utf-8 -*-
from osv import osv, fields


class GiscedataPolissa(osv.osv):
    """Pòlissa per afegir el camp teoric_maximum_consume_gc."""

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    _columns = {
        "teoric_maximum_consume_gc": fields.float(
            digits=(8, 2),
            string="Teoric maximum consume Grans Contractes",
            help=u"Màxim consum mensual teòric d'un contracte amb categoria Gran Consum associat a la validació SF03.",
        )
    }


GiscedataPolissa()


class GiscedataPolissaModcontractual(osv.osv):
    """Modificació Contractual d'una Pòlissa."""

    _name = "giscedata.polissa.modcontractual"
    _inherit = "giscedata.polissa.modcontractual"

    _columns = {
        "teoric_maximum_consume_gc": fields.float(
            digits=(8, 2), string="Teoric maximum consume Grans Contractes"
        )
    }


GiscedataPolissaModcontractual()
