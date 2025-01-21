# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import datetime, timedelta

from giscedata_serveis_generacio.giscedata_serveis_generacio import ESTATS_CONTRACTES_SERV_GEN

from osv import osv, fields

NOT_ALLOWED_COLLECTIVES = ['42', '43', '52', '55', '57', '58', '63', '64', '73', '74']


class GiscedataServeiGeneracio(osv.osv):
    _name = "giscedata.servei.generacio"
    _inherit = "giscedata.servei.generacio"

    def get_phf_calc_component(self, cursor, uid, facturador, curve, data_inici, context=None):
        if context is None:
            context = {}

        res = facturador.phf_calc_auvi(curve, data_inici)

        return res

    def create(self, cursor, uid, vals, context=None):
        if context is None:
            context = {}

        res_id = super(GiscedataServeiGeneracio, self).create(cursor, uid, vals, context)

        if vals.get('name'):
            imd_obj = self.pool.get('ir.model.data')
            categ_obj = self.pool.get('giscedata.polissa.category')

            new_name = " [AUVI] " + vals.get('name')
            new_code = "AUVI" + ''.join([x[0] for x in vals.get('name').split()]).upper()
            auvidi_categ_id = imd_obj.get_object_reference(
                cursor, uid, 'som_auvidi', 'polissa_category_auvidi_base'
            )[1]
            existing_ids = categ_obj.search(cursor, uid, [('name', '=', new_name)])
            new_vals = {}
            if len(existing_ids):
                new_vals.update({
                    'categoria_polissa': existing_ids[0]
                })
            else:
                categ_vals = {
                    'name': new_name,
                    'code': new_code,
                    'parent_id': auvidi_categ_id,
                }
                new_categ_id = categ_obj.create(cursor, uid, categ_vals, context=context)
                new_vals.update({
                    'categoria_polissa': new_categ_id
                })
            self.write(cursor, uid, [res_id], new_vals)
        return res_id

    _columns = {
        "categoria_polissa": fields.many2one("giscedata.polissa.category", "Categoria pòlissa"),
    }

    _defaults = {
        'mode_factura': lambda *a: 'contracte'
    }


GiscedataServeiGeneracio()


class GiscedataServeiGeneracioPolissa(osv.osv):
    _name = "giscedata.servei.generacio.polissa"
    _inherit = "giscedata.servei.generacio.polissa"

    def ff_get_state(self, cursor, uid, ids, name, arg, context=None):
        if context is None:
            context = {}

        imd = self.pool.get('ir.model.data')
        polissa_obj = self.pool.get('giscedata.polissa')
        modcon_obj = self.pool.get('giscedata.polissa.modcontractual')
        swi_obj = self.pool.get('giscedata.switching')
        m1_obj = self.pool.get('giscedata.switching.m1.01')
        polissa_category_obj = self.pool.get('giscedata.polissa.category')
        servei_gen_pol_obj = self.pool.get('giscedata.servei.generacio.polissa')

        res = {}
        today = datetime.today().strftime("%Y-%m-%d")
        read_params = ['data_sortida', 'data_inici', 'data_incorporacio', 'cups_name',
                       'servei_generacio_id', 'polissa_id', 'nif']

        # Categories GURB
        not_allowed_pol_category_ids = polissa_category_obj.search(
            cursor, 1, [('code', 'ilike', 'GURB')])

        # Categories AUVIDI
        auvidi_base_categ_id = imd.get_object_reference(
            cursor, uid, 'som_auvidi', 'polissa_category_auvidi_base')[1]
        auvidi_category_ids = polissa_category_obj.search(
            cursor, 1, [('parent_id', '=', auvidi_base_categ_id)])

        for sg_info in self.read(cursor, uid, ids, read_params, context=context):
            servei_gen_id = sg_info['servei_generacio_id'][0]
            polissa_id = sg_info.get('polissa_id')
            ctx = context.copy()
            ctx.update({'prefetch': False})

            # Te data_inici i aquesta és anterior o igual a avui
            actiu_today = sg_info.get('data_inici') and sg_info['data_inici'] <= today

            # Te data_sortida i aquesta és anterior o igual a avui
            anullat_today = sg_info.get('data_sortida') and sg_info['data_sortida'] <= today

            new_state = 'vinculat'
            if anullat_today:
                new_state = 'anullat'
                posteriors_params = [
                    ('servei_generacio_id', '=', sg_info['servei_generacio_id'][0]),
                    ('cups_name', '=', sg_info['cups_name']),
                    ('data_incorporacio', '>', sg_info['data_sortida'])
                ]

                if polissa_id:
                    posteriors_params.append(('polissa_id', '=', polissa_id[0]))

                sg_posteriors_id = self.search(
                    cursor, uid, posteriors_params, limit=1, order='data_incorporacio asc'
                )
                if len(sg_posteriors_id):
                    sg_posteriors_data = self.read(
                        cursor, uid, sg_posteriors_id[0], read_params, context=context
                    )
                    data_anterior = (datetime.strptime(
                        sg_posteriors_data['data_incorporacio'], "%Y-%m-%d"
                    ) - timedelta(days=1)).strftime("%Y-%m-%d")
                    # Si la data anterior a l'incorporació del nou és la sortida de l'anterior,
                    # és modificació
                    if data_anterior == sg_info['data_sortida']:
                        new_state = 'modificat'

            # Si no hi ha pòlissa o el sg_polissa ja ha sortit no cal que seguim mirant
            if not polissa_id or new_state != 'vinculat':
                res[sg_info['id']] = new_state
                continue
            else:
                polissa_id = polissa_id[0]
            polissa = polissa_obj.browse(cursor, uid, polissa_id, context=ctx)

            # Te autoconsum col.lectiu
            te_auto_collectiu = polissa_obj.te_autoconsum(
                cursor, uid, polissa_id, amb_o_sense_excedents=5, context=context)

            # Participació en altres AUVIDIs
            altres_auvidis = servei_gen_pol_obj.search(cursor, uid, [
                ('polissa_id', '=', polissa_id),
                ('servei_generacio_id', '!=', servei_gen_id)
            ])

            # Categories coincidents que no es permeten
            matching_category_ids = [
                cat.id for cat in polissa.category_id if cat.id in not_allowed_pol_category_ids
            ]

            # Te categoria AUVIDI
            te_auvidi_category = bool(len([
                cat.id for cat in polissa.category_id if cat.id in auvidi_category_ids
            ]))

            # TODO validar generationkwh
            te_generationkwh = polissa.te_assignacio_gkwh

            # La llista de preus és ESMASA
            te_llista_preus_esmasa = polissa.llista_preu.indexed_formula == 'Indexada ESMASA'

            # Condicions especifiques
            compleix_condicions = (not len(altres_auvidis)
                                   and not len(matching_category_ids)
                                   and not te_auto_collectiu
                                   and not te_generationkwh
                                   and not te_llista_preus_esmasa
                                   and polissa.mode_facturacio == 'index')

            # Condicions extra confirmat
            te_modi_pendent_canvi_mode_facturacio = False
            modcons_pendents = modcon_obj.search(cursor, uid, [
                ('polissa_id', '=', polissa_id),
                ('state', '=', 'pendent')
            ])
            if len(modcons_pendents):
                for modcon_pendent in modcons_pendents:
                    modcon = modcon_obj.browse(cursor, uid, modcon_pendent)
                    if modcon.mode_facturacio != modcon.modcontractual_ant.mode_facturacio:
                        te_modi_pendent_canvi_mode_facturacio = True

            sw_ids = swi_obj.search(cursor, uid, [
                ('cups_polissa_id', '=', polissa_id),
                ('state', 'in', ['open', 'draft']),
            ])

            m1s_canvi_autoconsum_collectiu = m1_obj.search(cursor, uid, [
                ('header_id.sw_id', 'in', sw_ids),
                ('sollicitudadm', 'in', ['N', 'A']),
                ('tipus_autoconsum', 'in', NOT_ALLOWED_COLLECTIVES)
            ])

            m1s_canvi_titular = m1_obj.search(cursor, uid, [
                ('header_id.sw_id', 'in', sw_ids),
                ('sollicitudadm', 'in', ['S', 'A']),
                ('canvi_titular', 'in', ['S', 'T'])
            ])

            te_m1_canvi_auto_collectiu = bool(len(m1s_canvi_autoconsum_collectiu))
            te_m1_canvi_titular = bool(len(m1s_canvi_titular))

            compleix_extra_condicions = (
                not te_modi_pendent_canvi_mode_facturacio
                and not te_m1_canvi_auto_collectiu
                and not te_m1_canvi_titular
            )

            # Let's check VAT is the correct one
            te_nif = sg_info.get('nif') and sg_info['nif']
            if (not te_nif or (te_nif and polissa.titular.vat not in sg_info['nif']
                               and sg_info['nif'] not in polissa.titular.vat)):
                new_state = 'pendent_incidencia'
            else:
                # Mirem l'estat de la pòlissa i les validacions específiques
                if anullat_today:
                    new_state = 'anullat'
                elif polissa.state in ['baixa', 'cancelada']:
                    if te_auvidi_category:
                        new_state = 'anullat'
                elif polissa.state == 'esborrany':
                    if compleix_condicions:
                        new_state = 'pendent'
                    else:
                        new_state = 'pendent_incidencia'
                elif polissa.state == 'activa':
                    if (compleix_condicions and te_auvidi_category
                            and actiu_today and compleix_extra_condicions):
                        new_state = 'confirmat'
                    elif te_auvidi_category and actiu_today:
                        new_state = 'confirmat_incidencia'
                    elif compleix_condicions:
                        new_state = 'pendent'
                    else:
                        new_state = 'pendent_incidencia'

            res[sg_info['id']] = new_state
        return res

    _columns = {
        'state': fields.function(
            ff_get_state, method=True, type='selection',
            selection=ESTATS_CONTRACTES_SERV_GEN, string='Estat'
        ),
    }


GiscedataServeiGeneracioPolissa()
