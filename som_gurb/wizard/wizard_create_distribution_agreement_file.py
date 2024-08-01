# -*- coding: utf-8 -*-
import base64
from osv import osv, fields
from datetime import datetime


class WizardCreateDistributionAgreement(osv.osv_memory):

    _name = 'wizard.create.distribution.agreement'

    def get_items(self, cursor, uid, today, context=None):
        if context is None:
            context = {}

        current_gurb = context.get('active_id')

        gurb_cups_o = self.pool.get('som.gurb.cups')

        search_params = [
            ("gurb_id", "=", current_gurb),
            ("active", "=", True),
            ("start_date", "<=", today),
        ]

        gurb_cups_ids = gurb_cups_o.search(cursor, uid, search_params, context=context)

        items = gurb_cups_o.read(cursor, uid, gurb_cups_ids, ['cups_id'], context=context)

        for item in items:
            if item.get("cups_id"):
                item["cups"] = item["cups_id"][1]
            else:
                raise osv.except_osv(
                    "Hi ha GURB CUPS sense CUPS definit!",
                    "El GURB CUPS amb id {} no té CUPS definit".format(item["id"])
                )

            beta = gurb_cups_o.get_beta_percentatge(
                cursor, uid, item["id"], context=context
            )[item["id"]] / 100

            item["coef"] = "{:1,.6f}".format(beta).replace(".", ",")

        return items

    def create_txt(self, cursor, uid, items, date, context=None):
        if context is None:
            context = {}

        file_name = "acord_de_repartiment_{}.txt".format(date)

        txt = ""

        for item in items:
            line = "{};{}\r\n".format(item["cups"], item["coef"])
            txt += line

        mfile = base64.b64encode(txt.encode('utf-8'))

        return file_name, mfile

    def create_distribution_agreement_txt(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        current_gurb = context.get('active_id')
        if not current_gurb:
            return False

        today = datetime.today().strftime('%Y-%m-%d')

        items = self.get_items(cursor, uid, today, context=context)

        file_name, mfile = self.create_txt(cursor, uid, items, today, context=context)

        write_vals = {
            "file": mfile,
            "state": "done",
            "file_name": file_name,
        }

        self.write(cursor, uid, ids, write_vals, context=context)

    _columns = {
        "state": fields.selection(
            [
                ("init", "Inicial"),
                ("done", "Final"),
            ],
            "State",
        ),
        "file": fields.binary("Acord de Repartiment"),
        "file_name": fields.char("Nom fitxer", size=128),
    }

    _defaults = {
        "state": lambda *a: "init",
    }


WizardCreateDistributionAgreement()
