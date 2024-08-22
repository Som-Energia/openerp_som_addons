# -*- coding: utf-8 -*-
from osv import osv, fields


class SomMunicipalTaxesPayment(osv.osv):
    _name = 'som.municipal.taxes.payment'

    _columns = {
        'config_id': fields.many2one('som.municipal.taxes.config', 'Municipi', required=True),

        'date_start': fields.date("Data inici"),
        'date_end': fields.date("Data final"),
        'quarter': fields.selection([("primer", "primer"), ("segon", "segon"), ("tercer", "tercer"),
                                     ("quart", "quart")], "trimestre"),
        'year': fields.integer("Any"),
        'amount': fields.float("Import"),
        'state': fields.selection([("esborrany", "esborrany"), ("pagat", "pagat"),
                                   ("erroni", "erroni")], "tipus"),
    }


SomMunicipalTaxesPayment()
