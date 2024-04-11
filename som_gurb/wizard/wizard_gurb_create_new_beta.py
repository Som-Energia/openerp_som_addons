# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime, timedelta
from tools.translate import _


class WizardGurbCreateNewBeta(osv.osv_memory):
    _name = "wizard.gurb.create.new.beta"

    def create_new_beta(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        gurb_cups_beta_o = self.pool.get("som.gurb.cups.beta")
        gurb_cups_id = context.get("active_id", False)
        wiz = self.browse(cursor, uid, ids[0], context=context)

        data = {
            "start_date": wiz.start_date,
            "beta_kw": wiz.beta_kw,
            "extra_beta_kw": wiz.extra_beta_kw,
            "gurb_cups_id": gurb_cups_id,
            "active": True
        }

        search_params = [
            ("active", "=", True),
            ("gurb_cups_id", "=", gurb_cups_id)
        ]

        old_beta_id = gurb_cups_beta_o.search(cursor, uid, search_params, context=context)
        if old_beta_id:
            read_vals = ["start_date", "beta_kw", "extra_beta_kw"]
            old_beta_vals = gurb_cups_beta_o.read(
                cursor, uid, old_beta_id[0], read_vals, context=context
            )
            same_extra_beta = wiz.extra_beta_kw == old_beta_vals["extra_beta_kw"]
            same_beta = wiz.beta_kw == old_beta_vals["beta_kw"]

            if same_extra_beta and same_beta:
                raise osv.except_osv(
                    _("Mateixos valors!"),
                    _("S'està creant una beta amb els mateixos valors que la beta anterior.")
                )
            if wiz.beta_kw < 0 or wiz.extra_beta_kw < 0:
                raise osv.except_osv(
                    _("Beta incorrecte!"),
                    _("La nova beta ha de ser més gran o igual que zero.")
                )
            if wiz.beta_kw == 0 and wiz.extra_beta_kw == 0:
                raise osv.except_osv(
                    _("Beta incorrecte!"),
                    _("El total de la beta i la beta extra ha de ser més gran a zero.")
                )
            if wiz.start_date <= old_beta_vals["start_date"]:
                raise osv.except_osv(
                    _("Data incorrecte!"),
                    _("La nova data inici ha de ser més gran que la data inici de la beta activa.")
                )

            write_params = {
                "active": False,
                "end_date": datetime.strptime(wiz.start_date, "%Y-%m-%d") - timedelta(days=1)
            }
            gurb_cups_beta_o.write(cursor, uid, old_beta_id[0], write_params, context=context)

        gurb_cups_beta_o.create(cursor, uid, data, context=context)

        return {"type": "ir.actions.act_window_close"}

    _columns = {
        "start_date": fields.date("Data inici", required=True),
        "beta_kw": fields.float(
            "Beta (kW)",
            digits=(10, 3),
            required=True,
        ),
        "extra_beta_kw": fields.float(
            "Extra Beta (kW)",
            digits=(10, 3),
            required=True,
        ),
    }

    _default = {
        "start_date": datetime.strftime(datetime.today(), "%Y-%m-%d"),
    }


WizardGurbCreateNewBeta()
