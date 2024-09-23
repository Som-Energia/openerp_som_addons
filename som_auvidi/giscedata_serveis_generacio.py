# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime, timedelta


class GiscedataServeiGeneracio(osv.osv):
    _name = "giscedata.servei.generacio"
    _inherit = "giscedata.servei.generacio"

    def onchange_name(self, cursor, uid, ids, name, context=None):
        if context is None:
            context = {}
        res = {}
        if name:
            imd_obj = self.pool.get('ir.model.data')
            categ_obj = self.pool.get('giscedata.polissa.category')

            new_name = "[AUVIDI] " + name
            new_code = "AVD" + ''.join([x[0] for x in name.split()]).upper()
            auvidi_categ_id = imd_obj.get_object_reference(
                cursor, uid, 'som_auvidi', 'polissa_category_auvidi_base'
            )[1]
            existing_ids = categ_obj.search(cursor, uid, [('name', '=', new_name)])
            if len(existing_ids):
                res.update({
                    'value': {'categoria_polissa': existing_ids[0]}
                })
            else:
                categ_vals = {
                    'name': new_name,
                    'code': new_code,
                    'parent_id': auvidi_categ_id,
                }
                new_categ_id = categ_obj.create(cursor, uid, categ_vals, context=context)
                res.update({
                    'value': {'categoria_polissa': new_categ_id}
                })
        return res

    _columns = {
        "categoria_polissa": fields.many2one("giscedata.polissa.category", "Categoria pòlissa"),
    }


GiscedataServeiGeneracio()
