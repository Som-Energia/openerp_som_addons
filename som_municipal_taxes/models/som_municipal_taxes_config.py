# -*- coding: utf-8 -*-
from osv import osv, fields


class SomMunicipalTaxesConfig(osv.osv):
    _name = 'som.municipal.taxes.config'

    def on_change_parnter_get_bank(self, cr, uid, ids, partner_id, context=None):
        partner_obj = self.pool.get('res.partner')
        bank_id = partner_obj.get_default_bank(cr, uid, partner_id)
        return {'value': {'bank_id': bank_id}}

    _columns = {
        'name': fields.char("Nom", size=128),
        'municipi_id': fields.many2one('res.municipi', 'Municipi', required=True),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'bank_id': fields.many2one('res.partner.bank', 'Compte bancari'),
        'type': fields.selection([("remesa", "remesa"), ("crawler", "crawler")],
                                 "Tipus de pagament"),
        'payment': fields.selection([("quarter", "Trimestral"), ("year", "Anual")],
                                    "Periode de pagament"),
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

    _defaults = {
        'type': lambda *_: 'remesa',
    }


SomMunicipalTaxesConfig()
