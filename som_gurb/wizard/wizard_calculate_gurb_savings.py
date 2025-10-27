# -*- coding: utf-8 -*-
from __future__ import absolute_import
from osv import osv, fields
from datetime import datetime
from StringIO import StringIO

import csv
import base64



HEADER = [
    "polissa", "estalvi_sense_impostos", "estalvi_amb_impostos", "kwh_excedents",
    "kwh_generacio_neta", "kwh_autoconsumits", "kwh_consumits"
]


class WizardCalculateGurbSavings(osv.osv_memory):
    _name = "wizard.calculate.gurb.savings"
    _description = "Wizard per calcular l'estalvi d'un Gurb Cups"

    def get_only_relevant_invoices(self, cursor, uid, polissa_id, date_from, date_to, context=None):
        if context is None:
            context = {}

        gff_obj = self.pool.get("giscedata.facturacio.factura")
        trimmed_list = []

        search_vals = [
            ("polissa_id", "=", polissa_id),
            ("data_inici", ">=", date_from),
            ("data_final", "<=", date_to),
            ("type", "=", "in_invoice"),
            ("rectificative_type", "in", ["N", "R", "RA"])
        ]
        invoice_ids = gff_obj.search(cursor, uid, search_vals, context=context)

        for invoice_id in invoice_ids:

            invoice = gff_obj.browse(cursor, uid, invoice_id, context=context)

            search_params = [
                ("polissa_id", "=", polissa_id),
                ("data_inici", "=", invoice.data_inici),
                ("data_final", "=", invoice.data_final),
                ("type", "=", "out_invoice")
            ]

            gff_ids = gff_obj.search(cursor, uid, search_params, context=context)
            if gff_ids:
                search_params = [
                    ("polissa_id", "=", polissa_id),
                    ("data_inici", ">=", invoice.data_inici),
                    ("data_final", "<=", invoice.data_final),
                    ("type", "=", "in_invoice"),
                    ("rectificative_type", "in", ["N", "R", "RA"])
                ]
                provider_invoice = gff_obj.search(
                    cursor, uid, search_params, order='date_invoice DESC', limit=1, context=context)
                if provider_invoice and provider_invoice[0] not in trimmed_list:
                    trimmed_list.append(provider_invoice[0])

        return trimmed_list

    def button_calculate(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        savings = []
        wiz = self.browse(cursor, uid, ids[0], context=context)

        active_ids = context.get("active_ids")
        for gurb_cups_id in active_ids:
            saving = self.calculate_gurb_cups_savings(
                cursor, uid, gurb_cups_id, wiz.date_from, wiz.date_to, context=context
            )
            savings.append(saving)
        self.generate_savings_csv(cursor, uid, ids[0], savings, context=context)

        result = {
            "state": "end",
            "info": "S'ha generat el fitxer d'estalvis correctament.",
        }

        self.write(cursor, uid, ids, result, context=context)

    def generate_savings_csv(self, cursor, uid, wiz_id, values, context=None):
        if context is None:
            context = {}

        wizard = self.browse(cursor, uid, wiz_id, context=context)

        csv_file = StringIO()
        writer = csv.DictWriter(csv_file, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(values)

        res_file = csv_file.getvalue()
        timestamp = datetime.today().strftime("%Y-%m-%d-%H:%M")
        filename = "estalvis-{}.csv".format(timestamp)
        wizard.write(
            {"report": base64.b64encode(res_file), "filename_report": filename}
        )

    def calculate_gurb_cups_savings(   # noqa: C901
        self, cursor, uid, gurb_cups_id, date_from, date_to, context=None
    ):
        if context is None:
            context = {}

        gurb_cups_obj = self.pool.get("som.gurb.cups")
        gff_obj = self.pool.get("giscedata.facturacio.factura")
        gffl_obj = self.pool.get("giscedata.facturacio.factura.linia")
        polissa_obj = self.pool.get("giscedata.polissa")
        prod_obj = self.pool.get("product.product")
        imd_o = self.pool.get("ir.model.data")

        gurb_product_id = imd_o.get_object_reference(
            cursor, uid, "som_gurb", "product_gurb"
        )[1]
        owner_product_id = imd_o.get_object_reference(
            cursor, uid, "som_gurb", "product_owner_gurb"
        )[1]
        enterprise_product_id = imd_o.get_object_reference(
            cursor, uid, "som_gurb", "product_enterprise_gurb"
        )[1]

        if not gurb_cups_id:
            raise osv.except_osv("Registre actiu", "Aquest assistent necessita un registre actiu!")

        polissa_id = gurb_cups_obj.get_polissa_gurb_cups(cursor, uid, gurb_cups_id, context=context)

        f1_ids = self.get_only_relevant_invoices(
            cursor, uid, polissa_id, date_from, date_to, context=context
        )

        profit_untaxed = 0
        profit = 0
        bad_f1s = 0
        kwh_auto = 0
        kwh_consumed = 0
        kwh_produced = 0

        for f1_id in f1_ids:
            # del f1
            linies_autoconsum_ids = gffl_obj.search(cursor, uid, ([("factura_id", "=", f1_id),
                                                                   ("tipus", "=", "autoconsum")]))
            linies_genneta_ids = gffl_obj.search(cursor, uid, ([("factura_id", "=", f1_id),
                                                                ("tipus", "=", "generacio_neta")]))

            f1 = gff_obj.browse(cursor, uid, f1_id)
            # de la gff
            gff_ids = gff_obj.search(cursor, uid, (
                [("polissa_id", "=", polissa_id),
                 ("data_inici", "=", f1.data_inici),
                    ("data_final", "=", f1.data_final),
                    ("type", "=", "out_invoice")]))
            if gff_ids:
                gff_id = gff_ids[0]
            else:
                bad_f1s += 1
                continue
            linies_gurb_ids = gffl_obj.search(cursor,
                                              uid,
                                              ([("factura_id", "=", gff_id),
                                                ("product_id", "in", [gurb_product_id,
                                                                      enterprise_product_id,
                                                                      owner_product_id])]))
            linies_energia_ids = gffl_obj.search(cursor, uid, ([("factura_id", "=", gff_id),
                                                                ("tipus", "=", "energia")]))
            linies_generacio_ids = gffl_obj.search(cursor, uid, ([("factura_id", "=", gff_id),
                                                                  ("tipus", "=", "generacio")]))

            # buscar la gff a partir del date to i from del f1?
            linies_generacio = gffl_obj.browse(cursor, uid, linies_generacio_ids)
            if linies_autoconsum_ids:
                linies_autoconsum = gffl_obj.browse(cursor, uid, linies_autoconsum_ids)
            else:
                linies_genneta = gffl_obj.browse(cursor, uid, linies_genneta_ids)
                linies_gen_dict = {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0, 'P5': 0, 'P6': 0}
                for linia_gen in linies_generacio:
                    linies_gen_dict[linia_gen.name] = linia_gen.quantity
            linies_gurb = gffl_obj.browse(cursor, uid, linies_gurb_ids)
            linies_energia = gffl_obj.browse(cursor, uid, linies_energia_ids)

            total_auto = {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0, 'P5': 0, 'P6': 0}
            if linies_autoconsum_ids:
                for linia_autoconsum in linies_autoconsum:
                    total_auto[linia_autoconsum.name] += linia_autoconsum.quantity
            else:
                for linia_genneta in linies_genneta:
                    total_auto[linia_genneta.name] += (
                        linia_genneta.quantity + linies_gen_dict[linia_genneta.name]
                    )

            auto_kwh = sum(total_auto.values())
            total_energia = {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0, 'P5': 0, 'P6': 0}
            price_energia = {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0, 'P5': 0, 'P6': 0}
            for linia_energia in linies_energia:
                if linia_energia.name in total_energia.keys():
                    total_energia[linia_energia.name] = linia_energia.quantity
                    price_energia[linia_energia.name] = linia_energia.price_unit
            energia_kwh = sum(total_energia.values())

            profit_fact = 0
            for k in total_auto:
                # en aquesta linia no hi ha impostos, també deixaràs de pagar iva, com ho calculem?
                profit_fact += total_auto[k] * price_energia[k]

            generacio_kwh = 0
            total_generacio = {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0, 'P5': 0, 'P6': 0}
            price_generacio = {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0, 'P5': 0, 'P6': 0}
            for linia_generacio in linies_generacio:
                if linia_generacio.name in total_generacio.keys():
                    generacio_kwh += linia_generacio.quantity
                    total_generacio[linia_generacio.name] += linia_generacio.quantity
                    price_generacio[linia_generacio.name] += linia_generacio.price_unit
            generacio_fact = 0
            for k in total_generacio:
                generacio_fact += total_generacio[k] * price_generacio[k]

            cost_gurb = 0
            for linia_gurb in linies_gurb:
                cost_gurb += linia_gurb.price_subtotal

            profit_untaxed += (profit_fact + abs(generacio_fact) - cost_gurb)

            profit_fact_taxed = 0
            if linies_energia:
                energy_prod_id = linies_energia[0].product_id.id
                profit_fact_taxed = prod_obj.add_taxes(
                    cursor, uid, energy_prod_id, profit_fact, False, context=context,
                )

            if linies_generacio:
                generacio_prod_id = linies_generacio[0].product_id.id
                profit_fact_taxed += abs(prod_obj.add_taxes(
                    cursor, uid, generacio_prod_id, generacio_fact, False, context=context,
                ))

            cost_gurb_taxed = 0
            if linies_gurb:
                cost_gurb_taxed = prod_obj.add_taxes(
                    cursor, uid, linies_gurb[0].product_id.id, cost_gurb, False, context=context
                )

            if linies_energia:
                profit += (profit_fact_taxed - cost_gurb_taxed)

            kwh_produced += generacio_kwh
            kwh_auto += auto_kwh
            kwh_consumed += energia_kwh

        polissa = polissa_obj.browse(cursor, uid, polissa_id, context=context)

        result = {
            "polissa": polissa.name,
            "estalvi_sense_impostos": round(profit_untaxed, 2),
            "estalvi_amb_impostos": round(profit, 2),
            "kwh_excedents": round(abs(kwh_produced), 2),
            "kwh_generacio_neta": round(abs(kwh_produced) + kwh_auto, 2),
            "kwh_autoconsumits": round(kwh_auto, 2),
            "kwh_consumits": round(kwh_consumed, 2),
        }

        return result

    _columns = {
        "date_from": fields.date("Data desde", required=True),
        "date_to": fields.date("Data fins", required=True),
        'info': fields.text('Description'),
        "state": fields.selection(
            [("init", "Init"), ("end", "End")],
            "State",
        ),
        'report': fields.binary('Resultat'),
        'filename_report': fields.char('Nom fitxer exportat', size=256),
    }

    _defaults = {
        "state": lambda *a: "init",
    }


WizardCalculateGurbSavings()
