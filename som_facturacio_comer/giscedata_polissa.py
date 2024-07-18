# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _
from giscedata_facturacio.giscedata_polissa import INTERVAL_INVOICING_FIELDS

INTERVAL_INVOICING_FIELDS += ['indexed_formula']

class GiscedataPolissa(osv.osv):
    """Pòlissa per afegir el camp teoric_maximum_consume_gc."""

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def search_factura(self, cursor, uid, ids, data_inici, data_final, context=None):
        if context is None:
            context = {}
        origen_obj = self.pool.get("giscedata.bateria.virtual.origen")
        origen_data = (
            origen_obj.q(cursor, uid)
            .read(["data_inici_descomptes"])
            .where([("origen_ref", "=", "giscedata.polissa,{}".format(str(ids[0])))])
        )

        if len(origen_data):
            data_inici_origen = origen_data[0].get("data_inici_descomptes")
        else:
            data_inici_origen = data_inici

        factura_obj = self.pool.get("giscedata.facturacio.factura")
        factura_ids = factura_obj.search(
            cursor,
            uid,
            [
                ("polissa_id", "=", ids[0]),
                ("data_inici", ">=", data_inici_origen),
                ("data_inici", "<=", data_final),
                ("state", "in", ("paid", "open")),
                ("type", "in", ("out_invoice", "out_refund")),
            ],
            context=context,
        )
        return factura_ids

    def _ff_observations_first_line(self, cursor, uid, ids, args, fields, context=None):
        if context is None:
            context = {}
        res = dict.fromkeys(ids, False)
        for pol_id in ids:
            observacions = self.read(
                cursor, uid, pol_id, ["observacions_comptables"], context=context
            )["observacions_comptables"]
            if observacions:
                res[pol_id] = observacions.splitlines()[0]

        return res

    def _ff_data_ultima_factura(self, cursor, uid, ids, args, fields, context=None):
        if context is None:
            context = {}
        fact_obj = self.pool.get("giscedata.facturacio.factura")
        res = dict.fromkeys(ids, False)
        for pol_id in ids:
            fact_date = (
                fact_obj.q(cursor, uid)
                .read(["date_invoice"], order_by=["invoice_id.date_invoice.desc"], limit=1)
                .where([("polissa_id", "=", pol_id)])
            )
            if len(fact_date):
                res[pol_id] = fact_date[0].get("date_invoice")

        return res

    def get_modcontractual_intervals(self, cursor, uid, polissa_id, data_inici, data_final, context=None):
        if context is None:
            context = {}

        modcon_o = self.pool.get('giscedata.polissa.modcontractual')
        price_o = self.pool.get('product.pricelist')
        dates_de_tall = super(GiscedataPolissa, self).get_modcontractual_intervals(cursor, uid, polissa_id, data_inici,
                                                                                   data_final, context)

        llista_preu_dades = []
        indexed_formula_old = ""
        changes = {}
        dates = {}

        for mod_data in sorted(dates_de_tall.keys()):
            values = ['llista_preu', 'data_inici', 'data_final']
            modcon_dades = modcon_o.read(cursor, uid, dates_de_tall[mod_data]['id'], values, context=context)

            llista_preu_dades.append((
                dates_de_tall[mod_data]['id'],
                mod_data,
                modcon_dades['llista_preu'][0],
                modcon_dades['data_inici'],
                modcon_dades['data_final']
            ))
        llista_preus = [dada[2] for dada in llista_preu_dades]
        if len(set(llista_preus)) > 1:

            for modcon_id, mod_data, llista_preu_id, data_inici, data_final in llista_preu_dades:
                indexed_formula = price_o.read(cursor, uid, llista_preu_id, ['indexed_formula'],
                                               context=context)['indexed_formula']

                if indexed_formula != indexed_formula_old and indexed_formula_old != "":
                    changes[modcon_id] = ['indexed_formula']
                    dates[modcon_id] = (data_inici, data_final)

                    # crear nou registre
                    dates_de_tall[mod_data].append({
                        'id': modcon_id,
                        'changes': changes,
                        'dates': dates
                    })

                indexed_formula_old = indexed_formula

        return dates_de_tall

    _columns = {
        "teoric_maximum_consume_gc": fields.float(
            digits=(8, 2),
            string="Teoric maximum consume Grans Contractes",
            help=u"Màxim consum mensual teòric d'un contracte amb categoria Gran Consum associat a la validació SF03.",  # noqa: E501
        ),
        "observacions_comptables": fields.text("Accounting Observations"),
        "resum_observacions_comptables": fields.function(
            _ff_observations_first_line,
            type="text",
            method=True,
            string=_("Accounting observations"),
        ),
        "data_ultima_factura": fields.function(
            _ff_data_ultima_factura, type="date", method=True, string=_("Last invoice date")
        ),
    }


GiscedataPolissa()


class GiscedataPolissaModcontractual(osv.osv):
    """Modificació Contractual d'una Pòlissa."""

    _name = "giscedata.polissa.modcontractual"
    _inherit = "giscedata.polissa.modcontractual"

    _columns = {
        "teoric_maximum_consume_gc": fields.float(
            digits=(8, 2), string="Teoric maximum consume Grans Contractes"
        )
    }


GiscedataPolissaModcontractual()
