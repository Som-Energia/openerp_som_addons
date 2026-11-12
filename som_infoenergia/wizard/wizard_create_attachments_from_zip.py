# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime
from tools.translate import _
import zipfile
import base64
from io import BytesIO
import os

STATES = [("init", "Estat Inicial"), ("finished", "Estat Final")]


class WizardCreateAttachmentsFromZip(osv.osv_memory):
    _name = "wizard.create.attachments.from.zip"

    _columns = {
        "state": fields.selection(STATES, _(u"Estat del wizard de creació d'adjunts des de ZIP")),
        "name": fields.char(_(u"Nom del fitxer"), size=256),
        "zip_file": fields.binary(_(u"Fitxer ZIP"), required=True),
    }

    _defaults = {"state": "init"}

    def attach_files(self, cursor, uid, ids, context=None):
        lot_obj = self.pool.get("som.infoenergia.lot.enviament")
        env_obj = self.pool.get("som.enviament.massiu")
        wiz = self.browse(cursor, uid, ids[0], context=context)
        lot_id = context.get("active_id", 0)

        lot = lot_obj.browse(cursor, uid, lot_id)
        if lot.tipus != "infoenergia":
            env_ids = env_obj.search(cursor, uid, [("lot_enviament", "=", lot_id)])
            zip_data = base64.b64decode(wiz.zip_file)

            tmp_dir = (
                "/tmp/enviament_massiu_"
                + str(lot.id)
                + "_"
                + datetime.now().strftime("%Y-%m-%d_%H_%M_%S_%f")
            )
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
            zip_file = zipfile.ZipFile(BytesIO(zip_data))
            zip_file.extractall(tmp_dir)
            filenames = zip_file.namelist()
            for env_id in env_ids:
                try:
                    env = env_obj.browse(cursor, uid, env_id)
                    filename_cat = "CONTRACTE_" + env.polissa_id.name + ".pdf"
                    filename_es = "CONTRATO_" + env.polissa_id.name + ".pdf"
                    if filename_cat in filenames:
                        filepath = os.path.join(tmp_dir, filename_cat)
                        env.attach_pdf(filepath, filename_cat)
                    elif filename_es in filenames:
                        filepath = os.path.join(tmp_dir, filename_es)
                        env.attach_pdf(filepath, filename_es)
                except Exception:
                    pass

        wiz.write({"state": "finished"})


WizardCreateAttachmentsFromZip()
