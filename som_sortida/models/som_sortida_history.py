# -*- coding: utf-8 -*-
from osv import osv, fields


class SomSortidaHistory(osv.osv):
    _name = "som.sortida.history"
    _inherit = "account.invoice.pending.history"
    _description = "Gestió de comunicacions de sortida a contractres sense sòcia"

    _columns = {
        "polissa_id": fields.many2one(
            "giscedata.polissa",
            "Pòlissa",
            required=True,
            help="Pòlissa de la qual s'ha fet la sortida",
        ),
        "pending_state_id": fields.many2one(
            "som.sortida.pending.state",
            "Estat de sortida pendent",
            help="Estat de sortida pendent assignat a la pòlissa",
        ),
    }


SomSortidaHistory()
