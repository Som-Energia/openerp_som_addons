# -*- coding: utf-8 -*-
from osv import osv
from som_indexada.exceptions import indexada_exceptions
from datetime import datetime

class SomIndexadaWebformsHelpers(osv.osv_memory):

    _name = 'som.indexada.webforms.helpers'


    def get_k_from_pricelist(self, cursor, uid, pricelist_id):
        pricelist_obj = self.pool.get('product.pricelist')
        pricelist = pricelist_obj.browse(cursor, uid, pricelist_id)
        today = datetime.today().strftime("%Y-%m-%d")
        vlp = None
        coefficient_k = None
        for lp in pricelist.version_id:
            if lp.date_start <= today and (not lp.date_end or lp.date_end >= today):
                vlp = lp
                break
        if vlp:
            for item in vlp.items_id:
                if item.name == 'Coeficient K':
                    coefficient_k = item.base_price
                    break
        if coefficient_k != None:
            return coefficient_k/1000
        else:
            raise indexada_exceptions.KCoefficientNotFound(pricelist_id)

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
                pricelist_name =  pricelist_obj.read(cursor, uid, pricelist_id, ['name'])['name']
                coefficient_k = self.get_k_from_pricelist(cursor, uid, pricelist_id)
                return {'tariff_name': pricelist_name,
                        'k_coefficient_eurkwh': coefficient_k}

            except indexada_exceptions.IndexadaException as e:
                cursor.rollback(savepoint)
                return dict(
                    e.to_dict(),
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
                context = {'active_id': polissa_id, 'webapps': True}
                wiz_id = wiz_o.create(cursor, uid, {}, context=context)
                return wiz_o.change_to_indexada(cursor, uid, [wiz_id], context=context)
            except indexada_exceptions.IndexadaException as e:
                cursor.rollback(savepoint)
                return dict(
                    e.to_dict(),
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

        polissa_categories = polissa_obj.read(cursor, uid, polissa_id, ['category_id'])
        imd_obj = self.pool.get('ir.model.data')
        prova_pilot_cat = imd_obj._get_obj(cursor, uid,
                'som_indexada',
                'category_indexada_prova_pilot')

        if prova_pilot_cat.id in polissa_categories['category_id']:
            return True
        return False

SomIndexadaWebformsHelpers()