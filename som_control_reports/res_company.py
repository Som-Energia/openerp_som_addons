# -*- coding: utf-8 -*-
from osv import osv
import pooler


class ResCompany(osv.osv):

    _name = "res.company"
    _inherit = "res.company"

    def get_company_report_data(self, cursor, uid, company_id=None, date=None, context=None):
        """
        Returns statistics from company to draw a control panel. You may select
        the last date to use
        :param company_id: Company id, 1 by default
        :param date: Date of the statistic data. today if empty.
        :return: A dict with the following data:
            solicituts_erronies: Bad manual contract's
            solicituts: contractes
            solicituts_30A: New 3.0A contracts
            solicituts_activated_30A: activats_30A
            solicituts_inactive: baixes
            solicituts_delayed: delayed_contracts
            solicituts_with_problems: problems_contracts
            solicituts_accepted: accepted_contracts
            solicituts_activated: activated_contracts
        """
        from tools.translate import _
        from dateutil.relativedelta import relativedelta
        import datetime

        pool = pooler.get_pool(cursor.dbname)
        pol_obj = pool.get("giscedata.polissa")
        sw_obj = pool.get("giscedata.switching")
        part_obj = pool.get("res.partner")
        fact_obj = pool.get("giscedata.facturacio.factura")
        # lang = pool.get('res.lang')
        # Search for lang
        # lang_code = context.get('lang', False)
        # lang_id = lang.search(cursor, uid, [('code', '=', lang_code)])

        today_dt = datetime.datetime.today()
        ahir_dt = today_dt - relativedelta(days=1)
        ahir = datetime.datetime.strftime(ahir_dt, "%Y-%m-%d")
        six_months = today_dt + relativedelta(months=-6)
        # TODO date_wizard per implmentar
        date_wizard = ahir

        datas = {}

        # Comercialitzacio general
        pol_obj.search(cursor, uid, [])
        solicituts = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("data_firma_contracte", "<=", date_wizard),
                ],
            )
        )
        activats = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("state", "=", "activa"),
                    ("data_firma_contracte", "<=", date_wizard),
                ],
            )
        )
        baixes = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("active", "=", 0),
                    ("data_firma_contracte", "<=", date_wizard),
                ],
            )
        )
        comercilizacio_general = {
            _(u"a. solicituts"): solicituts,
            _(u"b. sol·licituds contracte donats de baixa"): baixes,
            _(u"c. sol·licituds contractes activats"): activats,
        }

        # Interes Cooperativa
        socis = len(
            part_obj.search(
                cursor,
                uid,
                [
                    ("category_id.id", "=", "8"),
                    ("date", "<=", date_wizard),
                ],
            )
        )
        # TODO controlar si <= o <
        # TODO definir data des de quan
        socis_nous = len(
            part_obj.search(
                cursor,
                uid,
                [
                    ("date", ">", six_months),
                    ("date", "<=", date_wizard),
                    ("category_id.id", "=", "8"),
                ],
            )
        )
        socis_de_baixa = len(
            part_obj.search(
                cursor,
                uid,
                [
                    ("ref", "like", "S0"),
                    ("active", "=", False),
                    ("date", "<=", date_wizard),
                ],
            )
        )
        ratio_contractes_soci = round(float(socis) / float(solicituts), 4) * 100
        ratio_contractes_soci = str(ratio_contractes_soci) + " %"
        solicituts_donatius = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("donatiu", "=", "True"),
                    ("data_firma_contracte", "<=", date_wizard),
                ],
            )
        )
        ratio_donatius = round(float(solicituts_donatius) / float(solicituts), 4) * 100
        ratio_donatius = str(ratio_donatius) + " %"
        solicituts_cooperatives = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("titular_nif", "like", "ESF"),
                    ("data_firma_contracte", "<=", date_wizard),
                ],
            )
        )
        solicituts_asociacions = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("titular_nif", "like", "ESG"),
                    ("data_firma_contracte", "<=", date_wizard),
                ],
            )
        )
        interes_cooperativa = {
            _(u"a. socies total"): socis,
            _(u"b. socies nous"): socis_nous,
            _(u"c. socies de baixa"): socis_de_baixa,
            _(u"d. ratio socis vs contractes"): ratio_contractes_soci,
            _(u"e. ratio donatius"): ratio_donatius,
            _(u"f. sol·licituds cooperatives"): solicituts_cooperatives,
            _(u"g. sol·licituts asociacions"): solicituts_asociacions,
        }

        # Administracio Publica
        socis_ajuntaments = len(
            part_obj.search(
                cursor,
                uid,
                [("category_id.id", "=", "8"), ("date", "<=", date_wizard), ("vat", "like", "ESP")],
            )
        )
        solicituts_ajuntaments = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("titular_nif", "like", "ESP"),
                    ("data_firma_contracte", "<=", date_wizard),
                ],
            )
        )

        def count_diff_ajuntaments():
            pol_diff = []
            pol_ids = pol_obj.search(
                cursor,
                uid,
                [("data_firma_contracte", "<=", date_wizard), ("titular_nif", "like", "ESP")],
            )
            pol_reads = pol_obj.read(cursor, uid, pol_ids, ["titular_nif"])
            for pol_read in pol_reads:
                if pol_read["titular_nif"] not in pol_diff:
                    pol_diff.append(pol_read["titular_nif"])
            return len(pol_diff)

        contractes_ajuntaments_diferents = count_diff_ajuntaments()
        facturacio_percentatge = "NO IMPLEMENTAT"
        admin_publica = {
            _(u"a. Ajuntaments socis"): socis_ajuntaments,
            _(u"b. Contractes. Total"): solicituts_ajuntaments,
            _(u"c. Contractes. Ajuntaments titulars"): contractes_ajuntaments_diferents,
            _(u"d. % Facturacio ajuntaments vs total"): facturacio_percentatge,
        }

        # Contractes especiales
        solicituts_30A = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("tarifa", "=", "3.0A"),
                    ("data_firma_contracte", "<=", date_wizard),
                ],
            )
        )
        activats_30A = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("tarifa", "=", "3.0A"),
                    ("state", "=", "activa"),
                    ("data_firma_contracte", "<=", date_wizard),
                ],
            )
        )
        solicituts_31A = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("tarifa", "in", ["3.1A", "3.1A LB"]),
                    ("data_firma_contracte", "<=", date_wizard),
                ],
            )
        )
        solicituts_CCVV = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("titular_nif", "like", "ESH"),
                    ("data_firma_contracte", "<=", date_wizard),
                ],
            )
        )
        # TODO Poner var associaciones en algun sitio
        solicituts_ccvv_30 = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("tarifa", "=", "3.0A"),
                    ("titular_nif", "like", "ESH"),
                    ("data_firma_contracte", "<=", date_wizard),
                ],
            )
        )

        solicituts_asociacions_30 = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("tarifa", "=", "3.0A"),
                    ("titular_nif", "like", "ESG"),
                    ("data_firma_contracte", "<=", date_wizard),
                ],
            )
        )
        solicituts_ajuntaments_30 = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("tarifa", "=", "3.0A"),
                    ("titular_nif", "like", "ESP"),
                    ("data_firma_contracte", "<=", date_wizard),
                ],
            )
        )
        contractes_especials = {
            _(u"a. sol·licituds tarifa 3.0A"): solicituts_30A,
            _(u"b. sol·licituds activades 3.0A"): activats_30A,
            _(u"c. sol·licituds tarifa 3.1A"): solicituts_31A,
            _(u"d. sol·licituds CCVV"): solicituts_CCVV,
            _(u"e. sol·licituds CCVV amb 3.0A"): solicituts_ccvv_30,
            _(u"f. sol·licituds asociacions en 3.0A"): solicituts_asociacions_30,
            _(u"g. sol·licituds ajuntament en 3.0A"): solicituts_ajuntaments_30,
        }

        # Facturacio
        if date_wizard == ahir:
            contractes_endarrerits = len(
                pol_obj.search(
                    cursor,
                    uid,
                    [
                        ("facturacio_endarrerida", "=", "True"),
                    ],
                )
            )
            ratio_contractes_endarrerits = (
                round(float(contractes_endarrerits) / float(solicituts), 4) * 100
            )
            ratio_contractes_endarrerits = str(ratio_contractes_endarrerits) + " %"
        else:
            contractes_endarrerits = "No es pot calcular"
            ratio_contractes_endarrerits = "No es pot calcular"
        r1_oberts = "NO IMPLEMENTAT"
        facturacio = {
            _(u"a. Contractes amb facturacio endarrerida"): contractes_endarrerits,
            _(u"b. ratio facturacio endarrerida"): ratio_contractes_endarrerits,
            _(u" Reclamacions de les lectures"): r1_oberts,
        }

        # Impagaments
        polisses_1_6f = len(fact_obj.search(cursor, uid, [("pending_state", "not in", (1, 18))]))
        fact_1f = len(fact_obj.search(cursor, uid, [("pending_state", "like", "1F")]))
        fact_2f = len(fact_obj.search(cursor, uid, [("pending_state", "like", "2F")]))
        fact_3f = len(fact_obj.search(cursor, uid, [("pending_state", "like", "3F")]))
        fact_4f = len(fact_obj.search(cursor, uid, [("pending_state", "like", "4F")]))
        fact_5f = len(fact_obj.search(cursor, uid, [("pending_state", "like", "5F")]))
        fact_6f = len(fact_obj.search(cursor, uid, [("pending_state", "like", "6F")]))

        def totalPendent(months_quantity):
            data_filtre_dt = today_dt + relativedelta(months=-months_quantity)
            data_filtre = datetime.datetime.strftime(data_filtre_dt, "%Y-%m-%d")
            totalMoney = 0
            fact_total_pendent_ids = fact_obj.search(
                cursor,
                uid,
                [
                    ("pending_state", "not in", (1, 18)),  # Correctes i correcte amb devolució
                    ("date_invoice", "<=", data_filtre),
                    ("state", "=", "open"),
                ],
            )
            fact_reads = fact_obj.read(cursor, uid, fact_total_pendent_ids, ["residual"])
            for fact_read in fact_reads:
                totalMoney = totalMoney + fact_read["residual"]
            return round(totalMoney, 2)

        saldo_total = totalPendent(0)
        saldo_1_mes = totalPendent(1)
        saldo_3_mesos = totalPendent(3)

        rati_factures = "NO IMPLEMENTAT"
        impagaments = {
            _(u"a. Contractes amb factures retornades (1F-6F)"): polisses_1_6f,
            _(u"b0. Factures retornades (1F)"): fact_1f,
            _(u"b1. Factures retornades sense resposta (2F)"): fact_2f,
            _(u"b2. Factures retornades ultim avis (3F)"): fact_3f,
            _(u"b3. Factures retornades enviat a ajuntament per PE (4F)"): fact_4f,
            _(u"b4. Factures retornades Burofax tall (5F)"): fact_5f,
            _(u"b5. Factures retornades TALL (6F)"): fact_6f,
            _(u"b6. Factures retornades CUR o Advocats (6F)"): fact_6f,
            _(u"c. Saldo pendent total"): saldo_total,
            _(u"c1. Saldo pendent (més de 1 mes)"): saldo_1_mes,
            _(u"c2. Saldo pendent (més de 3 mesos)"): saldo_3_mesos,
            _(u"d % Factures retornades "): rati_factures,
        }

        # Gestio de contractes
        acceptats_oberts = len(
            sw_obj.search(
                cursor,
                uid,
                [
                    ("proces_id.name", "in", ["C1", "C2"]),
                    ("state", "=", "open"),
                    ("rebuig", "=", False),
                    ("step_id.name", "=", "02"),
                ],
            )
        )

        activats_oberts = len(
            sw_obj.search(
                cursor,
                uid,
                [
                    ("proces_id.name", "in", ["C1", "C2"]),
                    ("state", "=", "open"),
                    ("step_id.name", "in", ["05", "07"]),
                ],
            )
        )
        sol_ok = activats + acceptats_oberts + activats_oberts
        sol_problematiques = solicituts - sol_ok
        contractes_6m = len(
            pol_obj.search(
                cursor,
                uid,
                [
                    ("data_firma_contracte", "<", six_months),
                    ("state", "=", "esborrany"),
                ],
            )
        )
        solicituts_erronies = len(
            pol_obj.search(cursor, uid, [("data_firma_contracte", "=", False)])
        )
        canvi_titular = "NO IMPLEMENTAT"
        canvi_pottar = "NO IMPLEMENTAT"
        if date_wizard != ahir:
            acceptats_oberts = "No es pot calcular"
            activats_oberts = "No es pot calcular"
            sol_problematiques = "No es pot calcular"

        gestio_contractes = {
            _(u"a. Canvis comercializadora acceptats"): acceptats_oberts,
            _(u"b. Canvis comercializadora per activar"): activats_oberts,
            _(u"c. sol·licituds problematiques"): sol_problematiques,
            _(u"e. contractes de més de 6 m en esborrany"): contractes_6m,
            _(u"f. solicituts erronies"): solicituts_erronies,
            _(u"g. canvis de titularitat"): canvi_titular,
            _(u"h. canvis de potencia/tarifa"): canvi_pottar,
        }
        datas.update(
            {
                "1. Comercializacio General": comercilizacio_general,
                "2. Interés cooperativa": interes_cooperativa,
                "3. Administració pública": admin_publica,
                "4. Contractes especials": contractes_especials,
                "5. Facturació": facturacio,
                "6. Impagats": impagaments,
                "7. Gestió de contractes": gestio_contractes,
            }
        )
        return date_wizard, datas

        def get_translate_dict_description(self, datas):

            translate_id = {
                "solicituts_erronies": "solicitudes erroneas",
                "solicituts": "solicitudes",
                "solicituts_30A": "solicitudes tarifa 3.0A",
                "activats_30A": "solicitudes activadas 3.0A",
                "baixes": "solicitudes contrato dados de baja",
                "factures_endarrerides": "facturas atrasadas",
                "sol_problematiques": "solicitudes problematicas",
                "acceptats": "solicitudes contratos aceptados",
                "activats": "solicitudes contratos activados",
            }
            return translate_id


ResCompany()
