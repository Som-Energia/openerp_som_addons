# -*- coding: utf-8 -*-
import base64
from decimal import Decimal, ROUND_HALF_UP
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
            ("inscription_date", "<=", today),
            ("state", "in", [
                "comming_registration", "comming_modification", "active", "atr_pending"
            ]),
        ]

        gurb_cups_ids = gurb_cups_o.search(cursor, uid, search_params, context=context)

        items = gurb_cups_o.read(cursor, uid, gurb_cups_ids, ['cups_id'], context=context)

        coefs = []
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

            coefs.append(
                Decimal(str(beta)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            )

        # Adjust last coef to ensure the sum is exactly 1 (avoids float rounding errors)
        if coefs:
            diff = Decimal('1') - sum(coefs)
            max_rounding_error = Decimal('0.0000005') * len(coefs)
            if abs(diff) <= max_rounding_error:
                coefs[-1] += diff

        for item, coef in zip(items, coefs):
            item["coef"] = str(coef).replace(".", ",")

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

        write_vals['generation_date'] = today
        for wizard in self.read(
            cursor, uid, ids,
            ['state', 'save_attachment', 'update_agreement_date'], context=context
        ):
            if wizard['state'] == 'done':
                continue
            if wizard['save_attachment']:
                self.pool.get('ir.attachment').create(cursor, uid, {
                    'name': file_name,
                    'datas': mfile,
                    'datas_fname': file_name,
                    'res_model': 'som.gurb.cau',
                    'res_id': current_gurb,
                }, context=context)
            if wizard['update_agreement_date']:
                self.pool.get('som.gurb.cau').write(cursor, uid, [current_gurb], {
                    'last_distribution_agreement_date': today,
                }, context=context)
            self.write(cursor, uid, [wizard['id']], write_vals, context=context)

    _columns = {
        "state": fields.selection(
            [
                ("init", "Inicial"),
                ("done", "Final"),
            ],
            "State",
        ),
        "generation_date": fields.date("Data de generació", readonly=True),
        "save_attachment": fields.boolean("Guardar fitxer de coeficients al GURB CAU"),
        "update_agreement_date": fields.boolean(
            "Actualitzar data d'últim acord de repartiment al GURB CAU"
        ),
        "file": fields.binary("Fitxer de Coeficients"),
        "file_name": fields.char("Nom fitxer", size=128),
    }

    _defaults = {
        "state": lambda *a: "init",
        "generation_date": lambda *a: datetime.today().strftime('%Y-%m-%d'),
        "save_attachment": lambda *a: False,
        "update_agreement_date": lambda *a: False,
    }


WizardCreateCoeficicientsFile()
