# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _


_GURB_CANCEL_CASES = {
    "M1": ["02", "03", "04"],
}

_GURB_CLOSE_CASES = {
    "M1": ["05"],
    "D1": ["01", "02", "05"],
}


def is_unidirectional_colective_autocons_change(cursor, uid, pool, step_obj, step_id, context=None):
    if context is None:
        context = {}

    res = False

    step_obj = pool.get(step_obj)

    step = step_obj.browse(cursor, uid, step_id)
    step01_obj = pool.get('giscedata.switching.m1.01')
    # polissa_obj = pool.get('giscedata.polissa')
    step01_id = step01_obj.search(cursor, uid, [('sw_id', '=', step.sw_id.id)])
    if len(step01_id) == 0:
        # if step.data_activacio:
        #     data_consulta = datetime.strptime(step.data_activacio, '%Y-%m-%d') - timedelta(days=1)
        #     data_consulta = data_consulta.strftime('%Y-%m-%d')
        #     ctx_on_date = {'date': data_consulta, 'prefetch': False, 'dont_raise_exception': True}
        #     polissa = polissa_obj.browse(
        #         cursor, uid, step.sw_id.cups_polissa_id.id, context=ctx_on_date)
        #     if step.tipus_autoconsum in ["42", "43"] and polissa.autoconsumo == "00":
        res = True
    return res


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
    elif "(S)[R]" in sw.additional_info and sw.step_id.name == "05":
        return True
    elif step_m101_auto and sw.step_id.name == "02":
        step_m102_rebuig = step_m102_obj.search(
            cursor, uid, [("sw_id", "=", sw.id), ("rebuig", "=", True)], context=context
        )
        return step_m102_rebuig and step_m101_auto
    else:
        return bool(step_m101_auto)


def _is_case_cancellable(cursor, uid, pool, sw, context=None):
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


def _is_case_closable(cursor, uid, pool, sw, context=None):
    if context is None:
        context = {}

    if (
        not sw
        or sw.proces_id.name not in _GURB_CLOSE_CASES
        or sw.step_id.name not in _GURB_CLOSE_CASES[sw.proces_id.name]
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
        step_obj = self.pool.get("giscedata.switching.m1.05")
        sw = sw_obj.browse(cursor, uid, sw_id, context=context)

        if _is_case_cancellable(cursor, uid, self.pool, sw, context=context):
            msg = _("Cas cancel·lat per GURB")
            self.historize_msg(cursor, uid, sw.id, msg, context=context)
            sw_obj.write(cursor, uid, sw_id, {"state": "cancel"}, context=context)
            return _("Cas importat correctament.")
        elif _is_case_closable(cursor, uid, self.pool, sw, context=context):
            msg = _("Cas tancat per GURB")
            if sw.proces_id.name == "D1":
                step_obj = self.pool.get(sw.step_ids[-1].pas_id.split(",")[0])
            pas_id = int(sw.step_ids[-1].pas_id.split(",")[1])
            step_obj.write(
                cursor, uid, pas_id, {"notificacio_pendent": False}, context=context)
            self.historize_msg(cursor, uid, sw.id, msg, context=context)
            sw_obj.write(cursor, uid, sw_id, {"state": "done"}, context=context)
            if sw.step_id.name == "05" and sw.proces_id.name == "M1":
                return super(GiscedataSwitching, self).importar_xml_post_hook(
                    cursor, uid, sw_id, context=context
                )
            else:
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

        step_id = super(GiscedataSwitchingM1_02, self).create_from_xml(
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
                context=context
            )
            unidirectional_change = is_unidirectional_colective_autocons_change(
                cursor, uid, self.pool, "giscedata.switching.m1.02", step_id, context=context
            )

            if step_m101_auto or unidirectional_change:
                sw_step_header_id = self.read(cursor, uid, step_id, ['header_id'])['header_id'][0]
                sw_step_header_obj.write(
                    cursor, uid, sw_step_header_id, {'notificacio_pendent': False}
                )

        return step_id


GiscedataSwitchingM1_02()


class GiscedataSwitchingM1_03(osv.osv):
    _inherit = "giscedata.switching.m1.03"

    def create_from_xml(self, cursor, uid, sw_id, xml, context=None):
        if context is None:
            context = {}

        step_id = super(GiscedataSwitchingM1_03, self).create_from_xml(
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
                context=context
            )
            unidirectional_change = is_unidirectional_colective_autocons_change(
                cursor, uid, self.pool, "giscedata.switching.m1.03", step_id, context=context
            )

            if step_m101_auto or unidirectional_change:
                sw_step_header_id = self.read(cursor, uid, step_id, ['header_id'])['header_id'][0]
                sw_step_header_obj.write(
                    cursor, uid, sw_step_header_id, {'notificacio_pendent': False}
                )

        return step_id


GiscedataSwitchingM1_03()


class GiscedataSwitchingM1_04(osv.osv):
    _inherit = "giscedata.switching.m1.04"

    def create_from_xml(self, cursor, uid, sw_id, xml, context=None):
        if context is None:
            context = {}

        step_id = super(GiscedataSwitchingM1_04, self).create_from_xml(
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
                context=context
            )
            unidirectional_change = is_unidirectional_colective_autocons_change(
                cursor, uid, self.pool, "giscedata.switching.m1.04", step_id, context=context
            )

            if step_m101_auto or unidirectional_change:
                sw_step_header_id = self.read(cursor, uid, step_id, ['header_id'])['header_id'][0]
                sw_step_header_obj.write(
                    cursor, uid, sw_step_header_id, {'notificacio_pendent': False}
                )

        return step_id


GiscedataSwitchingM1_04()


class GiscedataSwitchingM1_05(osv.osv):
    _inherit = "giscedata.switching.m1.05"

    def create_from_xml(self, cursor, uid, sw_id, xml, context=None):
        if context is None:
            context = {}

        step_id = super(GiscedataSwitchingM1_05, self).create_from_xml(
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
            search_params = [("sw_id", "=", sw.id), ("solicitud_autoconsum", "=", "S")]
            step_m101_auto = step_m101_obj.search(cursor, uid, search_params, context=context)
            unidirectional_change = is_unidirectional_colective_autocons_change(
                cursor, uid, self.pool, "giscedata.switching.m1.05", step_id, context=context
            )

            if step_m101_auto or unidirectional_change:
                sw_step_header_id = self.read(cursor, uid, step_id, ['header_id'])['header_id'][0]
                sw_step_header_obj.write(
                    cursor, uid, sw_step_header_id, {'notificacio_pendent': False}
                )
                data_activacio = xml.datos_activacion.fecha
                gurb_obj.activate_gurb_from_m1_05(
                    cursor, uid, sw_id, data_activacio, context=context
                )

        return step_id


GiscedataSwitchingM1_05()


class GiscedataSwitchingD1_01(osv.osv):
    _inherit = "giscedata.switching.d1.01"

    def create_from_xml(self, cursor, uid, sw_id, xml, context=None):
        if context is None:
            context = {}

        step_id = super(GiscedataSwitchingD1_01, self).create_from_xml(
            cursor, uid, sw_id, xml, context=context
        )

        sw_obj = self.pool.get("giscedata.switching")
        sw_step_header_obj = self.pool.get("giscedata.switching.step.header")
        sw = sw_obj.browse(cursor, uid, sw_id, context=context)

        if sw and _contract_has_gurb_category(
            cursor, uid, self.pool, sw.cups_polissa_id.id, context=context
        ):
            sw_step_header_id = self.read(cursor, uid, step_id, ['header_id'])['header_id'][0]
            sw_step_header_obj.write(
                cursor, uid, sw_step_header_id, {'notificacio_pendent': False}
            )

        return step_id


GiscedataSwitchingD1_01()


class GiscedataSwitchingD1_02(osv.osv):
    _inherit = "giscedata.switching.d1.02"

    def create_from_xml(self, cursor, uid, sw_id, xml, context=None):
        if context is None:
            context = {}

        step_id = super(GiscedataSwitchingD1_02, self).create_from_xml(
            cursor, uid, sw_id, xml, context=context
        )

        sw_obj = self.pool.get("giscedata.switching")
        sw_step_header_obj = self.pool.get("giscedata.switching.step.header")
        sw = sw_obj.browse(cursor, uid, sw_id, context=context)

        if sw and _contract_has_gurb_category(
            cursor, uid, self.pool, sw.cups_polissa_id.id, context=context
        ):
            sw_step_header_id = self.read(cursor, uid, step_id, ['header_id'])['header_id'][0]
            sw_step_header_obj.write(
                cursor, uid, sw_step_header_id, {'notificacio_pendent': False}
            )

        return step_id


GiscedataSwitchingD1_02()
