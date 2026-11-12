# -*- coding: utf-8 -*-

from osv import osv


class PaymentOrder(osv.osv):
    """Modificació payment.order per cridar el wizard"""

    _name = "payment.order"
    _inherit = "payment.order"

    def pattern_remesa_description_parse_config_var(self, cursor, uid, invoice, context=None):
        factura_obj = self.pool.get("giscedata.facturacio.factura")

        factura_id = False
        if hasattr(invoice, "id"):
            factura_id = factura_obj.search(cursor, uid, [("invoice_id", "=", invoice.id)])
        remesa_description = super(PaymentOrder, self).pattern_remesa_description_parse_config_var(
            cursor, uid, invoice, context=context
        )
        additional_text = "SOM ENERGIA SCCL"

        if factura_id:
            factura = factura_obj.browse(cursor, uid, factura_id[0])
            if factura.cups_id and factura.cups_id.direccio:
                # We take only 97 chars in order to respect xml facet of 140 chars max length
                # The text "Factura FExxxxxxxxxx - Contracte yyyyyyy - " is 43 chars long
                # So we must take only 97 from address for we don't want to exceed the 140 chars restriction   # noqa: E501
                additional_text = unicode(factura.cups_id.direccio)[:97].encode("utf8")  # noqa: F821,E501
        return remesa_description.format(additional_text)


PaymentOrder()
