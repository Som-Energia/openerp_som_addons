# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from report_puppeteer.report_puppeteer import PuppeteerParser
from datetime import datetime

MONTHS = {
    "1": "de gener",
    "2": "de febrer",
    "3": "de març",
    "4": "d'abril",
    "5": "de maig",
    "6": "de juny",
    "7": "de juliol",
    "8": "d'agost",
    "9": "de setembre",
    "10": "d'octubre",
    "11": "de novembre",
    "12": "de desembre",
}


class ReportBackendSomGurbDocuments(ReportBackend):
    _source_model = "som.gurb.cups"
    _name = "report.backend.som.gurb.documents"

    def get_lang(self, cursor, uid, record_id, context=None):
        if context is None:
            context = {}

        gurb_cups_o = self.pool.get("som.gurb.cups")
        pol_o = self.pool.get("giscedata.polissa")

        gurb_cups_br = gurb_cups_o.browse(cursor, uid, record_id, context=context)
        pol_id = gurb_cups_o.get_polissa_gurb_cups(cursor, uid, gurb_cups_br.id)
        pol_br = pol_o.browse(cursor, uid, pol_id, context=context)

        return pol_br.titular.lang

    @report_browsify
    def get_data(self, cursor, uid, gurb_cups, context=None):
        if context is None:
            context = {}

        gurb_cups_o = self.pool.get("som.gurb.cups")
        partner_o = self.pool.get("res.partner")
        pol_o = self.pool.get("giscedata.polissa")

        pol_id = gurb_cups_o.get_polissa_gurb_cups(cursor, uid, gurb_cups.id)
        pol_br = pol_o.browse(cursor, uid, pol_id, context=context)

        data = {
            "name": pol_br.titular.name,
            "address": pol_br.cups.direccio,
            "nif": pol_br.titular.vat,
            "cups": pol_br.cups.name,
            "day": datetime.now().day,
            "month": MONTHS[str(datetime.now().month)],
            "year": datetime.now().year,
            "cau": gurb_cups.gurb_id.self_consumption_id.cau,
        }

        data["is_enterprise"] = partner_o.is_enterprise_vat(pol_br.titular.vat)
        if data["is_enterprise"]:
            data["representative"] = {
                "name": pol_br.representante_id.name,
                "vat": pol_br.representante_id.vat,
            }

        return data


ReportBackendSomGurbDocuments()

PuppeteerParser(
    "report.report_som_gurb_consentiment_baixa",
    "report.backend.som.gurb.documents",
    "som_gurb/reports/som_gurb_consentiment_baixa.mako",
    params={},
)

PuppeteerParser(
    "report.report_som_gurb_autoritzacio_representant",
    "report.backend.som.gurb.documents",
    "som_gurb/reports/som_gurb_autoritzacio_representant.mako",
    params={},
)
