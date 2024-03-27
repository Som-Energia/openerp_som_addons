# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import base64
import StringIO

import csv


class WizardInformeDadesDesagregades(osv.osv_memory):
    """
    Wizard per llençar l'informe dades desagregades de la factura
    """

    _name = "wizard.informe.dades_desagregades"

    def create_csv(self, items, from_date, to_date, context=None):
        file_name = "Informe_factures_dades_desagregades_{}_{}.csv".format(from_date, to_date)
        keys = items[0].keys()

        output_file = StringIO.StringIO()
        for e in items:
            for key, value in e.items():
                if isinstance(value, float):
                    e[key] = str(value).replace(".", ",")

        dict_writer = csv.DictWriter(output_file, keys, delimiter=";")
        dict_writer.writeheader()
        dict_writer.writerows(items)

        mfile = base64.b64encode(output_file.getvalue())
        output_file.close()

        return file_name, mfile

    def get_contract_ids(self, cursor, uid, contracts):
        pol_obj = self.pool.get("giscedata.polissa")

        # only 3.0TD and 6.xTD and TDVE
        search_params = [
            ("tarifa.codi_ocsum", "in", ["019", "020", "021", "022", "023", "024", "025"])
        ]
        if contracts:
            search_params.append(("name", "in", contracts))

        pol_ids = pol_obj.search(cursor, uid, search_params)

        return [int(x) for x in pol_ids]

    def find_invoices(self, cursor, uid, ids, pol_ids, from_date, to_date, context=None):
        if not context:
            context = {}

        self.browse(cursor, uid, ids[0], context=context)

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        pol_obj = self.pool.get("giscedata.polissa")

        items = {}

        for pol_id in pol_ids:
            pol = pol_obj.browse(cursor, uid, pol_id, context=context)
            subitem = OrderedDict(
                [
                    ("Contracte", pol.name),
                    ("Tarifa Comercialitzadora", pol.llista_preu.name if pol.llista_preu else ""),
                    (
                        "Indexada",
                        "Indexada"
                        if pol.llista_preu and "indexada" in pol.llista_preu.name.lower()
                        else "No",
                    ),
                    ("Energia activa", 0),
                    ("MAG", 0),
                    ("Penalització reactiva", 0),
                    ("Potència", 0),
                    ("Excés potència", 0),
                    ("Excedents", 0),
                    ("Excedents generats totals", 0),
                    ("Excedents saldo compensació", 0),
                    ("Lloguer comptador", 0),
                    ("IVA", 0),
                    ("IGIC", 0),
                    ("IESE", 0),
                    ("Flux Solar", 0),
                    ("Altres", 0),
                    ("TOTAL", 0),
                ]
            )
            items[pol_id] = subitem

        fact_ids = fact_obj.search(
            cursor,
            uid,
            [
                ("polissa_id.id", "in", pol_ids),
                ("data_inici", ">=", from_date),
                ("data_final", "<=", to_date),
                ("type", "in", ["out_invoice", "out_refund"]),
                ("state", "!=", "draft"),
            ],
            context=context,
        )

        for fact_id in fact_ids:
            fact = fact_obj.browse(cursor, uid, fact_id, context=context)
            pol_item = items[fact.polissa_id.id]

            factor = 1.0 if fact.type == "out_invoice" else -1.0
            for line in fact.linies_energia:
                if "topall del gas" in line.name:
                    pol_item["MAG"] += line.price_subtotal * factor
                else:
                    pol_item["Energia activa"] += line.price_subtotal * factor
            pol_item["Penalització reactiva"] += fact.total_reactiva * factor
            pol_item["Potència"] += fact.total_potencia * factor
            pol_item["Excés potència"] += fact.total_exces_potencia * factor
            pol_item["Excedents"] += fact.total_generacio * factor
            for line in fact.linies_generacio:
                if "Saldo excedentes de autoconsumo" in line.name:
                    pol_item["Excedents saldo compensació"] += line.price_subtotal * factor
                else:
                    pol_item["Excedents generats totals"] += line.price_subtotal * factor

            pol_item["Lloguer comptador"] += fact.total_lloguers * factor
            for tax_line in fact.tax_line:
                if "IVA" in tax_line.name:
                    pol_item["IVA"] += tax_line.amount * factor
                elif "IGIC" in tax_line.name:
                    pol_item["IGIC"] += tax_line.amount * factor
                else:
                    pol_item["IESE"] += tax_line.amount * factor
            flux = 0
            for line in fact.linia_ids:
                if line.tipus in ("altres", "cobrament") and line.product_id.code == "PBV":
                    flux += line.price_subtotal * factor
                    pol_item["Flux Solar"] += line.price_subtotal * factor
            pol_item["Altres"] += (fact.total_altres * factor) - flux
            pol_item["TOTAL"] += fact.amount_total * factor

            item_values = pol_item.items()
            for key, value in item_values:
                if isinstance(value, float):
                    pol_item[key] = round(value, 2)
            items[fact.polissa_id.id] = pol_item

        return items if len(fact_ids) > 0 else {}

    def action_crear_informe(self, cursor, uid, ids, context=None):
        if not context:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]

        wiz = self.browse(cursor, uid, ids[0])

        wiz_values = wiz.read()[0]

        to_date = wiz_values["to_date"]
        from_date = wiz_values["from_date"]

        contracts = wiz_values["contracts"]
        contracts_list = []
        if contracts:
            contracts_list = contracts.split(",")

        pol_ids = self.get_contract_ids(cursor, uid, contracts_list)

        items = self.find_invoices(cursor, uid, ids, pol_ids, from_date, to_date)

        if len(items) > 0:
            file_name, mfile = self.create_csv(items.values(), from_date, to_date)
            wiz.write({"file_name": file_name, "file": mfile, "state": "done"})
        else:
            raise osv.except_osv(
                _("No s'ha generat l'informe !"),
                _("No s'han trobat factures per aquestes dates i/o contractes!"),
            )

    def set_to_date(self, start_date):
        day_initial_date = int(start_date.strftime("%d"))
        return start_date - timedelta(days=day_initial_date)

    def set_from_date(self, start_date):
        to_date = self.set_to_date(start_date)
        return to_date - relativedelta(months=12) + timedelta(days=1)

    def onchange_start_date(self, cursor, uid, ids, start_date, context=None):
        res = {"value": {}}
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            res["value"]["to_date"] = datetime.strftime(self.set_to_date(start_date), "%Y-%m-%d")
            res["value"]["from_date"] = datetime.strftime(
                self.set_from_date(start_date), "%Y-%m-%d"
            )
        return res

    _columns = {
        "state": fields.char("Estat", size=16, required=True),
        "start_date": fields.date("Data inici càlcul", required=True),
        "from_date": fields.date("Data inici inf.", required=True),
        "to_date": fields.date("Data fi inf.", required=True),
        "contracts": fields.char(
            "Contractes",
            size=256,
            required=False,
            help="Entrar números de pòlissa separats amb una coma (Exemple: 0001453, 0001460)",
        ),
        "file": fields.binary("Informe"),
        "file_name": fields.char("Nom fitxer", size=32),
    }

    _defaults = {
        "state": lambda *a: "init",
        "start_date": datetime.strftime(datetime.today(), "%Y-%m-%d"),
    }


WizardInformeDadesDesagregades()
