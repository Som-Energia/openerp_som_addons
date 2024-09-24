# coding=utf-8
from __future__ import absolute_import
from osv import osv, fields


class GiscedataPolissa(osv.osv):
    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    _columns = {
        'te_auvidi': fields.boolean(
            'Té AUVIDI',
            readonly=True,
            states={
                'esborrany': [('readonly', False)],
                'validar': [('readonly', False)],
                'modcontractual': [('readonly', False)]
            }),
    }


GiscedataPolissa()


class GiscedataPolissaModcontractual(osv.osv):
    _name = "giscedata.polissa.modcontractual"
    _inherit = "giscedata.polissa.modcontractual"

    def _do_previous_actions_on_activation(self, cursor, uid, mc_id, context=None):
        res = super(GiscedataPolissaModcontractual, self)._do_previous_actions_on_activation(
            cursor, uid, mc_id, context
        )
        if res == 'OK':
            modcon = self.browse(cursor, uid, mc_id, context={'prefetch': False})
            te_auvidi_ara = modcon.te_auvidi
            tenia_auvidi_abans = modcon.modcontractual_ant.te_auvidi

            if modcon.modcontractual_ant and te_auvidi_ara and te_auvidi_ara != tenia_auvidi_abans:
                # Let's check if last F1 reading is prev to modcon creation date (without time)
                if not self._apply_modcon_date_last_f1_plus_1(cursor, uid, mc_id, context=None):
                    return 'error'
        return res

    _columns = {
        'te_auvidi': fields.boolean('Té AUVIDI'),
    }

GiscedataPolissaModcontractual()
