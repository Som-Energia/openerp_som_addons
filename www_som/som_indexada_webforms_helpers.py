# -*- coding: utf-8 -*-
from osv import osv
from som_polissa.exceptions import exceptions
from www_som.helpers import www_entry_point
import json
from datetime import datetime, timedelta

SUBSYSTEMS = [
    'PENINSULA',
    'BALEARES',
    'CANARIAS',
]


class SomIndexadaWebformsHelpers(osv.osv_memory):

    _name = "som.indexada.webforms.helpers"

    def get_k_from_pricelist(self, cursor, uid, pricelist_id):
        pricelist_obj = self.pool.get("product.pricelist")
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
                if item.name == "Coeficient K":
                    coefficient_k = item.base_price
                    break
        if coefficient_k is not None:
            return coefficient_k
        else:
            raise exceptions.KCoefficientNotFound(pricelist_id)

    def _get_change_type(self, cursor, uid, polissa_id):
        change_type = "from_period_to_index"
        cfg_obj = self.pool.get("res.config")
        # 'flag_change_tariff_switch' enables change tariff switching.
        # If value == 0, just change from period to index is available
        flag_change_tariff_switch = int(
            cfg_obj.get(cursor, uid, "som_flag_change_tariff_switch", "0")
        )

        if flag_change_tariff_switch:
            polissa_obj = self.pool.get("giscedata.polissa")
            polissa = polissa_obj.browse(cursor, uid, polissa_id)
            if polissa.mode_facturacio == "index":
                change_type = "from_index_to_period"

        return change_type

    @www_entry_point(
        expected_exceptions=exceptions.SomPolissaException,
    )
    def check_new_pricelist_www(self, cursor, uid, polissa_id, context=None):
        if context is None:
            context = {}

        tariff_name = context.get("tariff_name", "name")

        change_type = self._get_change_type(cursor, uid, polissa_id)

        polissa_obj = self.pool.get("giscedata.polissa")
        pricelist_obj = self.pool.get("product.pricelist")
        polissa = polissa_obj.browse(cursor, uid, polissa_id)

        wiz_o = self.pool.get("wizard.change.to.indexada")
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
            [tariff_name],
        )[tariff_name]
        coefficient_k = (
            self.get_k_from_pricelist(cursor, uid, pricelist_id)
            if change_type == "from_period_to_index"
            else None
        )
        return {
            "tariff_name": pricelist_name,
            "k_coefficient_eurkwh": coefficient_k,
        }

    def change_to_indexada_www(self, cursor, uid, polissa_id, context=None):
        """DEPRECATED: use change_pricelist_www instead"""
        return self.change_pricelist_www(cursor, uid, polissa_id, context)

    @www_entry_point(
        expected_exceptions=exceptions.SomPolissaException,
    )
    def change_pricelist_www(self, cursor, uid, polissa_id, context=None):
        change_type = self._get_change_type(cursor, uid, polissa_id)

        wiz_o = self.pool.get("wizard.change.to.indexada")
        context = {
            "active_id": polissa_id,
            "change_type": change_type,
            "webapps": True,
        }
        wiz_id = wiz_o.create(cursor, uid, {}, context=context)
        return wiz_o.change_to_indexada(
            cursor,
            uid,
            [wiz_id],
            context=context,
        )

    def has_indexada_prova_pilot_category_www(self, cursor, uid, polissa_id):
        polissa_obj = self.pool.get("giscedata.polissa")

        polissa_categories = polissa_obj.read(
            cursor,
            uid,
            polissa_id,
            ["category_id"],
        )
        imd_obj = self.pool.get("ir.model.data")
        prova_pilot_cat = imd_obj._get_obj(
            cursor,
            uid,
            "som_indexada",
            "category_indexada_prova_pilot",
        )
        if prova_pilot_cat.id in polissa_categories["category_id"]:
            return True
        return False

    def validate_parameters(self, cursor, uid, geo_zone, first_date, last_date, tariff=None):
        if geo_zone not in SUBSYSTEMS:
            raise exceptions.InvalidSubsystem(geo_zone)

        tariff_obj = self.pool.get('giscedata.polissa.tarifa')
        if tariff and not tariff_obj.search(cursor, uid, [('name', '=', tariff)]):
            raise exceptions.TariffNonExists(tariff)

        if first_date is None or last_date is None or \
           (first_date is not None and last_date is not None and last_date < first_date):
            raise exceptions.InvalidDates(first_date, last_date)

    def initial_final_times(self, first_date, last_date):
        initial_time = (datetime.strptime(first_date, '%Y-%m-%d')
                        + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        final_time = (datetime.strptime(last_date, '%Y-%m-%d')
                      + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        return initial_time, final_time

    @www_entry_point(
        expected_exceptions=exceptions.SomPolissaException,
    )
    def get_indexed_prices(
        self, cursor, uid, geo_zone, tariff, first_date, last_date, context=None
    ):
        prices_obj = self.pool.get('giscedata.next.days.energy.price')

        self.validate_parameters(cursor, uid, geo_zone, first_date, last_date, tariff)

        initial_time, final_time = self.initial_final_times(first_date, last_date)
        params = [
            ('hour_timestamp', '>=', initial_time),
            ('hour_timestamp', '<=', final_time),
            ('tarifa_id.name', '=', tariff),
            ('geom_zone', '=', geo_zone)
        ]
        price_ids = prices_obj.search(cursor, uid, params, order='hour_timestamp')

        curves = []
        for price_id in price_ids:
            curves.append(prices_obj.read(cursor, uid, price_id, ['initial_price', 'maturity']))

        json_prices = json.dumps(dict(
            first_date=first_date,
            last_date=last_date,
            curves=dict(
                geo_zone=geo_zone,
                tariff=tariff,
                price_euros_kwh=[curve.get('initial_price') for curve in curves],
                maturity=[curve.get('maturity') for curve in curves]
            ))
        )

        return json_prices

    @www_entry_point(
        expected_exceptions=exceptions.SomPolissaException,
    )
    def get_compensation_prices(
        self, cursor, uid, geo_zone, first_date, last_date, context=None
    ):
        prices_obj = self.pool.get('giscedata.next.days.energy.price')

        self.validate_parameters(cursor, uid, geo_zone, first_date, last_date, tariff=None)

        initial_time, final_time = self.initial_final_times(first_date, last_date)
        params = [
            ('hour_timestamp', '>=', initial_time),
            ('hour_timestamp', '<=', final_time),
            ('geom_zone', '=', geo_zone)
        ]
        price_ids = prices_obj.search(cursor, uid, params, order='hour_timestamp')

        curves = []
        for price_id in price_ids:
            curves.append(prices_obj.read(cursor, uid, price_id, ['prm_diari', 'maturity']))

        json_prices = json.dumps(dict(
            first_date=first_date,
            last_date=last_date,
            curves=dict(
                geo_zone=geo_zone,
                compensation_euros_kwh=[curve.get('prm_diari') for curve in curves],
                maturity=[curve.get('maturity') for curve in curves]
            ))
        )

        return json_prices


SomIndexadaWebformsHelpers()
