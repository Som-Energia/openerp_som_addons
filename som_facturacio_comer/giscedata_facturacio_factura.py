# -*- coding: utf-8 -*-

from osv import osv


class GiscedataFacturacioFactura(osv.osv):
    _inherit = "giscedata.facturacio.factura"

    def generate_unpayment_expenses(self, cursor, uid, fact_ids, context=None):
        """Comprovem que no té pobresa energètica abans de crear l'extra line"""
        if context is None:
            context = {}

        if len(fact_ids) > 1:
            raise Exception("Ha arribat més d'un id")

        imd_obj = self.pool.get("ir.model.data")

        factura_browse = self.browse(cursor, uid, fact_ids[0], context=context)

        res = {}
        pobresa_energetica = False

        # TODO: Posar semantic ID
        pobresa_id = imd_obj.get_object_reference(
            cursor, uid, "som_polissa", "categ_pobresa_energetica"
        )[1]

        if (
            pobresa_id
            and factura_browse.polissa_id.category_id
            and pobresa_id in [x.id for x in factura_browse.polissa_id.category_id]
        ):
            pobresa_energetica = True

        if not pobresa_energetica:
            res = super(GiscedataFacturacioFactura, self).generate_unpayment_expenses(
                cursor, uid, fact_ids, context=context
            )

        return res


GiscedataFacturacioFactura()
