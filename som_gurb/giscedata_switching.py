# -*- coding: utf-8 -*-
from __future__ import absolute_import

from osv import osv

class GiscedataSwitchingD1_01(osv.osv):
    """Classe pel pas 01"""

    _inherit = "giscedata.switching.d1.01"

    def create_from_xml(self, cursor, uid, sw_id, xml, context=None):
        if context is None:
            context = {}

        pol_obj = self.pool.get('giscedata.polissa')
        sw_obj = self.pool.get('giscedata.switching')
        ir_model_obj = self.pool.get('ir.model.data')
        sw_step_info_obj = self.pool.get('giscedata.switching.step.info')

        pas_id = super(GiscedataSwitchingD1_01, self).create_from_xml(cursor, uid, proces, where, context=context)
        ref_pas_id = 'giscedata.switching.d1.01,{}'.format(pas_id)

        search_parms = [
            ('pas_id', '=', ref_pas_id)
        ]

        sw_step_info_id = sw_step_info_obj.search(cursor, uid, search_parms, context=context)
        sw_id = sw_step_info_obj.read(cursor, uid, sw_step_info_id, ['sw_id'])['sw_id']

        pol_id = sw_obj.read(cursor, uid, sw_id, ['cups_polissa_id'], context=context)['cups_polissa_id']

        gurb_categ_id = ir_model_obj.get_object_reference(
            cursor, uid, 'som_gurb', 'categ_gurb_pilot'
        )[1]

        pol_category_ids = pol_obj.read(cursor, uid, pol_id, ['category_id'])['category_id']

        if gurb_categ_id in pol_category_ids:
            self.write(cursor, uid, sw_id, {
                'description': _('Cas cancel·lat per GURB'),
                'state': 'cancel'
            })

        return pas_id

GiscedataSwitchingD1_01()
