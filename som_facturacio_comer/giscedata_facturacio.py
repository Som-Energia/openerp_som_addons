# -*- coding: utf-8 -*-
"""Modificacions del model giscedata_facturacio_factura per SOMENERGIA.
"""

from osv import osv
from datetime import datetime


class GiscedataFacturacioFacturador(osv.osv):
    """Classe per la factura de comercialitzadora."""

    _name = "giscedata.facturacio.facturador"
    _inherit = "giscedata.facturacio.facturador"

    def get_rd_17_2021_discount_product(self, cursor, uid, context=None):
        if context is None:
            context = {}

        imd_obj = self.pool.get("ir.model.data")
        energy_discount_product_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio_comer", "descompte_rd_17_2012"
        )[1]

        power_discount_product_id = imd_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio_comer", "descompte_rd_17_2012_potencia"
        )[1]

        return [energy_discount_product_id, power_discount_product_id]

    def get_discount_line_vals(self, cursor, uid, line, context=None):
        if context is None:
            context = {}

        product_obj = self.pool.get("product.product")
        product_ids = self.get_rd_17_2021_discount_product(cursor, uid, context=context)

        if line.tipus == "potencia":
            discount_product = product_obj.browse(cursor, uid, product_ids[1])
        else:
            discount_product = product_obj.browse(cursor, uid, product_ids[0])
        line_desc = "{} {} {}".format(
            discount_product.description, line.product_id.name, line.tipus
        )
        vals = {
            "data_desde": line.data_desde,
            "data_fins": line.data_fins,
            "uos_id": line.product_id.uom_id.id,
            "quantity": line.quantity,
            "multi": line.multi,
            "product_id": discount_product.id,
            "tipus": "altres",
            "name": line_desc,
        }

        return vals

    def crear_linia(self, cursor, uid, factura_id, vals, context=None):
        if not context:
            context = {}

        if factura_id or 'factura_id' in vals:
            factura_obj = self.pool.get('giscedata.facturacio.factura')
            factura_info = factura_obj.read(cursor, uid, factura_id, ['type', 'data_inici', 'data_final'])
            if factura_info and factura_info['type'] in ('out_invoice', 'out_refund') and factura_info.get("data_inici") and factura_info.get("data_final"):
                any_desde = datetime.strptime(factura_info['data_inici'], '%Y-%m-%d').year
                any_fins = datetime.strptime(factura_info['data_final'], '%Y-%m-%d').year
                if any_desde != any_fins:
                    context.update({'group_line': False})
        return super(GiscedataFacturacioFacturador, self).crear_linia(
            cursor, uid, factura_id, vals, context=context
        )


GiscedataFacturacioFacturador()
