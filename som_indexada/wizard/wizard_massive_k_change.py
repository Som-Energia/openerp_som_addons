# -*- coding: utf-8 -*-
from osv import osv, fields
from StringIO import StringIO
from datetime import timedelta, date
import csv
import base64
from tools.translate import _


class WizardMassiveKChange(osv.osv_memory):
    _name = "wizard.massive.k.change"

    def change_k_from_csv(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz_og = self.browse(cursor, uid, ids[0], context=context)
        polissa_obj = self.pool.get("giscedata.polissa")
        sw_obj = self.pool.get("giscedata.switching")

        failed_polisses = []
        inexistent_polisses = []

        csv_file = StringIO(base64.b64decode(wiz_og.csv_file))
        reader = csv.reader(csv_file)
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
                result_extra_info[header[i]] = int(column) if column.isdigit() else column
                i += 1
            if result_extra_info:
                result[line[0]] = result_extra_info

        if result:
            for polissa_name in item_list:
                polissa_id = polissa_obj.search(cursor, uid, [("name", "=", polissa_name)])
                if not polissa_id:
                    inexistent_polisses.append(polissa_name)
                    continue
                polissa = polissa_obj.browse(cursor, uid, polissa_id)[0]
                try:
                    # Validations before creating new modcon
                    if polissa.state != "activa":
                        failed_polisses.append(polissa.name)
                        continue
                    prev_modcon = polissa.modcontractuals_ids[0]
                    if prev_modcon.state == "pendent":
                        failed_polisses.append(polissa.name)
                        continue
                    res = sw_obj.search(
                        cursor,
                        uid,
                        [
                            ("polissa_ref_id", "=", polissa.id),
                            ("state", "in", ["open", "draft", "pending"]),
                            ("proces_id.name", "!=", "R1"),
                        ],
                    )
                    if res:
                        failed_polisses.append(polissa.name)
                        continue
                    # Create new modcon
                    data_activacio = date.today() + timedelta(days=1)
                    vals_mod = result[polissa.name]
                    polissa.send_signal("modcontractual")
                    polissa_obj.write(cursor, uid, polissa_id[0], vals_mod, context=context)
                    wz_crear_mc_obj = self.pool.get("giscedata.polissa.crear.contracte")
                    ctx = {"active_id": polissa_id[0]}
                    params = {
                        "duracio": "nou",
                        "accio": "nou",
                    }
                    wiz_id = wz_crear_mc_obj.create(cursor, uid, params, context=ctx)
                    wiz = wz_crear_mc_obj.browse(cursor, uid, [wiz_id])[0]
                    res = wz_crear_mc_obj.onchange_duracio(
                        cursor, uid, [wiz.id], str(data_activacio), wiz.duracio, context=ctx
                    )
                    if res.get("warning", False):
                        polissa.send_signal("undo_modcontractual")
                        raise osv.except_osv("Error", res["warning"])
                    else:
                        wiz.write(
                            {
                                "data_inici": str(data_activacio),
                                "data_final": str(data_activacio + timedelta(days=364)),
                            }
                        )
                        wiz.action_crear_contracte()
                except Exception:
                    polissa.send_signal("undo_modcontractual")
                    failed_polisses.append(polissa.name)

        info = ""

        if inexistent_polisses:
            info = "Les pòlisses següents no existeixen: {}".format(str(inexistent_polisses))
        if failed_polisses:
            info += "\nLes pòlisses següents han fallat: {}".format(str(failed_polisses))
        if not inexistent_polisses and not failed_polisses:
            info = "Procés acabat correctament!"

        wiz_og.write({"state": "end", "info": info})

        return True

    _columns = {
        "state": fields.selection(
            [("init", "Init"), ("end", "End")],
            "State",
        ),
        "name": fields.char("Filename", size=256),
        "csv_file": fields.binary(
            "CSV File", required=True, help=(u"CSV amb les pòlisses a canviar la K")
        ),
        "info": fields.text("Description"),
    }

    _defaults = {
        "state": lambda *a: "init",
    }


WizardMassiveKChange()
