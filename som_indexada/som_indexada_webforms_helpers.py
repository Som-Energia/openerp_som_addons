# -*- coding: utf-8 -*-
from osv import osv

class SomIndexadaWebformsHelpers(osv.osv_memory):

    _name = 'som.indexada.webforms.helpers'

    def traceback_info(self, exception):
        import traceback
        import sys
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)

    def check_new_pricelist_www(self, cursor, uid, polissa_id, context=None):
            savepoint = 'check_new_pricelist_indexada_{}'.format(id(cursor))
            cursor.savepoint(savepoint)
            try:
                polissa_obj = self.pool.get('giscedata.polissa')
                pricelist_obj = self.pool.get('product.pricelist')
                polissa = polissa_obj.browse(cursor, uid, polissa_id)
                wiz_o = self.pool.get('wizard.change.to.indexada')
                wiz_id = wiz_o.create(cursor, uid, {}, context=context)
                wiz_o.validate_polissa_can_indexada(cursor, uid, polissa)
                pricelist_id =  wiz_o.calculate_new_pricelist(cursor, uid, polissa, context=context)
                return pricelist_obj.read(cursor, uid, pricelist_id, ['name'])['name']

            except osv.except_osv as e:
                cursor.rollback(savepoint)
                return dict(
                    error=str(e),
                    trace=self.traceback_info(e),
                )
            except Exception as e:
                cursor.rollback(savepoint)
                return dict(
                    error=str(e),
                    code="Unexpected",
                    trace=self.traceback_info(e),
                )

    def change_to_indexada_www(self, cursor, uid, polissa_id, context=None):
            savepoint = 'change_to_indexada_{}'.format(id(cursor))
            cursor.savepoint(savepoint)
            try:
                wiz_o = self.pool.get('wizard.change.to.indexada')
                context = {'active_id': polissa_id}
                wiz_id = wiz_o.create(cursor, uid, {}, context=context)
                return wiz_o.change_to_indexada(cursor, uid, [wiz_id], context=context)
            except osv.except_osv as e:
                cursor.rollback(savepoint)
                return dict(
                    error=str(e),
                    trace=self.traceback_info(e),
                )
            except Exception as e:
                cursor.rollback(savepoint)
                return dict(
                    error=str(e),
                    code="Unexpected",
                    trace=self.traceback_info(e),
                )

    def has_indexada_prova_pilot_category_www(self, cursor, uid, polissa_id):
        polissa_obj = self.pool.get('giscedata.polissa')
        polissa = polissa_obj.browse(cursor, uid, polissa_id)

        res_partner_obj = self.pool.get('res.partner')
        partner_categories = res_partner_obj.read(cursor, uid, polissa.titular.id, ['category_id'])
        imd_obj = self.pool.get('ir.model.data')
        prova_pilot_cat = imd_obj._get_obj(cursor, uid,
                'som_indexada',
                'res_partner_category_indexada_prova_pilot')

        if prova_pilot_cat.id in partner_categories['category_id']:
            return True
        return False

SomIndexadaWebformsHelpers()