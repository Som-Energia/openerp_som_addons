# coding=utf-8
from __future__ import absolute_import
from osv import osv, fields
from datetime import datetime, timedelta


class GiscedataPolissa(osv.osv):
    _name = "giscedata.polissa"
    _inherit = "giscedata.polissa"

    _columns = {
        'te_auvidi': fields.boolean(
            'Té Autoconsum Virtual',
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

    def aplicar_modificacio(self, cursor, uid, mod_id, polissa_id=None):
        """Aplica els canvis d'una modificació contractual a una pòlissa."""
        res = super(GiscedataPolissaModcontractual, self).aplicar_modificacio(
            cursor, uid, mod_id, polissa_id=polissa_id
        )
        polissa_obj = self.pool.get('giscedata.polissa')
        servei_gen_obj = self.pool.get('giscedata.servei.generacio')
        sg_polissa_obj = self.pool.get('giscedata.servei.generacio.polissa')

        if not polissa_id:
            polissa_id = self.simple_browse(cursor, uid, mod_id).polissa_id.id

        modcon = self.simple_browse(cursor, uid, mod_id)
        current_te_auvidi = modcon.te_auvidi
        cancels_auvidi = (modcon.modcontractual_ant
                          and modcon.modcontractual_ant.te_auvidi
                          and not modcon.te_auvidi)
        context = {}
        info = ''
        sg_pol_id = sg_polissa_obj.search(cursor, uid, [('polissa_id', '=', polissa_id)])
        if len(sg_pol_id):
            if current_te_auvidi:
                sg_polissa_obj.handle_polissa_sg_category(cursor, uid, polissa_id, action='assign', context=context)
                # # Actualitzem data inici si fa falta
                info = sg_polissa_obj.check_actualitzar_data_inici(
                    cursor, uid, sg_pol_id, modcon.data_inici
                )
            elif cancels_auvidi:
                sg_polissa_obj.handle_polissa_sg_category(cursor, uid, polissa_id, action='unassign', context=context)
                # Actualitzem data sortida si fa falta
                data_inici_modcon = datetime.strptime(modcon.data_inici, '%Y-%m-%d')
                data_sortida_sg = data_inici_modcon - timedelta(days=1)
                data_sortida_sg_str = data_sortida_sg.strftime('%Y-%m-%d')
                info = sg_polissa_obj.check_actualitzar_data_sortida(
                    cursor, uid, sg_pol_id, data_sortida_sg_str
                )

            if info:
                observacions = modcon.observacions + info
                modcon.write({'observacions': observacions})

        return res

    _columns = {
        'te_auvidi': fields.boolean('Té Autoconsum Virtual'),
    }


GiscedataPolissaModcontractual()
