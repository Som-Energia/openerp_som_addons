# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify


class ReportBackend347Email(ReportBackend):
    _source_model = "l10n.es.aeat.mod347.partner_record"
    _name = "report.backend.347.email"

    @report_browsify
    def get_data(self, cursor, uid, partner, context=None):
        if context is None:
            context = {}

        data = {
            "trimestre_1": partner.first_quarter,
            "trimestre_2": partner.second_quarter,
            "trimestre_3": partner.third_quarter,
            "trimestre_4": partner.fourth_quarter,
            "total": partner.amount,
            "limit": partner.report_id.operations_limit,
            "nom_partner": partner.partner_id.name,
            "cif_partner": partner.partner_vat,
            "any_exercici": partner.report_id.fiscalyear_id.name,
        }

        return data


ReportBackend347Email()
