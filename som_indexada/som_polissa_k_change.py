# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _

import logging

logger = logging.getLogger("openerp.{}".format(__name__))


class SomPolissaKChange(osv.osv):
    _name = "som.polissa.k.change"
    _description = _("Canvi de K de pòlissa")

    _columns = {
        "polissa_id": fields.many2one("giscedata.polissa", "Pòlissa"),
        "k_old": fields.float("K Antiga"),
        "k_new": fields.float("K Nova"),
    }

    _sql_constraints = [(
        "polissa_id_id_uniq",
        "unique(polissa_id)",
        "La pòlissa ha de ser única"
    )]


SomPolissaKChange()
