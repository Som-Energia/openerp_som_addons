# -*- coding: utf-8 -*-
from osv import osv
from som_indexada.exceptions import indexada_exceptions


class GiscedataPolissa(osv.osv):

    _inherit = 'giscedata.polissa'

    def send_signal(self, cursor, uid, ids, signals):
        polissa_obj = self.pool.get('giscedata.polissa')
        ctx = {'prefetch': False}

        for p_id in ids:
            pol = polissa_obj.browse(cursor, uid, p_id, context=ctx)
            if pol.modcontractuals_ids[0].state == 'pendent':
                raise indexada_exceptions.PolissaModconPending(pol.name)
            else:
                super(GiscedataPolissa, self).send_signal(
                    cursor, uid, p_id, signals
                )


GiscedataPolissa()
