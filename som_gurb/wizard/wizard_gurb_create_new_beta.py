# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime


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

        gurb_cups_beta_o.create(cursor, uid, data, context=context)

        return True

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
