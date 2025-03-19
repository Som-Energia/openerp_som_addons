# -*- coding: utf-8 -*-

from osv import osv


class GiscedataFacturacioFacturadorEnergetica(osv.osv):
    """Sobreescrivim el mètode per buscar el donatiu (per si és Energética)"""

    _name = "giscedata.facturacio.facturador"
    _inherit = "giscedata.facturacio.facturador"

    def get_donatiu_product(self, cursor, uid, polissa_id, context=None):
        product_obj = self.pool.get("product.product")
        polissa_obj = self.pool.get("giscedata.polissa")

        if polissa_obj.is_energetica(cursor, uid, polissa_id, context=context):
            return product_obj.search(cursor, uid, [("default_code", "=", "DN02")])[0]
        else:
            return super(GiscedataFacturacioFacturadorEnergetica, self).get_donatiu_product(
                cursor, uid, polissa_id, context=context
            )


GiscedataFacturacioFacturadorEnergetica()
