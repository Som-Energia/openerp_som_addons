# -*- coding: utf-8 -*-
from osv import osv, fields

class WizardChangeToIndexadaMulti(osv.osv_memory):

    _name = 'wizard.change.to.indexada.multi'


    def change_to_indexada_multi(self, cursor, uid, ids, context=None):
        if context is None:
            context = {}

        wiz_og = self.browse(cursor, uid, ids[0], context=context)

        pol_ids = context.get("active_ids")
        wz_chng_to_indx_obj = self.pool.get('wizard.change.to.indexada')
        failed_polisses = []
        pol_ok = []
        for pol in pol_ids:
            ctx = {'active_id': pol,
                'business_pricelist': wiz_og.pricelist.id,
                'coeficient_k': wiz_og.coeficient_k}
            params = {'change_type': 'from_period_to_index'}
            wiz_id = wz_chng_to_indx_obj.create(
                cursor, uid, params, context=ctx
            )
            wiz = wz_chng_to_indx_obj.browse(
                cursor, uid, [wiz_id]
            )[0]
            try:
                res = wz_chng_to_indx_obj.change_to_indexada(
                    cursor, uid, [wiz.id], context=ctx
                )
                pol_ok.append(pol)
            except Exception:
                failed_polisses.append(pol)

        info = ""
        if failed_polisses:
            info += "\nLes pòlisses següents han fallat: {}".format(str(failed_polisses))
        if not failed_polisses:
            info = "Procés acabat correctament!"

        wiz_og.write(
            {
                "state": "end",
                "info": info
            }
        )

    _columns = {
        'state': fields.selection([('init', 'Init'),
                                   ('end', 'End')], 'State'),
        'info': fields.text('Description'),
        'pricelist': fields.many2one('product.pricelist', "Tarifa"),
        'coeficient_k': fields.integer('Coeficient K'),
    }

    _defaults = {
        'state': lambda *a: 'init',
    }


WizardChangeToIndexadaMulti()
