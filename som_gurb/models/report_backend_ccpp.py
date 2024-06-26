# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from tools import float_round


class ReportBackendCondicionsParticulars(ReportBackend):
    _inherit = "report.backend.condicions.particulars"

    @report_browsify
    def get_data(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        data = super(ReportBackendCondicionsParticulars, self).get_data(
            cursor, uid, pol, context=context
        )

        gurb = self.get_gurb(cursor, uid, pol, context=context)

        if gurb:
            data["gurb"] = gurb

        return data

    def get_gurb(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        res = False
        gurb_cups_obj = self.pool.get("som.gurb.cups")
        product_obj = self.pool.get("product.product")
        pricelist_obj = self.pool.get("product.pricelist")

        gurb_cups_id = gurb_cups_obj.search(cursor, uid, [("cups_id", "=", pol.cups.id)])
        if gurb_cups_id:
            gurb_cups_br = gurb_cups_obj.browse(cursor, uid, gurb_cups_id[0])
            initial_product_id = gurb_cups_br.gurb_id.initial_product_id.id
            grub_pricelist_id = gurb_cups_br.gurb_id.pricelist_id.id

            initial_product_price = pricelist_obj.price_get(
                cursor,
                uid,
                [grub_pricelist_id],
                initial_product_id,
                gurb_cups_br.beta_kw,
                context=context,
            )
            initial_product_price_with_taxes = product_obj.add_taxes(
                cursor, uid, initial_product_id, initial_product_price, False, context=context
            )

            res = {
                "nom": gurb_cups_br.gurb_id.name,
                "cost": float_round(initial_product_price_with_taxes, 2),
                "potencia": gurb_cups_br.beta_kw,
                "quota": 0.35,  # TODO: Use pricelist
                "beta_percentatge": gurb_cups_br.beta_percentage
            }

        return res


ReportBackendCondicionsParticulars()
