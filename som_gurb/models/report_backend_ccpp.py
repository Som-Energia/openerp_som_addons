# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from tools import float_round
from datetime import datetime


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
        imd_obj = self.pool.get("ir.model.data")
        partner_obj = self.pool.get("res.partner")
        gurb_cups_obj = self.pool.get("som.gurb.cups")
        product_obj = self.pool.get("product.product")
        pricelist_obj = self.pool.get("product.pricelist")

        gurb_cups_id = gurb_cups_obj.search(cursor, uid, [("cups_id", "=", pol.cups.id)])
        if gurb_cups_id:
            gurb_cups_br = gurb_cups_obj.browse(cursor, uid, gurb_cups_id[0])
            gurb_pricelist_id = gurb_cups_br.gurb_cau_id.gurb_group_id.pricelist_id.id
            initial_product_id = imd_obj.get_object_reference(
                cursor, uid, "som_gurb", "initial_quota_gurb"
            )[1]
            if pol.tarifa.name == "2.0TD":
                quota_product_id = imd_obj.get_object_reference(
                    cursor, uid, "som_gurb", "product_gurb"
                )[1]
            elif pol.tarifa.name == "3.0TD":
                quota_product_id = imd_obj.get_object_reference(
                    cursor, uid, "som_gurb", "product_enterprise_gurb"
                )[1]

            context["date"] = gurb_cups_br.inscription_date or datetime.now().strftime("%Y-%m-%d")

            initial_product_price = pricelist_obj.price_get(
                cursor, uid, [gurb_pricelist_id], initial_product_id,
                gurb_cups_br.beta_kw, context=context,
            )[gurb_pricelist_id]

            initial_product_price_with_taxes = product_obj.add_taxes(
                cursor, uid, initial_product_id, initial_product_price, False, context=context
            )

            quota_price = pricelist_obj.price_get(
                cursor, uid, [gurb_pricelist_id], quota_product_id,
                gurb_cups_br.beta_kw, context=context
            )[gurb_pricelist_id]

            quota_with_taxes = product_obj.add_taxes(
                cursor, uid, quota_product_id, quota_price, False, context=context
            )

            gurb_cups_id = gurb_cups_obj.search(
                cursor, uid, [("polissa_id", "=", pol.id)], context=context)[0]
            gurb_cups_browse = gurb_cups_obj.browse(
                cursor, uid, gurb_cups_id, context=context)

            beta_kw = gurb_cups_browse.beta_kw
            beta_percentage = gurb_cups_browse.beta_percentage
            if gurb_cups_browse.future_beta_kw:
                beta_kw = gurb_cups_browse.future_beta_kw
                beta_percentage = gurb_cups_browse.future_beta_percentage

            annex = {
                "name": pol.titular.name,
                "address": pol.cups.direccio,
                "nif": pol.titular.vat,
                "cups": pol.cups.name,
                "day": datetime.now().day,
                "month": str(datetime.now().month).zfill(2),
                "year": datetime.now().year,
                "cau": gurb_cups_browse.gurb_cau_id.self_consumption_id.cau,
                "beta_kw": beta_kw,
                "beta_percentage": beta_percentage,
                "is_enterprise": partner_obj.is_enterprise_vat(pol.titular.vat)
            }

            res = {
                "nom": gurb_cups_br.gurb_cau_id.name,
                "cost": float_round(initial_product_price_with_taxes, 2),
                "potencia": gurb_cups_br.beta_kw,
                "quota": str(quota_with_taxes),
                "beta_percentatge": gurb_cups_br.beta_percentage,
                "annex": annex
            }

        return res


ReportBackendCondicionsParticulars()
