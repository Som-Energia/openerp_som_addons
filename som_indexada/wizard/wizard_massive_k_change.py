# -*- coding: utf-8 -*-
from osv import osv, fields
from StringIO import StringIO
import csv
import base64
from tools.translate import _


class WizardMassiveKChange(osv.osv_memory):
    _name = 'wizard.massive.k.change'

    def change_k_from_csv(self, cursor, uid, ids, context=None):
        import pudb; pu.db
        if context is None:
            context = {}

        wiz = self.browse(cursor, uid, ids[0], context=context)
        polissa_obj = self.pool.get("giscedata.polissa")
        ir_model_data = self.pool.get("ir.model.data")

        csv_file = StringIO(base64.b64decode(wiz.csv_file))
        reader = csv.reader(csv_file, encoding='utf-8')
        lines = list(reader)
        first_line = 0
        header = []
        if len(lines) > 0 and not lines[0][0].isdigit():
            if ";" in lines[0][0]:
                header = lines[0][0].split(";")
            else:
                header = lines[0]
            first_line = 1

        item_list = []
        result = {}
        for line in lines[first_line:]:
            if ";" in line[0]:
                line = line[0].split(";")
            item_list.append(line[0])
            if not header:
                continue
            i = 1
            result_extra_info = {}
            for column in line[1:]:
                result_extra_info[header[i]] = int(
                    column) if column.isdigit() else column
                i += 1
            if result_extra_info:
                result[line[0]] = result_extra_info

        ctx = {}
        if result:
            ctx["extra_text"] = result
            ctx["from_model"] = "polissa_id"

        template_id = ir_model_data.get_object_reference(
            cursor, uid, "som_indexada", "email_canvi_massiu_k"
        )[1]
        lot_obj = self.pool.get("som.infoenergia.lot.enviament")
        lot_id = lot_obj.create(
            cursor,
            uid,
            {
                "name": wiz.enviament_name,
                "tipus": "altres",  # Lot enviament massiu
                "email_template": template_id,
            },
            context=context
        )
        item_ids = polissa_obj.search(
            cursor,
            uid,
            [("name", "in", item_list)],
        )
        lot_obj.create_enviaments_from_object_list(
            cursor, uid, lot_id, item_ids, context=ctx
        )
        msg = _(
            u"Es crearan els enviaments de {} en segon pla"
            .format(len(item_ids))
        )
        wiz.write({"state": "finished", "info": msg})
        return True

    _columns = {
        "state": fields.selection(
            [("init", "Init"), ("end", "End")],
            "State",
        ),
        "name": fields.char("Filename", size=256),
        "enviament_name": fields.char("Nom del lot d'enviament", size=256),
        "csv_file": fields.binary(
            "CSV File",
            required=True,
            help=(u"CSV amb les pòlisses a canviar la K")
        ),
        "info": fields.text(
            _(u"Informació"),
            help=(u"Només es creen enviaments de pòlisses actives"),
            size=256,
            readonly=True,
        ),
    }

    _defaults = {
        "state": lambda *a: "init",
    }


WizardMassiveKChange()
