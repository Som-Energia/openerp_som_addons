# -*- coding: utf-8 -*-
from osv import osv
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class GiscedataFacturacioValidationValidator(osv.osv):
    _inherit = "giscedata.facturacio.validation.validator"
    _name = "giscedata.facturacio.validation.validator"

    def check_origin_readings_by_contract_category(self, cursor, uid, fact, parameters):

        if "categoria" not in parameters:
            return None

        pcat_obj = self.pool.get("giscedata.polissa.category")
        pcat_ids = pcat_obj.search(
            cursor, uid, [("name", "like", "%" + parameters["categoria"] + "%")]
        )

        if pcat_ids and pcat_ids[0] in [x.id for x in fact.polissa_id.category_id]:

            lect_obj = self.pool.get("giscedata.lectures.lectura")

            lo_obj = self.pool.get("giscedata.lectures.origen")
            loc_obj = self.pool.get("giscedata.lectures.origen_comer")

            not_alowed_origins_ids = lo_obj.search(
                cursor, uid, [("codi", "in", eval(parameters["lectures_origen_codes"]))]
            )
            not_alowed_origins_comer_ids = loc_obj.search(
                cursor, uid, [("codi", "in", eval(parameters["lectures_origen_comer_codes"]))]
            )

            data_inici = datetime.strptime(fact.data_inici, "%Y-%m-%d") - timedelta(days=1)

            clause = [
                ("comptador.polissa", "=", fact.polissa_id.id),
                ("comptador.active", "=", True),
                ("tipus", "=", "A"),
                ("name", ">=", data_inici.strftime("%Y-%m-%d")),
                ("name", "<=", fact.data_final),
            ]
            if not_alowed_origins_ids:
                clause.append(("origen_id", "in", not_alowed_origins_ids))
            if not_alowed_origins_comer_ids:
                clause.append(("origen_comer_id", "in", not_alowed_origins_comer_ids))

            lectures_ids = (
                lect_obj.q(cursor, uid)
                .read(["id", "name", "origen_id", "origen_comer_id"], order_by=["name.asc"])
                .where(clause)
            )

            if len(lectures_ids) == 0:
                return None

            origen_id = list(set([x["origen_id"] for x in lectures_ids]))
            origen_comer_id = list(set([x["origen_comer_id"] for x in lectures_ids]))

            origins = [x["name"] for x in lo_obj.read(cursor, uid, origen_id, ["name"])]
            origins_comer = [
                x["name"] for x in loc_obj.read(cursor, uid, origen_comer_id, ["name"])
            ]

            return {
                "categoria": parameters["categoria"],
                "origen": ",".join(origins),
                "origen_distri": ",".join(origins_comer),
            }

        return None

    def check_min_periods_and_teoric_maximum_consum(self, cursor, uid, fact, parameters):

        if "category" not in parameters:
            return None

        pcat_obj = self.pool.get("giscedata.polissa.category")
        pcat_ids = pcat_obj.search(
            cursor, uid, [("name", "like", "%" + parameters["category"] + "%")]
        )

        if pcat_ids and pcat_ids[0] in [x.id for x in fact.polissa_id.category_id]:

            fact_obj = self.pool.get("giscedata.facturacio.factura")

            pol_obj = self.pool.get("giscedata.polissa")
            teoric_maximum_consume_gc = pol_obj.read(
                cursor, uid, fact.polissa_id.id, ["teoric_maximum_consume_gc"]
            )["teoric_maximum_consume_gc"]

            n_months = parameters["n_months"]
            min_periods = parameters.get("min_periods", False)
            to_date = datetime.strptime(fact.data_inici, "%Y-%m-%d")
            from_date = to_date - relativedelta(months=n_months)

            context = {}
            if parameters.get("min_invoice_len"):
                context["min_invoice_len"] = parameters.get("min_invoice_len")

            parameter_by_date = fact_obj.get_parameter_by_contract(
                cursor,
                uid,
                fact.polissa_id.id,
                "energia_kwh",
                from_date,
                to_date,
                min_periods,
                context=context,
            )

            max_consume = False
            number_of_invoices = len(parameter_by_date)
            if number_of_invoices > 0:
                max_consume = max(parameter_by_date.values())

            if (not max_consume or number_of_invoices < n_months) and (
                not teoric_maximum_consume_gc or teoric_maximum_consume_gc == 0
            ):
                return {
                    "invoice_consume": fact.energia_kwh,
                }

        return None

    def check_consume_by_percentage_and_category(self, cursor, uid, fact, parameters):

        if "category" not in parameters:
            return None

        pcat_obj = self.pool.get("giscedata.polissa.category")
        pcat_ids = pcat_obj.search(
            cursor, uid, [("name", "like", "%" + parameters["category"] + "%")]
        )

        if pcat_ids and pcat_ids[0] in [x.id for x in fact.polissa_id.category_id]:

            fact_obj = self.pool.get("giscedata.facturacio.factura")

            if parameters.get("min_amount", False) and abs(fact.amount_total) <= parameters.get(
                "min_amount", 0.0
            ):
                return None

            n_months = parameters["n_months"]
            min_periods = parameters.get("min_periods", False)
            to_date = datetime.strptime(fact.data_inici, "%Y-%m-%d")
            from_date = to_date - relativedelta(months=n_months)

            context = {}
            if parameters.get("min_invoice_len"):
                context["min_invoice_len"] = parameters.get("min_invoice_len")

            parameter_by_date = fact_obj.get_parameter_by_contract(
                cursor,
                uid,
                fact.polissa_id.id,
                "energia_kwh",
                from_date,
                to_date,
                min_periods,
                context=context,
            )

            max_consume = False
            number_of_invoices = len(parameter_by_date)
            if number_of_invoices > 0:
                max_consume = max(parameter_by_date.values())

            pol_obj = self.pool.get("giscedata.polissa")
            teoric_maximum_consume_gc = pol_obj.read(
                cursor, uid, fact.polissa_id.id, ["teoric_maximum_consume_gc"]
            )["teoric_maximum_consume_gc"]

            if not max_consume or number_of_invoices < n_months:
                max_consume = False

            if not max_consume and teoric_maximum_consume_gc and teoric_maximum_consume_gc > 0:
                max_consume = teoric_maximum_consume_gc

            if max_consume:
                percentage_margin = parameters["overuse_percentage"]

                inv_consume = fact.energia_kwh
                if inv_consume > (max_consume * (100.0 + percentage_margin)) / 100.0:
                    return {
                        "invoice_consume": inv_consume,
                        "percentage": percentage_margin,
                        "maximum_consume": max_consume,
                        "n_months": n_months,
                        "maximum_teoric_consume_GC": teoric_maximum_consume_gc
                        if teoric_maximum_consume_gc
                        else 0,
                    }

        return None

    def check_consume_by_percentage(self, cursor, uid, fact, parameters):

        pcat_obj = self.pool.get("giscedata.polissa.category")
        pcat_ids = pcat_obj.search(cursor, uid, [("name", "like", "%Gran Contracte%")])

        if pcat_ids and pcat_ids[0] in [x.id for x in fact.polissa_id.category_id]:
            return None

        return super(GiscedataFacturacioValidationValidator, self).check_consume_by_percentage(
            cursor, uid, fact, parameters
        )

    def check_consume_by_amount(self, cursor, uid, fact, parameters):

        pcat_obj = self.pool.get("giscedata.polissa.category")
        pcat_ids = pcat_obj.search(cursor, uid, [("name", "like", "%%Gran Contracte%")])

        if pcat_ids and pcat_ids[0] in [x.id for x in fact.polissa_id.category_id]:
            return None

        return super(GiscedataFacturacioValidationValidator, self).check_consume_by_amount(
            cursor, uid, fact, parameters
        )

    def validate_one_invoice(self, cursor, uid, fact_id, validation_id, context=None):
        if context is None:
            context = {}

        fact_obj = self.pool.get("giscedata.facturacio.factura")
        tmpl_obj = self.pool.get("giscedata.facturacio.validation.warning.template")

        tmpl_fields = ["code", "method", "parameters", "description", "active"]
        template_vals = tmpl_obj.read(cursor, uid, validation_id, tmpl_fields, context)

        fact = fact_obj.browse(cursor, uid, fact_id)
        vals = getattr(self, template_vals["method"])(
            cursor, uid, fact, template_vals["parameters"]
        )

        ret = {
            "active": template_vals["active"],
            "code": template_vals["code"],
        }
        if vals is not None:
            ret.update(
                {
                    "message": template_vals["description"].format(**vals),
                    "validation_warning": True,
                }
            )
        else:
            ret.update(
                {
                    "message": "",
                    "validation_warning": False,
                }
            )
        return ret


GiscedataFacturacioValidationValidator()
