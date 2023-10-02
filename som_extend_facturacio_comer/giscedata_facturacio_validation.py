# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from osv import osv
from dateutil.relativedelta import relativedelta


class GiscedataFacturacioValidationValidator(osv.osv):
    _name = "giscedata.facturacio.validation.validator"
    _inherit = "giscedata.facturacio.validation.validator"
    _desc = "Validador de factures"

    def check_missing_days(self, cursor, uid, fact, parameters):
        modcontract_obj = self.pool.get("giscedata.polissa.modcontractual")
        fact_obj = self.pool.get("giscedata.facturacio.factura")

        trad_months_fact = {1: "n_days_mensual", 2: "n_days_bimensual", 12: "n_days_anual"}

        months_fact = fact.polissa_id.facturacio
        increment = relativedelta(months=months_fact, days=-1)

        start_date = datetime.strptime(fact.data_inici, "%Y-%m-%d")
        end_date = datetime.strptime(fact.data_final, "%Y-%m-%d")
        expected_final_date = start_date + increment

        expected = (expected_final_date - start_date).days
        actual = (end_date - start_date).days
        difference = expected - actual
        margin = parameters[trad_months_fact[months_fact]]

        if difference > margin:
            # Hi ha una modcon amb data: fact.data_final + 1 dies
            data_final = end_date + timedelta(days=1)
            polissa_id = fact.polissa_id.id
            mod = modcontract_obj.search(
                cursor,
                uid,
                [
                    ("polissa_id", "=", polissa_id),
                    ("data_inici", "=", data_final.strftime("%Y-%m-%d")),
                ],
            )

            # Hi ha una factura posterior
            posterior = fact_obj.search(
                cursor,
                uid,
                [
                    ("data_inici", ">", fact.data_inici),
                    ("id", "!=", fact.id),
                    ("polissa_id", "=", polissa_id),
                ],
            )

            if mod and not posterior:
                return {"margin": margin, "actual_days": actual, "expected_days": expected}

        return None


GiscedataFacturacioValidationValidator()
