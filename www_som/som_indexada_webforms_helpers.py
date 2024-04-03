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

    def _get_prices(self, cursor, geom_zone, tariff_id, first_timestamp_utc, last_timestamp_utc):
        """
        SQL query breakdown:

            1. Common Table Expressions (CTEs):
                * `filtered_data`: Filters data from `giscedata_next_days_energy_price`
                   based on specified criteria
                  (geom_zone, tarifa_id if asked, first_timestamp_utc, and last_timestamp_utc).
                * `filled_data`: Generates a series of timestamps between `first_timestamp_utc`
                  and `last_timestamp_utc`, and fills in NULL values for `geom_zone`, `maturity`,
                  `tarifa_id`, `initial_price` and `prm_diari` where there are gaps in data.
                * `final_data`: Joins the filtered and filled data, ensuring no gaps exist.
                * `ranked_data`: Assigns a rank to each record based on the maturity level.

            2. Main Query:
                * Selects aggregated data as a JSON object.
                * Aggregates data by `timestamp`.
                * Includes the following information in the JSON object:
                    * `geo_zone`: `PENINSULA', `CANARIAS` or `BALEARES'.
                    * `tariff_id`: tariff id.
                    * `first_timestamp_utc`: Start timestamp parameter.
                    * `last_timestamp_utc`: End timestamp parameter.
                    * `initial_price`: Array of actual initial_price, ordered by timestamp.
                    * `prm_diari`: Array of actual prm_diari, ordered by timestamp.
                    * `maturity`: Array of maturity levels, ordered by timestamp.

            3. Final Filtering:
                * Filters the results to only include records where qwith the highest
                  create_date for each timestamp.

        """
        cursor.execute(
            '''
                WITH filtered_data AS (
                    SELECT
                        hour_timestamp AT TIME ZONE 'UTC' AS hour_timestamp,
                        geom_zone,
                        tarifa_id,
                        initial_price,
                        prm_diari,
                        maturity,
                        create_date
                    FROM
                        giscedata_next_days_energy_price
                    WHERE
                        geom_zone = %(geom_zone)s
                        AND (%(tariff_id)s IS NULL OR tarifa_id = %(tariff_id)s)
                        AND hour_timestamp AT TIME ZONE 'UTC'
                        BETWEEN %(first_timestamp_utc)s AND %(last_timestamp_utc)s
                ),
                filled_data AS (
                    SELECT
                        generate_series AS hour_timestamp,
                        NULL AS geom_zone,
                        NULL AS tarifa_id,
                        NULL AS initial_price,
                        NULL AS prm_diari,
                        NULL AS maturity
                    FROM
                        generate_series(
                            %(first_timestamp_utc)s,
                            %(last_timestamp_utc)s,
                            INTERVAL '1 HOUR'
                        ) generate_series
                    LEFT JOIN
                        filtered_data fd ON generate_series.generate_series = fd.hour_timestamp
                    WHERE
                        fd.hour_timestamp IS NULL
                ),
                final_data AS (
                    SELECT
                        COALESCE(fd.hour_timestamp, fd2.hour_timestamp) AS hour_timestamp,
                        COALESCE(fd.geom_zone, NULL) AS geom_zone,
                        COALESCE(fd.tarifa_id, NULL) AS tarifa_id,
                        COALESCE(fd.initial_price, NULL) AS initial_price,
                        COALESCE(fd.prm_diari, NULL) AS prm_diari,
                        COALESCE(fd.maturity, fd2.maturity) AS maturity,
                        create_date
                    FROM
                        filtered_data fd
                    FULL JOIN
                        filled_data fd2 ON fd.hour_timestamp = fd2.hour_timestamp
                ),
                collapsed_data AS (
                    SELECT DISTINCT ON(hour_timestamp)
                        *
                    FROM
                        final_data
                    ORDER BY hour_timestamp ASC, create_date DESC
                )
                SELECT
                    JSON_BUILD_OBJECT(
                        'first_date', %(first_timestamp_utc)s,
                        'last_date', %(last_timestamp_utc)s,
                        'geo_zone', %(geom_zone)s,
                        'tariff_id', %(tariff_id)s,
                        'price_euros_kwh', COALESCE(ARRAY_AGG(initial_price
                                                    ORDER BY hour_timestamp ASC),
                                                    ARRAY[]::numeric[]),
                        'compensation_euros_kwh', COALESCE(ARRAY_AGG(prm_diari
                                                           ORDER BY hour_timestamp ASC),
                                                           ARRAY[]::numeric[]),
                        'maturity', COALESCE(ARRAY_AGG(maturity
                                             ORDER BY hour_timestamp ASC), ARRAY[]::text[])
                    ) AS data
                FROM
                    collapsed_data
            ''',
            {
                'geom_zone': geom_zone,
                'tariff_id': tariff_id,
                'first_timestamp_utc': first_timestamp_utc,
                'last_timestamp_utc': last_timestamp_utc
            }
        )

        return cursor.fetchall()

    @www_entry_point(
        expected_exceptions=exceptions.SomPolissaException,
    )
    def get_indexed_prices(
        self, cursor, uid, geo_zone, tariff, first_date, last_date, context=None
    ):
        self.validate_parameters(cursor, uid, geo_zone, first_date, last_date, tariff)

        tariff_obj = self.pool.get('giscedata.polissa.tarifa')

        tariff_id = tariff_obj.search(cursor, uid, [('name', '=', tariff)])

        initial_time, final_time = self.initial_final_times(first_date, last_date)

        curves_data = self._get_prices(
            cursor, geo_zone, tariff_id[0], initial_time, final_time)[0][0]

        keys_to_return = ['first_date', 'last_date',
                          'geo_zone', 'price_euros_kwh', 'maturity']

        filtered_data = {k: v for k, v in curves_data.items() if k in keys_to_return}

        json_prices = json.dumps(dict(
            first_date=filtered_data['first_date'],
            last_date=filtered_data['last_date'],
            curves=dict(
                tariff=tariff,
                geo_zone=filtered_data['geo_zone'],
                price_euros_kwh=filtered_data['price_euros_kwh'],
                maturity=filtered_data['maturity']
            ))
        )

        return json_prices

    @www_entry_point(
        expected_exceptions=exceptions.SomPolissaException,
    )
    def get_compensation_prices(
        self, cursor, uid, geo_zone, first_date, last_date, context=None
    ):
        self.validate_parameters(cursor, uid, geo_zone, first_date, last_date, tariff=None)

        initial_time, final_time = self.initial_final_times(first_date, last_date)

        curves_data = self._get_prices(cursor, geo_zone, None, initial_time, final_time)[0][0]

        keys_to_return = ['first_date', 'last_date',
                          'geo_zone', 'compensation_euros_kwh', 'maturity']

        filtered_data = {k: v for k, v in curves_data.items() if k in keys_to_return}

        json_prices = json.dumps(dict(
            first_date=filtered_data['first_date'],
            last_date=filtered_data['last_date'],
            curves=dict(
                geo_zone=filtered_data['geo_zone'],
                compensation_euros_kwh=filtered_data['compensation_euros_kwh'],
                maturity=filtered_data['maturity']
            ))
        )

        return json_prices


SomIndexadaWebformsHelpers()
