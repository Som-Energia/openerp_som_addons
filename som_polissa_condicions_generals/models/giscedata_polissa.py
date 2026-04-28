# -*- coding: utf-8 -*-
from __future__ import absolute_import
from osv import osv


class GiscedataPolissa(osv.osv):
    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def get_simplified_taxes(self, cursor, uid, polissa_id, context=False):
        if context is None:
            context = {}

        polissa = self.browse(cursor, uid, polissa_id, context=context)

        fp_obj = self.pool.get('account.fiscal.position')
        atax_obj = self.pool.get('account.tax')
        conf_obj = self.pool.get('res.config')

        fiscal_position = polissa.fiscal_position_id
        if not fiscal_position:
            fiscal_position = polissa.titular.property_account_position

        iva_tax_id = int(conf_obj.get(cursor, uid, 'default_iva_21_tax_id'))
        iese_tax_id = int(conf_obj.get(cursor, uid, 'default_iese_tax_id'))

        iva_tax = atax_obj.browse(cursor, uid, iva_tax_id, context=context)
        iese_tax = atax_obj.browse(cursor, uid, iese_tax_id, context=context)

        mapped_tax_ids = fp_obj.map_tax(
            cursor, uid, fiscal_position, [iva_tax, iese_tax], context=context)
        tax_data = atax_obj.read(
            cursor, uid, mapped_tax_ids, ['name', 'amount'], context=context)

        simplified_taxes = {}
        for tax in tax_data:
            if 'IVA' in tax['name']:
                simplified_taxes['IVA'] = 0.1 if context.get('iva10') else tax['amount']
            elif 'IGIC' in tax['name']:
                simplified_taxes['IGIC'] = tax['amount']
            else:
                simplified_taxes['IE'] = tax['amount']

        return simplified_taxes


GiscedataPolissa()
