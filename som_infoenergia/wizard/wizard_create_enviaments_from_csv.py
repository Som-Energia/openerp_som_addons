# -*- coding: utf-8 -*-
import base64
import csv
from StringIO import StringIO

from osv import osv, fields
from tools.translate import _


STATES = [("init", "Estat Inicial"), ("finished", "Estat Final")]

FROM_MODEL = [
    ("polissa", "Número de pòlissa"),
    ("partner", "Número de partner"),
]


class WizardCancelFromCSV(osv.osv_memory):
    _name = "wizard.create.enviaments.from.csv"
    _columns = {
        "name": fields.char(_(u"Nom del fitxer"), size=256),
        "csv_file": fields.binary(
            _(u"Fitxer CSV"),
            required=True,
            help=_(
                u"Número de pòlissa de les pòlisses o número de partners dels quals se'n vol crear un enviament"  # noqa: E501
            ),
        ),
        "state": fields.selection(STATES, _(u"Estat del wizard de crear enviaments des de CSV")),
        "info": fields.text(
            _(u"Informació"),
            help=_(u"Només es creen enviaments de pòlisses Activa=Si"),
            size=256,
            readonly=True,
        ),
        "model_name": fields.selection(FROM_MODEL, _(u"Tipus de model a importar")),
    }
    _defaults = {
        "state": "init",
        "model_name": "polissa",
    }

    def create_from_file(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        lot_obj = self.pool.get("som.infoenergia.lot.enviament")
        wiz = self.browse(cursor, uid, ids[0], context=context)

        model_name = "res.partner" if wiz.model_name == "partner" else "giscedata.polissa"
        model_desc = "partners" if wiz.model_name == "partner" else "pòlisses"
        model_id = "partner_id" if wiz.model_name == "partner" else "polissa_id"
        field_search = "ref" if wiz.model_name == "partner" else "name"
        model_obj = self.pool.get(model_name)

        vals = {"from_model": model_id}
        csv_file = StringIO(base64.b64decode(wiz.csv_file))
        reader = csv.reader(csv_file)
        linies = list(reader)
        n_linies = len(linies)
        start = 0
        header = []
        if n_linies > 0 and not linies[0][0].isdigit():
            if ";" in linies[0][0]:
                header = linies[0][0].split(";")
            else:
                header = linies[0]
            start = 1

        item_list = []
        result = {}
        for line in linies[start:]:
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
            vals["extra_text"] = result

        lot_id = context.get("active_id", [])
        item_ids = model_obj.search(cursor, uid, [(field_search, "in", item_list)])
        lot_obj.create_enviaments_from_object_list(cursor, uid, lot_id, item_ids, vals)
        msg = _(
            u"Es crearan els enviaments de {} {} en segon pla".format(len(item_ids), model_desc)
        )
        wiz.write({"state": "finished", "info": msg})
        return True


WizardCancelFromCSV()
