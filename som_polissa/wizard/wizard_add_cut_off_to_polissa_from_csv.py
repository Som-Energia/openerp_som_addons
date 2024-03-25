# -*- coding: utf-8 -*-
from osv import osv, fields
from StringIO import StringIO
import csv
import base64


class WizardAddCutOffToPolissaFromCSV(osv.osv_memory):
    _name = 'wizard.add.cut.off.to.polissa.from.csv'

    def add_cut_off_from_csv(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz = self.browse(cursor, uid, ids[0], context=context)
        polissa_obj = self.pool.get("giscedata.polissa")
        self.pool.get("giscedata.polissa.nocutoff")

        failed_polisses = []
        inexistent_polisses = []
        multiple_polisses = []

        csv_file = StringIO(base64.b64decode(wiz.csv_file))
        reader = csv.reader(csv_file)
        lines = list(reader)
        first_line = 0

        item_list = []
        for line in lines[first_line:]:
            if ";" in line[0]:
                line = line[0].split(";")
            item_list.append(line[0])

        for cups_name in item_list:
            polissa_id = polissa_obj.search(
                cursor, uid, [('cups.name', '=ilike', '{}%'.format(cups_name[:20]))]
            )
            if not polissa_id:
                inexistent_polisses.append(cups_name)
                continue
            if len(polissa_id) > 1:
                multiple_polisses.append(cups_name)
                continue
            polissa = polissa_obj.browse(cursor, uid, polissa_id)[0]
            try:
                if polissa.state != 'activa':
                    failed_polisses.append(polissa.name)
                    continue
                polissa_obj.write(cursor, uid, polissa_id, {'nocutoff': wiz.cut_off.id})

            except Exception:
                failed_polisses.append(polissa.name)

        info = ""

        if inexistent_polisses:
            info = "No s'ha trobat una pòlissa activa pels següents CUPS: {}".format(
                str(inexistent_polisses))
        if failed_polisses:
            info += "\nLes pòlisses següents han fallat: {}".format(str(failed_polisses))
        if multiple_polisses:
            info += "\nS'ha trobat meś d'una pòlissa pels següents CUPS: {}".format(
                str(multiple_polisses))
        if not inexistent_polisses and not failed_polisses and not multiple_polisses:
            info = "Procés acabat correctament!"

        wiz.write(
            {
                "state": "end",
                "info": info
            }
        )

        return True

    _columns = {
        "state": fields.selection(
            [("init", "Init"), ("end", "End")],
            "State",
        ),
        "name": fields.char("Filename", size=256),
        "csv_file": fields.binary(
            "CSV File",
            required=True,
            help=(u"CSV amb els CUPS de les pòlisses a marcar com a no tallables")
        ),
        'info': fields.text('Description'),
        'cut_off': fields.many2one('giscedata.polissa.nocutoff', "Motiu no tallable"),
    }

    _defaults = {
        "state": lambda *a: "init",
    }


WizardAddCutOffToPolissaFromCSV()
