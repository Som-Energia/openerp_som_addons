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

    def aplicar_modificacio(self, cursor, uid, mod_id, polissa_id=None):
        """Aplica els canvis d'una modificació contractual a una pòlissa."""
        res = super(GiscedataPolissaModcontractual, self).aplicar_modificacio(
            cursor, uid, mod_id, polissa_id=polissa_id
        )
        polissa_obj = self.pool.get('giscedata.polissa')
        servei_gen_obj = self.pool.get('giscedata.servei.generacio')
        sg_polissa_obj = self.pool.get('giscedata.servei.generacio.polissa')

        if not polissa_id:
            polissa_id = self.browse(cursor, uid, mod_id).polissa_id.id

        modcon = self.browse(cursor, uid, mod_id)
        current_te_auvidi = modcon.te_auvidi
        cancels_auvidi = (modcon.modcontractual_ant
                          and modcon.modcontractual_ant.te_auvidi
                          and not modcon.te_auvidi)

        if current_te_auvidi or cancels_auvidi:
            sg_pol_id = sg_polissa_obj.search(cursor, uid, [('polissa_id', '=', polissa_id)])
            if len(sg_pol_id):
                sg_pol_data = sg_polissa_obj.read(
                    cursor, uid, sg_pol_id[0], ['servei_generacio_id'])
                if sg_pol_data.get('servei_generacio_id'):
                    servei_gen_id = sg_pol_data.get('servei_generacio_id', [False])[0]
                    if servei_gen_id:
                        categoria_polissa = servei_gen_obj.read(
                            cursor, uid, servei_gen_id, ['categoria_polissa']
                        ).get('categoria_polissa')
                        polissa_current_categories = polissa_obj.read(
                            cursor, uid, polissa_id, ['category_id']
                        ).get('category_id', [])
                        polissa_current_categories = list(set(polissa_current_categories))
                        new_categories = []
                        # If AUVIDI is cancelled we must remove category
                        if (cancels_auvidi
                                and categoria_polissa
                                and categoria_polissa[0] in polissa_current_categories):
                            polissa_current_categories.remove(categoria_polissa[0])
                            new_categories = polissa_current_categories
                        # If AUVIDI and there's no category we must add it
                        elif (current_te_auvidi
                              and categoria_polissa
                              and categoria_polissa[0] not in polissa_current_categories):
                            new_categories = polissa_current_categories + [categoria_polissa[0]]

                        if new_categories:
                            polissa_obj.write(cursor, uid, polissa_id, {
                                'category_id': [(6, 0, new_categories)]})
        return res

    _columns = {
        'te_auvidi': fields.boolean('Té AUVIDI'),
    }


GiscedataPolissaModcontractual()
