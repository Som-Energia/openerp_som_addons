# -*- coding: utf-8 -*-

from osv import osv, fields
from datetime import datetime

from ..giscedata_polissa import PERMISSION_SELECTION, ERROR_CODES

AVAILABLE_STATES = [
    ("init", "Init"),
    ("admin_specified", "Nova administradora OV especificada"),
    ("done", "Done"),
]


class WizardModifyOVAdmin(osv.osv_memory):

    _name = "wizard.modify.ov.admin"

    def onchange_administradora(self, cursor, uid, ids, administradora_id):
        res = {"value": {"state": "init"}}
        if administradora_id:
            res = {"value": {"state": "admin_specified"}}
        return res

    def default_get(self, cr, uid, fields, context={}):
        active_id = context.get("active_id", False)

        res = {}
        if not active_id:
            return res

        if isinstance(active_id, (list, tuple)):
            active_id = active_id[0]

        pol_obj = self.pool.get("giscedata.polissa")
        titular = pol_obj.read(cr, uid, active_id, ["titular"])["titular"][0]

        res["claimant"] = titular
        res["state"] = "init"

        return res

    def annotate_legal_representative(self, cursor, uid, titular_id, repersentative_id):
        res_partner_obj = self.pool.get("res.partner")
        admin_comment = res_partner_obj.read(cursor, uid, titular_id, ["comment"]).get(
            "comment", ""
        )
        representative_vals = res_partner_obj.read(cursor, uid, repersentative_id, ["name", "vat"])
        data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = (
            u"Durant el procés d'assignació d'Administradora OV, aquest "
            + u"partner va declarar en {} que el partner ".format(data)
            + u"{} amb VAT {} és el representant legal d'aquest.".format(
                representative_vals["name"], representative_vals["vat"]
            )
        )
        if admin_comment:
            message = admin_comment + "\n\n" + message
        res_partner_obj.write(cursor, uid, titular_id, {"comment": message})

    def create_admin_notification_modification(
        self, cursor, uid, partner_id, ov_admin_modification, notification_receptor, semantic_id
    ):
        if partner_id is None:
            return

        mdata_obj = self.pool.get("ir.model.data")
        template_id = mdata_obj.get_object_reference(
            cursor, uid, "som_polissa_administradora", semantic_id
        )[1]

        admin_noti_obj = self.pool.get("som.admin.notification")
        if partner_id not in notification_receptor.keys():
            notification_receptor[partner_id] = admin_noti_obj.create(
                cursor,
                uid,
                {"receptor": partner_id, "pending_notification": True, "template_id": template_id},
            )

        admin_noti_obj.write(
            cursor,
            uid,
            notification_receptor[partner_id],
            {"modification": [(4, ov_admin_modification)]},
        )

    def action_assignar_administradora(self, cursor, uid, ids, context=None):
        active_ids = context.get("active_ids", [])

        if not active_ids:
            return {}

        pol_obj = self.pool.get("giscedata.polissa")
        partner_obj = self.pool.get("res.partner")
        admin_noti_obj = self.pool.get("som.admin.notification")
        admin_mod_obj = self.pool.get("som.admin.modification")

        wiz_vals = self.read(cursor, uid, ids)[0]
        new_administradora_id = wiz_vals.get("new_administradora", False)
        administradora_permissions = wiz_vals.get("administradora_permissions", False)
        is_legal_representative = wiz_vals.get("is_legal_representative", False)
        not_notify_changes = wiz_vals.get("not_notify_changes", False)

        # validate fields
        if not (new_administradora_id and administradora_permissions):
            raise osv.except_osv("Error!", u"Falten camps per emplenar")

        new_administradora_name = partner_obj.read(cursor, uid, new_administradora_id, ["name"])[
            "name"
        ]

        notification_receptor = {}
        titulars_anotats = []
        polisses = pol_obj.browse(cursor, uid, active_ids)
        info = ""
        for pol in polisses:
            # keep old administrator if there is
            old_administradora_id = None
            if pol.administradora:
                old_administradora_id = pol.administradora.id

            titular_id = pol.titular.id

            # perform assignment
            result = pol.add_contract_administrator(
                new_administradora_id,
                administradora_permissions,
                is_legal_representative=is_legal_representative,
            )

            error = result.get("error", None) is not None

            ov_admin_modification = None
            if error:
                error_msg = (
                    u"- S'ha produït un error al assignar l'administradora "
                    + u'per la pòlissa {}: "{}"\n'
                )
                error_msg = error_msg.format(pol.name, result["error_msg"])
                info += error_msg

                skip_error = ERROR_CODES.get(result["error"], {}).get("skip_error", False)
                if not skip_error:
                    vals = {
                        "old_administradora": old_administradora_id,
                        "new_administradora": new_administradora_id,
                        "permissions": administradora_permissions,
                        "is_legal_representative": is_legal_representative,
                        "error": True,
                        "info": error_msg,
                    }
                    ov_admin_modification = pol_obj.register_ov_admin_modification(
                        cursor, uid, pol.id, vals
                    )
                else:
                    continue
            else:
                ov_admin_modification = result["modification"]
                # update info if there's no error
                msg = ""
                if old_administradora_id is not None:
                    old_administradora_name = partner_obj.read(
                        cursor, uid, old_administradora_id, ["name"]
                    )["name"]
                    msg = (
                        u"- S'ha sustituit el partner '{}' (ID {}) pel partner "
                        + u"'{}' (ID {}) com a administradora OV a la pòlissa {}\n"
                    )
                    msg = msg.format(
                        old_administradora_name,
                        old_administradora_id,
                        new_administradora_name,
                        new_administradora_id,
                        pol.name,
                    )
                else:
                    msg = (
                        u"- S'ha assignat el partner '{}' (ID {}) "
                        + u"com a administradora OV a la pòlissa {}\n"
                    )
                    msg = msg.format(new_administradora_name, new_administradora_id, pol.name)

                admin_mod_obj.write(cursor, uid, ov_admin_modification, {"info": msg})

                info += msg

            # create notifications and associate with modification
            self.create_admin_notification_modification(
                cursor,
                uid,
                titular_id,
                ov_admin_modification,
                notification_receptor,
                "email_assignacio_a_titular",
            )
            self.create_admin_notification_modification(
                cursor,
                uid,
                old_administradora_id,
                ov_admin_modification,
                notification_receptor,
                "email_desassignacio_a_administradora",
            )
            self.create_admin_notification_modification(
                cursor,
                uid,
                new_administradora_id,
                ov_admin_modification,
                notification_receptor,
                "email_assignacio_a_administradora",
            )

            if is_legal_representative and titular_id not in titulars_anotats:
                self.annotate_legal_representative(cursor, uid, titular_id, new_administradora_id)
                titulars_anotats.append(titular_id)

        self.write(cursor, uid, ids, {"state": "done", "info": info})

        cursor.commit()

        if not not_notify_changes:
            # notify assignation
            for noti_id in notification_receptor.values():
                admin_noti_obj.send_email(cursor, uid, noti_id)

        return

    def action_desassignar_administradora(self, cursor, uid, ids, context=None):
        active_ids = context.get("active_ids", [])

        if not active_ids:
            return {}

        pol_obj = self.pool.get("giscedata.polissa")
        partner_obj = self.pool.get("res.partner")
        admin_noti_obj = self.pool.get("som.admin.notification")
        admin_mod_obj = self.pool.get("som.admin.modification")

        wiz_vals = self.read(cursor, uid, ids)[0]
        not_notify_changes = wiz_vals.get("not_notify_changes", False)

        notification_receptor = {}
        polisses = pol_obj.browse(cursor, uid, active_ids)
        info = ""
        for pol in polisses:
            # keep old administrator if there is
            old_administradora_id = None
            if pol.administradora:
                old_administradora_id = pol.administradora.id

            titular_id = pol.titular.id

            # perform unassignment
            result = pol.remove_contract_administrator()

            error = result.get("error", None) is not None

            ov_admin_modification = None
            if error:
                error_msg = (
                    u"- S'ha produït un error al assignar l'administradora "
                    + u'per la pòlissa {}: "{}"\n'
                )
                error_msg = error_msg.format(pol.name, result["error_msg"])
                info += error_msg

                skip_error = ERROR_CODES.get(result["error"], {}).get("skip_error", False)
                if not skip_error:
                    vals = {
                        "old_administradora": old_administradora_id,
                        "new_administradora": None,
                        "permissions": None,
                        "is_legal_representative": False,
                        "error": True,
                        "info": error_msg,
                    }
                    ov_admin_modification = pol_obj.register_ov_admin_modification(
                        cursor, uid, pol.id, vals
                    )
                else:
                    continue
            else:
                ov_admin_modification = result["modification"]
                # update info if there's no error
                old_administradora_name = partner_obj.read(
                    cursor, uid, old_administradora_id, ["name"]
                )["name"]
                msg = u"- S'ha desassignat el partner '{}' (ID {}) de la pòlissa {}\n".format(
                    old_administradora_name, old_administradora_id, pol.name
                )

                admin_mod_obj.write(cursor, uid, ov_admin_modification, {"info": msg})

                info += msg

            # create notifications and associate with modification
            self.create_admin_notification_modification(
                cursor,
                uid,
                titular_id,
                ov_admin_modification,
                notification_receptor,
                "email_desassignacio_a_titular",
            )
            self.create_admin_notification_modification(
                cursor,
                uid,
                old_administradora_id,
                ov_admin_modification,
                notification_receptor,
                "email_desassignacio_a_administradora",
            )

        self.write(cursor, uid, ids, {"state": "done", "info": info})

        cursor.commit()

        if not not_notify_changes:
            # notify assignation
            for noti_id in notification_receptor.values():
                admin_noti_obj.send_email(cursor, uid, noti_id)

        return

    _columns = {
        "new_administradora": fields.many2one("res.partner", "Nova Administradora OV"),
        "claimant": fields.many2one("res.partner", "Sol·licitant"),
        "is_legal_representative": fields.boolean(
            "Representant legal",
            help=u"Si s'activa, es deixarà una nota a la fitxa del titular amb el nom i VAT "
            + u"de l'Administradora OV, especificant que aquesta última és la representant "
            + u"legal del titular.",
        ),
        "administradora_permissions": fields.selection(
            PERMISSION_SELECTION,
            string="Permisos Administradora OV",
            help=u"Permisos de l'Administradora OV sobre la pòlissa",
        ),
        "state": fields.selection(selection=AVAILABLE_STATES, string="Estat"),
        "not_notify_changes": fields.boolean(
            "No notificar canvis",
            help=u"Si s'activa, els canvis d'Administradora no es notificaràn a ningú",
        ),
        "info": fields.text("Info"),
    }


WizardModifyOVAdmin()
