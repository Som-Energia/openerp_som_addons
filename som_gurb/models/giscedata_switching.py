# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _


_GURB_CANCEL_CASES = {
    "D1": ["01"],
    "M1": ["02", "03", "04", "05"],
}


def _contract_has_gurb_category(cursor, uid, pool, pol_id, context=None):
    if context is None:
        context = {}

    ir_model_obj = pool.get("ir.model.data")
    pol_obj = pool.get("giscedata.polissa")

    pol_category_ids = pol_obj.read(cursor, uid, pol_id, ["category_id"])["category_id"]
    gurb_categ_id = ir_model_obj.get_object_reference(
        cursor, uid, "som_gurb", "categ_gurb_pilot"  # TODO: Use the real category
    )[1]

    return gurb_categ_id in pol_category_ids


def _is_m1_closable(cursor, uid, pool, sw, context=None):
    if context is None:
        context = {}

    step_m101_obj = pool.get("giscedata.switching.m1.01")
    step_m102_obj = pool.get("giscedata.switching.m1.02")
    step_m101_auto = step_m101_obj.search(
        cursor, uid, [("sw_id", "=", sw.id), ("solicitud_autoconsum", "=", "S")], context=context
    )

    if "unidireccional" in sw.additional_info.lower():
        return True
    elif "(S)[R]" in sw.additional_info:
        return True
    elif step_m101_auto and sw.step_id.name == "02":
        step_m102_rebuig = step_m102_obj.search(
            cursor, uid, [("sw_id", "=", sw.id), ("rebuig", "=", True)], context=context
        )
        return step_m102_rebuig and step_m101_auto
    else:
        return bool(step_m101_auto)


def _is_case_closable(cursor, uid, pool, sw, context=None):
    if context is None:
        context = {}

    if (
        not sw
        or sw.proces_id.name not in _GURB_CANCEL_CASES
        or sw.step_id.name not in _GURB_CANCEL_CASES[sw.proces_id.name]
        or not _contract_has_gurb_category(cursor, uid, pool, sw.cups_polissa_id.id)
    ):
        return False

    if sw.proces_id.name == "M1":
        return _is_m1_closable(cursor, uid, pool, sw, context=context)

    return True


class GiscedataSwitching(osv.osv):
    _inherit = "giscedata.switching"

    def importar_xml_post_hook(self, cursor, uid, sw_id, context=None):
        """
        Cancel and avoid activation of some cases if related contract has GURB category.
        """
        if context is None:
            context = {}

        sw_obj = self.pool.get("giscedata.switching")
        sw = sw_obj.browse(cursor, uid, sw_id, context=context)

        if _is_case_closable(cursor, uid, self.pool, sw, context=context):
            msg = _("Cas cancel·lat per GURB")
            self.historize_msg(cursor, uid, sw.id, msg, context=context)
            sw_obj.write(cursor, uid, sw_id, {"state": "cancel"}, context=context)
            return _("Cas importat correctament.")
        else:
            return super(GiscedataSwitching, self).importar_xml_post_hook(
                cursor, uid, sw_id, context=context
            )


GiscedataSwitching()


class GiscedataSwitchingM1_02(osv.osv):
    _inherit = "giscedata.switching.m1.02"

    def create_from_xml(self, cursor, uid, sw_id, xml, context=None):
        if context is None:
            context = {}

        pas_id = super(GiscedataSwitchingM1_02, self).create_from_xml(
            cursor, uid, sw_id, xml, context=context
        )

        sw_obj = self.pool.get("giscedata.switching")
        step_m101_obj = self.pool.get("giscedata.switching.m1.01")
        sw_step_header_obj = self.pool.get("giscedata.switching.step.header")
        sw = sw_obj.browse(cursor, uid, sw_id, context=context)

        if sw and _contract_has_gurb_category(
            cursor, uid, self.pool, sw.cups_polissa_id.id, context=context
        ):
            step_m101_auto = step_m101_obj.search(
                cursor,
                uid,
                [("sw_id", "=", sw.id), ("solicitud_autoconsum", "=", "S")],
                context=context,
            )
            if step_m101_auto:
                sw_step_header_id = self.read(cursor, uid, pas_id, ['header_id'])['header_id'][0]
                sw_step_header_obj.write(
                    cursor, uid, sw_step_header_id, {'notificacio_pendent': False}
                )

        return pas_id


GiscedataSwitchingM1_02()


class GiscedataSwitchingM1_05(osv.osv):
    _inherit = "giscedata.switching.m1.05"

    def create_from_xml(self, cursor, uid, sw_id, xml, context=None):
        if context is None:
            context = {}

        pas_id = super(GiscedataSwitchingM1_05, self).create_from_xml(
            cursor, uid, sw_id, xml, context=context
        )

        sw_obj = self.pool.get("giscedata.switching")
        gurb_obj = self.pool.get("som.gurb")
        step_m101_obj = self.pool.get("giscedata.switching.m1.01")
        sw_step_header_obj = self.pool.get("giscedata.switching.step.header")
        sw = sw_obj.browse(cursor, uid, sw_id, context=context)

        if sw and _contract_has_gurb_category(
            cursor, uid, self.pool, sw.cups_polissa_id.id, context=context
        ):
            step_m101_auto = step_m101_obj.search(
                cursor,
                uid,
                [("sw_id", "=", sw.id), ("solicitud_autoconsum", "=", "S")],
                context=context,
            )
            if step_m101_auto:
                sw_step_header_id = self.read(cursor, uid, pas_id, ['header_id'])['header_id'][0]
                sw_step_header_obj.write(
                    cursor, uid, sw_step_header_id, {'notificacio_pendent': False}
                )
                data_activacio = xml.datos_activacion.fecha
                gurb_obj.activate_gurb_from_m1_05(
                    cursor, uid, sw_id, data_activacio, context=context
                )

        return pas_id


GiscedataSwitchingM1_05()
