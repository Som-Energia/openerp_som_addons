# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from report_backend.report_backend import ReportBackend, report_browsify
from report_puppeteer.report_puppeteer import PuppeteerParser
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from osv import osv


class ReportBackendSomEstalvi(ReportBackend):
    _source_model = "giscedata.polissa"
    _name = "report.backend.som.estalvi"

    _decimals = {
        ('potencia', 'potencies_contractades'): 3,
        ('potencia', 'optimizations', 'optimal_powers_P1'): 3,
        ('potencia', 'optimizations', 'optimal_powers_P2'): 3,
        ('potencia', 'optimizations', 'optimal_powers_P3'): 3,
        ('potencia', 'optimizations', 'optimal_powers_P4'): 3,
        ('potencia', 'optimizations', 'optimal_powers_P5'): 3,
        ('potencia', 'optimizations', 'optimal_powers_P6'): 3,
    }

    def get_lang(self, cursor, uid, record_id, context=None):
        if context is None:
            context = {}

        pol_o = self.pool.get("giscedata.polissa")
        pol_br = pol_o.browse(cursor, uid, record_id, context=context)

        return pol_br.titular.lang

    def get_dates(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        factura_obj = self.pool.get("giscedata.facturacio.factura")

        search_params = [
            ("polissa_id", "=", pol.id),
            ("type", "=", "out_invoice"),
            ("refund_by_id", "=", False),
        ]

        factura_id = factura_obj.search(
            cursor, uid, search_params, context=context, order="data_final DESC", limit=1
        )[0]

        end_date = factura_obj.read(
            cursor, uid, factura_id, ['data_final'], context=context
        )["data_final"]
        start_date = datetime.strftime(
            datetime.strptime(
                end_date, "%Y-%m-%d"
            ) - relativedelta(years=1) + relativedelta(days=1),
            '%Y-%m-%d'
        )

        return start_date, end_date

    def is_printable(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        factura_obj = self.pool.get("giscedata.facturacio.factura")

        _, end_date = self.get_dates(cursor, uid, pol, context=context)

        search_params = [
            ("polissa_id", "=", pol.id),
            ("type", "=", "out_invoice"),
            ("refund_by_id", "=", False),
            ("date_invoice", ">=", end_date),
        ]

        factura_id = factura_obj.search(
            cursor, uid, search_params, context=context, order="date_invoice DESC", limit=1
        )

        if not factura_id:
            raise osv.except_osv(
                "Aquest informe no es pot imprimir!",
                "El contracte ha de tenir les últimes 12 factures d'energia pagades amb SomEnergia"
            )

    @report_browsify
    def get_data(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        self.is_printable(cursor, uid, pol, context=context)

        data = {
            "titular": self.get_titular(cursor, uid, pol, context=context),
            "costs": self.get_costs(cursor, uid, pol, context=context),
            "potencia": self.get_potencia(cursor, uid, pol, context=context),
        }
        return data

    def get_titular(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        data = {
            "nom": pol.titular.name,
            "adreca": pol.cups.direccio,
            "cups": pol.cups.name,
            "peatge": pol.tarifa.name,
            "tarifa": pol.llista_preu.nom_comercial,
            # "grup_local": "",
        }
        return data

    def get_potencia(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        wiz_opti_obj = self.pool.get("wizard.contract.power.optimization")

        # Triar les dates del càlcul del MiniZinc
        start_date, end_date = self.get_dates(cursor, uid, pol, context=context)

        # Wizard del MiniZinc
        ctx = {
            "active_id": pol.id,
            "active_ids": [pol.id]
        }

        wiz_id = wiz_opti_obj.create(cursor, uid, {}, context=ctx)
        wiz_data = {
            'start_date': start_date,
            'end_date': end_date
        }
        wiz_opti_obj.write(cursor, uid, [wiz_id], wiz_data, context=ctx)
        wiz_opti_obj.button_get_optimization_required_data(cursor, uid, [wiz_id], context=ctx)
        wiz_opti_obj.serializate_wizard_data(cursor, uid, wiz_id, context=ctx)
        wiz_opti_obj._calculate_current_cost(cursor, uid, wiz_id, context=ctx)
        wiz_browse = wiz_opti_obj.browse(cursor, uid, wiz_id, context=ctx)
        optimizations = wiz_opti_obj.execute_optimization_script(
            cursor, uid, wiz_id, pol.id, context=context)

        ctx['decimal'] = True

        wiz_opti_obj.get_maximeters_power(cursor, uid, wiz_id, pol.id, context=ctx)

        wiz_maximeters_powers = wiz_browse.maximeters_powers
        maximeters_powers = json.loads(wiz_maximeters_powers)

        data = {
            "estimacio_cost_potencia_actual": wiz_browse.current_cost,
            "estimacio_cost_potencia_optima": optimizations['optimal_cost'],
            "maximetres": maximeters_powers,
            "potencies_contractades": [],
            "potencies_optimes": [],
            "optimizations": optimizations
        }

        for optimization in data["optimizations"].keys():
            data["optimizations"][optimization] = float(data["optimizations"][optimization])

        for periode in pol.potencies_periode:
            data["potencies_contractades"].append(periode.potencia)

        return data

    def get_costs(self, cursor, uid, pol, context=None):
        if context is None:
            context = {}

        informe_dades_obj = self.pool.get("wizard.informe.dades_desagregades")

        data = {
            "energia": 0.0,
            "potencia": 0.0,
            "exces": 0.0,
            "reactiva": 0.0,
            "descompte_generacio": 0.0,
        }

        start_date, end_date = self.get_dates(cursor, uid, pol, context=context)

        wiz_id = informe_dades_obj.create(cursor, uid, {}, context=context)
        dades_factures = informe_dades_obj.find_invoices(
            cursor, uid, [wiz_id], [pol.id], start_date, end_date, context=context
        )[pol.id]

        data["energia"] = dades_factures['Energia activa'] + dades_factures['MAG']
        data["exces"] = dades_factures[b'Excés potència']
        data["potencia"] = dades_factures[b'Potència']
        data["reactiva"] = dades_factures[b'Penalització reactiva']
        data["descompte_generacio"] = dades_factures['Flux Solar'] + dades_factures['Excedents']

        return data


ReportBackendSomEstalvi()


PuppeteerParser(
    'report.report_som_estalvi',
    'report.backend.som.estalvi',
    'som_estalvi/report/som_estalvi.mako',
    params={}
)
