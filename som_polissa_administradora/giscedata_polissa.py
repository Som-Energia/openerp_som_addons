# -*- coding: utf-8 -*-
from osv import osv, fields

import datetime


PERMISSION_SELECTION = [
    ("manage", u"Gestió"),
    ("readonly", u"Visualització"),
]

ERROR_CODES = {
    "00": {"msg": u"[00] La pòlissa no té cap modificació contractual", "skip_error": False},
    "01": {"msg": u"[01] No s'ha especificat un partner existent", "skip_error": True},
    "02": {"msg": u"[02] S'han d'especificar els permisos", "skip_error": True},
    "03": {"msg": u"[03] Partner '%s' ja administra aquesta pòlissa.", "skip_error": True},
    "04": {"msg": u"[04] La pòlissa no té persona administradora assignada", "skip_error": True},
    "05": {
        "msg": u"[05] La data final de l'última modificació contractual és anterior al dia d'avui",
        "skip_error": False,
    },
    "99": {"msg": u"[99] Error desconegut: %s", "skip_error": False},
}


class GiscedataPolissa(osv.osv):
    """Pòlissa per afegir el camp d'administradora."""

    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    def register_ov_admin_modification(self, cursor, uid, polissa_id, vals):
        """
        vals = {
            "old_administradora": ...,
            "new_administradora": ...,
            "permissions": ...,
            "is_legal_representative": ...
        }
        """
        vals["polissa_id"] = polissa_id
        admin_mod_obj = self.pool.get("som.admin.modification")
        admin_mod_id = admin_mod_obj.create(cursor, uid, vals)
        return admin_mod_id

    def create_modcon(self, cursor, uid, polissa_id, vals):
        pol = self.browse(cursor, uid, polissa_id)
        if len(pol.modcontractuals_ids) < 1:
            return {"modification": None, "error": "00", "error_msg": ERROR_CODES["00"]["msg"]}

        last_modcon = pol.modcontractuals_ids[0]
        data_final_modcon = datetime.datetime.strptime(last_modcon.data_final, "%Y-%m-%d").date()
        if datetime.date.today() > data_final_modcon:
            return {"modification": None, "error": "05", "error_msg": ERROR_CODES["05"]["msg"]}

        pol.send_signal(["modcontractual"])
        self.write(cursor, uid, polissa_id, vals)
        wz_crear_mc_obj = self.pool.get("giscedata.polissa.crear.contracte")

        ctx = {"active_id": polissa_id}
        params = {"duracio": "actual"}

        wz_id_mod = wz_crear_mc_obj.create(cursor, uid, params, ctx)
        wiz_mod = wz_crear_mc_obj.browse(cursor, uid, wz_id_mod, ctx)
        res = wz_crear_mc_obj.onchange_duracio(
            cursor, uid, [wz_id_mod], wiz_mod.data_inici, wiz_mod.duracio, ctx
        )
        wiz_mod.write({"data_final": res["value"]["data_final"]})
        wiz_mod.action_crear_contracte(ctx)

        return {}

    def validate_partner(self, cursor, uid, partner_id):
        res_partner_obj = self.pool.get("res.partner")

        partner = False
        if partner_id:
            partner = res_partner_obj.browse(cursor, uid, partner_id)

        if not partner:
            return {"modification": None, "error": "01", "error_msg": ERROR_CODES["01"]["msg"]}

        return {}

    def get_admin_cat(self, cursor, uid):
        imd_obj = self.pool.get("ir.model.data")
        return imd_obj._get_obj(
            cursor, uid, "som_polissa_administradora", "res_partner_category_administradora"
        )

    def remove_administrator_category(self, cursor, uid, partner_id):
        administrated_contracts = self.search(cursor, uid, [("administradora", "=", partner_id)])

        if len(administrated_contracts) == 1:
            admin_cat = self.get_admin_cat(cursor, uid)
            res_partner_obj = self.pool.get("res.partner")
            res_partner_obj.write(cursor, uid, partner_id, {"category_id": [(3, admin_cat.id)]})

    def add_administrator_category(self, cursor, uid, partner_id):
        res_partner_obj = self.pool.get("res.partner")
        partner_categories = res_partner_obj.read(cursor, uid, partner_id, ["category_id"])
        admin_cat = self.get_admin_cat(cursor, uid)

        if admin_cat.id not in partner_categories["category_id"]:
            res_partner_obj.write(cursor, uid, partner_id, {"category_id": [(4, admin_cat.id)]})

    def add_contract_administrator(
        self,
        cursor,
        uid,
        polissa_id,
        partner_id,
        permissions,
        is_legal_representative=False,
        context=None,
    ):
        if context is None:
            context = {}

        try:
            if isinstance(polissa_id, (list, tuple)):
                polissa_id = polissa_id[0]

            valid_partner = self.validate_partner(cursor, uid, partner_id)

            if valid_partner.get("error", "") != "":
                return valid_partner

            if permissions not in [p[0] for p in PERMISSION_SELECTION]:
                return {"modification": None, "error": "02", "error_msg": ERROR_CODES["02"]["msg"]}

            administradora = self.read(cursor, uid, polissa_id, ["administradora"])[
                "administradora"
            ]

            if administradora and administradora[0] == partner_id:
                return {
                    "modification": None,
                    "error": "03",
                    "error_msg": ERROR_CODES["03"]["msg"] % (administradora[1]),
                }

            if administradora and administradora[0] != partner_id:
                self.remove_administrator_category(cursor, uid, administradora[0])

            self.add_administrator_category(cursor, uid, partner_id)

            result = self.create_modcon(
                cursor,
                uid,
                polissa_id,
                {"administradora": partner_id, "administradora_permissions": permissions},
            )

            if result.get("error", "") != "":
                return result

            vals = {
                "polissa_id": polissa_id,
                "old_administradora": administradora[0] if administradora else None,
                "new_administradora": partner_id,
                "permissions": permissions,
                "is_legal_representative": is_legal_representative,
                "error": False,
            }
            return {
                "modification": self.register_ov_admin_modification(cursor, uid, polissa_id, vals),
                "error": None,
                "error_msg": "",
            }
        except Exception as e:
            return {
                "modification": None,
                "error": "99",
                "error_msg": ERROR_CODES["99"]["msg"] % str(e),
            }

    def remove_contract_administrator(self, cursor, uid, polissa_id, context=None):
        if context is None:
            context = {}

        try:
            if isinstance(polissa_id, (list, tuple)):
                polissa_id = polissa_id[0]

            administradora = self.read(cursor, uid, polissa_id, ["administradora"])[
                "administradora"
            ]

            if administradora:
                self.remove_administrator_category(cursor, uid, administradora[0])
                result = self.create_modcon(
                    cursor,
                    uid,
                    polissa_id,
                    {"administradora": None, "administradora_permissions": None},
                )

                if result.get("error", "") != "":
                    return result
            else:
                return {"modification": None, "error": "04", "error_msg": ERROR_CODES["04"]["msg"]}

            vals = {
                "polissa_id": polissa_id,
                "old_administradora": administradora[0] if administradora else None,
                "new_administradora": None,
                "permissions": None,
                "is_legal_representative": False,
                "error": False,
            }
            return {
                "modification": self.register_ov_admin_modification(cursor, uid, polissa_id, vals),
                "error": None,
                "error_msg": "",
            }
        except Exception as e:
            return {
                "modification": None,
                "error": "99",
                "error_msg": ERROR_CODES["99"]["msg"] % str(e),
            }

    _columns = {
        "administradora": fields.many2one(
            "res.partner",
            "Administradora",
            readonly=True,
            help=u"Qui podrà administrar aquest contracte",
        ),
        "administradora_nif": fields.related(
            "administradora", "vat", type="char", string="NIF administradora", readonly=True
        ),
        "administradora_permissions": fields.selection(
            PERMISSION_SELECTION,
            string="Permisos Administradora OV",
            readonly=True,
            states={
                "esborrany": [("readonly", False)],
                "validar": [("readonly", False)],
                "modcontractual": [("readonly", False)],
            },
            help=u"Permisos de l'Administradora OV sobre la pòlissa",
        ),
    }


GiscedataPolissa()


class GiscedataPolissaModcontractual(osv.osv):
    """Modificació Contractual d'una Pòlissa."""

    _name = "giscedata.polissa.modcontractual"
    _inherit = "giscedata.polissa.modcontractual"

    _columns = {
        "administradora": fields.many2one("res.partner", "Administradora"),
        "administradora_permissions": fields.selection(
            PERMISSION_SELECTION, string="Permisos Administradora OV"
        ),
    }


GiscedataPolissaModcontractual()
