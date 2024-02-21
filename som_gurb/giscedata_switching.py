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
    step_m101_auto = step_m101_obj.search(
        cursor, uid, [("sw_id", "=", sw.id), ("solicitud_autoconsum", "=", "S")]
    )

    return any([
        "unidireccional" in sw.additional_info.lower(),
        "(S)[R]" in sw.additional_info,
        bool(step_m101_auto),
    ])


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
