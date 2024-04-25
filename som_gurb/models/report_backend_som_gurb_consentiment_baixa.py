# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from report_puppeteer.report_puppeteer import PuppeteerParser


class ReportBackendSomGurbConsentimentBaixa(ReportBackend):
    _source_model = "som.gurb.cups"
    _name = "report.backend.som.gurb.consentiment.baixa"

    def get_lang(self, cursor, uid, record_id, context=None):
        if context is None:
            context = {}

        gurb_cups_o = self.pool.get("som.gurb.cups")
        pol_o = self.pool.get("giscedata.polissa")

        gurb_cups_br = gurb_cups_o.browse(cursor, uid, record_id, context=context)
        pol_id = gurb_cups_br.get_polissa_gurb_cups()
        pol_br = pol_o.browse(cursor, uid, pol_id, context=context)

        return pol_br.titular.lang

    @report_browsify
    def get_data(self, cursor, uid, gurb_cups, context=None):
        return {}


ReportBackendSomGurbConsentimentBaixa()


PuppeteerParser(
    "report.report_som_gurb_consentiment_baixa",
    "report.backend.som.gurb.consentiment.baixa",
    "som_gurb/reports/som_gurb_consentiment_baixa.mako",
    params={},
)
