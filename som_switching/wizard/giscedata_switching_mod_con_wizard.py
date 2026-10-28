# -*- coding: utf-8 -*-
from __future__ import absolute_import
from osv import osv, fields
import json
from datetime import datetime


class GiscedataSwitchingModConWizard(osv.osv_memory):
    _name = "giscedata.switching.mod.con.wizard"
    _inherit = "giscedata.switching.mod.con.wizard"

    def get_phone(self, cursor, uid, address_id, context=None):
        telephone_obj = self.pool.get("giscedata.switching.telefon")
        telephone_values = telephone_obj.get_atr_telephone_values(
            cursor, uid, address_id, context=context
        )
        if not telephone_values:
            return {"phone_num": ""}
        return {
            "phone_num": telephone_values[0]["numero"],
            "phone_pre": telephone_values[0]["prefix"],
        }

    def genera_casos_atr(self, cursor, uid, ids, context=None):
        if not context:
            context = {}

        wizard = self.browse(cursor, uid, ids[0], context)
        change_type = self.get_change_type(wizard.change_atr, wizard.change_adm)
        if (
            wizard.proces == "M1"
            and change_type == "owner"
            and wizard.generate_new_contract == "create"
        ):
            new_vals = {}
            soci_obj = self.pool.get("somenergia.soci")
            soci_id = soci_obj.search(cursor, uid, [("partner_id", "=", wizard.owner.id)])
            if soci_id:
                new_vals.update(
                    {
                        "soci": wizard.owner.id,
                    }
                )
            new_vals.update(
                {
                    # "empowering_profile_id": False,
                    # "empowering_channels_log": [(6, 0, [])],
                    # "empowering_profile": False,
                    # "empowering_service": False,
                    # "etag": False,
                    "enviament": "email",
                }
            )
            context.update(
                {
                    "new_contract_extra_vals": new_vals,
                }
            )

        res = super(GiscedataSwitchingModConWizard, self).genera_casos_atr(
            cursor, uid, ids, context=context
        )

        wizard = self.browse(cursor, uid, ids[0], context)
        if wizard.casos_generats and wizard.contract.data_ultima_lectura:
            dultima = datetime.strptime(wizard.contract.data_ultima_lectura, "%Y-%m-%d")
            if (datetime.today() - dultima).days > 35:
                casos_ids = json.loads(wizard.casos_generats)
                self.pool.get("giscedata.switching").write(
                    cursor, uid, casos_ids, {"validacio_pendent": True}
                )
        return res

    def _get_necessita_documentacio_tecnica(self, cursor, uid, context=None):
        if context is None:
            context = {}
        res = False
        pol_id = context.get("pol_id", context.get("active_id"))
        if pol_id:
            distri = self.pool.get("giscedata.polissa").read(
                cursor, uid, pol_id, ["distribuidora"]
            )["distribuidora"]
            if distri:
                dcode = self.pool.get("res.partner").read(cursor, uid, distri[0], ["ref"])["ref"]
                res = dcode in ["0021", "0022"]
        return res

    _columns = {
        "phone_pre": fields.char("Prefix", size=4),
        "necessita_documentacio_tecnica": fields.boolean(
            string="Necessita Documentació Tecnica", type="boolean"
        )
    }

    _defaults = {"necessita_documentacio_tecnica": _get_necessita_documentacio_tecnica}


GiscedataSwitchingModConWizard()
