# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import pooler

from osv import osv
from tools.translate import _


class SomHolderChangeM1(osv.osv_memory):
    _name = "som.holder.change.m1"
    _description = "Holder change M1 service"

    def _generate_new_contract(self, cursor, uid, owner_change_type):
        if owner_change_type == "T":
            return "create"
        config_obj = self.pool.get("res.config")
        creates_contract = bool(int(config_obj.get(
            cursor,
            uid,
            "sw_m1_owner_change_subrogacio_new_contract",
            "1",
        )))
        return "create" if creates_contract else "exists"

    def execute(
        self,
        cursor,
        uid,
        polissa_id,
        owner_change_type,
        resolved_values,
        context=None,
    ):
        if owner_change_type not in ("T", "S"):
            raise osv.except_osv(
                _("Invalid holder change"),
                _("The holder change type must be T or S."),
            )

        wizard_values = resolved_values.copy()
        wizard_values.update({
            "change_atr": False,
            "change_adm": True,
            "owner_change_type": owner_change_type,
            "generate_new_contract": self._generate_new_contract(
                cursor, uid, owner_change_type
            ),
            "change_retail_tariff": False,
            "retail_tariff": False,
            "activacio_cicle": "A",
        })
        if wizard_values["generate_new_contract"] == "exists":
            wizard_values["new_contract"] = False

        polissa_obj = self.pool.get("giscedata.polissa")
        switching_ids = polissa_obj.generate_M1_API(
            cursor,
            uid,
            polissa_id,
            wizard_values,
            context=context,
        )
        if len(switching_ids) != 1:
            raise osv.except_osv(
                _("M1 generation failed"),
                _("The holder change did not generate exactly one M1 case."),
            )

        switching_id = switching_ids[0]
        switching = self.pool.get("giscedata.switching").browse(
            cursor, uid, switching_id, context=context
        )
        return {
            "switching_id": switching_id,
            "result_polissa_id": switching.polissa_ref_id.id,
        }

    def simulate(
        self,
        cursor,
        uid,
        polissa_id,
        owner_change_type,
        resolved_values,
        context=None,
    ):
        simulation_cursor = pooler.get_db(cursor.dbname).cursor()
        simulation_context = (context or {}).copy()
        simulation_context["in_rollback_transaction"] = True
        try:
            self.execute(
                simulation_cursor,
                uid,
                polissa_id,
                owner_change_type,
                resolved_values,
                context=simulation_context,
            )
            return {"valid": True}
        finally:
            simulation_cursor.rollback()
            simulation_cursor.close()


SomHolderChangeM1()
