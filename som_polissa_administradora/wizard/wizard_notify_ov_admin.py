# -*- coding: utf-8 -*-

from osv import osv, fields
from datetime import datetime

AVAILABLE_STATES = [("init", "Init"), ("done", "Done")]


class WizardNotifyOVAdmin(osv.osv_memory):

    _name = "wizard.notify.ov.admin"

    def default_get(self, cursor, uid, fields, context={}):
        active_ids = context.get("active_ids", False)

        res = super(WizardNotifyOVAdmin, self).default_get(cursor, uid, fields, context)
        if not active_ids:
            return res

        admin_noti_obj = self.pool.get("som.admin.notification")

        def elipsis(text, length=100):
            if len(text) > length:
                return text[:length] + "..."
            return text

        info = ""
        for noti_id in active_ids:
            noti = admin_noti_obj.browse(cursor, uid, noti_id)
            info += "ID: {}, Receptor: {}".format(noti_id, noti.receptor.name)
            if noti.info:
                info += ", Info: {}".format(elipsis(noti.info))
            info += "\n"

        res["state"] = "init"
        res["info"] = info
        return res

    def send_email(self, cursor, uid, ids, context=None):
        active_ids = context.get("active_ids", [])

        if not active_ids:
            return {}

        admin_noti_obj = self.pool.get("som.admin.notification")

        info = ""

        for noti_id in active_ids:
            try:
                admin_noti_obj.send_email(cursor, uid, noti_id)
                info += "Notificació amb id {}, encuada\n".format(noti_id)
            except Exception as e:
                info += "Notificació amb id {}, error: {}\n".format(
                    noti_id, e.message.replace("\n", " - ")
                )

        self.write(cursor, uid, ids, {"state": "done", "info": info})

        return

    _columns = {
        "state": fields.selection(selection=AVAILABLE_STATES, string="Estat"),
        "info": fields.text("Info"),
    }


WizardNotifyOVAdmin()
