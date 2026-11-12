# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime
from tools.translate import _


class WizardGurbCreateNewBeta(osv.osv_memory):
    _name = "wizard.gurb.create.new.beta"

    def create_new_beta(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        gurb_cups_o = self.pool.get("som.gurb.cups")
        gurb_cups_beta_o = self.pool.get("som.gurb.cups.beta")
        gurb_cups_id = context.get("active_id", False)
        wiz = self.browse(cursor, uid, ids[0], context=context)

        data = {
            "start_date": wiz.start_date,
            "beta_kw": wiz.beta_kw,
            "extra_beta_kw": wiz.extra_beta_kw,
            "gift_beta_kw": wiz.gift_beta_kw,
            "gurb_cups_id": gurb_cups_id,
            "active": True,
            "future_beta": True,
        }

        search_params = [
            ("active", "=", True),
            ("gurb_cups_id", "=", gurb_cups_id),
            ("future_beta", "=", False),
        ]

        gurb_cups_state = gurb_cups_o.read(
            cursor, uid, gurb_cups_id, ["state"], context=context
        )["state"]

        old_beta_id = gurb_cups_beta_o.search(cursor, uid, search_params, context=context)
        if old_beta_id:
            read_vals = ["start_date", "beta_kw", "extra_beta_kw", "gift_beta_kw"]
            old_beta_vals = gurb_cups_beta_o.read(
                cursor, uid, old_beta_id[0], read_vals, context=context
            )
            same_extra_beta = wiz.extra_beta_kw == old_beta_vals["extra_beta_kw"]
            same_gift_beta = wiz.gift_beta_kw == old_beta_vals["gift_beta_kw"]
            same_beta = wiz.beta_kw == old_beta_vals["beta_kw"]

            if same_extra_beta and same_beta and same_gift_beta:
                raise osv.except_osv(
                    _("Mateixos valors!"),
                    _("S'està creant una beta amb els mateixos valors que la beta anterior.")
                )
            if wiz.beta_kw < 0 or wiz.extra_beta_kw < 0 or wiz.gift_beta_kw < 0:
                raise osv.except_osv(
                    _("Beta incorrecte!"),
                    _("La nova beta ha de ser més gran o igual que zero.")
                )
            if wiz.beta_kw == 0 and wiz.extra_beta_kw == 0 and wiz.gift_beta_kw == 0:
                raise osv.except_osv(
                    _("Beta incorrecte!"),
                    _("El total de la beta, la beta extra i la beta regal"),
                    _("ha de ser més gran a zero.")
                )
            if wiz.start_date <= old_beta_vals["start_date"]:
                raise osv.except_osv(
                    _("Data incorrecte!"),
                    _("La nova data inici ha de ser més gran que la data inici de la beta activa.")
                )
            if wiz.start_date > datetime.strftime(datetime.today(), "%Y-%m-%d"):
                raise osv.except_osv(
                    _("Data incorrecte!"),
                    _("No es pot fer un canvi de beta a futur.")
                )

        search_params = [
            ("active", "=", True),
            ("gurb_cups_id", "=", gurb_cups_id),
            ("future_beta", "=", True),
        ]
        future_beta_id = gurb_cups_beta_o.search(cursor, uid, search_params, context=context)
        if future_beta_id:
            gurb_cups_beta_o.write(
                cursor, uid, future_beta_id[0], data, context=context
            )
        else:
            gurb_cups_beta_o.create(cursor, uid, data, context=context)

        if gurb_cups_state in ["draft"]:
            gurb_cups_o.send_signal(cursor, uid, [gurb_cups_id], "button_create_cups")
        elif gurb_cups_state in ["active"]:
            gurb_cups_o.send_signal(cursor, uid, [gurb_cups_id], "button_pending_modification")
        elif gurb_cups_state in ["comming_cancellation", "cancel", "atr_pending"]:
            raise osv.except_osv(
                _("Estat incorrecte!"),
                _("No es pot crear una nova beta en estat {}.").format(gurb_cups_state)
            )

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
        "gift_beta_kw": fields.float(
            "Beta regal (kW)",
            digits=(10, 3),
            required=True,
        ),
    }

    _defaults = {
        "start_date": lambda *a: datetime.strftime(datetime.today(), "%Y-%m-%d"),
    }


WizardGurbCreateNewBeta()
