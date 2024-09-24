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
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'bank_id': fields.many2one('res.partner.bank', 'Compte bancari'),
        'payment_order': fields.boolean('Remesa', help="Marcar si es vol crear \
                                        remesa de pagament"),
        'red_sara': fields.boolean('Red SARA', help="Marcar si es demanar carta de  \
                                   pagament al Registre General"),
        'active': fields.boolean('Active'),
        'payment': fields.selection([("quarter", "Trimestral"), ("year", "Anual")],
                                    "Periode de pagament"),
    }


SomMunicipalTaxesConfig()
