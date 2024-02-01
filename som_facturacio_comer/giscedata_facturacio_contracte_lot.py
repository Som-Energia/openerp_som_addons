# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from osv import osv, fields
from tools.translate import _
from gestionatr.defs import TABLA_113
import re
import logging

TIPO_AUTOCONSUMO_SEL = [(ac[0], "[{}] - {}".format(ac[0], ac[1])) for ac in TABLA_113]


class GiscedataFacturacioContracteLot(osv.osv):
    """Contracte Lot per comercialitzadora."""

    _name = "giscedata.facturacio.contracte_lot"
    _inherit = "giscedata.facturacio.contracte_lot"

    _STORE_WHEN_INVOICE_ADDED = {
        "giscedata.facturacio.contracte_lot": (
            lambda self, cr, uid, ids, context=None: ids,
            ["n_factures"],
            10,
        )
    }

    _STORE_WHEN_ERRORS_ADDED = {
        "giscedata.facturacio.contracte_lot": (
            lambda self, cr, uid, ids, context=None: ids,
            ["status", "state"],
            10,
        )
    }

    def total_incidencies(self, cr, uid, id, context=None):
        status = self.read(cr, uid, id, ["status"])["status"]
        if status:
            r1 = re.findall(r"(\[[a-zA-Z]{1,2}[\d]{2,3}\])", status)
            return len(set(r1))
        return 0

    def date_invoice(self, cr, uid, id, context=None):
        """Retorna la data de les factures"""
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        contracte_lot_data = self.read(cr, uid, id, ["lot_id", "polissa_id"])
        date_invoice = 0
        try:
            lot_id = contracte_lot_data["lot_id"][0]
            pol_id = contracte_lot_data["polissa_id"][0]
            fact_ids = fact_obj.search(
                cr, uid, [("lot_facturacio", "=", lot_id), ("polissa_id", "=", pol_id)]
            )
            if fact_ids:
                date_invoice = fact_obj.read(cr, uid, fact_ids[0], ["date_invoice"])["date_invoice"]
        except Exception as e:
            logger = logging.getLogger("openerp" + __name__)
            logger.error(
                "Error calculant el camp funcio date_invoice del contracte_lot ID {}. {}".format(
                    id, e
                )
            )

        return date_invoice

    def _get_fact_origen(self, cr, uid, id, context=None):
        if isinstance(id, list):
            id = id[0]

        fact_obj = self.pool.get("giscedata.facturacio.factura")

        contracte_lot_data = self.read(cr, uid, id, ["lot_id", "polissa_id"])
        lot_id = contracte_lot_data["lot_id"][0]
        pol_id = contracte_lot_data["polissa_id"][0]

        fact_ids = fact_obj.search(
            cr, uid, [("lot_facturacio", "=", lot_id), ("polissa_id", "=", pol_id)]
        )

        if fact_ids:
            for fact_id in fact_ids:
                energy_readings_o = self.pool.get("giscedata.facturacio.lectures.energia")
                reading_origin_o = self.pool.get("giscedata.lectures.origen")

                energy_readings_f = ["tipus", "name", "factura_id", "origen_id", "ajust"]
                dmn = [("factura_id", "=", fact_id)]

                energy_reading_vs = energy_readings_o.q(cr, uid).read(energy_readings_f).where(dmn)
                if not energy_reading_vs:
                    return "Sense Lectures"
                for energy_reading_v in energy_reading_vs:
                    estimada_ids = reading_origin_o.search(cr, uid, [("codi", "=", "40")])
                    if energy_reading_v["origen_id"] in estimada_ids:
                        return "Estimada"
            return "Real"
        return "Sense Factures"

    def consum_facturat(self, cr, uid, id, context=None):
        n_factures = self.read(cr, uid, id, ["n_factures"])["n_factures"]
        if n_factures:
            origen = self._get_fact_origen(cr, uid, id)
            return origen
        return "Sense Factures"

    def te_generation(self, cr, uid, id, context=None):
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        contracte_lot_data = self.read(cr, uid, id, ["lot_id", "polissa_id"])
        try:
            lot_id = contracte_lot_data["lot_id"][0]
            pol_id = contracte_lot_data["polissa_id"][0]
            fact_ids = fact_obj.search(
                cr, uid, [("lot_facturacio", "=", lot_id), ("polissa_id", "=", pol_id)]
            )
            for fact_id in fact_ids:
                te_generation = fact_obj.read(cr, uid, fact_id, ["is_gkwh"])["is_gkwh"]
                if te_generation:
                    return True
        except Exception as e:
            logger = logging.getLogger("openerp" + __name__)
            logger.error(
                "Error calculant el camp funcio te_generation del contracte_lot ID {}. {}".format(
                    id, e
                )
            )

    def _ff_gran_contracte(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        pcat_obj = self.pool.get("giscedata.polissa.category")
        pcat_ids = pcat_obj.search(cr, uid, [("name", "=", "Gran Contracte")])
        for id in ids:
            contracte_lot_data = self.browse(cr, uid, id)
            polissa_id = contracte_lot_data.polissa_id
            if pcat_ids and pcat_ids[0] in [x.id for x in polissa_id.category_id]:
                res[id] = True
        return res

    def _get_clots_from_polissa(self, cr, uid, ids, context=None):
        """ids són els ids de pòlisses que han canviat. Hem de retornar els ids de clot que cal recalcular"""
        cl_obj = self.pool.get("giscedata.facturacio.contracte_lot")
        return cl_obj.search(cr, uid, [("polissa_id", "in", ids)])

    def data_final(self, cr, uid, id, context=None):
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        contracte_lot_data = self.read(cr, uid, id, ["lot_id", "polissa_id"])
        try:
            lot_id = contracte_lot_data["lot_id"][0]
            pol_id = contracte_lot_data["polissa_id"][0]
            fact_ids = fact_obj.search(
                cr,
                uid,
                [("lot_facturacio", "=", lot_id), ("polissa_id", "=", pol_id)],
                order="data_final desc",
                limit=1,
            )
            if fact_ids:
                return fact_obj.read(cr, uid, fact_ids[0], ["data_final"])["data_final"]
        except Exception as e:
            logger = logging.getLogger("openerp" + __name__)
            logger.error(
                "Error calculant el camp funcio te_generation del contracte_lot ID %s: %s ", id, e
            )

    def _ff_import_factures(self, cr, uid, ids, name, args, context=None):
        factura_o = self.pool.get("giscedata.facturacio.factura")
        res = {}

        for id in ids:
            #  per cada contracte lot
            info = self.read(cr, uid, id, ["polissa_id", "lot_id"])

            #  obtenim les factures relacionades
            factura_ids = factura_o.search(
                cr,
                uid,
                [
                    ("polissa_id", "=", info["polissa_id"][0]),
                    ("lot_facturacio", "=", info["lot_id"][0]),
                ],
            )

            import_total = 0
            #  sumem els amount_total de les factures
            for factura_id in factura_ids:
                amount_total = factura_o.read(cr, uid, factura_id, ["amount_total"])["amount_total"]
                if amount_total:
                    import_total += amount_total
            res[id] = import_total

        return res

    def _ff_update_fields(self, cr, uid, ids, name, args, context=None):
        res = {id: {"total_incidencies": 0} for id in ids}
        for id in ids:
            res[id]["total_incidencies"] = self.total_incidencies(cr, uid, id)
            res[id]["date_invoice"] = self.date_invoice(cr, uid, id)
            res[id]["te_generation"] = self.te_generation(cr, uid, id)
            res[id]["data_final"] = self.data_final(cr, uid, id)
            res[id]["consum_facturat"] = self.consum_facturat(cr, uid, id)
        return res

    _columns = {
        "polissa_distribuidora": fields.related(
            "polissa_id",
            "distribuidora",
            type="many2one",
            relation="res.partner",
            string="Distribuidora",
            readonly=True,
        ),
        "autoconsum": fields.related(
            "polissa_id",
            "autoconsumo",
            type="selection",
            selection=TIPO_AUTOCONSUMO_SEL,
            string="Autoconsum",
            readonly=True,
        ),
        "tarifaATR": fields.related(
            "polissa_id", "tarifa", "name", type="char", string=_("Tarifa Accés"), readonly=True
        ),
        "llista_preu": fields.related(
            "polissa_id",
            "llista_preu",
            "name",
            type="char",
            string=_("Tarifa Comercialitzadora"),
            readonly=True,
        ),
        "total_incidencies": fields.function(
            _ff_update_fields,
            multi="totals",
            string="Nombre total dincidencies",
            type="integer",
            store=_STORE_WHEN_ERRORS_ADDED,
            method=True,
        ),
        "date_invoice": fields.function(
            _ff_update_fields,
            multi="totals",
            string="Data de la factura",
            type="date",
            size=12,
            store=_STORE_WHEN_INVOICE_ADDED,
            method=True,
        ),
        "consum_facturat": fields.function(
            _ff_update_fields,
            multi="totals",
            string="Origen consum facturat",
            type="char",
            size=32,
            store=_STORE_WHEN_INVOICE_ADDED,
            method=True,
        ),
        "data_alta_contracte": fields.related(
            "polissa_id", "data_alta", type="date", string=_("Data alta contracte"), readonly=True
        ),
        "data_ultima_lectura": fields.related(
            "polissa_id",
            "data_ultima_lectura",
            type="date",
            string=_("Data ultima lectura real facturada"),
            readonly=True,
        ),
        "info_gestions_massives": fields.related(
            "polissa_id",
            "info_gestions_massives",
            type="text",
            string=_("Gestions Massives"),
            readonly=True,
        ),
        "mode_facturacio": fields.related(
            "polissa_id",
            "facturacio_potencia",
            type="char",
            string="Mode facturació",
            readonly=True,
        ),
        "canal_enviament": fields.related(
            "polissa_id", "enviament", type="char", string="Canal enviament", readonly=True
        ),
        "te_generation": fields.function(
            _ff_update_fields,
            multi="totals",
            string="Factura té generation",
            type="boolean",
            store=_STORE_WHEN_INVOICE_ADDED,
            method=True,
        ),
        "gran_contracte": fields.function(
            _ff_gran_contracte,
            string="Gran Contract",
            method=True,
            type="boolean",
            store={
                "giscedata.polissa": (_get_clots_from_polissa, ["category_id"], 10),
                "giscedata.facturacio.contracte_lot": (
                    lambda self, cr, uid, ids, context=None: ids,
                    ["polissa_id"],
                    10,
                ),
            },
        ),
        "data_final": fields.function(
            _ff_update_fields,
            multi="totals",
            string="Data final factura",
            type="date",
            method=True,
            store=_STORE_WHEN_INVOICE_ADDED,
        ),
        "te_generation_polissa": fields.related(
            "polissa_id",
            "te_assignacio_gkwh",
            type="boolean",
            relation="giscedata.polissa",
            string=_("Pòlissa té generation"),
            readonly=True,
        ),
        "data_alta_auto": fields.related(
            "polissa_id",
            "data_alta_autoconsum",
            type="date",
            relation="giscedata.polissa",
            string=_("Data alta autoconsum"),
            readonly=True,
        ),
        "n_retrocedir_lot": fields.integer(
            string="Num retrocedir",
            help="Número de vegades que la pòlissa en el lot s'ha retrocedit de lot",
            readonly=True,
        ),
        "import_factures": fields.function(
            _ff_import_factures, string="Import factures", type="float", method=True
        ),
    }

    _defaults = {
        "total_incidencies": lambda *a: 0,
        "n_retrocedir_lot": lambda *a: 0,
    }


GiscedataFacturacioContracteLot()
