# -*- coding: utf-8 -*-
from osv import osv


class GiscedataSwitchingC1_02(osv.osv):
    """Classe pel pas 02
    """
    _name = "giscedata.switching.c1.02"
    _inherit = "giscedata.switching.c1.02"

    def onchange_rebuig(self, cursor, uid, ids, rebuig, context=None):
        if not context:
            context = {}
        if ids and isinstance(ids, (list, tuple)):
            ids = ids[0]

        if rebuig:
            pass
            # sw.case_close o self.case_close()
            # fer C2 automàticament
            # wiz_obj = self.pool.get("giscedata.switching.mod.con.wizard")
            # wiz_id = wiz_obj.create(cursor, uid, {}, context={"cas": "C2", "pol_id": pol_id})
            # wiz_obj.genera_casos_atr(cursor, uid, [wiz_id], context={"pol_id": pol_id})

        return super(GiscedataSwitchingC1_02, self).onchange_rebuig(
            cursor, uid, ids, rebuig, context=None
        )


GiscedataSwitchingC1_02()
