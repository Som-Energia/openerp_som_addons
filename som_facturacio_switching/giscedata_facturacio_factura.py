# -*- coding: utf-8 -*-

from osv import osv


class GiscedataFacturacioFactura(osv.osv):
    _inherit = "giscedata.facturacio.factura"

    def generate_unpayment_expenses(self, cursor, uid, fact_ids, context=None):
        res = {}
        pobresa_energetica = self.check_pobresa_energetica(cursor, uid, fact_ids, context=context)
        too_much_unpayment_expenses = self.check_total_invoice_more_than_unpaymnet_expenses(
            cursor, uid, fact_ids, context=context)
        if not pobresa_energetica and not too_much_unpayment_expenses:
            res = super(GiscedataFacturacioFactura, self).generate_unpayment_expenses(
                cursor, uid, fact_ids, context=context
            )
        return res

    def check_pobresa_energetica(self, cursor, uid, fact_ids, context=None):
        """Comprovem que no té pobresa energètica abans de crear l'extra line"""
        if context is None:
            context = {}

        if len(fact_ids) > 1:
            raise Exception("Ha arribat més d'un id")

        imd_obj = self.pool.get("ir.model.data")

        factura_browse = self.browse(cursor, uid, fact_ids[0], context=context)

        pobresa_energetica = False

        pobresa_id = imd_obj.get_object_reference(
            cursor, uid, "som_polissa", "categ_pobresa_energetica"
        )[1]

        if (
            pobresa_id
            and factura_browse.polissa_id.category_id
            and pobresa_id in [x.id for x in factura_browse.polissa_id.category_id]
        ):
            pobresa_energetica = True

        return pobresa_energetica

    def check_total_invoice_more_than_unpaymnet_expenses(self, cursor, uid, fact_ids, context=None):
        """Comprovem que la factura no té un import total inferior a l'import de l'extra line"""
        if context is None:
            context = {}
        if len(fact_ids) > 1:
            raise Exception("Ha arribat més d'un id")

        imd_obj = self.pool.get("ir.model.data")
        prod_obj = self.pool.get('product.product')
        extra_obj = self.pool.get('giscedata.facturacio.extra')

        factura_browse = self.browse(cursor, uid, fact_ids[0], context=context)

        total_invoice_more_than_unpaymnet_expenses = False

        unpayment_fee_product_id = imd_obj.get_object_reference(cursor, uid,
                                                                'giscedata_facturacio_impagat',
                                                                'product_unpaid_management'
                                                                )[1]
        unpayment_fee_product = prod_obj.browse(
            cursor, uid, unpayment_fee_product_id, context=context
        )

        existing_lines = extra_obj.search(cursor, uid,
                                          [('polissa_id', '=', factura_browse.polissa_id.id),
                                           ('product_id', '=', unpayment_fee_product_id),
                                              ('name', 'ilike', factura_browse.number)],
                                          context={'active_test': False})
        if existing_lines:
            pending_lines = unpayment_fee_product.list_price
            for line in existing_lines:
                pending_lines += extra_obj.read(
                    cursor, uid, line, ['price_subtotal'],
                    context=context)['price_subtotal']

            if factura_browse.amount_total <= pending_lines:
                total_invoice_more_than_unpaymnet_expenses = True

        return total_invoice_more_than_unpaymnet_expenses


GiscedataFacturacioFactura()
