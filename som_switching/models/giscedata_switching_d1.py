# -*- coding: utf-8 -*-
from osv import osv


class GiscedataSwitchingD1_01(osv.osv):
    """Classe per gestionar el canvi de comercialitzador"""

    _name = "giscedata.switching.d1.01"
    _inherit = "giscedata.switching.d1.01"

    def create(self, cursor, uid, values, context=None):
        res_id = super(GiscedataSwitchingD1_01, self).create(cursor, uid, values, context=context)
        # Forcem el recomput del camp function
        obj = self.browse(cursor, uid, res_id, context=context)
        if obj.dades_cau:
            self.pool.get('giscedata.switching')._store_set_values(
                cursor, uid, [obj.sw_id.id], ['collectiu_atr'], context)

        return res_id


GiscedataSwitchingD1_01()
