# -*- coding: utf-8 -*-
from osv import osv
from som_indexada.exceptions import indexada_exceptions
from datetime import datetime
from decorator import decorator

@decorator
def www_entry_point(f, self, cursor *args, expected_exceptions=tuple(), **kwds):
    """
    Wrapps an erp method so that it can be called safely from the web.

    - Establishes a database savepoint to return at if an exception happens.
    - Translates any expected_exceptions to a error dictionary.
    - Any other exception will be also translated but with code 'Unexpected'
    - To any exception, expected or unexpected,
      it adds the backtrace as attribute of the dictionary.
    """
    def traceback_info(exception):
        import traceback
        import sys
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)

    savepoint = 'change_pricelist_{}'.format(id(cursor))
    cursor.savepoint(savepoint)
    try:
        return f(self, cursor, *args, **kwds)
    except expected_exceptions as e:
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

class SomIndexadaWebformsHelpers(osv.osv_memory):

    _name = 'som.indexada.webforms.helpers'

    def get_k_from_pricelist(self, cursor, uid, pricelist_id):
        pricelist_obj = self.pool.get('product.pricelist')
        pricelist = pricelist_obj.browse(cursor, uid, pricelist_id)
        today = datetime.today().strftime("%Y-%m-%d")
        vlp = None
        coefficient_k = None
        for lp in pricelist.version_id:
            if lp.date_start <= today and (
                not lp.date_end or lp.date_end >= today
            ):
                vlp = lp
                break
        if vlp:
            for item in vlp.items_id:
                if item.name == 'Coeficient K':
                    coefficient_k = item.base_price
                    break
        if coefficient_k is not None:
            return coefficient_k
        else:
            raise indexada_exceptions.KCoefficientNotFound(pricelist_id)

    def _get_change_type(self, cursor, uid, polissa_id):
        change_type = "from_period_to_index"
        cfg_obj = self.pool.get('res.config')
        # 'flag_change_tariff_switch' enables change tariff switching.
        # If value == 0, just change from period to index is available
        flag_change_tariff_switch = int(cfg_obj.get(cursor, uid, 'som_flag_change_tariff_switch', '0'))

        if flag_change_tariff_switch:
            polissa_obj = self.pool.get('giscedata.polissa')
            polissa = polissa_obj.browse(cursor, uid, polissa_id)
            if polissa.mode_facturacio == "index":
                change_type = "from_index_to_period"

        return change_type

    @www_entry_point(
        expected_exceptions=indexada_exceptions.IndexadaException,
    )
    def check_new_pricelist_www(self, cursor, uid, polissa_id, context=None):
        change_type = self._get_change_type(cursor, uid, polissa_id)

        polissa_obj = self.pool.get('giscedata.polissa')
        pricelist_obj = self.pool.get('product.pricelist')
        polissa = polissa_obj.browse(cursor, uid, polissa_id)

        wiz_o = self.pool.get('wizard.change.to.indexada')
        wiz_o.validate_polissa_can_change(
            cursor,
            uid,
            polissa,
            change_type,
            only_standard_prices=True,
        )
        pricelist_id = wiz_o.calculate_new_pricelist(
            cursor,
            uid,
            polissa,
            change_type,
            context=context,
        )
        pricelist_name = pricelist_obj.read(
            cursor,
            uid,
            pricelist_id,
            ['name', 'nom_comercial'],
        )
        if pricelist_name.get('nom_comercial'):
            pricelist_name = pricelist_name['nom_comercial']
        else:
            pricelist_name = pricelist_name['name']
        coefficient_k = self.get_k_from_pricelist(
            cursor,
            uid,
            pricelist_id
        ) if change_type == "from_period_to_index" else None
        return {
            'tariff_name': pricelist_name,
            'k_coefficient_eurkwh': coefficient_k,
        }

    def change_to_indexada_www(self, cursor, uid, polissa_id, context=None):
        return self.change_pricelist_www(cursor, uid, polissa_id, context)

    @www_entry_point(
        expected_exceptions=indexada_exceptions.IndexadaException,
    )
    def change_pricelist_www(self, cursor, uid, polissa_id, context=None):
        change_type = self._get_change_type(cursor, uid, polissa_id)

        wiz_o = self.pool.get('wizard.change.to.indexada')
        context = {
            'active_id': polissa_id,
            'change_type': change_type,
            'webapps': True,
        }
        wiz_id = wiz_o.create(cursor, uid, {}, context=context)
        return wiz_o.change_to_indexada(
            cursor,
            uid,
            [wiz_id],
            context=context,
        )

    def has_indexada_prova_pilot_category_www(self, cursor, uid, polissa_id):
        polissa_obj = self.pool.get('giscedata.polissa')

        polissa_categories = polissa_obj.read(
            cursor,
            uid,
            polissa_id,
            ['category_id'],
        )
        imd_obj = self.pool.get('ir.model.data')
        prova_pilot_cat = imd_obj._get_obj(
            cursor,
            uid,
            'som_indexada',
            'category_indexada_prova_pilot',
        )
        if prova_pilot_cat.id in polissa_categories['category_id']:
            return True
        return False


SomIndexadaWebformsHelpers()
