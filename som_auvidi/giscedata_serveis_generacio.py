# -*- coding: utf-8 -*-
from osv import osv, fields


class GiscedataServeiGeneracio(osv.osv):
    _name = "giscedata.servei.generacio"
    _inherit = "giscedata.servei.generacio"

    def config_facturador_autoconsumida(self, cursor, uid, facturador, context=None):
        if context is None:
            context = {}

        facturador.phf_function = 'phf_calc_auvi'
        res = super(GiscedataServeiGeneracio, self).config_facturador_autoconsumida(
                cursor, uid, facturador, context=context
                )

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
