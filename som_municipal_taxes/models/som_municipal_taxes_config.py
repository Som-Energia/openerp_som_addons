# -*- coding: utf-8 -*-
from osv import osv, fields


class SomMunicipalTaxesConfig(osv.osv):
    _name = 'som.municipal.taxes.config'

    _columns = {
        'name': fields.char("Nom", size=128),
        'municipi_id': fields.many2one('res.municipi', 'Municipi', required=True),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'type': fields.selection([("remesa", "remesa"), ("crawler", "crawler")], "tipus"),
        'url_portal': fields.char(
            "URL del portal",
            size=300,
            required=False,
            help="URL del portal web",
        ),
        'usuari': fields.char(
            "Usuari del portal",
            size=20,
            unique=True,
            help="Usuari del portal web",
        ),
        'password': fields.char(
            "Contrasenya del portal",
            size=30,
            help="Contrasenya del portal web",
        ),
    }


SomMunicipalTaxesConfig()
