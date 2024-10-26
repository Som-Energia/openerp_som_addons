# -*- coding: utf-8 -*-
from datetime import datetime

from osv import osv, fields


class GiscedataServeiGeneracio(osv.osv):
    _name = "giscedata.servei.generacio"
    _inherit = "giscedata.servei.generacio"

    def create(self, cursor, uid, vals, context=None):
        if context is None:
            context = {}

        res_id = super(GiscedataServeiGeneracio, self).create(cursor, uid, vals, context)

        if vals.get('name'):
            imd_obj = self.pool.get('ir.model.data')
            categ_obj = self.pool.get('giscedata.polissa.category')

            new_name = "[AUVIDI] " + vals.get('name')
            new_code = "AVD" + ''.join([x[0] for x in vals.get('name').split()]).upper()
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
            servei_gen_id = sg_info.get['servei_generacio_id'][0]
            polissa_id = sg_info.get['polissa_id'][0]
            ctx = context.copy()
            ctx.update({'prefetch': False})
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

            # Condicions especifiques
            compleix_condicions = not len(altres_auvidis) and not len(matching_category_ids) \
                                  and not te_auto_collectiu and not te_generationkwh \
                                  and polissa.mode_facturacio == 'index'

            new_state = 'vinculat'
            # TODO validat NIF, s'ha d'aplicar el NIF al giscedata.servei.generacio.polissa
            # Let's check VAT is the correct one
            if polissa.titular.vat not in sg_info.get['polissa_id'] and \
                    sg_info.get['polissa_id'] not in polissa.titular.vat:
                new_state = 'pendent_incidencia'

            else:
                # Mirem l'estat de la pòlissa i les validacions específiques
                if polissa.state in ['baixa', 'cancelada']:
                    if te_auvidi_category:
                        new_state = 'anullat'
                elif polissa.state == 'esborrany':
                    if compleix_condicions:
                        new_state = 'pendent'
                    else:
                        new_state = 'pendent_incidencia'
                elif polissa.state == 'activa':
                    if compleix_condicions and te_auvidi_category:
                        new_state = 'confirmat'
                    elif te_auvidi_category:
                        new_state = 'confirmat_incidencia'
                    elif compleix_condicions:
                        new_state = 'pendent'
                    else:
                        new_state = 'pendent_incidencia'
            # new_state = 'vinculat'
            # if 'data_inici' in sg_info and sg_info['data_inici']:
            #     new_state = 'confirmat'
            # if 'data_sortida' in sg_info and sg_info['data_sortida']:
            #     if sg_info['data_sortida'] <= today:
            #         new_state = 'anullat'
            #     sg_posteriors_id = self.search(cursor, uid, [
            #         ('servei_generacio_id', '=', sg_info['servei_generacio_id'][0]),
            #         ('cups_name', '=', sg_info['cups_name']),
            #         ('data_incorporacio', '>', sg_info['data_sortida'])
            #     ], limit=1, order='data_incorporacio asc')
            #     if len(sg_posteriors_id):
            #         sg_posteriors_data = self.read(cursor, uid, sg_posteriors_id[0], read_params,
            #                                        context=context)
            #         data_anterior = (datetime.strptime(sg_posteriors_data['data_incorporacio'],
            #                                            "%Y-%m-%d") - timedelta(days=1)).strftime(
            #             "%Y-%m-%d")
            #         # Si la data anterior a l'incorporació del nou és la sortida de l'anterior, és modificació
            #         if data_anterior == sg_info['data_sortida']:
            #             new_state = 'modificat'

            res[sg_info['id']] = new_state
        return res

GiscedataServeiGeneracioPolissa()
