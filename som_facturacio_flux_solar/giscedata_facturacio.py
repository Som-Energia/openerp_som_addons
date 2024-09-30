# -*- coding: utf-8 -*-
from osv import osv
from tools import decimal_round


class GiscedataFacturacioFacturador(osv.osv):
    _name = 'giscedata.facturacio.facturador'
    _inherit = 'giscedata.facturacio.facturador'

    def get_max_descompte_total_factura_sense_impostos(self, cursor, uid, factura_id, line_vals, context=None):
        if context is None:
            context = {}

        imd_obj = self.pool.get('ir.model.data')
        linia_obj = self.pool.get('giscedata.facturacio.factura.linia')

        # Es vol descomptar el total dels conceptes del sector electric
        max_descompte = 0

        # Producte de descompte de la bateria virtual
        product_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio_bateria_virtual",
            "bateria_virtual_product"
        )[1]

        # Si tenen bo social, les linies de bo social s'han de tenir en compte tot i ser de tipus "altres"
        # No es lo millor, pero per dependencies és infinitament més simple fer-ho aqui.
        tenen_bo_social = self.pool.get("ir.module.module").search(
            cursor, uid, [("state", "=", "installed"), ('name', '=', 'giscedata_repercusio_bo_social')],
            context=context
        )

        pbosocial_id = None
        if tenen_bo_social:
            pbosocial_id = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_repercusio_bo_social', 'bosocial_BS01'
            )[1]

        linies_utilitzades_ids = []
        for dict_vals in line_vals:
            if dict_vals['tipus'] not in ('altres', 'subtotal_xml', 'subtotal_xml_ren', 'subtotal_xml_oth'):
                max_descompte += dict_vals['price_subtotal']
                if 'id' in dict_vals:
                    linies_utilitzades_ids.append(dict_vals['id'])
            elif tenen_bo_social and dict_vals['product_id'] and pbosocial_id == dict_vals['product_id'][0]:
                max_descompte += dict_vals['price_subtotal']
                linies_utilitzades_ids.append(dict_vals['id'])
            elif product_id == dict_vals['product_id'][0]:
                max_descompte += dict_vals['price_subtotal']
                if 'id' in dict_vals:
                    linies_utilitzades_ids.append(dict_vals['id'])
            else:
                # Si tenen IESE, son del sector electric
                impostos_linia = dict_vals['invoice_line_tax_id']
                for impostos_linia_info in self.pool.get("account.tax").read(cursor, uid, impostos_linia, ['name'],
                                                                             context=context):
                    if 'especial' in impostos_linia_info['name'].lower():
                        max_descompte += dict_vals['price_subtotal']
                        if 'id' in dict_vals:
                            linies_utilitzades_ids.append(dict_vals['id'])

        iese_base = iese_quota = iese_amount = 0.0
        iva_base = iva_quota = iva_amount = 0.0
        for line in linia_obj.browse(cursor, uid, linies_utilitzades_ids, context={'prefetch': False}):
            if not line.name:  # Si el ID no existeix, al consultar el nom retornara False
                continue

            taxes_dict = {}
            for tax in line.invoice_line_id.invoice_line_tax_id:
                taxes_dict[tax.name] = tax.amount
            has_iese = [v for x, v  in taxes_dict.items() if 'especial' in x.lower()]
            other_taxes = [v for x, v  in taxes_dict.items() if 'especial' not in x.lower()]
            if has_iese:
                # We asume there's only one IESE and only one VAT
                iese_base += line.price_subtotal
                iese_quota = has_iese[0]
            if other_taxes:
                # We asume there's only one IESE and only one VAT
                iva_base += line.price_subtotal
                iva_quota = has_iese[0]

        if iese_base:
            iese_amount = iese_base * iese_quota
            iese_amount = decimal_round(iese_amount, '.01')
        if iva_base:
            iva_amount = (iva_base + iese_amount) * iva_quota
            iva_amount = decimal_round(iva_amount, '.01')

        max_descompte += iese_amount + iva_amount

        return linies_utilitzades_ids, max_descompte

GiscedataFacturacioFacturador()
