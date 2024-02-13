# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _


_GURB_CANCEL_CASES = {
    "D1": ["01"],
    "M1": ["02", "03", "04", "05"],
}


class GiscedataSwitching(osv.osv):
    _inherit = "giscedata.switching"

    def importar_xml_post_hook(self, cursor, uid, sw_id, context=None):
        """
        Cancel and avoid activation of some cases if related contract has GURB category.
        """
        if context is None:
            context = {}

        pol_obj = self.pool.get("giscedata.polissa")
        sw_obj = self.pool.get("giscedata.switching")
        ir_model_obj = self.pool.get("ir.model.data")

        sw = sw_obj.browse(cursor, uid, sw_id, context=context)
        pol_id = sw.cups_polissa_id.id
        pol_category_ids = pol_obj.read(cursor, uid, pol_id, ["category_id"])["category_id"]

        gurb_categ_id = ir_model_obj.get_object_reference(
            cursor, uid, "som_gurb", "categ_gurb_pilot"  # TODO: Use the real category
        )[1]

        if (
            sw
            and sw.proces_id.name in _GURB_CANCEL_CASES
            and sw.step_id.name in _GURB_CANCEL_CASES[sw.proces_id.name]
            and gurb_categ_id in pol_category_ids
        ):
            msg = _("Cas cancel·lat per GURB")
            self.historize_msg(cursor, uid, sw.id, msg, context=context)
            sw_obj.write(cursor, uid, sw_id, {"state": "cancel"}, context=context)
            return _("Cas importat correctament.")
        else:
            return super(GiscedataSwitching, self).importar_xml_post_hook(
                cursor, uid, sw_id, context=context
            )


GiscedataSwitching()
