# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _


class GiscedataFacturacioFacturador(osv.osv):
    """Sobreescrivim el mètode per facturar per incloure el donatiu"""

    _name = "giscedata.facturacio.facturador"
    _inherit = "giscedata.facturacio.facturador"

    def get_donatiu_product(self, cursor, uid, polissa_id, context=None):
        product_obj = self.pool.get("product.product")
        return product_obj.search(cursor, uid, [("default_code", "=", "DN01")])[0]

    def fact_via_lectures(self, cursor, uid, polissa_id, lot_id, context=None):
        """Sobreescrivim el mètode per incloure-hi la línia de factura
        rel·lacionada amb el donatiu si s'escau"""
        if not context:
            context = {}
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        polissa_obj = self.pool.get("giscedata.polissa")
        product_obj = self.pool.get("product.product")
        factures_creades = super(GiscedataFacturacioFacturador, self).fact_via_lectures(
            cursor, uid, polissa_id, lot_id, context
        )
        ctx = context.copy()

        factures_creades_modificables = []
        donatiu_pol = polissa_obj.read(cursor, uid, polissa_id, ["donatiu"], ctx)["donatiu"]
        if donatiu_pol:
            factures_creades_modificables = factures_creades

        if factures_creades_modificables:
            # identificar el producte donacions
            pdona_id = self.get_donatiu_product(cursor, uid, polissa_id, context)

            journal_codes = self.pool.get("res.config").get(
                cursor, uid, "som_invoice_bo_social_journal_codes", ["ENERGIA", "ENERGIA.R"]
            )
            for fact in fact_obj.browse(cursor, uid, factures_creades_modificables, context):
                if fact.journal_id.code in journal_codes:
                    if fact.polissa_id.donatiu:
                        # si la factura és del diari d'energia s'afegeix la línia de
                        # factura rel·lacionada amb el producte donatiu
                        ctx.update({"lang": fact.partner_id.lang})
                        p_br = product_obj.browse(cursor, uid, pdona_id, ctx)
                        # identificar la línia d'energia excloent el preu del MAG (RD 10/2022)
                        kwh = sum(
                            [
                                x.quantity if x.price_unit >= 0 else -x.quantity
                                for x in fact.linia_ids
                                if x.tipus == "energia" and x.product_id.code != "RMAG"
                            ]
                        )
                        vals = {
                            "data_desde": fact.data_inici,
                            "data_fins": fact.data_final,
                            "force_price": 0.01,
                            "uos_id": p_br.uom_id.id,
                            "quantity": kwh,
                            "multi": 1,
                            "product_id": pdona_id,
                            "tipus": "altres",
                            "name": p_br.description,
                        }
                        self.crear_linia(cursor, uid, fact.id, vals, ctx)

        return factures_creades


GiscedataFacturacioFacturador()


class GiscedataFacturacioFactura(osv.osv):
    """Modificació de la factura per poder-la afegir a una remesa"""

    _name = "giscedata.facturacio.factura"
    _inherit = "giscedata.facturacio.factura"

    _columns = {
        "visible_ov": fields.boolean(
            "Visible OV",
            help=_(u"Camp per indicar si la factura " u"sera visible a la Oficina Virtual"),
        )
    }

    _defaults = {"visible_ov": lambda *a: True}


GiscedataFacturacioFactura()
