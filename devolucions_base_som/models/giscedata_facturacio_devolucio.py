# -*- coding: utf-8 -*-
from osv import osv


class GiscedataFacturacioDevolucio(osv.osv):
    _name = 'giscedata.facturacio.devolucio'
    _inherit = 'giscedata.facturacio.devolucio'

    def process_devolucio_lines_moviment_unic(
        self, cr, uid, devolucio_id, linies_ids, move_pstate, context=None
    ):
        if context is None:
            context = {}

        invoice_obj = self.pool.get('account.invoice')
        payment_order_obj = self.pool.get('payment.order')
        line_obj = self.pool.get("giscedata.facturacio.devolucio.linia")

        inv_ids = []
        for linia in line_obj.browse(cr, uid, linies_ids, context={'prefetch': False}):
            inv_id = self.get_invoice(cr, uid, linia.numfactura, getattr(linia, "import"), context)
            if inv_id:
                inv_ids.append(inv_id['id'])

        result = super(GiscedataFacturacioDevolucio, self).process_devolucio_lines_moviment_unic(
            cr, uid, devolucio_id, linies_ids, move_pstate, context
        )

        payment_order_ids = set()
        for inv in invoice_obj.browse(cr, uid, inv_ids, context={'prefetch': False}):
            if inv.payment_order_id:
                payment_order_ids.add(inv.payment_order_id.id)

        for order_id in payment_order_ids:
            payment_order_obj.check_order_paid(cr, uid, [order_id], context=context)

        return result


GiscedataFacturacioDevolucio()
