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
            "costs": self.get_costs(cursor, uid, pol, context=context),
            "potencia": self.get_potencia(cursor, uid, pol, context=context),
            "estimacio": self.get_estimacio(cursor, uid, pol, context=context),
        }
        return data

    def get_titular(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        data = {
            "nom": pol.titular.name,
            "adreca": pol.cups.direccio,
            "cups": pol.cups.name,
            "peatge": pol.llista_preu.nom_comercial,
            # "grup_local": "",
        }
        return data

    def get_estimacio(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        wiz_opti_obj = self.pool.get("wizard.contract.power.optimization")

        ctx = {"active_id": pol.id}

        wiz = wiz_opti_obj.create({}, context=ctx)
        wiz.get_optimization_required_data(cursor, uid, wiz.id, pol.id, context=ctx)
        wiz_opti_obj.serializate_wizard_data(cursor, uid, wiz.id, context=ctx)
        wiz.get_periods_power(context=ctx)

        data = {
            "potencia_actual": "",
            "potencia_optima": "",
        }

        return data

    def get_potencia(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        data = {}

        return data

    def get_ultimes_12_factures(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        factura_obj = self.pool.get("giscedata.facturacio.factura")

        search_params = [
            ("polissa_id", "=", pol.id),
            ("type", "=", "out_invoice"),
            ("refund_by_id", "=", False),
            ("state", "=", "paid")
        ]

        factures_ids = factura_obj.search(
            cursor, uid, search_params, context=context, order="date_invoice DESC", limit=12
        )

        return factures_ids

    def get_costs(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        factura_obj = self.pool.get("giscedata.facturacio.factura")
        ir_model_obj = self.pool.get("ir.model.data")
        flux_solar = ir_model_obj.get_object_reference(
            cursor, uid, "giscedata_facturacio_bateria_virtual", "bateria_virtual_product"
        )[1]

        data = {
            "energia": 0.0,
            "potencia": 0.0,
            "exces": 0.0,
            "reactiva": 0.0,
            "descompte_generacio": 0.0,
        }

        factures_ids = self.get_ultimes_12_factures(cursor, uid, pol, context=context)

        for factura in factura_obj.browse(cursor, uid, factures_ids):
            data["energia"] += factura.total_energia
            data["exces"] += factura.total_exces_potencia
            data["potencia"] += factura.total_potencia
            data["reactiva"] += factura.total_reactiva
            data["descompte_generacio"] += abs(factura.total_generacio)

            for linia in factura.linia_ids:
                if linia.product_id == flux_solar:
                    data["descompte_generacio"] += abs(linia.price_subtotal)
        return data


ReportBackendSomEstalvi()
