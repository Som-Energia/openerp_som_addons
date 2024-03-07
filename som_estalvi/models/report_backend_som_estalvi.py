# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify


class ReportBackendSomEstalvi(ReportBackend):
    _source_model = "giscedata.polissa"
    _name = "report.backend.som.estalvi"

    @report_browsify
    def get_data(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        data = {
            "titular": self.get_titular(cursor, uid, pol, context=context),
            "energia": self.get_energia(cursor, uid, pol, context=context),
            "costs": self.get_costs(cursor, uid, pol, context=context),
            "potencia": self.get_potencia(cursor, uid, pol, context=context),
            "estimacio": self.get_potencia(cursor, uid, pol, context=context),
        }
        return data

    def get_titular(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        data = {
            "nom": "",
            "adreca": "",
            "cups": "",
            "peatge": "",
            "grup_local": "",
        }
        return data

    def get_energia(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        data = {}

        return data

    def get_estimacio(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        data = {
            'potencia_actual': '',
            'potencia_optima': '',
        }

        return data

    def get_potencia(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        data = {}

        return data

    def get_costs(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        data = {
            'electricitat': '',
            'mag': '',
            'potencia': '',
            'exces': '',
            'reactiva': '',
        }

        return data


ReportBackendSomEstalvi()
