# -*- coding: utf-8 -*-
from osv import osv


class CupsHelper(osv.osv_memory):
    _name = "cups.helper"

    def _has_open_cases(self, cursor, uid, polissa_id, context=None):
        if context is None:
            context = {}
        sw_obj = self.pool.get("giscedata.switching")
        pol_obj = self.pool.get("giscedata.polissa")
        polissa_br = pol_obj.browse(cursor, uid, polissa_id, context=context)
        sw_ids = sw_obj.search(cursor, uid, [
            ('cups_polissa_id', '=', polissa_br.id),
            ('state', '=', 'open'),
            ('proces_id', 'not in', ["R1"])
        ])
        return bool(sw_ids)

    def _get_polissa_id(self, cursor, uid, cups_id, context=None):
        if context is None:
            context = {}
        polissa_obj = self.pool.get("giscedata.polissa")
        search_params = [
            ("cups", "=", cups_id),
            ("state", "in", ["activa", "esborrany"]),
        ]
        polissa_ids = polissa_obj.search(
            cursor, uid, search_params, order="create_date DESC", limit=1
        )
        if polissa_ids:
            polissa_br = polissa_obj.browse(cursor, uid, polissa_ids[0], context=context)
            if polissa_br.state == "activa":
                has_open_cases = self._has_open_cases(
                    cursor, uid, polissa_ids[0], context=context
                )
                if has_open_cases:
                    return False
            return polissa_ids[0]
        return None

    def _cups_status(self, cursor, uid, cups_id, context=None):
        if context is None:
            context = {}

        pol_obj = self.pool.get("giscedata.polissa")

        contract_ids = pol_obj.search(cursor, uid, [('cups', '=', cups_id)], context=context)
        if not contract_ids:
            return 'inactive'
        has_open_cases = self._has_open_cases(
            cursor, uid, contract_ids[0], context=context
        )
        ctx = context.copy()
        ctx['active_test'] = False
        unactive_ids = pol_obj.search(
            cursor, uid, [('cups', '=', cups_id), ("state", "=", "baixa")], context=ctx
        )
        if has_open_cases or unactive_ids:
            return 'busy'
        return 'active'

    def _get_cups_data(self, cursor, uid, cups_id, context=None):
        if context is None:
            context = {}

        pol_obj = self.pool.get("giscedata.polissa")
        cups_obj = self.pool.get("giscedata.cups.ps")

        result = {}

        result["address"] = cups_obj.read(cursor, uid, cups_id, ["nv"], context=context)["nv"]

        search_params = [
            ("cups", "=", cups_id),
        ]
        pol_ids = pol_obj.search(cursor, uid, search_params, context=context)
        if not pol_ids:
            return ''

        pol_br = pol_obj.browse(cursor, uid, pol_ids[0], context=context)

        result["tariff_type"] = pol_br.mode_facturacio
        result["tariff_name"] = pol_br.tarifa.name

        return result

    def check_cups(self, cursor, uid, cups_name, context=None):
        if context is None:
            context = {}
        cups_obj = self.pool.get("giscedata.cups.ps")
        pol_obj = self.pool.get("giscedata.polissa")

        result = {
            "cups": cups_name,
            "status": "",
            "tariff_type": "",
            "tariff_name": "",
            "address": ""
        }

        context["active_test"] = False

        cups_id = cups_obj.search(
            cursor, uid, [("name", "like", cups_name[:20])], context=context
        )

        result["knowledge_of_distri"] = pol_obj.www_get_distributor_id(cursor, uid, cups_name)
        if cups_id:
            cups_data = self._get_cups_data(
                cursor, uid, cups_id[0], context=context
            )
            result.update(cups_data)
            result["status"] = self._cups_status(cursor, uid, cups_id[0], context=context)
        else:
            result["status"] = "new"

        return result


CupsHelper()
