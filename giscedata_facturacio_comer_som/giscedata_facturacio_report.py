# -*- coding: utf-8 -*-
from osv import osv
from yamlns import namespace as ns
from datetime import datetime, timedelta
import inspect
from tools.translate import _
import json
from operator import attrgetter
from collections import Counter
import base64

SENSE_EXCEDENTS = ["31", "32", "33"]

agreementPartners = {
    "S019753": {"logo": "logo_S019753.png"},
    "S076331": {"logo": "logo_S076331.png"},
}

new_tariff_with_power_tolls_date = "2021-04-01"
BOE17_2021_dates = {
    "start": "2021-09-16",
    "end": "2021-12-31",
}

factors_kp_change_calculation_date = "2021-10-18"

mean_zipcode_consumption_dates = {
    "start": "2022-12-01",
    "end": "2050-12-31",
}

show_iva_column_date = "2023-10-10"

auvi_logo_attachment_name = "auvi_logo.png"

compl_cat = "Facturació Complementaria imputada per part de la Distribuïdora"
compl_cas = "Facturación Complementaria imputada por parte de la Distribuidora"


# -----------------------------------
# helper functions
# -----------------------------------


def is_leap_year(year):
    if year % 4 == 0:
        if year % 100 == 0:
            return year % 400 == 0
        else:
            return True
    return False


def leap_replace(data, year):
    if data.month == 2 and data.day == 29 and not is_leap_year(year):
        return datetime(year, 2, 28)
    return datetime(year, data.month, data.day)


def get_renovation_date(data_alta, today):
    alta = datetime.strptime(data_alta, "%Y-%m-%d")
    reno = leap_replace(alta, today.year)
    if reno < today:
        reno = leap_replace(alta, today.year + 1)
    return reno.strftime("%Y-%m-%d")


def te_autoconsum(fact, pol):
    ctxt = {"date": fact.data_final}
    return pol.te_autoconsum(amb_o_sense_excedents=2, context=ctxt)


def te_autoconsum_sense_excedents(fact, pol):
    ctxt = {"date": fact.data_final}
    return pol.te_autoconsum(amb_o_sense_excedents=1, context=ctxt)


def te_autoconsum_amb_excedents(fact, pol):
    ctxt = {"date": fact.data_final}
    return pol.te_autoconsum(amb_o_sense_excedents=3, context=ctxt)


def te_autoconsum_collectiu(fact, pol):
    if te_autoconsum(fact, pol):
        for cups_autoconsum in pol.autoconsum_cups_ids:
            if cups_autoconsum.collectiu:
                return True
    return False


def te_autoconsum_no_collectiu(fact, pol):
    if te_autoconsum(fact, pol):
        if len(pol.autoconsum_cups_ids) == 0:  # old cases not migrated
            return True

        for cups_autoconsum in pol.autoconsum_cups_ids:
            if cups_autoconsum.collectiu is False:
                return True
    return False


def te_gkwh(fact):
    return fact.is_gkwh


def te_quartihoraria(pol):
    return pol.tipo_medida in ["01", "02", "03"]


def is_6X(pol):
    return pol.tarifa.codi_ocsum in ("012", "013", "014", "015", "016", "017")


def is_3X(pol):
    return pol.tarifa.codi_ocsum in ("003", "011", "014", "015", "016", "017")


def is_2X(pol):
    return pol.tarifa.codi_ocsum in ("001", "005", "004", "007", "006", "008")


def is_DHS(pol):
    return pol.tarifa.codi_ocsum in ("007", "008")


def is_DHA(pol):
    return pol.tarifa.codi_ocsum in ("004", "006")


def is_TD(pol):
    return pol.tarifa.codi_ocsum in ("018", "019", "020", "021", "022", "023", "024", "025")


def is_2XTD(pol):
    return pol.tarifa.codi_ocsum in ("018")


def is_3XTD(pol):
    return pol.tarifa.codi_ocsum in ("019", "024")


def is_6XTD(pol):
    return pol.tarifa.codi_ocsum in ("020", "021", "022", "023", "025")


def is_indexed(fact):
    return "Indexada" in fact.llista_preu.name


def has_iva_column(fact):
    return val(fact.date_invoice) >= show_iva_column_date


def val(object):
    try:
        return object.val
    except Exception:
        return object


def dateformat(date):
    return datetime.strptime(val(date), "%Y-%m-%d").strftime("%d/%m/%Y")


def counter_to_dict(lines, periods, keyswap):
    data = {}
    for p in periods:
        if p in lines:
            item = {}
            for k in lines[p].keys():
                item[keyswap.get(k, k)] = lines[p][k]
            data[p] = item
    return data


def get_tariffs_from_libfacturacioatr():
    from libfacturacioatr import tarifes

    tariffs = [x for x in dir(tarifes) if x.startswith("Tarifa")]
    codes_tariffs = {}
    for tariff in tariffs:
        obj = eval("tarifes." + tariff)
        if hasattr(obj, "code"):
            codes_tariffs[obj.code] = obj

    return codes_tariffs


def get_tariff_from_libfacturacioatr(code):
    tariffs = get_tariffs_from_libfacturacioatr()
    return tariffs.get(code, None)


def get_iva_line(line):
    for tax in line.invoice_line_tax_id:
        if "IVA" in tax.name:
            return tax.name[:].replace("IVA", "").split()[0].strip()
        if "IGIC" in tax.name and "Exent" in tax.name:
            return ""
        if "IGIC" in tax.name:
            return tax.name[:].replace("IGIC", "").split()[0].strip()
    return ""


def clean_tax_name(tax_name):
    return tax_name.replace("(Vendes)", "").strip()


def get_reactive_lines_clean(fact):
    return [l for l in fact.linies_reactiva if  # noqa: E741
            compl_cat not in l.name and compl_cas not in l.name]  # noqa: E741


class GiscedataFacturacioFacturaReport(osv.osv):

    _auto = False
    _name = "giscedata.facturacio.factura.report"
    _inherit = "giscedata.facturacio.factura.report"

    def __init__(self, pool, cursor):
        super(GiscedataFacturacioFacturaReport, self).__init__(pool, cursor)
        self.readings_cache = {}
        self.historic_cache = {}
        self.text_real = _(u"real")
        self.text_estimada_distri = _(u"estimada distribuïdora")
        self.text_calculada_som = _(u"calculada per Som Energia")

    def get_components_data(self, cursor, uid, ids, context=None):
        """
        Obtains the invoice component info.
        :param cursor:
        :param uid:
        :param ids: <giscedata.facturacio.factura> ids
        :param context:
        :return: Dictionary where the key is the invoice id and the value is a
            dictionary with the following structure:
                - Component data A
                - Component data B
                ....
                - Component data Z
            Each component data _ consists in a dictionary with the mako
            component data needs.
        """
        self.cursor = cursor
        self.uid = uid

        if not isinstance(ids, list):
            ids = [ids]

        if context == None:  # noqa: E711
            context = {}

        fac_obj = self.pool.get("giscedata.facturacio.factura")
        pol_obj = self.pool.get("giscedata.polissa")

        fill_methods = self.find_all_components_data(context)
        res = {}
        for fac_id in ids:
            fac = fac_obj.browse(cursor, uid, fac_id, context)
            if context and "not_testing_old_polissa" in context:
                ctxt = {}
            else:
                ctxt = context
                ctxt["date"] = val(fac.data_final)
            pol = pol_obj.browse(cursor, uid, fac.polissa_id.id, ctxt)
            res[fac_id] = self.fill_all_components_data(fill_methods, fac, pol, ctxt)
        return res

    def get_report_data(self, cursor, uid, objects, context=None):
        ids = [fact.id for fact in objects]
        return self.get_components_data(cursor, uid, ids, context)

    def get_components_data_yaml(self, cursor, uid, ids, context=None):
        import traceback

        try:
            return ns(self.get_components_data(cursor, uid, ids, context)).dump()
        except Exception as e:
            tb = traceback.format_exc()
            return str(e) + str(tb)

    def find_all_components_data(self, context=None):
        """
        Searches all the class methods that generates component data
        """
        head = "get_component_"
        tail = "_data"
        n_head = len(head)
        n_tail = len(tail) * (-1)
        fill_methods = dict(
            (name[n_head:n_tail], func)
            for name, func in inspect.getmembers(self)
            if name.startswith(head) and name.endswith(tail)
        )
        if context and "allow_list" in context:
            fill_methods = {a: b for (a, b) in fill_methods.items() if a in context["allow_list"]}
        if context and "deny_list" in context:
            fill_methods = {
                a: b for (a, b) in fill_methods.items() if a not in context["deny_list"]
            }

        return fill_methods

    def fill_all_components_data(self, fill_methods, fac, pol, ctxt):
        """
        Executes the given list of class methods and generates a yamlns
        namespace with all the results.
        """
        self.cleanup_data(fac)
        self.context = ctxt

        data = {}
        for name, method in fill_methods.items():
            data[name] = method(fac, pol)

        self.cleanup_data(fac)
        return ns.loads(ns(data).dump())

    def cleanup_data(self, fact):
        self.del_historic_data(fact)
        self.del_readings_data(fact)

    def get_origen_lectura(self, lectura):
        """Busquem l'origen de la lectura cercant-la a les lectures de facturació"""
        res = {lectura.data_actual: "", lectura.data_anterior: ""}

        lectura_obj = lectura.pool.get("giscedata.lectures.lectura")
        tarifa_obj = lectura.pool.get("giscedata.polissa.tarifa")
        origen_obj = lectura.pool.get("giscedata.lectures.origen")
        origen_comer_obj = lectura.pool.get("giscedata.lectures.origen_comer")

        # Busquem la tarifa
        tarifa_id = tarifa_obj.search(self.cursor, self.uid, [("name", "=", lectura.name[:-5])])
        if tarifa_id:
            estimada_id = origen_obj.search(self.cursor, self.uid, [("codi", "=", "40")])[0]
            sin_lectura_id = origen_obj.search(self.cursor, self.uid, [("codi", "=", "99")])[0]
            estimada_som_id = origen_comer_obj.search(
                self.cursor, self.uid, [("codi", "=", "ES")])[0]
            calculada_som_id = origen_obj.search(self.cursor, self.uid, [("codi", "=", "LC")])
            calculada_som_id = calculada_som_id[0] if calculada_som_id else None
            tipus = lectura.tipus == "activa" and "A" or "R"

            search_vals = [
                ("comptador", "=", lectura.comptador),
                ("periode.name", "=", lectura.name[-3:-1]),
                ("periode.tarifa", "=", tarifa_id[0]),
                ("tipus", "=", tipus),
                ("name", "in", [lectura.data_actual, lectura.data_anterior]),
            ]
            lect_ids = lectura_obj.search(self.cursor, self.uid, search_vals)
            lect_vals = lectura_obj.read(
                self.cursor, self.uid, lect_ids, ["name", "origen_comer_id", "origen_id"]
            )
            for lect in lect_vals:
                # En funció dels origens, escrivim el text
                # Si Estimada (40) o Sin Lectura (99) i Estimada (ES): Estimada Somenergia
                # Si Estimada (40) o Sin Lectura (99) i F1/Q1/etc...(!ES): Estimada distribuïdora
                # La resta: Real
                origen_txt = self.text_real
                if lect["origen_id"][0] in [estimada_id, sin_lectura_id]:
                    if lect["origen_comer_id"][0] == estimada_som_id:
                        origen_txt = self.text_calculada_som
                    else:
                        origen_txt = _(u"estimada distribuïdora")
                if lect["origen_id"][0] == calculada_som_id:
                    origen_txt = self.text_estimada_distri
                res[lect["name"]] = "%s" % (origen_txt)

        return res

    def get_readings_data(self, fact):
        if fact.id not in self.readings_cache:
            self.readings_cache[fact.id] = self.get_readings_data_fill(fact)

        return self.readings_cache[fact.id]

    def del_readings_data(self, fact):
        self.readings_cache.pop(fact.id, None)

    def get_readings_data_fill(self, fact):  # noqa: C901
        """
        Calculate the active and reactive energy readings data
        """

        periodes_a = sorted(
            list(
                set(
                    [
                        lectura.name[-3:-1]
                        for lectura in fact.lectures_energia_ids
                        if lectura.tipus == "activa" and lectura.magnitud == "AE"
                    ]
                )
            )
        )
        periodes_r = sorted(
            list(
                set(
                    [
                        lectura.name[-3:-1]
                        for lectura in fact.lectures_energia_ids
                        if lectura.tipus == "reactiva" and lectura.magnitud == "R1"
                    ]
                )
            )
        )
        periodes_c = sorted(
            list(
                set(
                    [
                        lectura.name[-3:-1]
                        for lectura in fact.lectures_energia_ids
                        if lectura.tipus == "reactiva" and lectura.magnitud == "R4"
                    ]
                )
            )
        )
        periodes_g = sorted(
            list(
                set(
                    [
                        lectura.name[-3:-1]
                        for lectura in fact.lectures_energia_ids
                        if lectura.tipus == "activa" and lectura.magnitud == "AS"
                    ]
                )
            )
        )

        lectures_a = {}
        lectures_r = {}
        lectures_c = {}
        lectures_g = {}

        lectures_real_a = {}
        lectures_real_r = {}
        lectures_real_c = {}
        lectures_real_g = {}

        for lectura in fact.lectures_energia_ids:
            origens = self.get_origen_lectura(lectura)
            if lectura.tipus == "activa" and lectura.magnitud == "AE":
                lectures_a.setdefault(lectura.comptador, [])
                lectures_a[lectura.comptador].append(
                    (
                        lectura.name[-3:-1],
                        val(lectura.lect_anterior),
                        val(lectura.lect_actual),
                        val(lectura.consum),
                        dateformat(lectura.data_anterior),
                        dateformat(lectura.data_actual),
                        origens[lectura.data_anterior],
                        origens[lectura.data_actual],
                        val(lectura.ajust),
                        val(lectura.motiu_ajust),
                    )
                )
                lectura_real = self.get_last_active_lectura_real_from_pool(lectura)
                lectures_real_a.setdefault(lectura.comptador, [])
                if len(lectura_real) > 0:
                    lectures_real_a[lectura.comptador].append(
                        (
                            lectura.name[-3:-1],
                            val(lectura_real[0]['lectura']),
                            dateformat(lectura_real[0]['name']),
                        )
                    )
                else:
                    lectura_real = self.get_last_active_lectura_real_from_lectures(lectura)
                    if len(lectura_real) > 0:
                        lectures_real_a[lectura.comptador].append(
                            (
                                lectura.name[-3:-1],
                                val(lectura_real[0]['lectura']),
                                dateformat(lectura_real[0]['name']),
                            )
                        )

            elif lectura.tipus == "activa" and lectura.magnitud == "AS":
                lectures_g.setdefault(lectura.comptador, [])
                lectures_g[lectura.comptador].append(
                    (
                        lectura.name[-3:-1],
                        val(lectura.lect_anterior),
                        val(lectura.lect_actual),
                        val(lectura.consum),
                        dateformat(lectura.data_anterior),
                        dateformat(lectura.data_actual),
                        origens[lectura.data_anterior],
                        origens[lectura.data_actual],
                        val(lectura.ajust),
                        val(lectura.motiu_ajust),
                    )
                )
                lectura_real = self.get_last_active_lectura_real_from_pool(lectura)
                lectures_real_g.setdefault(lectura.comptador, [])
                if len(lectura_real) > 0:
                    lectures_real_g[lectura.comptador].append(
                        (
                            lectura.name[-3:-1],
                            val(lectura_real[0]['lectura']),
                            dateformat(lectura_real[0]['name']),
                        )
                    )
                else:
                    lectura_real = self.get_last_active_lectura_real_from_lectures(lectura)
                    if len(lectura_real) > 0:
                        lectures_real_g[lectura.comptador].append(
                            (
                                lectura.name[-3:-1],
                                val(lectura_real[0]['lectura']),
                                dateformat(lectura_real[0]['name']),
                            )
                        )

            elif lectura.tipus == "reactiva" and lectura.magnitud == "R1":
                lectures_r.setdefault(lectura.comptador, [])
                lectures_r[lectura.comptador].append(
                    (
                        lectura.name[-3:-1],
                        val(lectura.lect_anterior),
                        val(lectura.lect_actual),
                        val(lectura.consum),
                        dateformat(lectura.data_anterior),
                        dateformat(lectura.data_actual),
                        origens[lectura.data_anterior],
                        origens[lectura.data_actual],
                    )
                )
                lectura_real = self.get_last_reactive_lectura_real_from_pool(lectura)
                lectures_real_r.setdefault(lectura.comptador, [])
                if len(lectura_real) > 0:
                    lectures_real_r[lectura.comptador].append(
                        (
                            lectura.name[-3:-1],
                            val(lectura_real[0]['lectura']),
                            dateformat(lectura_real[0]['name']),
                        )
                    )
                else:
                    lectura_real = self.get_last_reactive_lectura_real_from_lectures(lectura)
                    if len(lectura_real) > 0:
                        lectures_real_r[lectura.comptador].append(
                            (
                                lectura.name[-3:-1],
                                val(lectura_real[0]['lectura']),
                                dateformat(lectura_real[0]['name']),
                            )
                        )

            elif lectura.tipus == "reactiva" and lectura.magnitud == "R4":
                lectures_c.setdefault(lectura.comptador, [])
                lectures_c[lectura.comptador].append(
                    (
                        lectura.name[-3:-1],
                        val(lectura.lect_anterior),
                        val(lectura.lect_actual),
                        val(lectura.consum),
                        dateformat(lectura.data_anterior),
                        dateformat(lectura.data_actual),
                        origens[lectura.data_anterior],
                        origens[lectura.data_actual],
                    )
                )
                lectura_real = self.get_last_reactive_lectura_real_from_pool(lectura)
                lectures_real_c.setdefault(lectura.comptador, [])
                if len(lectura_real) > 0:
                    lectures_real_c[lectura.comptador].append(
                        (
                            lectura.name[-3:-1],
                            val(lectura_real[0]['lectura']),
                            dateformat(lectura_real[0]['name']),
                        )
                    )
                else:
                    lectura_real = self.get_last_reactive_lectura_real_from_lectures(lectura)
                    if len(lectura_real) > 0:
                        lectures_real_c[lectura.comptador].append(
                            (
                                lectura.name[-3:-1],
                                val(lectura_real[0]['lectura']),
                                dateformat(lectura_real[0]['name']),
                            )
                        )

        total_lectures_a = dict([(p, 0) for p in periodes_a])
        total_lectures_r = dict([(p, 0) for p in periodes_r])
        total_lectures_c = dict([(p, 0) for p in periodes_c])
        total_lectures_g = dict([(p, 0) for p in periodes_g])

        for c, ls in lectures_a.items():
            for l in ls:  # noqa: E741
                total_lectures_a[l[0]] += l[3]

        for c, ls in lectures_r.items():
            for l in ls:  # noqa: E741
                total_lectures_r[l[0]] += l[3]

        for c, ls in lectures_c.items():
            for l in ls:  # noqa: E741
                total_lectures_c[l[0]] += l[3]

        for c, ls in lectures_g.items():
            for l in ls:  # noqa: E741
                total_lectures_g[l[0]] += l[3]

        has_adjust_a = False
        for k, v in lectures_a.items():
            for l in v:  # noqa: E741
                if l[8] != 0:
                    has_adjust_a = True

        has_readings_g = False
        has_adjust_g = False
        for k, v in lectures_g.items():
            for l in v:  # noqa: E741
                if l[1] != 0 or l[2] != 0:
                    has_readings_g = True
                if l[8] != 0:
                    has_adjust_g = True

        return (
            periodes_a,
            periodes_r,
            periodes_c,
            periodes_g,
            lectures_a,
            lectures_r,
            lectures_c,
            lectures_g,
            lectures_real_a,
            lectures_real_r,
            lectures_real_c,
            lectures_real_g,
            total_lectures_a,
            total_lectures_r,
            total_lectures_c,
            total_lectures_g,
            has_adjust_a,
            has_adjust_g,
            has_readings_g,
        )

    def get_last_active_lectura_real_from_pool(self, lectura):
        return self._get_last_lectura_real(
            lectura, 'giscedata.lectures.lectura.pool', 'A', [7, 9, 22, 23])

    def get_last_active_lectura_real_from_lectures(self, lectura):
        return self._get_last_lectura_real(
            lectura, 'giscedata.lectures.lectura', 'A', [7, 9, 22, 23])

    def get_last_reactive_lectura_real_from_pool(self, lectura):
        return self._get_last_lectura_real(
            lectura, 'giscedata.lectures.lectura.pool', 'R', [7, 22, 23])

    def get_last_reactive_lectura_real_from_lectures(self, lectura):
        return self._get_last_lectura_real(
            lectura, 'giscedata.lectures.lectura', 'R', [7, 22, 23])

    def _get_last_lectura_real(self, lectura, model_name, type_, invalid_origins):
        lect_obj = self.pool.get(model_name)
        sql = lect_obj.q(self.cursor, self.uid).select(
            ['lectura', 'name'], order_by=('name.desc',), limit=1
        ).where([
            ('comptador', '=', lectura.comptador_id.id),
            ('tipus', '=', type_),
            ('periode.tarifa.name', '=', lectura.name.split(" ")[0]),
            ('periode.product_id.product_tmpl_id.name', '=', lectura.name.split("(")[1][:-1]),
            ('origen_id', 'not in', invalid_origins),
            ('name', '<', lectura.data_actual)
        ])
        self.cursor.execute(*sql)
        return self.cursor.dictfetchall()

    def get_historic_data(self, fact):
        if fact.id not in self.historic_cache:
            self.historic_cache[fact.id] = self.get_historic_data_fill(fact)

        return self.historic_cache[fact.id]

    def del_historic_data(self, fact):
        self.historic_cache.pop(fact.id, None)

    def get_historic_data_fill(self, fact):
        """
        Calculate the historic energy consumption data
        """
        historic_sql = """SELECT * FROM (
        SELECT mes AS mes,
        periode AS periode,
        sum(suma_fact) AS facturat,
        sum(suma_consum) AS consum,
        min(data_ini) AS data_ini,
        max(data_fin) AS data_fin
        FROM (
        SELECT f.polissa_id AS polissa_id,
            to_char(f.data_inici, 'YYYY/MM') AS mes,
            pt.name AS periode,
            COALESCE(SUM(il.quantity*(fl.tipus='energia')::int*(CASE WHEN i.type='out_refund' THEN -1 ELSE 1 END)),0.0) as suma_consum,
            COALESCE(SUM(il.price_subtotal*(fl.tipus='energia')::int*(CASE WHEN i.type='out_refund' THEN -1 ELSE 1 END)),0.0) as suma_fact,
            MIN(f.data_inici) data_ini,
            MAX(f.data_final) data_fin
            FROM
                    giscedata_facturacio_factura f
                    LEFT JOIN account_invoice i on f.invoice_id = i.id
                    LEFT JOIN giscedata_facturacio_factura_linia fl on f.id=fl.factura_id
                    LEFT JOIN account_invoice_line il on il.id=fl.invoice_line_id
                    LEFT JOIN product_product pp on il.product_id=pp.id
                    LEFT JOIN product_template pt on pp.product_tmpl_id=pt.id
            WHERE
                    fl.tipus = 'energia' AND
                    f.polissa_id = %(p_id)s AND
                    f.data_inici <= %(data_inicial)s AND
                    f.data_inici >= date_trunc('month', date %(data_final)s) - interval '%(interval)s month'
                    AND (fl.isdiscount IS NULL OR NOT fl.isdiscount)
                    AND i.type IN ('out_invoice','out_refund')
                    AND il.name not like '%%Facturaci%%Compleme%%Distri%%'
                    AND pt.name like 'P%%'
            GROUP BY
                    f.polissa_id, pt.name, f.data_inici
            ORDER BY f.data_inici DESC ) AS consums
        GROUP BY polissa_id, periode, mes
        ORDER BY mes DESC, periode ASC
        ) consums_ordenats
        ORDER BY mes ASC"""  # noqa: E501

        interval = 13 if fact.data_inici[0:7] == fact.data_final[0:7] else 14

        fact._cr.execute(
            historic_sql,
            {
                "p_id": fact.polissa_id.id,
                "data_inicial": fact.data_inici,
                "data_final": fact.data_final,
                "interval": interval,
            },
        )
        historic = fact._cr.dictfetchall()

        historic_graf = {}
        periodes_graf = []

        for row in historic:
            historic_graf.setdefault(row["mes"], {})
            historic_graf[row["mes"]].update({row["periode"]: row["consum"]})
            periodes_graf.append(row["periode"])

        periodes_graf = list(set(periodes_graf))

        historic_js = []
        for mes in sorted(historic_graf):
            consums = historic_graf[mes]
            p_js = {"mes": datetime.strptime(mes, "%Y/%m").strftime("%m/%y")}
            for p in periodes_graf:
                p_js.update({p: consums.get(p, 0.0)})
            historic_js.append(p_js)

        return (historic, historic_js)

    def get_distri_phone(self, polissa):
        """Per telèfons de ENDESA segons CUPS, aprofitant funció de switching"""
        sw_obj = polissa.pool.get("giscedata.switching")
        pa_obj = polissa.pool.get("res.partner.address")

        partner_id = sw_obj.partner_map(
            self.cursor, self.uid, polissa.cups, polissa.distribuidora.id
        )
        try:
            if partner_id:
                pa_ids = pa_obj.search(self.cursor, self.uid, [("partner_id", "=", partner_id)])
                return (
                    pa_obj.read(self.cursor, self.uid, [pa_ids[0]], ["phone"])[0]["phone"]
                    or polissa.distribuidora.address[0].phone
                )
            else:
                return polissa.distribuidora.address[0].phone
        except Exception:
            return polissa.distribuidora.www_phone

    def get_atr_price(self, fact, tarifa, linia):
        pricelist_obj = linia.pool.get("product.pricelist")
        uom_obj = linia.pool.get("product.uom")
        model_obj = fact.pool.get("ir.model.data")
        factura_obj = fact.pool.get("giscedata.facturacio.factura")
        period_obj = fact.pool.get("giscedata.polissa.tarifa.periodes")
        factura_linia_obj = fact.pool.get("giscedata.facturacio.factura.linia")

        tipus = linia.tipus
        uom_data = {"uom_name": linia.uos_id.name, "factor": 1}
        quantity = linia.quantity
        product_id = linia.product_id.id
        gkwh_products = factura_linia_obj.get_gkwh_products(self.cursor, self.uid)
        context_price = {}

        if tipus == "potencia":
            uom_data = {"uom_name": "kW/mes", "factor": 1}
        elif tipus == "reactiva":
            model_ids = model_obj.search(
                self.cursor,
                self.uid,
                [("module", "=", "giscedata_facturacio"), ("name", "=", "product_cosfi")],
            )
            product_id = model_obj.read(self.cursor, self.uid, model_ids[0], ["res_id"])["res_id"]
            quantity = linia.cosfi * 100
        elif linia.tipus == "generacio":
            return linia.price_unit
        elif product_id in gkwh_products:
            # GKWH product. We need atr product to calc "peatges"
            period_atr_id = factura_obj.get_fare_period(
                self.cursor, self.uid, product_id, context=self.context
            )
            product_id = period_obj.read(
                self.cursor, self.uid, period_atr_id, ["product_id"], context=self.context
            )["product_id"][0]

        uom_id = uom_obj.search(self.cursor, self.uid, [("name", "=", uom_data["uom_name"])])[0]
        context_price["date"] = linia.data_desde
        context_price["uom_name"] = uom_id

        atr_price = pricelist_obj.price_get(
            self.cursor,
            self.uid,
            [tarifa],
            product_id,
            quantity,
            fact.company_id.partner_id.id,
            context_price,
        )[tarifa]
        return atr_price

    def get_total_excess_power_consumed(self, fact):
        total_exces_consumida = 0.0
        exces_potencia = sorted(
            sorted(
                [l for l in fact.linia_ids if l.tipus == "exces_potencia"],  # noqa: E741
                key=attrgetter("price_unit_multi"),
                reverse=True,
            ),
            key=attrgetter("name"),
        )
        if exces_potencia:
            for line in exces_potencia:
                total_exces_consumida += line.price_subtotal
        return total_exces_consumida, len(exces_potencia) > 0

    def get_nom_cognoms(self, owner):
        """Returns name surnames. It considers enterprise/person"""

        partner_obj = owner.pool.get("res.partner")

        name_dict = partner_obj.separa_cognoms(self.cursor, self.uid, owner.name)
        is_enterprise = partner_obj.vat_es_empresa(self.cursor, self.uid, owner.vat)

        if is_enterprise:
            return name_dict["nom"]

        return "{0} {1}".format(name_dict["nom"], " ".join(name_dict["cognoms"]))

    def get_gkwh_owner(self, line):
        """Gets owner of gkwh line kwh"""
        if not line.is_gkwh().values()[0]:
            return ""

        line_owner_obj = line.pool.get("generationkwh.invoice.line.owner")
        line_owner_id = line_owner_obj.search(
            self.cursor, self.uid, ([("factura_line_id", "=", line.id)])
        )
        if not line_owner_id:
            return ""
        partner_obj = line.pool.get("res.partner")

        owner_vals = line_owner_obj.read(self.cursor, self.uid, line_owner_id[0], ["owner_id"])

        owner = partner_obj.browse(self.cursor, self.uid, owner_vals["owner_id"][0])

        return self.get_nom_cognoms(owner)

    def get_tarifa_elect_atr(self, fact, pricelist_name="pricelist_tarifas_electricidad"):
        res = []
        model_obj = fact.pool.get("ir.model.data")
        model_ids = model_obj.search(
            self.cursor,
            self.uid,
            [("module", "=", "giscedata_facturacio"), ("name", "=", pricelist_name)],
        )
        if model_ids:
            res = model_obj.read(self.cursor, self.uid, model_ids[0], ["res_id"])["res_id"]
        elif pricelist_name != "pricelist_tarifas_electricidad":
            res = self.get_tarifa_elect_atr(fact)
        return res

    def get_autoconsum_excedents_product_id(self, fact):
        model_obj = fact.pool.get("ir.model.data")
        return model_obj.get_object_reference(
            self.cursor, self.uid, "giscedata_facturacio_comer", "saldo_excedents_autoconsum"
        )[1]

    def get_lines_in_extralines(self, fact, pol):
        extra_obj = fact.pool.get("giscedata.facturacio.extra")
        extra_ids = extra_obj.search(
            self.cursor,
            self.uid,
            [
                ("polissa_id", "=", pol.id),
                ("factura_ids", "in", fact.id),
            ],
        )
        extra_linia_datas = extra_obj.read(self.cursor, self.uid, extra_ids, ["factura_linia_ids"])

        factura_linia_ids = []

        for eld in extra_linia_datas:
            factura_linia_ids.extend(eld["factura_linia_ids"])
        return factura_linia_ids

    def get_all_lines_in_extralines(self, pol):
        extra_obj = pol.pool.get("giscedata.facturacio.extra")
        extra_ids = extra_obj.search(
            self.cursor,
            self.uid,
            [("polissa_id", "=", pol.id), ],
            context={"active_test": False}
        )
        extra_linia_datas = extra_obj.read(self.cursor, self.uid, extra_ids, ["factura_linia_ids"])

        factura_linia_ids = []
        for eld in extra_linia_datas:
            factura_linia_ids.extend(eld["factura_linia_ids"])
        return factura_linia_ids

    def get_real_energy_lines(self, fact, pol):
        real_energy = []
        lines_extra_ids = self.get_lines_in_extralines(fact, pol)
        for l in fact.linies_energia:  # noqa: E741
            if l.id not in lines_extra_ids and l.name.startswith("P"):
                real_energy.append(l)
        return real_energy

    def get_extra_energy_lines(self, fact, pol):
        real_energy = []
        lines_extra_ids = self.get_lines_in_extralines(fact, pol)
        for l in fact.linies_energia:  # noqa: E741
            if l.id in lines_extra_ids:
                real_energy.append(l)
        return real_energy

    def get_extra_reactive_lines(self, fact, pol):
        extra_reactive = []
        lines_extra_ids = self.get_lines_in_extralines(fact, pol)
        for l in fact.linies_reactiva:  # noqa: E741
            if l.id in lines_extra_ids:
                extra_reactive.append(l)
        return extra_reactive

    def max_requested_powers(self, pol, fact):
        conf_obj = fact.pool.get("res.config")
        first_date_qr_pot_max = conf_obj.get(
            self.cursor, self.uid, "first_date_qr_pot_max", "2021-09-01"
        )
        max_potencies_demandades = []
        required_max_requested_powers = is_2XTD(pol) and fact.date_invoice >= first_date_qr_pot_max
        if required_max_requested_powers:
            max_potencies_demandades = self.get_max_potencies_demandades(fact)

        return required_max_requested_powers, max_potencies_demandades

    def get_max_potencies_demandades(self, fact):
        """
        Retorna [{'periode': str, 'potencia':float},...], ordenada per 'periode'
        """
        self.pool.get("giscedata.facturacio.maximetre.consumidor")
        maximetres_ids = fact.maximetre_consumidor_ids
        maximetres_data = []
        if maximetres_ids:
            for m in maximetres_ids:
                maximetres_data.append(
                    {
                        "periode": m.periode_id.name,
                        "potencia": m.maximetre,
                        "data_inici": dateformat(m.data_inici),
                        "data_final": dateformat(m.data_final),
                    }
                )

        return sorted(maximetres_data, key=lambda x: x["periode"])

    def get_codi_qr(self, fact):
        """
        Retorna {'qr': str b64, 'link': str}
        """
        report_v2_obj = self.pool.get("giscedata.facturacio.factura.report.v2")
        url, qr = report_v2_obj.get_qr_comparador_cnmc(self.cursor, self.uid, fact.id)

        return {"qr": qr, "url": url}

    def mag_get_ajust_topall_gas_info(self, fact):
        self.pool.get("giscedata.facturacio.factura.report.v2")
        ok = True
        try:
            # res = report_v2_obj.get_ajust_topall_gas_info(self.cursor, self.uid, fact.id)
            res = self.get_ajust_topall_gas_info(self.cursor, self.uid, fact)
        except Exception as e:
            ok = False
            import traceback

            res = str(e) + "\n" + traceback.format_exc()
        return ok, res

    # Duplicated code until V108 and molule giscedata_omie_comer can be installed, then remove it
    def get_ajust_topall_gas_info(self, cursor, uid, fra, context=None):
        res = {
            "periode_facturacio": {
                "aplica": self.aplica_ajust_topall_gas(cursor, uid, fra, context=context)
            }
        }
        if res["periode_facturacio"]["aplica"]:
            res["mes_natural_anterior"] = self.get_preu_mitja_mensual_mes_anterior_ajust(
                cursor, uid, fra, context=context
            )
            efecto_reductor_precio_mayorista_mecanismo_ajuste = (
                self.get_efecto_reductor_precio_mayorista_mecanismo_ajuste(
                    cursor, uid, fra, context=context
                )
            )
            res["periode_facturacio"].update(efecto_reductor_precio_mayorista_mecanismo_ajuste)
        return res

    def aplica_ajust_topall_gas(self, cursor, uid, fra, context=None):
        varconf_o = self.pool.get("res.config")
        data_inici_ajust_topall_gas = varconf_o.get(cursor, uid, "start_date_mecanisme_ajust_gas")
        data_fi_ajust_topall_gas = varconf_o.get(cursor, uid, "end_date_mecanisme_ajust_gas")
        if not data_inici_ajust_topall_gas or not data_fi_ajust_topall_gas:
            raise osv.except_osv(
                "Error !",
                _(
                    u"Variables que marquen l'inici i/o final de l'aplicació del "
                    u"mecanisme del topall de gas no estàn configurades"
                ),
            )
        aplica = True
        if (
            fra.data_inici > data_fi_ajust_topall_gas
            or fra.data_final < data_inici_ajust_topall_gas
        ):
            aplica = False
        return aplica

    def get_preu_mitja_mensual_mes_anterior_ajust(self, cursor, uid, fra, context=None):
        pmm_ajust_q = self.pool.get("giscedata.monthly.price.ajom").q(cursor, uid)
        data_fi = datetime.strptime(fra.data_final, "%Y-%m-%d")
        mes_anterior = data_fi.month - 1 if data_fi.month > 1 else 12
        year = data_fi.year - 1 if mes_anterior == 12 else data_fi.year
        dmn = [("name", "=", "{}/{}".format(year, str(mes_anterior).zfill(2)))]
        pmm_ajust_vs = pmm_ajust_q.read(["price"]).where(dmn)
        res = 0.0
        if pmm_ajust_vs:
            res = pmm_ajust_vs[0]["price"]
        return {"preu_mig_mensual_ajust": res, "mes": mes_anterior, "any": year}

    def get_efecto_reductor_precio_mayorista_mecanismo_ajuste(self, cursor, uid, fra, context=None):
        ph_ajust_q = self.pool.get("giscedata.omie.ajom").q(cursor, uid)
        dmn = [
            ("local_timestamp", ">=", "{} 01:00:00".format(fra.data_inici)),
            (
                "local_timestamp",
                "<=",
                (datetime.strptime(val(fra.data_final), "%Y-%m-%d") + timedelta(days=1)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            ),
        ]
        ph_ajust_vs = ph_ajust_q.read(["value", "unit_amount", "omie_price"]).where(dmn)
        sum_preu_reduccio = 0.0
        sum_preu_omie = 0.0
        sum_preu_ajust = 0.0
        sum_preu_cost_unitari = 0.0
        for ph_ajust_v in ph_ajust_vs:
            sum_preu_reduccio += ph_ajust_v["value"] - ph_ajust_v["unit_amount"]
            sum_preu_omie += ph_ajust_v["omie_price"]
            sum_preu_ajust += ph_ajust_v["value"]
            sum_preu_cost_unitari += ph_ajust_v["unit_amount"]

        res = {
            "preu_mitja_reduccio": sum_preu_reduccio / (len(ph_ajust_vs) or 1),
            "preu_mitja_omie": sum_preu_omie / (len(ph_ajust_vs) or 1),
            "preu_mitja_ajust": sum_preu_ajust / (len(ph_ajust_vs) or 1),
            "preu_mitja_cost_unitari": sum_preu_cost_unitari / (len(ph_ajust_vs) or 1),
        }
        return res

    # Duplicated code until V108 and molule giscedata_omie_comer can be installed, then remove it

    def get_mag_lines_info(self, fact):
        rmag_line_ids = fact.get_rmag_lines()
        if not rmag_line_ids:
            return False
        gffl_obj = self.pool.get("giscedata.facturacio.factura.linia")
        rmag_line = gffl_obj.browse(self.cursor, self.uid, rmag_line_ids[0])
        data = {
            "date_from": dateformat(rmag_line.data_desde),
            "date_to": dateformat(rmag_line.data_fins),
            "price": rmag_line.price_unit,
            "quantity": rmag_line.quantity,
            "total": rmag_line.price_subtotal,
            "iva": get_iva_line(rmag_line),
        }
        return data

    def get_auvi_product_categ_id(self, fact):
        model_obj = fact.pool.get("ir.model.data")
        return model_obj.get_object_reference(
            self.cursor, self.uid,
            "giscedata_serveis_generacio",
            "categ_serveis_generacio_facturar_contracte",
        )[1]

    def get_auvi_lines(self, fact):
        id_auvi_product_categ = self.get_auvi_product_categ_id(fact)
        auvi_lines = [
            line
            for line in fact.linia_ids
            if line.product_id and line.product_id.categ_id.id == id_auvi_product_categ
        ]
        return auvi_lines

    def get_auvi_data(self, fact, pol):
        auvi_lines = self.get_auvi_lines(fact)
        if not auvi_lines:
            return False
        date_ref = auvi_lines[0]['data_fins']
        sgpol_obj = fact.pool.get('giscedata.servei.generacio.polissa')
        sgpol_ids = sgpol_obj.search(self.cursor, self.uid, [
            ('polissa_id', '=', pol.id),
            ('cups_name', '=', pol.cups.name),
            '|',
            ('data_sortida', '=', False),
            ('data_sortida', '>', date_ref),
            '|',
            '&',
            ('data_inici', '!=', False),
            ('data_inici', '<=', date_ref),
            '&',
            ('data_inici', '=', False),
            ('data_incorporacio', '<=', date_ref),
        ])
        if not sgpol_ids:
            return False
        sgpol = sgpol_obj.browse(self.cursor, self.uid, sgpol_ids[0])
        res = {
            'auvi_id': sgpol.servei_generacio_id.id,
            'auvi_name': sgpol.servei_generacio_id.name,
            'auvi_percent': sgpol.percentatge or 0.0,
        }
        return res

    def get_auvi_logo(self, fact, pol):
        auvi_data = self.get_auvi_data(fact, pol)
        if not auvi_data:
            return False
        attachment_obj = fact.pool.get('ir.attachment')
        id_att = attachment_obj.search(self.cursor, self.uid, [
            ('res_model', '=', 'giscedata.servei.generacio'),
            ('res_id', '=', auvi_data['auvi_id']),
            ('name', '=', auvi_logo_attachment_name),
        ])
        if id_att:
            b64_content = attachment_obj.read(
                self.cursor,
                self.uid,
                id_att,
                ["datas"],
                context=self.context
            )[0]["datas"]
            content = base64.b64decode(b64_content)
            return content
        else:
            return False

    # -----------------------------
    # Component fill data functions
    # -----------------------------
    def get_component_logo_data(self, fact, pol):
        """
        returns a dictionary with all required logo component data
        """
        data = {"logo": "logo_som2.png"}
        if pol.soci.ref in agreementPartners.keys():
            data["has_agreement_partner"] = True
            data["logo_agreement_partner"] = agreementPartners[pol.soci.ref]["logo"]
        else:
            data["has_agreement_partner"] = False
        auvi_logo = self.get_auvi_logo(fact, pol)
        if auvi_logo:
            data["has_agreement_partner"] = False
            data["has_auvi"] = True
            data["auvi_logo"] = auvi_logo
        else:
            data["has_auvi"] = False
        return data

    def get_component_company_data(self, fact, pol):
        """
        returns a dictionary with all required company address data
        """
        data = {
            "name": fact.company_id.partner_id.name,
            "cif": fact.company_id.partner_id.vat.replace("ES", ""),
            "street": fact.company_id.partner_id.address[0].street,
            "zip": fact.company_id.partner_id.address[0].zip,
            "city": fact.company_id.partner_id.address[0].city,
            "email": fact.company_id.partner_id.address[0].email,
        }
        return data

    def get_component_gdo_data(self, fact, pol):
        """
        return a dictionary with all GdO clock data needs, data from 2020
        """
        lang = fact.lang_partner.lower()[0:2]

        example_data_2020 = """{{
                'wind_power': 359390,
                'photovoltaic': 75672,
                'hydraulics': 30034,
                'biogas': 7194,
                'biomassa': 0,
                'total': 472290,
                'lang': '{}',
                'graph': 'gdo_graf_{}_2020.png',
                'year': 2020}}""".format(
            lang, lang
        )

        conf_obj = fact.pool.get("res.config")

        swich_date = conf_obj.get(
            self.cursor, self.uid, "gdo_and_impact_yearly_switch_date", "2099-05-01"
        )

        if fact.date_invoice < swich_date:
            data = eval(example_data_2020)
            data = json.dumps(data)
            data = json.loads(data)
        else:
            gdo_som = conf_obj.get(self.cursor, self.uid, "component_gdo_data", example_data_2020)
            try:
                gdo_som = eval(gdo_som)
                gdo_som = json.dumps(gdo_som)
                data = json.loads(gdo_som)
                data["lang"] = lang
                data["graph"] = "gdo_graf_{}_{}.png".format(lang, data["year"])
            except Exception:
                data = eval(example_data_2020)
                data = json.dumps(data)
                data = json.loads(data)

        return data

    def get_component_flags_data(self, fact, pol):
        """
        returns a dictionary with all the flags data needed for the flag component
        """
        lang = fact.lang_partner.lower()[0:2]
        data = {
            "is_autoconsum": te_autoconsum(fact, pol),  # fact.te_autoconsum
            "autoconsum_flag": "flag_auto_little_{}.png".format(lang),
            "is_gkwh": te_gkwh(fact),
            "gkwh_flag": "flag_gkwh_little.png",
        }
        return data

    def get_component_contract_data_data(self, fact, pol):
        """
        returns a dictionary with all the contract data needed for the contract_data component
        """
        periodes_a = sorted(
            list(
                set(
                    [
                        lectura.name[-3:-1]
                        for lectura in fact.lectures_energia_ids
                        if lectura.tipus == "activa"
                    ]
                )
            )
        )
        pricelist = pol.llista_preu.nom_comercial or pol.llista_preu.name
        auvi_data = self.get_auvi_data(fact, pol)
        data = {
            "start_date": pol.data_alta,
            "renovation_date": get_renovation_date(pol.data_alta, datetime.now()),
            "cnae": pol.cnae.name,
            "cups": fact.cups_id.name,
            "cups_direction": fact.cups_id.direccio,
            "tariff": pol.tarifa.name,
            "pricelist": pricelist,
            "invoicing_mode": pol.mode_facturacio,
            "remote_managed_meter": pol.tg in ["1", "3"],
            "power": pol.potencia,
            "powers": sorted(
                [
                    (potencia.periode_id.name, potencia.potencia)
                    for potencia in pol.potencies_periode
                ],
                key=lambda l: l[0],  # noqa: E741
            ),
            "is_autoconsum": te_autoconsum(fact, pol),  # fact.te_autoconsum
            "autoconsum": pol.tipus_subseccio,
            "autoconsum_cau": pol.autoconsum_id.cau if pol.autoconsum_id and pol.tipus_subseccio != '00' else "",  # noqa: E501
            "is_autoconsum_colectiu": te_autoconsum_collectiu(
                fact, pol
            ),  # fact.te_autoconsum and fact.polissa_id.autoconsum_id
            # and fact.polissa_id.autoconsum_id.collectiu
            "autoconsum_colectiu_repartiment": float(pol.coef_repartiment),
            "power_invoicing_type": pol.facturacio_potencia == "max" or len(periodes_a) > 3,
            "small_text": self.is_visible_readings_g_table(fact, pol)
            and (is_3X(pol) or is_DHS(pol)),
            "is_auvi": True if auvi_data else False,
            "auvi_data": auvi_data,
        }
        return data

    def get_component_contract_data_td_data(self, fact, pol):
        data = self.get_component_contract_data_data(fact, pol)
        data["start_date"] = dateformat(data["start_date"])
        data["renovation_date"] = dateformat(data["renovation_date"])
        data["has_permanence"] = False
        for cat in pol.category_id:
            if cat.name == u"Fixa":
                data["has_permanence"] = True
        if data["power_invoicing_type"]:
            if te_quartihoraria(pol):
                power_invoicing_type = 2
            else:
                power_invoicing_type = 1
        else:
            power_invoicing_type = 0
        data["power_invoicing_type"] = power_invoicing_type
        segment_tarif = {
            u"2.0TD": 1,
            u"3.0TD": 2,
            u"6.1TD": 3,
            u"6.2TD": 4,
            u"6.3TD": 5,
            u"6.4TD": 6,
        }

        if data["autoconsum"] == '00' or len(pol.autoconsum_cups_ids) == 0:
            data["autoconsum_caus"] = [data["autoconsum_cau"]]
        else:
            data["autoconsum_caus"] = []
            for mcau in pol.autoconsum_cups_ids:
                data["autoconsum_caus"].append(mcau.autoconsum_id.cau)

        data["segment_tariff"] = segment_tarif.get(pol.tarifa.name, "")
        return data

    def get_component_readings_table_data(self, fact, pol):
        """
        return a dictionary with all readings table component needed data
        """
        (
            periodes_a,
            _,
            _,
            _,
            lectures_a,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            total_lectures_a,
            _,
            _,
            _,
            _,
            _,
            _,
        ) = self.get_readings_data(fact)

        dies_factura = (
            datetime.strptime(fact.data_final, "%Y-%m-%d")
            - datetime.strptime(fact.data_inici, "%Y-%m-%d")
        ).days + 1
        diari_factura_actual_eur = fact.total_energia / (dies_factura or 1.0)
        diari_factura_actual_kwh = (fact.energia_kwh * 1.0) / (dies_factura or 1.0)

        fact.lang_partner

        data = {
            "periodes_a": periodes_a,
            "lectures_a": lectures_a,
            "total_lectures_a": total_lectures_a,
            "dies_factura": dies_factura,
            "diari_factura_actual_eur": diari_factura_actual_eur,
            "diari_factura_actual_kwh": diari_factura_actual_kwh,
            "has_autoconsum": te_autoconsum(fact, pol),
        }

        return data

    def is_visible_readings_g_table(self, fact, pol):
        (
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            has_adjust_g,
            has_readings_g,
        ) = self.get_readings_data(fact)
        return te_autoconsum(fact, pol) and has_adjust_g and has_readings_g

    def get_component_readings_g_table_data(self, fact, pol):
        """
        return a dictionary with all readings table component needed data
        """
        (
            _,
            _,
            _,
            periodes_g,
            _,
            _,
            _,
            lectures_g,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            total_lectures_g,
            _,
            _,
            _,
        ) = self.get_readings_data(fact)
        data = {
            "periodes_g": periodes_g,
            "lectures_g": lectures_g,
            "total_lectures_g": total_lectures_g,
            "is_visible": self.is_visible_readings_g_table(fact, pol),
        }

        return data

    def get_component_readings_text_data(self, fact, pol):
        (
            periodes_a,
            _,
            _,
            _,
            lectures_a,
            _,
            _,
            lectures_g,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            has_adjust_a,
            has_adjust_g,
            has_readings_g,
        ) = self.get_readings_data(fact)
        data = {
            "periodes_a": periodes_a,
            "is_visible": has_adjust_a
            or (te_autoconsum(fact, pol) and has_readings_g and has_adjust_g),
            "lang": fact.lang_partner,
            "has_autoconsum": te_autoconsum(fact, pol),
        }

        return data

    def get_component_energy_consumption_graphic_data(self, fact, pol):
        """
        return a dictionary with data needes for the consumption graphic and related text
        """
        (historic, historic_js) = self.get_historic_data(fact)
        (periodes_a, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _) = self.get_readings_data(
            fact
        )

        total_historic_kw = sum([h["consum"] for h in historic])
        total_historic_eur = sum([h["facturat"] for h in historic])
        if historic:
            data_ini = min([h["data_ini"] for h in historic])
            data_fin = max([h["data_fin"] for h in historic])
        else:
            data_ini = val(fact.data_inici)
            data_fin = val(fact.data_final)

        historic_dies = (
            datetime.strptime(data_fin, "%Y-%m-%d") - datetime.strptime(data_ini, "%Y-%m-%d")
        ).days
        historic_dies_or_1 = historic_dies or 1.0

        mes_any_inicial = (
            datetime.strptime(fact.data_inici, "%Y-%m-%d") - timedelta(days=365)
        ).strftime("%Y/%m")
        total_any = sum([h["consum"] for h in historic if h["mes"] > mes_any_inicial])

        data = {
            "fact_id": fact.id,
            "total_historic_eur_dia": (total_historic_eur * 1.0) / historic_dies_or_1,
            "total_historic_kw_dia": (total_historic_kw * 1.0) / historic_dies_or_1,
            "historic_dies": historic_dies_or_1,
            "total_any": total_any,
            "historic_json": json.dumps(historic_js),
            "periodes_a": periodes_a,
            "is_6X": is_6X(pol),
            "average_30_days": historic_dies * 1.0 / 30,
        }

        return data

    def get_conany_kwh_energy_consumption_graphic_td_data(self, cursor, uid, fact_id, context=None):
        """
        Simplification to avoid generate all the invoice data to get the year's kwh
        """
        fac_obj = self.pool.get('giscedata.facturacio.factura')
        fact = fac_obj.browse(cursor, uid, fact_id, context)
        (historic, historic_js) = self.get_historic_data(fact)

        def get_as_time(text):
            return datetime.strptime(text, '%Y-%m-%d')

        data_inici_any = get_as_time(fact.data_inici) - timedelta(days=365)
        mes_any_inicial = data_inici_any.strftime("%Y/%m")

        conany_kwh = 0.0
        conany_kwh_p1 = 0.0
        conany_kwh_p2 = 0.0
        conany_kwh_p3 = 0.0
        conany_kwh_p4 = 0.0
        conany_kwh_p5 = 0.0
        conany_kwh_p6 = 0.0
        data_ini = None
        data_fin = None

        for h in historic:
            if h['mes'] > mes_any_inicial:
                conany_kwh += h['consum']
                if h['periode'] == 'P1':
                    conany_kwh_p1 += h['consum']
                elif h['periode'] == 'P2':
                    conany_kwh_p2 += h['consum']
                elif h['periode'] == 'P3':
                    conany_kwh_p3 += h['consum']
                elif h['periode'] == 'P4':
                    conany_kwh_p4 += h['consum']
                elif h['periode'] == 'P5':
                    conany_kwh_p5 += h['consum']
                elif h['periode'] == 'P6':
                    conany_kwh_p6 += h['consum']
                if data_ini is None or data_ini > h["data_ini"]:
                    data_ini = h["data_ini"]
                if data_fin is None or data_fin < h["data_fin"]:
                    data_fin = h["data_fin"]

        if data_ini and data_fin:
            historic_dies = (get_as_time(data_fin) - get_as_time(data_ini)).days
        else:
            historic_dies = 0

        data = {
            'consum': conany_kwh,
            'P1': conany_kwh_p1,
            'P2': conany_kwh_p2,
            'P3': conany_kwh_p3,
            'P4': conany_kwh_p4,
            'P5': conany_kwh_p5,
            'P6': conany_kwh_p6,
            'days': historic_dies,
        }
        return data

    def complete_historic_js(self, data, length):
        data_len = len(data)
        if data_len == 0 or data_len >= length:
            return data

        first_date = data[0]['mes'].split("/")
        month = int(first_date[0]) - 1
        year = int(first_date[1])
        rest = []
        for i in range(0, length - len(data)):
            if month == 0:
                month = 12
                year -= 1

            item = {
                u'P1': 0.0,
                u'P2': 0.0,
                u'P3': 0.0,
                u'mes': '{:02}/{:02}'.format(month, year),
            }
            if u'P4' in data[0]:
                item[u'P4'] = 0.0
                item[u'P5'] = 0.0
                item[u'P6'] = 0.0
            rest.append(item)
            month -= 1

        rest.reverse()
        rest.extend(data)
        return rest

    def get_component_energy_consumption_graphic_td_data(self, fact, pol):
        """
        return a dictionary with data needes for the consumption graphic and related text
        """
        if not is_TD(pol):
            return {}

        shortMonths = {
            "es_ES": {
                "01": "Ene",
                "02": "Feb",
                "03": "Mar",
                "04": "Abr",
                "05": "May",
                "06": "Jun",
                "07": "Jul",
                "08": "Ago",
                "09": "Sep",
                "10": "Oct",
                "11": "Nov",
                "12": "Dic",
            },
            "ca_ES": {
                "01": "Gen",
                "02": "Feb",
                "03": "Mar",
                "04": "Abr",
                "05": "Mai",
                "06": "Jun",
                "07": "Jul",
                "08": "Ago",
                "09": "Set",
                "10": "Oct",
                "11": "Nov",
                "12": "Des",
            },
            "en_US": {
                "01": "Jan",
                "02": "Feb",
                "03": "Mar",
                "04": "Apr",
                "05": "May",
                "06": "Jun",
                "07": "Jul",
                "08": "Aug",
                "09": "Sep",
                "10": "Oct",
                "11": "Nov",
                "12": "Dec",
            },
        }

        labels = {
            "es_ES": {"P1": "Punta", "P2": "Llano", "P3": "Valle"},
            "ca_ES": {"P1": "Punta", "P2": "Pla", "P3": "Vall"},
            "en_US": {"P1": "Peak", "P2": "Mid-peak", "P3": "Off-peak"},
        }

        average_text = {
            "es_ES": "Media",
            "ca_ES": "Mitjana",
            "en_US": "Average",
        }

        (historic, historic_js) = self.get_historic_data(fact)
        historic_js = self.complete_historic_js(historic_js, 12)
        for h_js in historic_js:
            periode = h_js["mes"].split("/")
            if (int(periode[0]) >= 6 and int(periode[1]) == 21) or (int(periode[1]) > 21):
                h_js["labels"] = labels[fact.lang_partner]
            h_js["mes"] = shortMonths[fact.lang_partner][periode[0]] + "/" + periode[1]

        mes_any_inicial = (
            datetime.strptime(fact.data_inici, "%Y-%m-%d") - timedelta(days=365)
        ).strftime("%Y/%m")
        historic = [h for h in historic if h["mes"] > mes_any_inicial]

        total_historic_kw = sum([h["consum"] for h in historic])
        total_historic_eur = sum([h["facturat"] for h in historic])
        if historic:
            data_ini = min([h["data_ini"] for h in historic])
            data_fin = max([h["data_fin"] for h in historic])
        else:
            data_ini = val(fact.data_inici)
            data_fin = val(fact.data_final)

        historic_dies = (
            datetime.strptime(data_fin, "%Y-%m-%d") - datetime.strptime(data_ini, "%Y-%m-%d")
        ).days
        historic_dies_or_1 = historic_dies or 1.0

        total_any = sum([h["consum"] for h in historic])

        required_max_requested_powers, max_potencies_demandades = self.max_requested_powers(
            pol, fact
        )

        mean_zipcode_consumption = 0
        show_mean_zipcode_consumption = (
            pol.tipo_medida == "05"
            and mean_zipcode_consumption_dates["start"]
            <= fact.data_inici
            < mean_zipcode_consumption_dates["end"]
        )
        if show_mean_zipcode_consumption:
            try:
                mean_zipcode_consumption = fact.consum_cp_ids[0].consum
            except Exception:
                # consum_cp_ids is in another module and may be not installed or empty
                pass

        data = {
            "fact_id": fact.id,
            "total_historic_eur_dia": (total_historic_eur * 1.0) / historic_dies_or_1,
            "total_historic_kw_dia": (total_historic_kw * 1.0) / historic_dies_or_1,
            "historic_dies": historic_dies_or_1,
            "total_any": total_any,
            "historic_json": json.dumps(historic_js),
            "is_big": is_6XTD(pol) or is_3XTD(pol),
            "average_30_days": historic_dies * 1.0 / 30,
            "max_requested_powers": max_potencies_demandades,
            "required_max_requested_powers": required_max_requested_powers,
            "distri_name": pol.distribuidora.name,
            "show_mean_zipcode_consumption": show_mean_zipcode_consumption,
            "zipcode": fact.cups_id.dp,
            "mean_zipcode_consumption": mean_zipcode_consumption,
            "average_text": average_text[fact.lang_partner],
        }

        return data

    def get_component_meters_data(self, fact, pol):
        """
        return a dictionary with all meters component needed data
        this component will be used in 2 different locations according
        to 'location' variable
        """
        (
            periodes_a,
            _,
            _,
            _,
            lectures_a,
            _,
            _,
            _,
            lectures_real_a,
            _,
            _,
            _,
            total_lectures_a,
            _,
            _,
            _,
            _,
            _,
            _,
        ) = self.get_readings_data(fact)
        show_meter = any(
            [
                lectures_a[comptador][0][7] != "real"
                for comptador in sorted(lectures_a)
                if len(lectures_real_a[comptador]) > 0
            ]
        )
        data = {
            "location": "up" if (show_meter and len(periodes_a) < 3) else "down",
            "show_component": show_meter,
            "periodes_a": periodes_a,
            "lectures_a": lectures_a,
            "total_lectures_a": total_lectures_a,
            "lectures_real_a": lectures_real_a,
        }
        return data

    def get_component_emergency_complaints_data(self, fact, pol):
        """
        return a dictionary with all emergency complaints conponent data
        This component is used in 2 diferents locations according to
        'location' variable.
        """
        dphone = self.get_distri_phone(pol) or " "
        cphone = fact.company_id.partner_id.address[0].phone

        (periodes_a, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _) = self.get_readings_data(
            fact
        )

        data = {
            "location": "up" if (len(periodes_a) < 3 or is_6X(pol)) else "down",
            "is_6X": is_6X(pol),
            "distri_name": pol.distribuidora.name,
            "distri_contract": pol.ref_dist or "",
            "distri_phone": ".".join([dphone[i: i + 3] for i in range(0, len(dphone), 3)])
            if "." not in dphone
            else dphone,
            "has_agreement_partner": pol.soci.ref in agreementPartners.keys(),
            "agreement_partner_name": pol.soci.name,
            "is_energetica": pol.soci.ref in agreementPartners.keys() and pol.soci.ref == "S019753",
            "comer_phone": ".".join([cphone[i: i + 3] for i in range(0, len(cphone), 3)])
            if "." not in cphone
            else cphone,
        }
        return data

    def get_component_emergency_complaints_td_data(self, fact, pol):
        """
        return a dictionary with all emergency complaints conponent data
        This component is used in 2 diferents locations according to
        'location' variable.
        """
        dphone = self.get_distri_phone(pol) or " "
        cphone = fact.company_id.partner_id.address[0].phone

        data = {
            "distri_name": pol.distribuidora.name,
            "distri_contract": pol.ref_dist or "",
            "distri_phone": ".".join([dphone[i: i + 3] for i in range(0, len(dphone), 3)])
            if "." not in dphone
            else dphone,
            "has_agreement_partner": pol.soci.ref in agreementPartners.keys(),
            "agreement_partner_name": pol.soci.name,
            "is_energetica": pol.soci.ref in agreementPartners.keys() and pol.soci.ref == "S019753",
            "comer_phone": ".".join([cphone[i: i + 3] for i in range(0, len(cphone), 3)])
            if "." not in cphone
            else cphone,
            "lang": fact.lang_partner,
        }
        return data

    def get_component_invoice_details_power_data(self, fact, pol):
        atr_linies_potencia = {}  # ATR Peatges Energia dict
        power_lines = []
        tarifa_elect_atr = self.get_tarifa_elect_atr(fact)
        for l in sorted(  # noqa: E741
            sorted(fact.linies_potencia, key=attrgetter("data_desde")), key=attrgetter("name")
        ):
            days_year = (
                is_leap_year(datetime.strptime(l.data_desde, "%Y-%m-%d").year) and 366 or 365
            )
            power_lines.append(
                {
                    "name": l.name,
                    "quantity": l.quantity,
                    "atr_price": self.get_atr_price(fact, pol.llista_preu.id, l),
                    "multi": l.multi,
                    "days_per_year": days_year,
                    "price_subtotal": l.price_subtotal,
                }
            )
            l_count = Counter(
                {
                    "atrprice_subtotal": l.atrprice_subtotal,
                    "multi": l.multi,
                }
            )
            l_name = l.name[:2]
            if not l_name in atr_linies_potencia.keys():  # noqa: E713
                atr_linies_potencia[l.name[:2]] = l_count
                atr_linies_potencia[l.name[:2]].update(
                    {
                        "price": self.get_atr_price(fact, tarifa_elect_atr, l),
                        "days_per_year": days_year,
                        "quantity": l.quantity,
                    }
                )
            else:
                atr_linies_potencia[l.name[:2]] += l_count

        for k, v in atr_linies_potencia.items():
            atr_linies_potencia[k] = {
                "quantity": v["quantity"],
                "atrprice_subtotal": v["atrprice_subtotal"],
                "price": v["price"],
                "multi": v["multi"],
                "days_per_year": v["days_per_year"],
            }

        data = {
            "power_lines": power_lines,
            "is_6X": is_6X(pol),
            "total_exces_consumida": self.get_total_excess_power_consumed(fact)[0],
            "atr_power_lines": atr_linies_potencia,
            "is_power_tolls_visible": fact.data_final > new_tariff_with_power_tolls_date
            and is_2X(pol),
        }
        return data

    def get_component_invoice_details_energy_data(self, fact, pol):
        atr_linies_energia = {}  # ATR Peatges Energia dict
        power_lines = []
        tarifa_elect_atr = self.get_tarifa_elect_atr(fact)
        linies_energia = self.get_real_energy_lines(fact, pol)
        for l in sorted(  # noqa: E741
            sorted(linies_energia, key=attrgetter("data_desde")), key=attrgetter("name")
        ):
            power_lines.append(
                {
                    "name": l.name,
                    "quantity": l.quantity,
                    "price_unit_multi": l.price_unit_multi,
                    "price_subtotal": l.price_subtotal,
                    "gkwh_owner": self.get_gkwh_owner(l),
                }
            )
            l_count = Counter({"quantity": l.quantity, "atrprice_subtotal": l.atrprice_subtotal})
            l_name = l.name[:2]
            if not l_name in atr_linies_energia.keys():  # noqa: E713
                atr_linies_energia[l.name[:2]] = l_count
                atr_linies_energia[l.name[:2]].update(
                    {"price": self.get_atr_price(fact, tarifa_elect_atr, l)}
                )
            else:
                atr_linies_energia[l.name[:2]] += l_count

        for k, v in atr_linies_energia.items():
            atr_linies_energia[k] = {
                "quantity": v["quantity"],
                "atrprice_subtotal": v["atrprice_subtotal"],
                "price": v["price"],
            }

        data = {
            "energy_lines": power_lines,
            "atr_energy_lines": atr_linies_energia,
            "is_new_tariff_message_visible": fact.data_final > new_tariff_with_power_tolls_date,
        }
        return data

    def get_component_invoice_details_generation_data(self, fact, pol):
        autoconsum_excedents_product_id = self.get_autoconsum_excedents_product_id(fact)
        generation_lines = []
        for l in sorted(  # noqa: E741
            sorted(fact.linies_generacio, key=attrgetter("data_desde")), key=attrgetter("name")
        ):
            generation_lines.append(
                {
                    "name": l.name,
                    "is_visible": not l.product_id
                    or l.product_id.id != autoconsum_excedents_product_id,
                    "quantity": l.quantity,
                    "price_unit_multi": l.price_unit_multi,
                    "price_subtotal": l.price_subtotal,
                }
            )

        data = {
            "generation_lines": generation_lines,
            "has_autoconsum": te_autoconsum_amb_excedents(fact, pol),
        }
        return data

    def get_component_invoice_details_reactive_data(self, fact, pol):
        tarifa_elect_atr = self.get_tarifa_elect_atr(fact)
        reactive_lines = []
        for l in sorted(  # noqa: E741
            sorted(get_reactive_lines_clean(fact), key=attrgetter("data_desde")),
            key=attrgetter("name")
        ):
            reactive_lines.append(
                {
                    "name": l.name,
                    "quantity": l.quantity,
                    "price_unit_multi": l.price_unit_multi,
                    "price_subtotal": l.price_subtotal,
                    "atrprice_subtotal": l.atrprice_subtotal,
                    "atr_price": self.get_atr_price(fact, tarifa_elect_atr, l),
                }
            )

        data = {
            "reactive_lines": reactive_lines,
            "is_visible": bool(fact.total_reactiva),
        }
        return data

    def get_component_invoice_details_other_concepts_data(self, fact, pol):  # noqa: C901
        def get_tax_type(l):  # noqa: E741
            if l.tax_id.description == "IESE_RD_17_2021":
                return "0.5percent"
            elif l.tax_id.description == "IESE_RDL_8_2023_25":
                return "2.5percent"
            elif l.tax_id.description == "IESE_RDL_8_2023_38":
                return "3.8percent"
            elif l.tax_id.description == "IESE_99.2_1":
                return "1euroMWh"
            elif l.tax_id.description == "IESE_99.2_0.5":
                return "0.5euroMWh"
            elif l.tax_id.description and l.tax_id.description.startswith("IESE_RD_17_2021_85"):
                return "excempcio"
            return "5.11percent"

        lines_extra_ids = self.get_all_lines_in_extralines(pol)
        lloguer_lines = []
        bosocial_lines = []
        donatiu_lines = []
        altres_lines = []
        compl_lines = []
        iva_energia = None
        iva_potencia = None
        for l in fact.linia_ids:  # noqa: E741
            if l.tipus in "energia":
                iva_energia = get_iva_line(l)
            if l.tipus in "potencia":
                iva_potencia = get_iva_line(l)
            if l.tipus in "lloguer":
                lloguer_lines.append(
                    {
                        "quantity": l.quantity,
                        "price_unit": l.price_unit,
                        "price_subtotal": l.price_subtotal,
                        "iva": get_iva_line(l),
                    }
                )
            if l.tipus in "altres" and l.invoice_line_id.product_id.code == "BS01":
                bosocial_lines.append(
                    {
                        "quantity": l.quantity,
                        "price_unit": l.price_unit,
                        "price_subtotal": l.price_subtotal,
                        "iva": get_iva_line(l),
                    }
                )
            if l.tipus in "altres" and l.invoice_line_id.product_id.code == "DN01":
                donatiu_lines.append(
                    {
                        "quantity": l.quantity,
                        "price_unit_multi": l.price_unit_multi,
                        "price_subtotal": l.price_subtotal,
                        "iva": get_iva_line(l),
                    }
                )
            if l.tipus in ("altres", "cobrament") and l.invoice_line_id.product_id.code not in (
                "DN01",
                "BS01",
                "DESC1721",
                "DESC1721ENE",
                "DESC1721POT",
                "RBS",
                "PBV",
            ):
                altres_lines.append(
                    {
                        "name": l.name,
                        "price_subtotal": l.price_subtotal,
                        "iva": get_iva_line(l),
                    }
                )
            if l.tipus in "energia" and l.id in lines_extra_ids:
                if compl_cat not in l.name and compl_cas not in l.name:
                    altres_lines.append(
                        {
                            "name": l.name,
                            "price_subtotal": l.price_subtotal,
                            "iva": get_iva_line(l),
                        }
                    )
            if l.id in lines_extra_ids and (compl_cat in l.name or compl_cas in l.name):
                compl_lines.append(
                    {
                        "id": l.id,
                        "name": l.name,
                        "price_subtotal": l.price_subtotal,
                        "iva": get_iva_line(l),
                    }
                )

        iva_iese = ""
        if iva_potencia:
            iva_iese = iva_potencia
        if iva_energia:
            iva_iese = iva_energia

        iese_lines = []
        fiscal_position = (
            fact.fiscal_position
            and "IESE" in fact.fiscal_position.name
            and "%" in fact.fiscal_position.name
        )
        excempcio = None
        percentatges_exempcio_splitted = None
        percentatges_exempcio = None
        is_excempcio_IE_base = None

        if fiscal_position:
            excempcio = fact.fiscal_position.tax_ids[0].tax_dest_id.name
            excempcio = excempcio[excempcio.find("(") + 1: excempcio.find(")")]
            percentatges_exempcio_splitted = excempcio.split(" ")
            if len(percentatges_exempcio_splitted) == 3:
                percentatges_exempcio = (
                    abs(float(percentatges_exempcio_splitted[0].replace("%", "")) / 100),
                    abs(float(percentatges_exempcio_splitted[2].replace("%", "")) / 100),
                )
            is_excempcio_IE_base = (
                len(percentatges_exempcio_splitted) == 3 and len(percentatges_exempcio) == 2
            )

            for l in fact.tax_line:  # noqa: E741
                tax_type = get_tax_type(l)
                if "IVA" not in l.name and "IGIC" not in l.name:
                    if (
                        len(percentatges_exempcio_splitted) == 3
                        and tax_type == "excempcio"
                        and is_excempcio_IE_base
                    ):
                        base_iese = l.base_amount * (
                            1 - percentatges_exempcio[0] * percentatges_exempcio[1]
                        )
                    else:
                        base_iese = l.base_amount

                    iese_lines.append(
                        {
                            "base_iese": base_iese,
                            "tax_amount": l.tax_amount,
                            "tax_type": tax_type,
                            "iva": iva_iese,
                        }
                    )
        else:
            fiscal_position = False
            for l in fact.tax_line:  # noqa: E741
                if "IVA" not in l.name and "IGIC" not in l.name:
                    iese_lines.append(
                        {
                            "base_amount": l.base_amount,
                            "tax_amount": l.tax_amount,
                            "tax_type": get_tax_type(l),
                            "iva": iva_iese,
                        }
                    )

        iva_lines = []
        igic_lines = []
        for l in fact.tax_line:  # noqa: E741
            if "IVA" in l.name:
                iva_lines.append(
                    {
                        "name": clean_tax_name(l.name),
                        "base": l.base,
                        "amount": l.amount,
                        "disclaimer_21_to_5": l.name == "IVA 5%",
                        "disclaimer_21_to_10": l.name == "IVA 10%",
                    }
                )
            if "IGIC" in l.name:
                igic_lines.append(
                    {
                        "name": l.name,
                        "base": l.base,
                        "amount": l.amount,
                    }
                )

        data = {
            "lloguer_lines": lloguer_lines,
            "bosocial_lines": bosocial_lines,
            "donatiu_lines": donatiu_lines,
            "altres_lines": altres_lines,
            "compl_lines": compl_lines,
            "iese_lines": iese_lines,
            "iva_lines": iva_lines,
            "igic_lines": igic_lines,
            "fiscal_position": fiscal_position,
            "excempcio": excempcio,
            "percentatges_exempcio_splitted": percentatges_exempcio_splitted,
            "percentatges_exempcio": percentatges_exempcio,
            "is_excempcio_IE_base": is_excempcio_IE_base,
            "donatiu": sum([l["price_subtotal"] for l in donatiu_lines]),  # noqa: E741
            "amount_total": fact.amount_total,
        }
        return data

    def get_component_invoice_details_comments_data(self, fact, pol):
        """
        returns a dictionary with all the comments data needed for the invoice details comments component
        """  # noqa: E501
        invoice_comment = (
            fact.comment
            if fact.journal_id.code.startswith("RECUPERACION_IVA") and fact.comment
            else None
        )
        data = {
            "invoice_comment": invoice_comment,
            "has_web": bool(pol.distribuidora.website),
            "web_distri": pol.distribuidora.website,
            "language": fact.lang_partner,
            "distri_name": pol.distribuidora.name,
        }
        return data

    def get_component_invoice_details_tec271_data(self, fact, pol):
        """
        returns a dictionary with all the tec271 data needed for the invoice details tec271 component
        """  # noqa: E501
        polissa_obj = fact.pool.get("giscedata.polissa")
        cups = polissa_obj.read(self.cursor, self.uid, pol.id, ["cups"])["cups"][1]
        sup_territorials_tec_271_comer_obj = fact.pool.get(
            "giscedata.suplements.territorials.2013.tec271.comer"
        )
        text = sup_territorials_tec_271_comer_obj.get_info_text(self.cursor, self.uid, cups)
        if text:
            text = text.format(distribuidora=pol.distribuidora.name)

        data = {
            "is_visible": fact.has_tec271_line(),
            "distri_name": pol.distribuidora.name,
            "html_table": sup_territorials_tec_271_comer_obj.get_info_html(
                self.cursor, self.uid, cups
            ),
            "text": text,
        }
        return data

    def get_component_amount_destination_data(self, fact, pol):
        """
        returns a dictionary with all the amount destination data needed
        """
        # Repartiment segons BOE
        rep_BOE = {"i": 39.44, "c": 40.33, "o": 20.23}

        altres_lines = [
            l
            for l in fact.linia_ids  # noqa: E741
            if l.tipus in ("altres", "cobrament")
            and l.invoice_line_id.product_id.code
            not in ("DN01", "BS01", "DESC1721", "DESC1721ENE", "DESC1721POT")
        ]

        total_altres = sum([l.price_subtotal for l in altres_lines])  # noqa: E741

        pie_total = fact.amount_total - fact.total_lloguers
        pie_regulats = fact.total_atr + total_altres
        pie_impostos = float(fact.amount_tax)
        pie_costos = pie_total - pie_regulats - pie_impostos

        data = {
            "is_visible": is_2X(pol),
            "factura_id": fact.id,
            "amount_total": fact.amount_total,
            "total_lloguers": fact.total_lloguers,
            "pie_total": pie_total,
            "pie_regulats": pie_regulats,
            "pie_impostos": pie_impostos,
            "pie_costos": pie_costos,
            "rep_BOE": rep_BOE,
        }
        return data

    def is_visible_reactive(self, fact):
        (_, periodes_r, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _) = self.get_readings_data(
            fact
        )
        return len(periodes_r) > 0

    def is_visible_maximeter(self, fact, pol):
        (periodes_a, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _) = self.get_readings_data(
            fact
        )
        return pol.facturacio_potencia == "max" or len(periodes_a) > 3

    def is_visible_reactive_and_maximeter(self, fact, pol):
        return self.is_visible_reactive(fact) and self.is_visible_maximeter(fact, pol)

    def get_component_reactive_readings_table_data(self, fact, pol):
        (
            _,
            periodes_r,
            _,
            _,
            _,
            lectures_r,
            _,
            _,
            _,
            lectures_real_r,
            _,
            _,
            _,
            total_lectures_r,
            _,
            _,
            _,
            _,
            _,
        ) = self.get_readings_data(fact)
        data = {
            "visible_side_by_side": "side_by_side_react"
            if self.is_visible_reactive_and_maximeter(fact, pol)
            else "",
            "is_visible": self.is_visible_reactive(fact),
            "periodes_r": periodes_r,
            "lectures_r": lectures_r,
            "lectures_real_r": lectures_real_r,
            "total_lectures_r": total_lectures_r,
        }
        return data

    def get_component_maximeter_readings_table_data(self, fact, pol):
        (_, periodes_r, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _) = self.get_readings_data(
            fact
        )
        exces_potencia = sorted(
            sorted(
                [l for l in fact.linia_ids if l.tipus == "exces_potencia"],  # noqa: E741
                key=attrgetter("price_unit_multi"),
                reverse=True,
            ),
            key=attrgetter("name"),
        )
        periodes_m = sorted(list(set([lectura.name for lectura in fact.lectures_potencia_ids])))

        lectures_m = []
        for lectura in fact.lectures_potencia_ids:
            lectures_m.append((lectura.name, lectura.pot_contract, lectura.pot_maximetre))
        for lects in lectures_m:
            sorted(lectures_m, key=lambda x: x[0])

        fact_potencia = dict([(p, 0) for p in periodes_m])
        for p in [(p.product_id.name, p.quantity) for p in fact.linies_potencia]:
            fact_potencia.update({p[0]: max(fact_potencia.get(p[0], 0), p[1])})

        dades_exces_potencia = dict([(p, (0, 0)) for p in periodes_m])
        for l in exces_potencia:  # noqa: E741
            dades_exces_potencia[l.name] = (l.quantity, l.price_subtotal)

        exces_m = []
        for periode in periodes_m:
            exces_m.append(dades_exces_potencia[periode])

        data = {
            "visible_side_by_side": "side_by_side_max"
            if self.is_visible_reactive_and_maximeter(fact, pol)
            else "",
            "is_visible": self.is_visible_maximeter(fact, pol),
            "periodes_r": periodes_r,
            "has_exces_potencia": len(exces_potencia),
            "exces_m": exces_m,
            "periodes_m": periodes_m,
            "lectures_m": lectures_m,
            "fact_potencia": fact_potencia,
        }
        return data

    def get_component_environmental_impact_data(self, fact, pol):

        conf_obj = fact.pool.get("res.config")
        swich_date = conf_obj.get(
            self.cursor, self.uid, "gdo_and_impact_yearly_switch_date", "2099-05-01"
        )

        data = {
            "is_visible": fact.date_invoice < swich_date,
            "c02_emissions": {
                "national_average": "0,15",
                "som_energia": "0,00",
            },
            "radioactive_waste": {
                "national_average": "0,49",
                "som_energia": "0,00",
            },
        }
        return data

    def get_component_electricity_information_data(self, fact, pol):

        conf_obj = fact.pool.get("res.config")
        swich_date = conf_obj.get(
            self.cursor, self.uid, "gdo_and_impact_yearly_switch_date", "2099-05-01"
        )

        data = {
            "is_visible": fact.date_invoice < swich_date,
            "year_graph": 2020,
            "is_inport": True,
            "inport_export_value": 1.3,
            "mix_image_som_energia": "electricity_information_mix_som.png",
            "mix_image_rest": "electricity_information_mix_rest_"
            + fact.lang_partner.lower()
            + "_2021.png",
            "renovable": {
                "som_energia": "100%",
                "mix": "43,6%",
            },
            "high_effic_cogener": {
                "som_energia": "0%",
                "mix": "3,7%",
            },
            "cogener": {
                "som_energia": "0%",
                "mix": "7,3%",
            },
            "cc_nat_gas": {
                "som_energia": "0%",
                "mix": "17,9%",
            },
            "coal": {
                "som_energia": "0%",
                "mix": "2%",
            },
            "fuel_gas": {
                "som_energia": "0%",
                "mix": "1,7%",
            },
            "nuclear": {
                "som_energia": "0%",
                "mix": "22,8%",
            },
            "others": {
                "som_energia": "0%",
                "mix": "1,0%",
            },
        }
        return data

    def get_component_invoice_info_data(self, fact, pol):
        data = {
            "has_agreement_partner": pol.soci.ref in agreementPartners.keys(),
            "amount_total": fact.amount_total,
            "type": fact.invoice_id.type,
            "number": fact.number,
            "ref": bool(fact.ref),
            "ref_number": fact.ref.number,
            "date_invoice": dateformat(fact.date_invoice),
            "start_date": dateformat(fact.data_inici),
            "end_date": dateformat(fact.data_final),
            "contract_number": pol.name,
            "address": fact.cups_id.direccio,
            "due_date": dateformat(fact.date_due),
        }
        return data

    def get_component_invoice_summary_data(self, fact, pol):
        total_exces_consumida, has_exces_potencia = self.get_total_excess_power_consumed(fact)
        impostos = {}
        iese = 0
        for l in fact.tax_line:  # noqa: E741
            if "IVA" in l.name or "IGIC" in l.name:
                impostos.update({clean_tax_name(l.name): l.amount})
            else:
                iese += l.amount

        bosocial_lines = [
            l
            for l in fact.linia_ids  # noqa: E741
            if l.tipus in "altres" and l.invoice_line_id.product_id.code == "BS01"
        ]
        donatiu_lines = [
            l
            for l in fact.linia_ids  # noqa: E741
            if l.tipus in "altres" and l.invoice_line_id.product_id.code == "DN01"
        ]
        altres_lines = [
            l
            for l in fact.linia_ids  # noqa: E741
            if l.tipus in ("altres", "cobrament")
            and l.invoice_line_id.product_id.code not in ("DN01", "BS01", "RBS", "PBV")
        ]

        extra_energy_lines = self.get_extra_energy_lines(fact, pol)
        extra_reactive_lines = self.get_extra_reactive_lines(fact, pol)

        donatiu = sum([l.price_subtotal for l in donatiu_lines])  # noqa: E741

        total_bosocial = sum([l.price_subtotal for l in bosocial_lines])  # noqa: E741

        total_altres = sum([l.price_subtotal for l in altres_lines])  # noqa: E741

        total_extra_energy = sum([l.price_subtotal for l in extra_energy_lines])  # noqa: E741
        total_extra_reactive = sum([l.price_subtotal for l in extra_reactive_lines])  # noqa: E741

        total_altres += total_extra_energy + total_extra_reactive

        total_energia = sum([l.price_subtotal for l in fact.linies_energia])  # noqa: E741
        total_energia = total_energia - total_extra_energy

        data = {
            "total_exces_consumida": total_exces_consumida,
            "has_exces_potencia": has_exces_potencia,
            "total_energy": total_energia,
            "total_power": fact.total_potencia,
            "total_ractive": fact.total_reactiva,
            "total_rent": fact.total_lloguers,
            "total_amount": fact.amount_total,
            "has_autoconsum": te_autoconsum(fact, pol),
            "autoconsum_total_compensada": sum([l.price_subtotal for l in fact.linies_generacio]),  # noqa: E741, E501
            "impostos": impostos,
            "iese": iese,
            "donatiu": donatiu,
            "total_bosocial": total_bosocial,
            "total_altres": total_altres,
        }
        return data

    def get_component_invoice_summary_td_data(self, fact, pol):
        data = self.get_component_invoice_summary_data(fact, pol)
        inductive = self.sub_component_invoice_details_td_inductive_data_visibility(fact, pol)
        capacitive = self.sub_component_invoice_details_td_capacitive_data_visibility(fact, pol)
        data["inductive_is_visible"] = inductive[0]
        data["total_inductive"] = inductive[1]
        data["capacitive_is_visible"] = capacitive[0]
        data["total_capacitive"] = capacitive[1]
        data[
            "total_boe17_2021"
        ] = self.get_sub_component_invoice_details_td_power_discount_BOE17_2021_data(fact, pol)[
            "total"
        ]
        data[
            "total_boe17_2021"
        ] += self.get_sub_component_invoice_details_td_energy_discount_BOE17_2021_data(fact, pol)[
            "total"
        ]
        total_altres = data["total_altres"] - data["total_boe17_2021"]
        data["total_altres"] = total_altres if abs(total_altres) > 0.001 else 0
        bosocial2023_lines = [
            l
            for l in fact.linia_ids  # noqa: E741
            if l.tipus in "altres" and l.invoice_line_id.product_id.code == "RBS"
        ]
        data["total_bosocial2023"] = sum([l.price_subtotal for l in bosocial2023_lines])  # noqa: E741, E501

        flux_lines = [
            l
            for l in fact.linia_ids  # noqa: E741
            if l.tipus in ("altres", "cobrament") and l.invoice_line_id.product_id.code == "PBV"
        ]

        data["has_flux_solar_discount"] = len(flux_lines) > 0
        data["flux_solar_discount"] = sum([l.price_subtotal for l in flux_lines])  # noqa: E741
        return data

    def get_component_partner_info_data(self, fact, pol):
        cc_name = _(u"")
        bank_name = _(u"")
        if pol.tipo_pago.code != "TRANSFERENCIA_CSB":
            if fact.partner_bank:
                cc_name = "**** " * 5 + fact.partner_bank.iban[-4:]
                if fact.partner_bank.bank:
                    bank_name = fact.partner_bank.bank.name
        else:
            cc_name = pol.payment_mode_id.bank_id.iban + _(" (Som Energia, SCCL)")
            bank_name = _(u"TRANSFERÈNCIA")
        data = {
            "pol_name": pol.titular.name,
            "vat": pol.titular.vat.replace("ES", ""),
            "is_out_refund": fact.invoice_id.type == "out_refund",
            "payment_type": pol.tipo_pago.code,
            "cc_name": cc_name,
            "bank_name": bank_name,
        }
        return data

    def get_component_lateral_text_data(self, fact, pol):
        data = {
            "name": fact.company_id.name,
            "street": fact.company_id.partner_id.address[0].street,
            "cp": fact.company_id.partner_id.address[0].zip,
            "city": fact.company_id.partner_id.address[0].city,
            "vat": fact.company_id.partner_id.vat.replace("ES", ""),
        }
        return data

    def get_component_readings_6x_data(self, fact, pol):
        # "comptadors" es un dicconario con la siguiente estructura:
        #     - Clave: tupla con 3 valores: (Número de serie, fecha actual, fecha anterior)
        #     - Valor: lista con 3 elementos:
        #         * Primer elemento: lecturas activa
        #         * Segundo elemento: lecturas reactiva
        #         * Tercer elemento: potencia maxímetro
        if not is_6X(pol):
            return {"is_visible": False}

        periodes_act = sorted(
            sorted(
                list(
                    [lectura for lectura in fact.lectures_energia_ids if lectura.tipus == "activa"]
                ),
                key=attrgetter("name"),
            ),
            key=attrgetter("comptador"),
            reverse=True,
        )
        periodes_rea = sorted(
            sorted(
                list(
                    [
                        lectura
                        for lectura in fact.lectures_energia_ids
                        if lectura.tipus == "reactiva"
                    ]
                ),
                key=attrgetter("name"),
            ),
            key=attrgetter("comptador"),
            reverse=True,
        )
        periodes_max = sorted(
            sorted(
                list([lectura for lectura in fact.lectures_potencia_ids]), key=attrgetter("name")
            ),
            key=attrgetter("comptador"),
            reverse=True,
        )

        def origen_to_text(origin_code):
            tipus_lectura = ""
            if origin_code == "40":
                tipus_lectura = _("(estimada)")
            elif origin_code == "99":
                tipus_lectura = _("(sense lectura)")
            else:
                tipus_lectura = _("(real)")
            return tipus_lectura

        def read_lectures(p):
            return {
                "lect_anterior": p.lect_anterior,
                "lect_actual": p.lect_actual,
                "ajust": p.ajust,
                "motiu_ajust": p.motiu_ajust,
                "consum": p.consum,
                "comptador": p.comptador,
                "data_anterior": dateformat(p.data_anterior),
                "data_actual": dateformat(p.data_actual),
                "origen_codi": p.origen_id.codi,
                "origen_text": origen_to_text(p.origen_id.codi),
            }

        periodes_act_d = [read_lectures(p) for p in periodes_act]
        periodes_rea_d = [read_lectures(p) for p in periodes_rea]

        parametres = ["comptador", "data_anterior", "data_actual"]
        periodes_max_d = [p.read(parametres)[0] for p in periodes_max]

        lectures = map(None, periodes_act_d, periodes_rea_d, periodes_max_d)

        comptador_actual = None
        comptador_anterior = None
        comptadors = {}
        llista_lect = []
        for lect in lectures:
            if lect[0]:
                comptador_actual = lect[0]["comptador"]
                data_ant = lect[0]["data_anterior"]
                data_act = lect[0]["data_actual"]
            elif lect[1]:
                comptador_actual = lect[1]["comptador"]
                data_ant = lect[1]["data_anterior"]
                data_act = lect[1]["data_actual"]
            elif lect[2]:
                comptador_actual = lect[2]["comptador"]
                data_ant = lect[2]["data_anterior"]
                data_act = lect[2]["data_actual"]
            if comptador_anterior and comptador_actual != comptador_anterior:
                comptadors[(comptador_anterior, data_actual_pre, data_ant_pre)] = llista_lect  # noqa: F821, E501
                llista_lect = []
            if data_act:
                comptadors[(comptador_actual, data_act, data_ant)] = llista_lect
                llista_lect.append((lect[0], lect[1], lect[2], lect[0]["origen_text"]))
                comptador_anterior = comptador_actual

        dies_factura = (
            datetime.strptime(fact.data_final, "%Y-%m-%d")
            - datetime.strptime(fact.data_inici, "%Y-%m-%d")
        ).days + 1
        diari_factura_actual_eur = fact.total_energia / (dies_factura or 1.0)
        diari_factura_actual_kwh = (fact.energia_kwh * 1.0) / (dies_factura or 1.0)

        data = {
            "is_visible": is_6X(pol),
            "comptadors": comptadors,
            "dies_factura": dies_factura,
            "diari_factura_actual_eur": diari_factura_actual_eur,
            "diari_factura_actual_kwh": diari_factura_actual_kwh,
        }
        return data

    def get_component_hourly_curve_data(self, fact, pol):
        is_visible = is_6X(pol) or is_6XTD(pol) or is_indexed(fact)
        data = {
            "is_visible": is_visible,
            "has_agreement_partner": pol.soci.ref in agreementPartners.keys(),
            "factura_data": fact.get_curve_as_csv().get(fact.id, None) if is_visible else None,
        }
        data["profiled_curve"] = data["factura_data"] and "REEPROFILE" in data["factura_data"]
        return data

    def get_component_globals_data(self, fact, pol):
        (periodes_a, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _) = self.get_readings_data(
            fact
        )
        data = {
            "num_periodes": len(periodes_a),
            "is_6x": is_6X(pol),
            "is_TD": is_TD(pol),
            "is_6xTD": is_6XTD(pol),
            "is_indexed": is_indexed(fact),
        }
        return data

    def get_component_rectificative_banner_data(self, fact, pol):
        data = {
            "is_visible": bool(fact.journal_id.code == "RECUPERACION_IVA.R" and fact.rectifying_id)
        }
        if data["is_visible"]:
            tax_obj = fact.pool.get("account.invoice.tax")
            tax_ids = tax_obj.search(
                self.cursor,
                self.uid,
                [("name", "like", "IVA%"), ("invoice_id", "=", fact.rectifying_id.id)],
            )
            if not tax_ids:
                quota = fact.rectifying_id.amount_total - fact.amount_total
            else:
                tax_data = tax_obj.read(self.cursor, self.uid, tax_ids, ["amount"])
                quota = sum([tax["amount"] for tax in tax_data if "amount" in tax])

            data.update(
                {
                    "invoice": fact.rectifying_id.number,
                    "date": dateformat(fact.rectifying_id.date_invoice),
                    "quota": quota,
                }
            )
        return data

    # ---------------------------------------------------
    # Invoice_details_td component data and subcomponents
    # ---------------------------------------------------
    def get_matrix_show_periods(self, pol):
        requested_power_periods = 3 if is_2XTD(pol) else 6
        return ["P{}".format(i + 1) for i in range(0, requested_power_periods)]

    def get_component_invoice_details_td_data(self, fact, pol):
        if not is_TD(pol):
            return {}

        power_discount_BOE17_2021 = (
            self.get_sub_component_invoice_details_td_power_discount_BOE17_2021_data(fact, pol)
        )
        energy_discount_BOE17_2021 = (
            self.get_sub_component_invoice_details_td_energy_discount_BOE17_2021_data(fact, pol)
        )
        data = {
            "showing_periods": self.get_matrix_show_periods(pol),
            "power": self.get_sub_component_invoice_details_td_power_data(fact, pol),
            "power_discount_BOE17_2021": power_discount_BOE17_2021,
            "power_tolls": self.get_sub_component_invoice_details_td_power_tolls_data(fact, pol),
            "power_charges": self.get_sub_component_invoice_details_td_power_charges_data(
                fact, pol, power_discount_BOE17_2021
            ),
            "energy": self.get_sub_component_invoice_details_td_energy_data(
                fact, pol, energy_discount_BOE17_2021
            ),
            # 'energy_generationkwh' :
            # self.get_sub_component_invoice_details_td_energy_generationkwh_data(fact, pol),
            "energy_discount_BOE17_2021": energy_discount_BOE17_2021,
            "energy_tolls": self.get_sub_component_invoice_details_td_energy_tolls_data(fact, pol),
            "energy_charges": self.get_sub_component_invoice_details_td_energy_charges_data(
                fact, pol, energy_discount_BOE17_2021
            ),
            "other_concepts": self.get_sub_component_invoice_details_td_other_concepts_data(
                fact, pol
            ),
            "excess_power_maximeter": self.get_sub_component_invoice_details_td_excess_power_maximeter(  # noqa: E501
                fact, pol
            ),
            "excess_power_quarterhours": self.get_sub_component_invoice_details_td_excess_power_quarterhours(  # noqa: E501
                fact, pol
            ),
            "bo_social_2023": self.get_sub_component_invoice_details_td_bo_social_2023_data(
                fact, pol
            ),
            "flux_solar": self.get_sub_component_invoice_details_td_flux_solar_data(fact, pol),
            "generation": self.get_sub_component_invoice_details_td_generation_data(fact, pol),
            "inductive": self.get_sub_component_invoice_details_td_inductive_data(fact, pol),
            "capacitive": self.get_sub_component_invoice_details_td_capacitive_data(fact, pol),
            "is_canaries": pol.cups.id_provincia.id in [37, 41],
            "iva_column": has_iva_column(fact),
            "amount_total": fact.amount_total,
        }
        return data

    def get_sub_component_invoice_details_td(self, fact, pol, linies, lectures=None):
        readings = {}
        if lectures != None:  # noqa: E711
            for comptador_name, lectures_comptador in lectures.items():
                for lectura in lectures_comptador:
                    if lectura[0] == u"P1":
                        data = str(
                            datetime.strptime(lectura[4], "%d/%m/%Y").date() + timedelta(days=1)
                        )
                        origin = _(u"estimada")
                        if lectura[6] == "real" and lectura[7] == "real":
                            origin = _(u"real")
                        elif (
                            lectura[6] == "estimada distribuïdora" or lectura[6] == "real"
                        ) and lectura[7] == "calculada":
                            origin = _(u"calculada")
                        elif lectura[6] == "calculada" and (
                            lectura[7] == "calculada" or lectura[7] == "real"
                        ):
                            origin = _(u"calculada")

                        readings[data] = origin

        lines_data = {}
        block = 0
        sorted_linies = sorted(linies, key=attrgetter("data_desde"))
        data_desde = sorted_linies[0]["data_desde"] if len(sorted_linies) > 0 else None
        for l in sorted_linies:  # noqa: E741
            if data_desde != l["data_desde"]:
                block += 1
                data_desde = l["data_desde"]

            if block not in lines_data:
                lines_data[block] = {"total": 0, "multi": 0, "days_per_year": 0}

            days_per_year = (
                is_leap_year(datetime.strptime(l.data_desde, "%Y-%m-%d").year) and 366 or 365
            )

            if lines_data.has_key(block) and lines_data[block].has_key(l.name):  # noqa: W601
                lines_data[block][l.name]["quantity"] = (
                    lines_data[block][l.name]["quantity"] + l.quantity
                )
                lines_data[block][l.name]["price_subtotal"] = (
                    lines_data[block][l.name]["price_subtotal"] + l.price_subtotal
                )
            else:
                lines_data[block][l.name] = {
                    "quantity": l.quantity,
                    "atr_price": self.get_atr_price(fact, pol.llista_preu.id, l),
                    "price_subtotal": l.price_subtotal,
                    "price_unit_multi": l.price_unit_multi,
                    "price_unit": l.price_unit,
                    "extra": l.multi,
                }
            lines_data[block]["multi"] = l.multi
            lines_data[block]["days_per_year"] = days_per_year
            lines_data[block]["total"] += l.price_subtotal
            lines_data[block]["origin"] = (
                readings[l.data_desde] if l.data_desde in readings else _(u"sense lectura")
            )
            lines_data[block]["data"] = data_desde
            lines_data[block]["days"] = (
                datetime.strptime(l.data_fins, "%Y-%m-%d")
                - datetime.strptime(l.data_desde, "%Y-%m-%d")
            ).days + 1
            lines_data[block]["date_from"] = dateformat(l.data_desde)
            lines_data[block]["date_to_d"] = (
                val(l.data_fins)
                if "date_to_d" not in lines_data[block]
                or lines_data[block]["date_to_d"] > val(l.data_fins)
                else lines_data[block]["date_to_d"]
            )
            lines_data[block]["date_to"] = dateformat(lines_data[block]["date_to_d"])
            lines_data[block]["iva"] = get_iva_line(l)

        lines_data = [lines_data[k] for k in sorted(lines_data.keys())]
        return lines_data

    def get_sub_component_invoice_details_td_accumulative(self, fact, pol, linies):
        lines_data = {}
        total = 0
        iva = 0

        for l in linies:  # noqa: E741
            l_count = Counter(
                {
                    "quantity": l.quantity,
                    "price_subtotal": l.price_subtotal,
                }
            )

            if l.name not in lines_data:
                lines_data[l.name] = l_count
                lines_data[l.name].update(
                    {
                        "price_unit_multi": l.price_unit_multi,
                    }
                )
            else:
                lines_data[l.name] += l_count

            total += l.price_subtotal
            iva = get_iva_line(l)

        for k, v in lines_data.items():
            lines_data[k] = {
                "quantity": v["quantity"],
                "price_subtotal": v["price_subtotal"],
                "price_unit_multi": v["price_unit_multi"],
            }

        lines_data["total"] = total
        lines_data["iva"] = iva
        return lines_data

    def get_sub_component_invoice_details_td_power_data(self, fact, pol):
        power_lines_data = self.get_sub_component_invoice_details_td(
            fact, pol, fact.linies_potencia
        )

        data = {
            "power_lines_data": power_lines_data,
            "header_multi": 3 * len(power_lines_data),
            "showing_periods": self.get_matrix_show_periods(pol),
            "iva_column": has_iva_column(fact),
        }
        return data

    def get_sub_component_invoice_details_td_power_discount_BOE17_2021_data(self, fact, pol):
        is_index = is_indexed(fact)
        discount_lines = [
            l
            for l in fact.linia_ids  # noqa: E741
            if l.tipus in "altres"
            and l.invoice_line_id.product_id.code in ("DESC1721", "DESC1721POT", "DESC1721ENE")
            and "potencia" in l.name
        ]

        discount_power_lines = {}
        total = 0
        iva = ""
        days_year = 365
        for l in discount_lines:  # noqa: E741
            days_year = (
                is_leap_year(datetime.strptime(l.data_desde, "%Y-%m-%d").year) and 366 or 365
            )
            price_subtotal = l.price_unit * l.quantity if is_index else l.price_subtotal
            l_count = Counter(
                {
                    "price_subtotal": price_subtotal,
                    "days": l.multi,
                }
            )
            name = l.name[-11:-9]
            if name not in discount_power_lines:
                discount_power_lines[name] = l_count
                discount_power_lines[name].update(
                    {
                        "price_unit": l.price_unit,
                    }
                )
            else:
                discount_power_lines[name].update(l_count)
            total += l.price_subtotal
            iva = get_iva_line(l)

        for k, v in discount_power_lines.items():
            discount_power_lines[k] = {
                "price_subtotal": v["price_subtotal"],
                "days": v["days"],
                "price_unit": v["price_unit"] * float(days_year) / v["days"],
            }

        data = discount_power_lines
        data["total"] = total
        data["is_visible"] = len(discount_lines) > 0
        data["showing_periods"] = self.get_matrix_show_periods(pol)
        data["dies"] = (
            int(discount_power_lines["P1"]["days"]) if "P1" in discount_power_lines else 0
        )
        data["dies_any"] = days_year
        data["is_indexed"] = is_index
        data["iva"] = iva
        data["iva_column"] = has_iva_column(fact)
        return data

    def get_sub_component_invoice_details_td_energy_discount_BOE17_2021_data(self, fact, pol):
        is_index = is_indexed(fact)
        discount_lines = [
            l
            for l in fact.linia_ids  # noqa: E741
            if l.tipus in "altres"
            and l.invoice_line_id.product_id.code in ("DESC1721", "DESC1721POT", "DESC1721ENE")
            and "energia" in l.name
        ]

        discount_energy_lines = {}
        total = 0
        iva = ""
        for l in discount_lines:  # noqa: E741
            price_subtotal = l.price_unit * l.quantity if is_index else l.price_subtotal
            l_count = Counter(
                {
                    "price_subtotal": price_subtotal,
                }
            )
            name = l.name[-10:-8]
            if name not in discount_energy_lines:
                discount_energy_lines[name] = l_count
                discount_energy_lines[name].update(
                    {
                        "price_unit": l.price_unit,
                    }
                )
            else:
                discount_energy_lines[name].update(l_count)
            total += l.price_subtotal
            iva = get_iva_line(l)

        for k, v in discount_energy_lines.items():
            discount_energy_lines[k] = {
                "price_subtotal": v["price_subtotal"],
                "price_unit": v["price_unit"],
            }

        data = discount_energy_lines
        data["total"] = total
        data["is_visible"] = len(discount_lines) > 0
        data["showing_periods"] = self.get_matrix_show_periods(pol)
        data["is_indexed"] = is_index
        data["iva"] = iva
        data["iva_column"] = has_iva_column(fact)
        return data

    def get_sub_component_invoice_details_td_power_tolls_data(self, fact, pol):
        atr_linies_potencia = {}  # ATR Peatges Potencia dict
        tarifa_elect_atr = self.get_tarifa_elect_atr(fact, "pricelist_tarifas_peajes_electricidad")
        days_year = 0
        for l in sorted(  # noqa: E741
            sorted(fact.linies_potencia, key=attrgetter("data_desde")), key=attrgetter("name")
        ):
            days_year = (
                is_leap_year(datetime.strptime(l.data_desde, "%Y-%m-%d").year) and 366 or 365
            )
            l_count = Counter(
                {
                    "atrprice_subtotal": l.atrprice_subtotal,
                    "multi": l.multi,
                }
            )
            l_name = l.name[:2]
            if not l_name in atr_linies_potencia.keys():  # noqa: E713
                atr_linies_potencia[l_name] = l_count
                atr_linies_potencia[l_name].update(
                    {
                        "price": self.get_atr_price(fact, tarifa_elect_atr, l),
                    }
                )
            else:
                atr_linies_potencia[l_name] += l_count

        for k, v in atr_linies_potencia.items():
            atr_linies_potencia[k] = {
                "atr_peatge": v["atrprice_subtotal"],
                "preu_peatge": v["price"],
                "days": v["multi"],
            }

        data = atr_linies_potencia
        data["showing_periods"] = self.get_matrix_show_periods(pol)
        data["dies"] = int(atr_linies_potencia["P1"]["days"]) if "P1" in atr_linies_potencia else 0
        data["dies_any"] = days_year
        data["iva_column"] = has_iva_column(fact)
        return data

    def get_sub_component_invoice_details_td_power_charges_data(self, fact, pol, discount):
        charges_lines_potencia = {}
        tarifa_elect_atr = self.get_tarifa_elect_atr(fact, "pricelist_tarifas_cargos_electricidad")

        days_year = 0
        for l in fact.linies_potencia:  # noqa: E741
            days_year = (
                is_leap_year(datetime.strptime(l.data_desde, "%Y-%m-%d").year) and 366 or 365
            )
            if "price_unit_cargos" in l:
                l_count = Counter(
                    {
                        "preu_cargos": l.price_unit_cargos,
                        "atr_cargos": l.cargos_price_subtotal,
                        "our_cargos": float(
                            l.quantity * self.get_atr_price(fact, tarifa_elect_atr, l) * l.multi
                        )
                        / float(days_year),
                        "multi": l.multi,
                    }
                )
            else:  # TODO remove at release and the data model is right
                l_count = Counter(
                    {
                        "preu_cargos": 0.0,
                        "atr_cargos": 0.0,
                        "our_cargos": 0.0,
                        "multi": l.multi,
                    }
                )

            l_name = l.name[:2]
            if not l_name in charges_lines_potencia.keys():  # noqa: E713
                if (
                    l.data_desde >= BOE17_2021_dates["start"]
                    and l.data_desde <= BOE17_2021_dates["end"]
                    and l_name in discount
                ):
                    add_discount = discount[l_name]["price_unit"]
                else:
                    add_discount = 0.0
                charges_lines_potencia[l_name] = l_count
                charges_lines_potencia[l_name].update(
                    {
                        "price": self.get_atr_price(fact, tarifa_elect_atr, l) - add_discount,
                    }
                )
            else:
                charges_lines_potencia[l_name] += l_count

        for k, v in charges_lines_potencia.items():
            d = discount[k]["price_subtotal"] if discount["is_visible"] else 0
            charges_lines_potencia[k] = {
                "preu_cargos": v["price"],  # TODO switch back when lines comes well calculated
                "atr_cargos": v["our_cargos"]
                - d,  # TODO switch back when lines comes well calculated
                "days": v["multi"],
            }
        data = charges_lines_potencia
        data["showing_periods"] = self.get_matrix_show_periods(pol)
        data["dies"] = (
            int(charges_lines_potencia["P1"]["days"]) if "P1" in charges_lines_potencia else 0
        )
        data["dies_any"] = days_year
        data["header_multi"] = 4 if discount["is_visible"] else 2
        data["iva_column"] = has_iva_column(fact)
        return data

    def get_component_invoice_details_info_td_data(self, fact, pol):
        has_mag = True if self.get_mag_lines_info(fact) else False
        if not has_mag:
            return {
                "has_autoconsum": te_autoconsum(fact, pol),
                "has_mag": has_mag,
            }

        ok, mag_info = self.mag_get_ajust_topall_gas_info(fact)
        if not ok:
            return {
                "has_autoconsum": te_autoconsum(fact, pol),
                "has_mag": False,
                "library_error": mag_info.split("\n"),
            }

        if (
            "periode_facturacio" not in mag_info
            or "aplica" not in mag_info["periode_facturacio"]
            or not mag_info["periode_facturacio"]["aplica"]
        ):
            return {
                "has_autoconsum": te_autoconsum(fact, pol),
                "has_mag": False,
                "library_error": "no aplica periode de facturacio",
                "data": mag_info,
            }

        data = {
            "has_autoconsum": te_autoconsum(fact, pol),
            "has_mag": has_mag,
            "preu_mitja_mag_darrer_mes": mag_info["mes_natural_anterior"]["preu_mig_mensual_ajust"],
            "mes_mag_darrer_mes": mag_info["mes_natural_anterior"]["mes"],
            "any_mag_darrer_mes": mag_info["mes_natural_anterior"]["any"],
            "reductor_mag": abs(mag_info["periode_facturacio"]["preu_mitja_reduccio"]),
            "majorista_sense_mag": mag_info["periode_facturacio"]["preu_mitja_omie"]
            + mag_info["periode_facturacio"]["preu_mitja_ajust"],
            "majorista_amb_mag": mag_info["periode_facturacio"]["preu_mitja_omie"]
            + mag_info["periode_facturacio"]["preu_mitja_cost_unitari"],
        }
        return data

    def get_sub_component_invoice_details_td_energy_data(self, fact, pol, discount):
        (a, a, a, a, lectures_a, a, a, a, a, a, a, a, a, a, a, a, a, a, a) = self.get_readings_data(
            fact
        )
        linies_energia = self.get_real_energy_lines(fact, pol)
        no_generationkWh_lines = [l for l in linies_energia if "GkWh" not in l.name]  # noqa: E741
        energy_lines_data = self.get_sub_component_invoice_details_td(
            fact, pol, no_generationkWh_lines, lectures_a
        )

        generationkwh_lines = [l for l in linies_energia if "GkWh" in l.name]  # noqa: E741
        gkwh_energy_lines_data = self.get_sub_component_invoice_details_td(
            fact, pol, generationkwh_lines
        )
        mag_line_data = self.get_mag_lines_info(fact)

        auvi_lines = self.get_auvi_lines(fact)
        auvi_energy_lines_data = self.get_sub_component_invoice_details_td(
            fact, pol, auvi_lines
        )

        for e in energy_lines_data:
            if (
                e["data"] >= BOE17_2021_dates["start"]
                and e["data"] <= BOE17_2021_dates["end"]
                and u"P1" in discount
            ):
                e["has_discount"] = True

        for e in gkwh_energy_lines_data:
            if (
                e["data"] >= BOE17_2021_dates["start"]
                and e["data"] <= BOE17_2021_dates["end"]
                and u"P1" in discount
            ):
                e["has_discount"] = True

        for e in auvi_energy_lines_data:
            if (
                e["data"] >= BOE17_2021_dates["start"]
                and e["data"] <= BOE17_2021_dates["end"]
                and u"P1" in discount
            ):
                e["has_discount"] = True

        data = {
            "energy_lines_data": energy_lines_data,
            "gkwh_energy_lines_data": gkwh_energy_lines_data,
            "header_multi": 3 * (len(energy_lines_data) + len(gkwh_energy_lines_data))
            + (1 if mag_line_data else 0) + (3 if auvi_energy_lines_data else 0),
            "showing_periods": self.get_matrix_show_periods(pol),
            "mag_line_data": mag_line_data,
            "indexed": pol.mode_facturacio == "index",
            "iva_column": has_iva_column(fact),
            "auvi_energy_lines_data": auvi_energy_lines_data,
        }
        return data

    def get_sub_component_invoice_details_td_energy_tolls_data(self, fact, pol):
        atr_linies_energia = {}  # ATR Peatges Energia dict
        tarifa_elect_atr = self.get_tarifa_elect_atr(fact, "pricelist_tarifas_peajes_electricidad")
        linies_energia = self.get_real_energy_lines(fact, pol)
        for l in sorted(  # noqa: E741
            sorted(linies_energia, key=attrgetter("data_desde")), key=attrgetter("name")
        ):
            l_count = Counter({"quantity": l.quantity, "atrprice_subtotal": l.atrprice_subtotal})
            l_name = l.name[:2]
            if not l_name in atr_linies_energia.keys():  # noqa: E713
                atr_linies_energia[l_name] = l_count
                atr_linies_energia[l_name].update(
                    {"price": self.get_atr_price(fact, tarifa_elect_atr, l)}
                )
            else:
                atr_linies_energia[l_name] += l_count

        for k, v in atr_linies_energia.items():
            atr_linies_energia[k] = {
                "atr_peatge": v["atrprice_subtotal"],
                "preu_peatge": v["price"],
            }

        data = atr_linies_energia
        data["showing_periods"] = self.get_matrix_show_periods(pol)
        data["iva_column"] = has_iva_column(fact)
        return data

    def get_sub_component_invoice_details_td_energy_charges_data(self, fact, pol, discount):
        charges_lines_energy = {}
        tarifa_elect_atr = self.get_tarifa_elect_atr(fact, "pricelist_tarifas_cargos_electricidad")
        linies_energia = self.get_real_energy_lines(fact, pol)
        for l in linies_energia:  # noqa: E741
            if "price_unit_cargos" in l:
                l_count = Counter(
                    {
                        "preu_cargos": l.price_unit_cargos,
                        "atr_cargos": l.cargos_price_subtotal,
                        "our_cargos": float(
                            l.quantity * self.get_atr_price(fact, tarifa_elect_atr, l)
                        ),
                    }
                )
            else:  # TODO remove at release and the data model is right
                l_count = Counter(
                    {
                        "preu_cargos": 0.0,
                        "atr_cargos": 0.0,
                        "our_cargos": 0.0,
                    }
                )

            l_name = l.name[:2]
            if not l_name in charges_lines_energy.keys():  # noqa: E713
                if (
                    l.data_desde >= BOE17_2021_dates["start"]
                    and l.data_desde <= BOE17_2021_dates["end"]
                    and l_name in discount
                ):
                    add_discount = discount[l_name]["price_unit"]
                else:
                    add_discount = 0.0
                charges_lines_energy[l_name] = l_count
                charges_lines_energy[l_name].update(
                    {
                        "price": self.get_atr_price(fact, tarifa_elect_atr, l) - add_discount,
                    }
                )
            else:
                charges_lines_energy[l_name] += l_count

        for k, v in charges_lines_energy.items():
            d = discount[k]["price_subtotal"] if discount["is_visible"] and k in discount else 0
            charges_lines_energy[k] = {
                "preu_cargos": v["price"],  # TODO switch back when lines comes well calculated
                "atr_cargos": v["our_cargos"]
                - d,  # TODO switch back when lines comes well calculated
            }
        data = charges_lines_energy
        data["showing_periods"] = self.get_matrix_show_periods(pol)
        data["header_multi"] = 4 if discount["is_visible"] else 2
        data["iva_column"] = has_iva_column(fact)
        return data

    def get_sub_component_invoice_details_td_other_concepts_data(self, fact, pol):
        data = self.get_component_invoice_details_other_concepts_data(fact, pol)
        data["header_multi"] = len(
            data["bosocial_lines"] + data["altres_lines"] + data["donatiu_lines"]
        )
        data["last_row"] = (
            "donatiu"
            if len(data["donatiu_lines"])
            else "altres"
            if len(data["altres_lines"])
            else "compl"
            if len(data["compl_lines"])
            else "bosocial"
        )
        data["number_of_columns"] = len(self.get_matrix_show_periods(pol)) + 1
        data["iva_column"] = has_iva_column(fact)
        data["showing_periods"] = self.get_matrix_show_periods(pol)

        if data['compl_lines']:
            data['compl_info'] = self.get_sub_component_expedient_data(
                fact, pol, data['compl_lines'])
        return data

    def get_sub_component_expedient_data(self, fact, pol, lines):
        extra_obj = fact.pool.get("giscedata.facturacio.extra")
        f1_obj = fact.pool.get("giscedata.facturacio.importacio.linia")
        f1f_obj = fact.pool.get("giscedata.facturacio.importacio.linia.factura")
        l_obj = fact.pool.get("giscedata.facturacio.factura.linia")

        compl_ids = [x['id'] for x in lines]
        extra_ids = extra_obj.search(
            self.cursor,
            self.uid,
            [
                ("polissa_id", "=", pol.id),
                ("factura_ids", "in", fact.id),
                ("factura_linia_ids", "in", compl_ids)
            ],
            context={"active_test": False}
        )
        extra_data = extra_obj.read(
            self.cursor,
            self.uid,
            extra_ids,
            ['origin_invoice']
        )
        origins = list(set([x['origin_invoice'] for x in extra_data]))
        f1_ids = f1_obj.search(
            self.cursor,
            self.uid,
            [
                ("cups_id", "=", pol.cups.id),
                ("invoice_number_text", "in", origins),
                ("type_factura", "=", "C")
            ],
            context={"active_test": False}
        )
        if len(f1_ids) == 0:
            raise osv.except_osv(
                "Error !",
                _(
                    u"No s'han trobats F1's d'expedient de anomalia/frau al generar pdf per {}"
                ).format(len(f1_ids), fact.number),
            )

        f1_datas = f1_obj.read(
            self.cursor,
            self.uid,
            f1_ids,
            ['num_expedient']
        )
        expedient = ','.join(list(set([f1_data['num_expedient'] for f1_data in f1_datas])))
        f1f_ids = f1f_obj.search(
            self.cursor,
            self.uid,
            [('linia_id', 'in', f1_ids)]
        )
        f1f_datas = f1f_obj.read(
            self.cursor,
            self.uid,
            f1f_ids,
            ['tipo_factura']
        )
        types = list(set([f1f_data['tipo_factura']
                     for f1f_data in f1f_datas if f1f_data['tipo_factura']]))
        data = {
            'expedient': expedient,
            'tipus': '06' if '06' in types else '11'
        }

        tarifa_cargos = self.get_tarifa_elect_atr(fact, "pricelist_tarifas_cargos_electricidad")
        tarifa_peajes = self.get_tarifa_elect_atr(fact, "pricelist_tarifas_peajes_electricidad")
        compl_lines = l_obj.browse(self.cursor, self.uid, compl_ids)

        compl_lines_energia = []
        compl_lines_reactiva = []
        compl_lines_potencia = []

        for compl_line in compl_lines:
            if compl_line.tipus == 'energia':
                compl_lines_energia.append(compl_line)
            elif compl_line.tipus == 'reactiva':
                compl_lines_reactiva.append(compl_line)
            elif compl_line.tipus == 'potencia':
                compl_lines_potencia.append(compl_line)
            elif compl_line.tipus == 'altres':
                if 'Energia' in compl_line.name:
                    compl_lines_energia.append(compl_line)
                elif 'Reactiva' in compl_line.name:
                    compl_lines_reactiva.append(compl_line)
                elif 'Potencia' in compl_line.name:
                    compl_lines_potencia.append(compl_line)
                else:
                    compl_lines_energia.append(compl_line)
            else:
                raise osv.except_osv(
                    "Error !",
                    _(
                        u"Factura amb linies complementaries de tipus desconegut {}"
                    ).format(fact.number),
                )

        compl_matrix = [
            ("energia", "kWh", compl_lines_energia),
            ("potencia", "kW", compl_lines_potencia),
            ("reactiva", "kVArh", compl_lines_reactiva),
        ]

        block = []
        for type, units, compl_lines_x in compl_matrix:
            for start_date in sorted(set([x.data_desde for x in compl_lines_x])):
                date_lines = [x for x in compl_lines_x if x.data_desde == start_date]
                lines = {}
                total = 0.0
                for l in date_lines:  # noqa: E741
                    atr_tolls = self.get_atr_price(fact, tarifa_peajes, l)
                    atr_charges = self.get_atr_price(fact, tarifa_cargos, l)
                    lines[l.product_id.name] = {
                        "quantity": l["quantity"],
                        "price_subtotal": l["price_subtotal"],
                        "price_unit_multi": l["price_unit_multi"],
                        "price_tolls": atr_tolls,
                        "price_charges": atr_charges,
                        "tolls": atr_tolls * l["quantity"],
                        "charges": atr_charges * l["quantity"],
                    }
                    total += l["price_subtotal"]
                lines["total"] = total
                lines["iva"] = get_iva_line(l)
                lines["data_inici"] = start_date
                lines["data_fi"] = l.data_fins
                lines["type"] = type
                lines["units"] = units
                block.append(lines)

        data['energy_lines_data'] = block
        return data

    def get_sub_component_invoice_details_td_excess_power_maximeter(self, fact, pol):
        excess_lines = [l for l in fact.linia_ids if l.tipus == "exces_potencia"]  # noqa: E741
        if not excess_lines:
            return {"is_visible": False}

        if te_quartihoraria(pol):
            return {"is_visible": False}

        excess_lines_data = self.get_sub_component_invoice_details_td(fact, pol, excess_lines)

        lectures_m = []
        for lectura in fact.lectures_potencia_ids:
            lectures_m.append((lectura.name, lectura.pot_maximetre))
        readings = dict(lectures_m)

        excess_data = []
        showing_periods = self.get_matrix_show_periods(pol)

        for excess_lines in excess_lines_data:
            items = {}
            for p in showing_periods:
                if p in excess_lines:
                    item = {}
                    item["power_maximeter"] = readings.get(p, 0)
                    item["power_excess"] = excess_lines[p]["quantity"]
                    item["price_excess"] = excess_lines[p]["price_unit_multi"]
                    item["price_subtotal"] = excess_lines[p]["price_subtotal"]
                    items[p] = item
                items["multi"] = excess_lines["multi"]
                items["total"] = excess_lines["total"]
                items["date_from"] = excess_lines["date_from"]
                items["date_to"] = excess_lines["date_to"]
                items["pre_2025_04_01"] = datetime.strptime(
                    excess_lines["date_to"], "%d/%m/%Y") < datetime(2025, 04, 1)
                items["iva"] = excess_lines["iva"]
            excess_data.append(items)
        data = {
            "showing_periods": showing_periods,
            "excess_data": excess_data,
            "header_multi": 4 * (len(excess_lines_data)),
            "days": (
                datetime.strptime(fact.data_final, "%Y-%m-%d")
                - datetime.strptime(fact.data_inici, "%Y-%m-%d")
            ).days
            + 1,
            "is_visible": True,
            "iva_column": has_iva_column(fact),
        }
        return data

    def get_sub_component_invoice_details_td_excess_power_quarterhours(self, fact, pol):
        excess_lines = [l for l in fact.linia_ids if l.tipus == "exces_potencia"]  # noqa: E741
        if not excess_lines:
            return {"is_visible": False}

        if not te_quartihoraria(pol):
            return {"is_visible": False}

        excess_lines_data = self.get_sub_component_invoice_details_td(fact, pol, excess_lines)
        showing_periods = self.get_matrix_show_periods(pol)

        tariff = get_tariff_from_libfacturacioatr(pol.tarifa.name)
        replace_kp = tariff and fact.date_invoice > factors_kp_change_calculation_date
        # before this date the kp was right, the calculation was wrong
        # after this date has a 31/30 factor depending on month lenght and must be corrected

        excess_data = []
        for excess_lines in excess_lines_data:
            items = {}
            for p in showing_periods:
                if p in excess_lines:
                    item = {}
                    item["kp"] = tariff.factors_k[p] if replace_kp else excess_lines[p]["extra"]
                    item["power_excess"] = excess_lines[p]["quantity"]
                    item["price_excess"] = excess_lines[p]["price_unit_multi"]
                    item["price_subtotal"] = excess_lines[p]["price_subtotal"]
                    items[p] = item
                items["visible_days_month"] = replace_kp and excess_lines["data"]
                items["days"] = excess_lines["days"]
                items["total"] = excess_lines["total"]
                items["date_from"] = excess_lines["date_from"]
                items["date_to"] = excess_lines["date_to"]
                items["iva"] = excess_lines["iva"]
            excess_data.append(items)
        data = {
            "showing_periods": showing_periods,
            "excess_data": excess_data,
            "is_visible": True,
            "header_multi": 4 * (len(excess_data)),
            "iva_column": has_iva_column(fact),
        }
        return data

    def get_sub_component_invoice_details_td_bo_social_2023_data(self, fact, pol):
        visible = False
        rbs_price_per_days = {}
        rbs_lines = []
        for l in fact.linia_ids:  # noqa: E741
            if l.tipus in "altres" and l.invoice_line_id.product_id.code == "RBS":
                if l.price_unit not in rbs_price_per_days:
                    line = {
                        "days": l.quantity,
                        "price_per_day": l.price_unit,
                        "subtotal": l.price_subtotal,
                        "iva": get_iva_line(l),
                    }
                    rbs_price_per_days[l.price_unit] = line
                    rbs_lines.append(line)
                else:
                    line = rbs_price_per_days[l.price_unit]
                    line["days"] += l.quantity
                    line["subtotal"] += l.price_subtotal
                visible = True

        data = {
            "is_visible": visible,
            "number_of_columns": len(self.get_matrix_show_periods(pol)) + 1,
            "iva_column": has_iva_column(fact),
            "lines": rbs_lines,
            "header_multi": len(rbs_lines),
        }
        return data

    def get_sub_component_invoice_details_td_flux_solar_data(self, fact, pol):
        subtotal = 0.0
        visible = False
        iva = ""

        for l in fact.linia_ids:  # noqa: E741
            if l.tipus in "altres" and l.invoice_line_id.product_id.code == "PBV":
                subtotal += l.price_subtotal
                iva = get_iva_line(l)
                visible = True

        data = {
            "is_visible": visible,
            "number_of_columns": len(self.get_matrix_show_periods(pol)) + 1,
            "subtotal": subtotal,
            "iva_column": has_iva_column(fact),
            "iva": iva,
        }
        return data

    def get_sub_component_invoice_details_td_generation_data(self, fact, pol):
        if not fact.linies_generacio or not te_autoconsum_amb_excedents(fact, pol):
            return {"is_visible": False}

        autoconsum_excedents_product_id = self.get_autoconsum_excedents_product_id(fact)
        generation_lines = []
        ajustment = 0.0
        iva = ""
        for l in fact.linies_generacio:  # noqa: E741
            if l.product_id.id == autoconsum_excedents_product_id:
                ajustment += l.price_subtotal
                iva = get_iva_line(l)
            else:
                generation_lines.append(l)

        generation_lines_data = self.get_sub_component_invoice_details_td(
            fact, pol, generation_lines
        )
        ajustment_visible = ajustment > 0.0
        length_generation_lines_data = 3 * (len(generation_lines_data))
        data = {
            "generation_lines_data": generation_lines_data,
            "header_multi": length_generation_lines_data + 1
            if ajustment_visible
            else length_generation_lines_data,
            "showing_periods": self.get_matrix_show_periods(pol),
            "is_visible": True,
            "is_ajustment_visible": ajustment_visible,
            "ajustment": ajustment,
            "ajustment_iva": iva,
            "iva_column": has_iva_column(fact),
        }
        return data

    def sub_component_invoice_details_td_inductive_data_visibility(self, fact, pol):
        data = self.get_sub_component_invoice_details_td_inductive_data(fact, pol)
        if data["is_visible"]:
            return (True, data["inductive_data"]["total"])
        return (False, 0.0)

    def get_sub_component_invoice_details_td_inductive_data(self, fact, pol):
        linies_reactiva = get_reactive_lines_clean(fact)
        if is_6XTD(pol):
            linies_inductiva = [l for l in linies_reactiva if l.name not in (u"P6")]  # noqa: E741, E501
        else:
            linies_inductiva = linies_reactiva
        if not linies_inductiva:
            return {"is_visible": False}

        inductive_data = self.get_sub_component_invoice_details_td_accumulative(
            fact, pol, linies_inductiva
        )
        data = {
            "inductive_data": inductive_data,
            "showing_periods": self.get_matrix_show_periods(pol),
            "is_visible": True,
            "iva_column": has_iva_column(fact),
        }
        return data

    def sub_component_invoice_details_td_capacitive_data_visibility(self, fact, pol):
        data = self.get_sub_component_invoice_details_td_capacitive_data(fact, pol)
        if data["is_visible"]:
            return (True, data["capacitive_data"]["total"])
        return (False, 0.0)

    def get_sub_component_invoice_details_td_capacitive_data(self, fact, pol):
        linies_reactiva = get_reactive_lines_clean(fact)
        linies_capacitiva = [l for l in linies_reactiva if l.name in (u"P6")]  # noqa: E741

        if not linies_capacitiva or not is_6XTD(pol):
            return {"is_visible": False}

        capacitive_data = self.get_sub_component_invoice_details_td_accumulative(
            fact, pol, linies_capacitiva
        )
        data = {
            "capacitive_data": capacitive_data,
            "showing_periods": self.get_matrix_show_periods(pol),
            "is_visible": True,
            "iva_column": has_iva_column(fact),
        }
        return data

    def get_component_amount_destination_td_data(self, fact, pol):
        """
        returns a dictionary with all the amount destination data needed
        """
        if not is_TD(pol):
            return {"is_visible": False}

        # Remove the discounts from the amount total
        flux_solar = 0
        for line in fact.linia_ids:
            if line.tipus in ("altres", "cobrament") and line.product_id.code == "PBV":
                flux_solar += line.price_subtotal

        has_flux = flux_solar > 0
        amount_total = fact.amount_total - flux_solar

        # Repartiment segons BOE
        conf_obj = fact.pool.get("res.config")

        example_data_2023 = {"r": 0.76, "d": 71.0, "t": 27.58, "o": 0.66}
        rep_BOE = conf_obj.get(self.cursor, self.uid, "rep_boe_data", example_data_2023)
        rep_BOE = eval(rep_BOE)

        pie_total = round(amount_total, 2)
        pie_renting = round(fact.total_lloguers, 2)
        pie_taxes = round(float(fact.amount_tax), 2)
        pie_tolls = round(fact.total_atr, 2)
        pie_charges = round(float(fact.total_cargos), 2) if "total_cargos" in fact else 0.0

        # TODO remove this when fields return correct values
        all_tolls = 0.0
        p_tolls = self.get_sub_component_invoice_details_td_power_tolls_data(fact, pol)
        for p_toll in p_tolls.keys():
            if p_toll.startswith(u"P"):
                all_tolls += round(p_tolls[p_toll]["atr_peatge"], 2)
        e_tolls = self.get_sub_component_invoice_details_td_energy_tolls_data(fact, pol)
        for e_toll in e_tolls.keys():
            if e_toll.startswith(u"P"):
                all_tolls += round(e_tolls[e_toll]["atr_peatge"], 2)

        discount_power = self.get_sub_component_invoice_details_td_power_discount_BOE17_2021_data(
            fact, pol
        )
        discount_energy = self.get_sub_component_invoice_details_td_energy_discount_BOE17_2021_data(
            fact, pol
        )
        all_charges = 0.0
        p_charges = self.get_sub_component_invoice_details_td_power_charges_data(
            fact, pol, discount_power
        )
        for p_charge in p_charges.keys():
            if p_charge.startswith(u"P"):
                all_charges += round(p_charges[p_charge]["atr_cargos"], 2)
        e_charges = self.get_sub_component_invoice_details_td_energy_charges_data(
            fact, pol, discount_energy
        )
        for e_charge in e_charges.keys():
            if e_charge.startswith(u"P"):
                all_charges += round(e_charges[e_charge]["atr_cargos"], 2)
        pie_tolls = round(all_tolls, 2)

        # BOE17/2021 wrong calculations in the invoice charges needs to remove twice the discount
        all_charges += discount_power["total"]
        all_charges += discount_energy["total"]
        pie_charges = round(all_charges, 2)
        # END of TODO

        pie_energy = round(pie_total - pie_renting - pie_taxes - pie_tolls - pie_charges, 2)
        data = {
            "is_visible": is_TD(pol),
            "factura_id": fact.id,
            "amount_total": amount_total,
            "pie_renting": pie_renting,
            "pie_taxes": pie_taxes,
            "pie_tolls": pie_tolls,
            "pie_charges": pie_charges,
            "pie_energy": pie_energy,
            "pie_total": pie_total,
            "rep_BOE": rep_BOE,
            "has_flux": has_flux,
        }
        return data

    def get_component_energy_consumption_detail_td_data(self, fact, pol):
        if not is_TD(pol):
            return {}

        adjust_reason = []
        meters = []
        for meter in pol.comptadors:
            data = self.get_sub_component_energy_consumption_detail_meter_td_data(fact, pol, meter)
            if data["is_visible"]:
                meters.append(data)

            adjust_reason.append(data["adjust_reason"])

        collectives = []
        if te_autoconsum_collectiu(fact, pol):
            data = self.get_sub_component_energy_consumption_detail_collective_td_data(fact, pol)
            if data["is_visible"]:
                collectives.append(data)

        highest_adjust_reason = self.adjust_readings_priority(adjust_reason)
        data = {
            "meters": meters,
            "collectives": collectives,
            "info": self.get_sub_component_energy_consumption_detail_td_info_data(
                fact, pol, highest_adjust_reason
            ),
        }
        return data

    def get_sub_component_energy_consumption_detail_meter_td_data(self, fact, pol, meter):
        def visibility(subs):
            return any([sub["is_visible"] for sub in subs])

        def adjust_reason(subs):
            return [sub["adjust_reason"] for sub in subs]

        def add_last_visible(item, subs):
            item["last_visible"] = not visibility(subs)
            return item

        active = self.get_sub_component_energy_consumption_detail_td_active_data(fact, pol, meter)
        surplus = self.get_sub_component_energy_consumption_detail_td_surplus_data(fact, pol, meter)
        inductive = self.get_sub_component_energy_consumption_detail_td_inductive_data(
            fact, pol, meter
        )
        capacitive = self.get_sub_component_energy_consumption_detail_td_capacitive_data(
            fact, pol, meter
        )
        maximeter = self.get_sub_component_energy_consumption_detail_td_maximeter_data(
            fact, pol, meter
        )

        data = {
            "name": meter.name,
            "showing_periods": self.get_matrix_show_periods(pol),
            "active": add_last_visible(active, [surplus, inductive, capacitive, maximeter]),
            "surplus": add_last_visible(surplus, [inductive, capacitive, maximeter]),
            "inductive": add_last_visible(inductive, [capacitive, maximeter]),
            "capacitive": add_last_visible(capacitive, [maximeter]),
            "maximeter": maximeter,
            "is_visible": visibility([active, surplus, inductive, capacitive]),
            "adjust_reason": self.adjust_readings_priority(
                adjust_reason([active, surplus, inductive, capacitive, maximeter])
            ),
        }
        return data

    def adjust_readings_priority(self, adjust_readings_list):
        adjust_readings_list = [adjust for adjust in adjust_readings_list if adjust != False]  # noqa: E712, E501
        if len(adjust_readings_list) == 0:
            return False

        adjust_auto = "98" in adjust_readings_list
        adjust_trTD = "97" in adjust_readings_list
        "96" in adjust_readings_list
        adjust_remaining = [
            adjust for adjust in adjust_readings_list if adjust not in ("98", "97", "96")
        ]
        if len(adjust_remaining) > 0:
            return "99"
        if adjust_auto:
            return "98"
        if adjust_trTD:
            return "97"
        return False

    def get_sub_component_energy_consumption_detail_td_active_data(self, fact, pol, meter):
        (a, a, a, a, lectures_a, a, a, a, a, a, a, a, a, a, a, a, a, a, a) = self.get_readings_data(
            fact
        )
        lectures = lectures_a
        data = {
            "showing_periods": self.get_matrix_show_periods(pol),
            "is_visible": False,
            "title": _(u"Energia Activa (kWh)"),
            "is_active": True,
        }

        adjust_reason = []
        if meter.name in lectures:
            data["is_visible"] = len(lectures[meter.name]) > 0
            for reading in lectures[meter.name]:
                data[reading[0]] = {
                    "initial": reading[1],
                    "final": reading[2],
                    "total": reading[3],
                }
                data["initial_date"] = reading[4]
                if "initial_type" not in data or reading[6] != u"real":
                    data["initial_type"] = reading[6]
                data["final_date"] = reading[5]
                if "final_type" not in data or reading[7] != u"real":
                    data["final_type"] = reading[7]
                adjust_reason.append(reading[9])

        data["adjust_reason"] = self.adjust_readings_priority(adjust_reason)
        return data

    def get_sub_component_energy_consumption_detail_td_surplus_data(self, fact, pol, meter):
        (a, a, a, a, a, a, a, lectures_g, a, a, a, a, a, a, a, a, a, a, a) = self.get_readings_data(
            fact
        )
        lectures = lectures_g
        data = {
            "showing_periods": self.get_matrix_show_periods(pol),
            "is_visible": False,
            "title": _(u"Energia Excedentària (kWh)"),
            "is_active": False,
        }

        adjust_reason = []
        if meter.name in lectures:
            data["is_visible"] = (
                len(lectures[meter.name]) > 0
                and te_autoconsum_amb_excedents(fact, pol)
                and te_autoconsum_no_collectiu(fact, pol)
            )
            for reading in lectures[meter.name]:
                data[reading[0]] = {
                    "initial": reading[1],
                    "final": reading[2],
                    "total": reading[3],
                }
                data["initial_date"] = reading[4]
                if "initial_type" not in data or reading[6] != u"real":
                    data["initial_type"] = reading[6]
                data["final_date"] = reading[5]
                if "final_type" not in data or reading[7] != u"real":
                    data["final_type"] = reading[7]
                adjust_reason.append(reading[9])
        data["hide_total_surplus"] = (
            te_autoconsum_collectiu(fact, pol) and te_autoconsum_no_collectiu(fact, pol)
        )
        data["adjust_reason"] = self.adjust_readings_priority(adjust_reason)
        return data

    def get_sub_component_energy_consumption_detail_td_inductive_data(self, fact, pol, meter):
        (a, a, a, a, a, lectures_r, a, a, a, a, a, a, a, a, a, a, a, a, a) = self.get_readings_data(
            fact
        )
        data = {
            "showing_periods": self.get_matrix_show_periods(pol),
            "is_visible": False,
            "title": _(u"Energia Reactiva Inductiva (kVArh)"),
            "adjust_reason": False,
            "is_active": False,
        }
        if meter.name in lectures_r:
            readings_list = lectures_r[meter.name]
            for reading in readings_list:
                data["is_visible"] = (True,)
                data[reading[0]] = {
                    "initial": reading[1],
                    "final": reading[2],
                    "total": reading[3],
                }
                data["initial_date"] = reading[4]
                if "initial_type" not in data or reading[6] != u"real":
                    data["initial_type"] = reading[6]
                data["final_date"] = reading[5]
                if "final_type" not in data or reading[7] != u"real":
                    data["final_type"] = reading[7]
                if len(reading) == 9 and reading[8] != 0.0:
                    data["has_adjust"] = True

        return data

    def get_sub_component_energy_consumption_detail_td_capacitive_data(self, fact, pol, meter):
        (a, a, a, a, a, a, lectures_c, a, a, a, a, a, a, a, a, a, a, a, a) = self.get_readings_data(
            fact
        )
        data = {
            "showing_periods": self.get_matrix_show_periods(pol),
            "is_visible": False,
            "title": _(u"Energia Reactiva Capacitiva (kVArh)"),
            "adjust_reason": False,
            "is_active": False,
        }
        if meter.name in lectures_c:
            readings_list = lectures_c[meter.name]
            for reading in readings_list:
                data["is_visible"] = (True,)
                data[reading[0]] = {
                    "initial": reading[1],
                    "final": reading[2],
                    "total": reading[3],
                }
                data["initial_date"] = reading[4]
                if "initial_type" not in data or reading[6] != u"real":
                    data["initial_type"] = reading[6]
                data["final_date"] = reading[5]
                if "final_type" not in data or reading[7] != u"real":
                    data["final_type"] = reading[7]
                if len(reading) == 9 and reading[8] != 0.0:
                    data["has_adjust"] = True

        return data

    def get_sub_component_energy_consumption_detail_td_maximeter_data(self, fact, pol, meter):
        excess_lines = [l for l in fact.linia_ids if l.tipus == "exces_potencia"]  # noqa: E741

        data = {
            "showing_periods": self.get_matrix_show_periods(pol),
            "is_visible": pol.facturacio_potencia == "max",
            "title": _(u"Maxímetre (kW)"),
            "adjust_reason": False,
            "is_active": False,
            "is_visible_surplus": len(excess_lines) > 0 and te_quartihoraria(pol),
        }

        periodes_m = sorted(list(set([lectura.name for lectura in fact.lectures_potencia_ids])))

        lectures_m = []
        for lectura in fact.lectures_potencia_ids:
            lectures_m.append((lectura.name, lectura.pot_contract, lectura.pot_maximetre))

        fact_potencia = dict([(p, 0) for p in periodes_m])
        for p in [(p.product_id.name, p.quantity) for p in excess_lines]:
            fact_potencia.update({p[0]: max(fact_potencia.get(p[0], 0), p[1])})

        for reading in lectures_m:
            data[reading[0]] = {
                "contracted": reading[1],
                "reading": reading[2],
                "surplus": fact_potencia[reading[0]],
            }
        return data

    def get_sub_component_energy_consumption_detail_td_info_data(self, fact, pol, adjust_reason):
        dies_factura = (
            datetime.strptime(fact.data_final, "%Y-%m-%d")
            - datetime.strptime(fact.data_inici, "%Y-%m-%d")
        ).days + 1
        diari_factura_actual_eur = fact.total_energia / (dies_factura or 1.0)
        diari_factura_actual_kwh = (fact.energia_kwh * 1.0) / (dies_factura or 1.0)
        lang = fact.lang_partner.lower()

        data = {
            "diari_factura_actual_eur": diari_factura_actual_eur,
            "diari_factura_actual_kwh": diari_factura_actual_kwh,
            "dies_factura": dies_factura,
            "lang": lang,
            "adjust_reason": adjust_reason,
            "has_web": bool(pol.distribuidora.website),
            "web_distri": pol.distribuidora.website,
            "distri_name": pol.distribuidora.name,
        }
        return data

    def get_sub_component_energy_consumption_detail_collective_td_data(self, fact, pol):
        def visibility(subs):
            return any([sub["is_visible"] for sub in subs])

        generated = self.get_sub_component_energy_consumption_detail_td_collective_data_data(
            fact, pol)
        generated["last_visible"] = True
        data = {
            "name": "",
            "showing_periods": self.get_matrix_show_periods(pol),
            "generated": generated,
            "is_visible": visibility([generated]),
            "adjust_reason": False,
        }
        return data

    def get_sub_component_energy_consumption_detail_td_collective_data_data(self, fact, pol):
        f1_obj = fact.pool.get("giscedata.facturacio.importacio.linia")
        f1_lf_obj = fact.pool.get('giscedata.facturacio.importacio.linia.factura')
        f1_cups_ids = f1_obj.search(
            self.cursor,
            self.uid,
            [('cups_id', '=', fact.cups_id.id)],
        )
        f1_lf_ids = f1_lf_obj.search(
            self.cursor,
            self.uid,
            [
                ('linia_id', 'in', f1_cups_ids),
                ('data_inici', '=', fact.data_inici),
                ('data_final', '=', fact.data_final),
                ('type', '=', 'in_invoice'),
            ]
        )

        linies = []
        if f1_lf_ids:
            f1_lf = f1_lf_obj.browse(
                self.cursor,
                self.uid,
                f1_lf_ids[-1]
            )
            linies = [
                linia for linia in f1_lf.factura_id.linia_ids if linia.tipus in [
                    'generacio_neta', 'generacio', 'autoconsum',
                ]
            ]

        data = {
            "showing_periods": self.get_matrix_show_periods(pol),
            "is_visible": False,
            "title": _(u"Autoconsum compartit (kWh)"),
            "is_active": False,
            "hide_total_surplus": (
                te_autoconsum_collectiu(fact, pol) and te_autoconsum_no_collectiu(fact, pol)
            ),
        }

        data["is_visible"] = len(linies) > 0 and te_autoconsum_amb_excedents(fact, pol)

        for p in data["showing_periods"]:
            data[p] = {}

        for linia in linies:
            if linia.name not in data and linia.quantity == 0.0:
                continue
            data[linia.name][linia.tipus] = linia.quantity
            data["initial_date"] = dateformat(linia.data_desde)
            data["final_date"] = dateformat(linia.data_fins)

        return data

    def get_sub_component_energy_consumption_detail_td_collective_data_data_old(self, fact, pol, collective):  # noqa: E501
        # TODO: this function generates dummy data for developing purposes
        (a, a, a, a, a, a, a, lectures_g, a, a, a, a, a, a, a, a, a, a, a) = self.get_readings_data(
            fact
        )
        lectures = lectures_g
        data = {
            "showing_periods": self.get_matrix_show_periods(pol),
            "is_visible": False,
            "title": _(u"Autoconsum compartit (kWh)"),
            "is_active": False,
        }

        meter_name = "304798778"
        adjust_reason = []
        if meter_name in lectures:
            data["is_visible"] = len(lectures[meter_name]) > 0 and te_autoconsum_amb_excedents(
                fact, pol
            )
            for reading in lectures[meter_name]:
                data[reading[0]] = {
                    "generated_coef": reading[1],
                    "auto_consumed": reading[2],
                    "surplus": reading[3],
                }
                data["initial_date"] = reading[4]
                data["final_date"] = reading[5]
                adjust_reason.append(reading[9])

        data["adjust_reason"] = self.adjust_readings_priority(adjust_reason)
        return data

    def get_component_cnmc_comparator_qr_link_data(self, fact, pol):
        # fact needs to have max_potencies_demandades for the QR to be correct
        required_max_requested_powers, max_potencies_demandades = self.max_requested_powers(
            pol, fact
        )

        if not required_max_requested_powers:
            return {
                "is_visible": False,
                "lang": fact.lang_partner.lower(),
            }
        qr_data = self.get_codi_qr(fact)
        data = {
            "is_visible": True,
            "lang": fact.lang_partner.lower(),
            "link_qr": qr_data["url"] if qr_data["url"] else "https://comparador.cnmc.gob.es/",
            "has_gkwh": te_gkwh(fact),
            "qr_image": qr_data["qr"],
        }
        return data

    def get_component_simplified_enviromental_impact_data(self, fact, pol):
        example_mitjana_2020 = """{
            'renovable': 4.9,
            'cae': 4.9,
            'gasNatural': 21.5,
            'carbo': 1.9,
            'fuelGas': 2.2,
            'nuclear': 21.8,
            'altres': 7.7,
            'emisionCo2': 204,
            'residuRadio': 530,
            'year': '2020'}"""
        example_som_2020 = """{
            'renovable': 100.0,
            'cae': 0.0,
            'gasNatural': 0.0,
            'carbo': 0.0,
            'fuelGas': 0.0,
            'nuclear': 0.0,
            'altres': 0.0,
            'emisionCo2': 0,
            'residuRadio': 0,
            'year': '2020'}"""

        def eval_and_json(text):
            text_eval = eval(text)
            text_json = json.dumps(text_eval)
            return json.loads(text_json)

        conf_obj = fact.pool.get("res.config")
        swich_date = conf_obj.get(
            self.cursor, self.uid, "gdo_and_impact_yearly_switch_date", "2099-05-01"
        )

        data = {"is_visible": fact.date_invoice >= swich_date}

        seid_som = conf_obj.get(
            self.cursor, self.uid, "som_environmental_impact_data", example_som_2020
        )
        try:
            data["som"] = eval_and_json(seid_som)
        except Exception:
            data["som"] = eval_and_json(example_som_2020)

        seid_mit = conf_obj.get(
            self.cursor, self.uid, "mitjana_environmental_impact_data", example_mitjana_2020
        )
        try:
            data["mitjana"] = eval_and_json(seid_mit)
        except Exception:
            data["mitjana"] = eval_and_json(example_mitjana_2020)

        return data

    def get_component_solar_flux_info_data(self, fact, pol):

        def has_active_flux_solar(fact, pol):
            for fl in pol.bateria_ids:
                if not fl.data_final or fl.data_final > fact.data_inici:
                    return True
            return False

        if not(te_autoconsum_amb_excedents(fact, pol) or pol.tipus_subseccio == '11'):
            return {"is_visible": False}

        if not has_active_flux_solar(fact, pol):
            return {"is_visible": False}

        imd_obj = self.pool.get("ir.model.data")
        hidden_flux_id = imd_obj.get_object_reference(
            self.cursor, self.uid, "som_polissa", "categ_flux_solar_ocult_ov"
        )[1]
        for categ in pol.category_id:
            if categ.id == hidden_flux_id:
                return {"is_visible": False}

        autoconsum_excedents_product_id = self.get_autoconsum_excedents_product_id(fact)
        ajustment = 0.0
        surplus_kwh = 0.0
        surplus_e = 0.0
        for l in fact.linies_generacio:  # noqa: E741
            if l.product_id.id == autoconsum_excedents_product_id:
                ajustment += l.price_subtotal
            else:
                surplus_kwh += l.quantity
                surplus_e += l.price_subtotal

        surplus_kwh = surplus_kwh * -1.0
        surplus_e = surplus_e * -1.0

        flux_lines = [
            l
            for l in fact.linia_ids  # noqa: E741
            if l.tipus in ("altres", "cobrament") and l.invoice_line_id.product_id.code == "PBV"
        ]

        lang = fact.lang_partner.lower()
        if lang == 'ca_es':
            link_help = 'https://ca.support.somenergia.coop/article/1371-que-es-el-flux-solar'
            link_ov_suns = 'https://oficinavirtual.somenergia.coop/ca/flux-solar/'
            link_nc = 'https://ca.support.somenergia.coop/article/1397-que-son-els-excedents-no-compensats'  # noqa: E501
        else:
            link_help = 'https://es.support.somenergia.coop/article/1372-que-es-el-flux-solar'
            link_ov_suns = 'https://oficinavirtual.somenergia.coop/es/flux-solar/'
            link_nc = 'https://es.support.somenergia.coop/article/1398-que-son-los-excedentes-no-compensados'  # noqa: E501

        return {
            'is_visible': True,
            'surplus_kwh': surplus_kwh,
            'surplus_e': surplus_e,
            'compensation_e': surplus_e - ajustment,
            'ajustment_e': ajustment,
            'suns_generated': ajustment * 0.80,
            'suns_used': sum([l.price_subtotal for l in flux_lines]) * -1.0,   # noqa: E741
            'link_help': link_help,
            'link_ov_suns': link_ov_suns,
            'link_no_compens': link_nc,
        }


GiscedataFacturacioFacturaReport()
