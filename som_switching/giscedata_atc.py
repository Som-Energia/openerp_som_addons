# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.translate import _


class GiscedataAtc(osv.osv):

    _inherit = 'giscedata.atc'

    def case_close_pre_hook(self, cursor, uid, ids, *args):
        if len(args):
            context = args[0]
        else:
            context = {}

        res = super(GiscedataAtc, self).case_close_pre_hook(cursor, uid, ids, *args)

        conf_obj = self.pool.get("res.config")
        treure = int(conf_obj.get(cursor, uid, "treure_facturacio_suspesa_on_cac_close", "0"))
        if treure:
            pol_ids = self.read(cursor, uid, ids, ['polissa_id'], context=context)
            pol_ids = [x['polissa_id'][0] for x in pol_ids]
            self.pool.get("giscedata.polissa").write(cursor, uid, pol_ids, {'facturacio_suspesa': False})
        return res


GiscedataAtc()
