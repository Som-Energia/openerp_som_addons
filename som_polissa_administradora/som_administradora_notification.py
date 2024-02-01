# -*- coding: utf-8 -*-
import logging

from osv import osv, fields
from giscedata_polissa import PERMISSION_SELECTION


class SomAdministradoraModification(osv.osv):
    """Registra cada modificació sobre una pòlissa quan hi ha canvis d'adminsitradora OV"""

    _name = "som.admin.modification"

    def _ff_info(self, cursor, uid, ids, field_name, arg, context):
        res = {}
        info_text = self.read(cursor, uid, ids, ["info"], context=context)
        for it in info_text:
            res[it["id"]] = it
        return res

    def _ff_info_search(self, cursor, uid, obj, name, args, context=None):
        if not context:
            context = {}
        if not args:
            return [("id", "=", 0)]
        modi_obj = self.pool.get("som.admin.modification")
        search_str = args[0][2]

        info_ids = modi_obj.search(cursor, uid, [("info", "ilike", "%{}%".format(search_str))])
        pol_ids = modi_obj.search(
            cursor, uid, [("polissa_id.name", "ilike", "%{}%".format(search_str))]
        )
        old_admin_ids = modi_obj.search(
            cursor, uid, [("old_administradora.name", "ilike", "%{}%".format(search_str))]
        )
        new_admin_ids = modi_obj.search(
            cursor, uid, [("new_administradora.name", "ilike", "%{}%".format(search_str))]
        )
        claimant_ids = modi_obj.search(
            cursor, uid, [("claimant.name", "ilike", "%{}%".format(search_str))]
        )
        return [("id", "in", info_ids + pol_ids + old_admin_ids + new_admin_ids + claimant_ids)]

    _columns = {
        "name": fields.function(
            _ff_info, method=True, string="Nom", type="string", fnct_search=_ff_info_search
        ),
        "claimant": fields.many2one("res.partner", u"Sol·licitant", readonly=True),
        "polissa_id": fields.many2one(
            "giscedata.polissa",
            "Polissa afectada per modificació d'Administradora OV",
            readonly=True,
        ),
        "old_administradora": fields.many2one(
            "res.partner", "Administradora desassignada", readonly=True
        ),
        "new_administradora": fields.many2one(
            "res.partner", "Administradora assignada", readonly=True
        ),
        "permissions": fields.selection(
            PERMISSION_SELECTION, string="Permisos Administradora OV", readonly=True
        ),
        "is_legal_representative": fields.boolean(
            "És el representant legal del titular de la pòlissa"
        ),
        "info": fields.text("Info"),
        "error": fields.boolean(u"Indica si hi ha hagut error o no"),
    }


SomAdministradoraModification()


class SomAdministradoraNotification(osv.osv):
    """Registra els receptors de notifications quan hi ha canvis d'administradora OV"""

    _name = "som.admin.notification"
    _order = "id desc"

    _columns = {
        "name": fields.char("Nom", size=64, required=False),
        "receptor": fields.many2one(
            "res.partner", u"Receptor de la notificació (Titular o Administradora)", readonly=True
        ),
        "receptor_nif": fields.related(
            "receptor", "vat", type="char", string="NIF receptor", readonly=True
        ),
        "pending_notification": fields.boolean("E-mail de notificació pendent d'enviar"),
        "modification": fields.many2many(
            "som.admin.modification",
            "som_admin_noti_modi_rel",
            "admin_noti_id",
            "admin_modi_id",
            "Modificacions",
        ),
        "template_id": fields.many2one(
            "poweremail.templates", u"Plantilla de Poweremail a enviar", readonly=True
        ),
        "info": fields.text("Info"),
        "create_date": fields.datetime("Creation date", readonly=True),
    }

    def create(self, cursor, uid, values, context=None):
        """Assign a name to the object if not done yet"""

        if "name" not in values or not values["name"]:
            values["name"] = "Administradora notification"

        return super(SomAdministradoraNotification, self).create(
            cursor, uid, values, context=context
        )

    def notificacio_valida(self, cursor, uid, noti_id):
        """Retorna True si alguna de les modificacions no té error
        retorna False en qualsevol altre cas"""

        admin_noti_obj = self.pool.get("som.admin.notification")
        admin_mod_obj = self.pool.get("som.admin.modification")

        modi_ids = admin_noti_obj.read(cursor, uid, noti_id, ["modification"])["modification"]

        for modi_id in modi_ids:
            if not admin_mod_obj.read(cursor, uid, modi_id, ["error"])["error"]:
                return True

        return False

    def send_email(self, cursor, uid, ids, context=None):
        if isinstance(ids, (list, tuple)):
            ids = ids[0]

        if not context:
            context = {}

        if not self.notificacio_valida(cursor, uid, ids):
            return False

        pwswz_obj = self.pool.get("poweremail.send.wizard")
        pwt_obj = self.pool.get("poweremail.templates")

        template_id = self.read(cursor, uid, ids, ["template_id"])["template_id"][0]
        template = pwt_obj.browse(cursor, uid, template_id)
        mail_from = template.enforce_from_account.id

        ctx = {
            "active_ids": [ids],
            "active_id": ids,
            "template_id": template_id,
            "src_rec_ids": [ids],
            "src_rec_id": ids,
            "src_model": "som.admin.notification",
            "from": mail_from,
            "state": "single",
            "priority": "0",
            "folder": "outbox",
            "save_async": True,
        }
        params = {"state": "single", "priority": "0", "from": ctx["from"]}

        pwswz_id = pwswz_obj.create(cursor, uid, params, ctx)
        pwemb_id = pwswz_obj.save_to_mailbox(cursor, uid, [pwswz_id], ctx)

        return True

    def poweremail_write_callback(self, cursor, uid, ids, vals, context=None):
        logger = logging.getLogger("openerp.{0}.poweremail_write_callback".format(__name__))
        logger.info(
            "PE callback for mark as send Admin OV notifications {0} and from user {1}".format(
                ids, uid
            )
        )
        if context is None:
            context = {}
        meta = context.get("meta")
        attach_obj = self.pool.get("ir.attachment")
        mail_obj = self.pool.get("poweremail.mailbox")
        noti_obj = self.pool.get("som.admin.notification")
        for noti_id in ids:
            if not meta:
                meta = {}
            model = meta[noti_id].get("model", False)
            if "folder" in vals and "date_mail" in vals:
                if vals.get("folder", False) == "sent":
                    noti_obj.write(
                        cursor,
                        uid,
                        noti_id,
                        {"info": u"Notificat correctament", "pending_notification": False},
                    )
                else:
                    noti_obj.write(
                        cursor,
                        uid,
                        noti_id,
                        {
                            "info": u"Hi ha hagut algún error durant l'enviament",
                            "pending_notification": True,
                        },
                    )
        return True


SomAdministradoraNotification()
