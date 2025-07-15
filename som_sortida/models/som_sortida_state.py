# -*- coding: utf-8 -*-
from osv import osv


class SomSortidaState(osv.osv):
    _name = "som.sortida.state"
    _inherit = "account.invoice.pending.state"
    _description = "Estats d'una pòlissa en el procés de sortida"


SomSortidaState()
