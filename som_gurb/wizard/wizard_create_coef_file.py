# -*- coding: utf-8 -*-
import base64
from osv import osv, fields
from datetime import datetime


class WizardCreateCoeficicientsFile(osv.osv_memory):

    _name = "wizard.create.coeficients.file"

    def get_items(self, cursor, uid, today, context=None):
        if context is None:
            context = {}

        current_gurb = context.get('active_id')

        gurb_cups_o = self.pool.get('som.gurb.cups')

        search_params = [
            ("gurb_cau_id", "=", current_gurb),
            ("active", "=", True),
            ("start_date", "<=", today),
            ("state", "in", [
                "comming_registration", "comming_modification", "active", "atr_pending"
            ]),
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

            beta = gurb_cups_o.get_new_beta_percentatge(
                cursor, uid, item["id"], context=context
            )[item["id"]] / 100

            item["coef"] = "{:1,.6f}".format(beta).replace(".", ",")

        return items

    def create_txt(self, cursor, uid, items, date, context=None):
        if context is None:
            context = {}

        current_gurb = context.get('active_id')

        gurb_o = self.pool.get('som.gurb.cau')
        self_cons_name = gurb_o.read(
            cursor, uid, current_gurb, ['self_consumption_id']
        )['self_consumption_id'][1]

        file_name = "{}_{}.txt".format(self_cons_name, date[:4])

        txt = ""

        for item in items:
            line = "{};{}\r\n".format(item["cups"], item["coef"])
            txt += line

        mfile = base64.b64encode(txt[:-2].encode('utf-8'))

        return file_name, mfile

    def create_coeficients_file_txt(self, cursor, uid, ids, context=None):
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
        "file": fields.binary("Fitxer de Coeficients"),
        "file_name": fields.char("Nom fitxer", size=128),
    }

    _defaults = {
        "state": lambda *a: "init",
    }


WizardCreateCoeficicientsFile()
