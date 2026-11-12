# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _


STATES = [("init", "Estat Inicial"), ("finished", "Estat Final")]


class WizardDownloadCSV(osv.osv_memory):
    _name = "wizard.infoenergia.download.csv"

    def download_csv(self, cursor, uid, ids, context=None):
        wiz = self.browse(cursor, uid, ids[0], context=context)
        lot_obj = self.pool.get("som.infoenergia.lot.enviament")

        lot_id = context.get("active_id", [])
        context["path_csv"] = wiz.path_csv
        context["path_pdf"] = wiz.path_pdf

        wiz.write({"state": "finished"})
        lot = lot_obj.browse(cursor, uid, lot_id)
        lot.get_csv(context=context)

    _columns = {
        "state": fields.selection(STATES, _(u"Estat del wizard de baixada de CSV")),
        "path_pdf": fields.char(_("Ruta carpeta dels PDFs"), size=256),
        "path_csv": fields.char(_("Ruta fitxer CSV"), size=256),
    }

    _defaults = {"state": "init"}


WizardDownloadCSV()
