# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv
from tools.translate import _


def cancel_switching_if_gurb(cursor, uid, pool, sw_id, context=None):
    if context is None:
        context = {}

    pol_obj = pool.get('giscedata.polissa')
    sw_obj = pool.get('giscedata.switching')
    ir_model_obj = pool.get('ir.model.data')

    pol_id = sw_obj.read(
        cursor, uid, sw_id, ['cups_polissa_id'], context=context
    )['cups_polissa_id']

    gurb_categ_id = ir_model_obj.get_object_reference(
        cursor, uid, 'som_gurb', 'categ_gurb_pilot'
    )[1]

    pol_category_ids = pol_obj.read(cursor, uid, pol_id, ['category_id'])['category_id']

    if gurb_categ_id in pol_category_ids:
        write_params = {
            'description': _('Cas cancel·lat per GURB'),
            'state': 'cancel'
        }
        sw_obj.write(cursor, uid, sw_id, write_params, context=context)


class GiscedataSwitchingD1_01(osv.osv):
    _inherit = "giscedata.switching.d1.01"

    def create_from_xml(self, cursor, uid, sw_id, xml, context=None):
        if context is None:
            context = {}

        pas_id = super(GiscedataSwitchingD1_01, self).create_from_xml(
            cursor, uid, sw_id, xml, context=context
        )
        cancel_switching_if_gurb(cursor, uid, self.pool, sw_id, context=context)

        return pas_id


GiscedataSwitchingD1_01()


class GiscedataSwitchingM1_02(osv.osv):
    _inherit = "giscedata.switching.m1.02"

    def create_from_xml(self, cursor, uid, sw_id, xml, context=None):
        if context is None:
            context = {}

        pas_id = super(GiscedataSwitchingD1_01, self).create_from_xml(
            cursor, uid, sw_id, xml, context=context
        )
        cancel_switching_if_gurb(cursor, uid, self.pool, sw_id, context=context)

        return pas_id


GiscedataSwitchingM1_02()


class GiscedataSwitchingM1_03(osv.osv):
    _inherit = "giscedata.switching.m1.03"

    def create_from_xml(self, cursor, uid, sw_id, xml, context=None):
        if context is None:
            context = {}

        pas_id = super(GiscedataSwitchingD1_01, self).create_from_xml(
            cursor, uid, sw_id, xml, context=context
        )
        cancel_switching_if_gurb(cursor, uid, self.pool, sw_id, context=context)

        return pas_id


GiscedataSwitchingM1_03()


class GiscedataSwitchingM1_04(osv.osv):
    _inherit = "giscedata.switching.m1.04"

    def create_from_xml(self, cursor, uid, sw_id, xml, context=None):
        if context is None:
            context = {}

        pas_id = super(GiscedataSwitchingD1_01, self).create_from_xml(
            cursor, uid, sw_id, xml, context=context
        )
        cancel_switching_if_gurb(cursor, uid, self.pool, sw_id, context=context)

        return pas_id


GiscedataSwitchingM1_04()


class GiscedataSwitchingM1_05(osv.osv):
    _inherit = "giscedata.switching.m1.05"

    def create_from_xml(self, cursor, uid, sw_id, xml, context=None):
        if context is None:
            context = {}

        pas_id = super(GiscedataSwitchingD1_01, self).create_from_xml(
            cursor, uid, sw_id, xml, context=context
        )
        cancel_switching_if_gurb(cursor, uid, self.pool, sw_id, context=context)

        return pas_id


GiscedataSwitchingM1_05()
