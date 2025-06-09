# -*- coding: utf-8 -*-
from __future__ import absolute_import
from osv import osv, fields


class WizardCalculateGurbSavings(osv.osv_memory):
    _name = "wizard.calculate.gurb.savings"
    _description = "Wizard per calcular l'estalvi d'un Gurb Cups"

    def _default_email(self, cursor, uid, context=None):
        if context is None:
            context = {}

        email = False

        gurb_cups_id = context.get('active_id')
        gurb_cups_obj = self.pool.get('som.gurb.cups')
        gurb_cups = gurb_cups_obj.browse(cursor, uid, gurb_cups_id, context=context)
        if gurb_cups.polissa_id:
            email = gurb_cups.polissa_id.direccio_pagament.email
        return email

    def calculate_gurb_savings(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        # imd_obj = self.pool.get("ir.model.data")
        # partner_obj = self.pool.get("res.partner")
        # attach_obj = self.pool.get("ir.attachment")
        gurb_cups_obj = self.pool.get("som.gurb.cups")
        gff_obj = self.pool.get("giscedata.facturacio.factura")
        # pro_obj = self.pool.get("giscedata.signatura.process")
        # pol_obj = self.pool.get("giscedata.polissa")
        gffl_obj = self.pool.get("giscedata.facturacio.factura.linia")
        prod_obj = self.pool.get("product.product")

        wiz = self.browse(cursor, uid, ids[0], context=context)
        gurb_cups_id = context.get("active_id", False)

        self.validate_gurb_cups(cursor, uid, gurb_cups_id, context=context)

        if not gurb_cups_id:
            raise osv.except_osv("Registre actiu", "Aquest assistent necessita un registre actiu!")

        polissa_id = gurb_cups_obj.get_polissa_gurb_cups(cursor, uid, gurb_cups_id, context=context)

        f1_ids = gff_obj.search(cursor, uid, (
            [("polissa_id", "=", polissa_id),
             ("data_inici", ">=", wiz.date_from),
                ("data_final", "<=", wiz.date_to),
                ("type", "=", "in_invoice")]))

        profit_untaxed = 0
        profit = 0

        for f1_id in f1_ids:
            # del f1
            linies_autoconsum_ids = gffl_obj.search(cursor, uid, ([("factura_id", "in", f1_id),
                                                                   ("tipus", "=", "autoconsum")]))
            linies_generacio_ids = gffl_obj.search(cursor, uid, ([("factura_id", "in", f1_id),
                                                                  ("tipus", "=", "generacio")]))
            linies_energia_f1_ids = gffl_obj.search(cursor, uid, ([("factura_id", "in", f1_id),
                                                                   ("tipus", "=", "energia")]))

            f1 = gff_obj.browse(cursor, uid, f1_id)
            # de la gff
            gff_id = gff_obj.search(cursor, uid, (
                [("polissa_id", "=", polissa_id),
                 ("data_inici", ">=", f1.data_inici),
                    ("data_final", "<=", f1.data_final),
                    ("type", "=", "out_invoice")]))[0]
            linies_gurb_ids = gffl_obj.search(cursor,
                                              uid,
                                              ([("factura_id", "in", gff_id),
                                                ("name", "=", "Quota del servei GURB")]))
            linies_energia_ids = gffl_obj.search(cursor, uid, ([("factura_id", "in", gff_id),
                                                                ("tipus", "=", "energia")]))

            # buscar la gff a partir del date to i from del f1?

            linies_autoconsum = gffl_obj.browse(cursor, uid, linies_autoconsum_ids)
            linies_generacio = gffl_obj.browse(cursor, uid, linies_generacio_ids)
            linies_energia_f1 = gffl_obj.browse(cursor, uid, linies_energia_f1_ids)
            linies_gurb = gffl_obj.browse(cursor, uid, linies_gurb_ids)
            linies_energia = gffl_obj.browse(cursor, uid, linies_energia_ids)

            total_auto = {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0, 'P5': 0, 'P6': 0}
            for linia_autoconsum in linies_autoconsum:
                total_auto[linia_autoconsum.name] += linia_autoconsum.quantity

            total_energia = {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0, 'P5': 0, 'P6': 0}
            # el price_energia ha de ser de la factura i no del f1
            price_energia = {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0, 'P5': 0, 'P6': 0}
            for linia_energia_f1 in linies_energia_f1:
                total_energia[linia_energia_f1.name] += linia_energia_f1.quantity

            for linia_energia in linies_energia:
                price_energia[linia_energia.name] = linia_energia.price_unit

            profit_fact = 0
            for k, _ in total_auto:
                # en aquesta linia no hi ha impostos, també deixaràs de pagar iva, com ho calculem?
                profit_fact += ((total_energia[k] * price_energia[k]) - ((total_energia[k] - total_auto[k]) * price_energia[k]))  # noqa: E501

            total_generacio = 0
            for linia_generacio in linies_generacio:
                total_generacio += (linia_generacio.quantity * linia_generacio.price_unit)

            # profit_fact += total_generacio

            cost_gurb = 0
            for linia_gurb in linies_gurb:
                cost_gurb += linia_gurb.price_subtotal

            # al gurb se li han d'aplicar els impostos? si és empresa dona igual?
            profit_fact -= cost_gurb

            profit_untaxed += (profit_fact + total_generacio - cost_gurb)

            profit_fact_taxed = prod_obj.add_taxes(cursor, uid, linies_energia[0].product_id.id,
                                                   profit_fact, False, context=context,
                                                   )
            cost_gurb_taxed = prod_obj.add_taxes(cursor, uid, linies_gurb[0].product_id.id,
                                                 cost_gurb, False, context=context,
                                                 )

            profit += (profit_fact_taxed + total_generacio - cost_gurb_taxed)

        res = {'profit_untaxed': profit_untaxed, 'profit': profit}
        wiz.write(
            {
                "state": "end",
                "info": res
            }
        )
        return res

    _columns = {
        "date_from": fields.date("Data desde"),
        "date_to": fields.date("Data fins"),
        'info': fields.text('Description'),
        "state": fields.selection(
            [("init", "Init"), ("end", "End")],
            "State",
        ),
    }

    _defaults = {
        "state": lambda *a: "init",
    }


WizardCalculateGurbSavings()
