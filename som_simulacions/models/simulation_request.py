# -*- coding: utf-8 -*-
from osv import osv, fields
from decimal import Decimal, ROUND_HALF_UP


class SomSimulacioRequest(osv.osv):
    _name = 'som.simulacio.request'
    _description = 'Indexed estimate simulation request'

    _columns = {
        'name': fields.char('Reference', size=64, required=True),
        'year': fields.integer('Year', required=True),
        'month': fields.integer('Month', required=True),
        'tariff_code': fields.char('Tariff code', size=16, required=True),
        'power_p1': fields.float('Power P1', digits=(16, 6)),
        'power_p2': fields.float('Power P2', digits=(16, 6)),
        'power_p3': fields.float('Power P3', digits=(16, 6)),
        'result_ids': fields.one2many('som.simulacio.result', 'request_id', 'Results'),
    }

    _CSV_ANNUAL_KWH_BY_POWER = {
        1: 2500,
        2: 2750,
        3: 3000,
        4: 3250,
        5: 3500,
        6: 3750,
        7: 4000,
        8: 4250,
        9: 4500,
        10: 4750,
        11: 5000,
        12: 5250,
        13: 5500,
        14: 5750,
        15: 6000,
        20: 8000,
        25: 10000,
        30: 12000,
        35: 15000,
        40: 19000,
        45: 22000,
        50: 26000,
        60: 30000,
        70: 35000,
        80: 40000,
        90: 45000,
        100: 50000,
    }

    def _round_2(self, value):
        return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    def _round_0(self, value):
        return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    def _get_annual_kwh_from_csv(self, max_power):
        power_key = int(round(max_power))
        if power_key not in self._CSV_ANNUAL_KWH_BY_POWER:
            raise osv.except_osv(
                'Missing data',
                'Pot Cont MAX %s not defined in CSV lookup table.' % power_key
            )
        return float(self._CSV_ANNUAL_KWH_BY_POWER[power_key])

    def _get_power_price_total(self, power_price, powers):
        components = power_price.get('components') or {}
        if components:
            p1_price = components.get('p1') or 0.0
            p2_price = components.get('p2') or 0.0
            return ((powers[0][1] * p1_price) + (powers[1][1] * p2_price)) / 12.0
        return power_price.get('value') or 0.0

    def _get_request_powers(self, request_data):
        return [
            ('P1', request_data.get('power_p1') or 0.0),
            ('P2', request_data.get('power_p2') or 0.0),
            ('P3', request_data.get('power_p3') or 0.0),
        ]

    def _validate_request_input(self, request):
        tariff_code = (request.get('tariff_code') or '').strip()
        if not tariff_code:
            raise osv.except_osv('Validation error', 'Tariff context is required.')

        powers = self._get_request_powers(request)
        for period, value in powers:
            if value < 0.0:
                raise osv.except_osv(
                    'Validation error',
                    'Power %s must be non-negative.' % period
                )

        # if not [value for _period, value in powers if value > 0.0]:
        #     raise osv.except_osv(
        #         'Validation error',
        #         'At least one period power must be greater than zero.'
        #     )

        return tariff_code, powers

    def _validate_coverage(
        self, cr, uid, request, tariff_code, powers, coeff_obj, price_obj, context=None
    ):
        coeff_ids = coeff_obj.search(cr, uid, [
            ('tariff_code', '=', tariff_code),
        ], context=context)
        if not coeff_ids:
            raise osv.except_osv(
                'Missing data',
                'Annual coefficients missing for tariff %s.'
                % (tariff_code)
            )

        coeff_rows = coeff_obj.read(
            cr, uid, coeff_ids, ['id', 'period', 'ratio'], context=context)
        # coeff_periods = [row.get('period') for row in coeff_rows]
        # required_periods = [period for period, value in powers if value > 0.0]
        # for period in required_periods:
        #     if period not in coeff_periods:
        #         raise osv.except_osv(
        #             'Missing data',
        #             'Annual coefficient missing for period %s.' % period
        #         )

        # for period in coeff_periods:
        # price_ids = price_obj.search(cr, uid, [
        #     ('year', '=', request['year']),
        #     ('month', '=', request['month']),
        #     ('period', '=', period),
        #     ('tariff_code', '=', tariff_code),
        # ], context=context)
        # if not price_ids:
        #     raise osv.except_osv(
        #         'Missing data',
        #         'Monthly energy price missing for %s' % period
        #     )

        return coeff_rows

    def compute_indexed_estimate(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        # result_obj = self.pool.get('som.simulacio.result')
        # line_obj = self.pool.get('som.simulacio.result.line')
        coeff_obj = self.pool.get('som.simulacio.annual.coeff')
        price_obj = self.pool.get('som.simulacio.energy.price.monthly')
        adapter = self.pool.get('som.simulacio.erp.adapter')

        # created_result_ids = []
        for request in self.read(cr, uid, ids, context=context):
            tariff_code, powers = self._validate_request_input(request)
            when_date = '%04d-%02d-01' % (request['year'], request['month'])

            power_price = adapter.get_power_price(
                cr, uid, when_date, tariff_code=tariff_code, context=context
            )
            social_bonus = adapter.get_social_bonus(
                cr, uid, when_date, tariff_code=tariff_code, context=context
            )
            meter_charge = adapter.get_meter_charge(
                cr, uid, when_date, tariff_code=tariff_code, context=context
            )

            coeff_rows = self._validate_coverage(
                cr,
                uid,
                request,
                tariff_code,
                powers,
                coeff_obj,
                price_obj,
                context=context,
            )

            prices_by_period = {}
            selected_energy_price_id = False
            for coeff_row in coeff_rows:
                price_ids = price_obj.search(cr, uid, [
                    ('year', '=', request['year']),
                    ('month', '=', request['month']),
                    ('period', '=', coeff_row['period']),
                    ('tariff_code', '=', tariff_code),
                ], context=context)
                # if not price_ids:
                #     raise osv.except_osv(
                #         'Missing data',
                #         'Monthly energy price missing for %s' % coeff_row['period']
                #     )
                price_row = price_obj.read(cr, uid, price_ids[0], ['id', 'price'], context=context)
                prices_by_period[coeff_row['period']] = price_row['price']
                if not selected_energy_price_id:
                    selected_energy_price_id = price_row['id']

            max_power = max([power for _period, power in powers])
            annual_kwh = self._get_annual_kwh_from_csv(max_power)
            monthly_kwh_exact = annual_kwh / 12.0
            # monthly_kwh = self._round_2(monthly_kwh_exact)

            variable_total = 0.0
            period_kwh_map = {}
            period_kwh_exact_map = {}
            for coeff_row in coeff_rows:
                period = coeff_row['period']
                period_kwh_exact = monthly_kwh_exact * (coeff_row['ratio'] or 0.0)
                period_kwh = self._round_0(period_kwh_exact)
                period_kwh_map[period] = period_kwh
                period_kwh_exact_map[period] = period_kwh_exact
                period_energy = period_kwh_exact * prices_by_period[period]
                variable_total += period_energy

            fixed_total = (
                self._get_power_price_total(power_price, powers)
                + (social_bonus.get('value') or 0.0)
                + (meter_charge.get('value') or 0.0)
            )
            untaxed_total = self._round_2(fixed_total + variable_total)

            # fallback_flags = {
            #     'power_price': power_price.get('fallback_used'),
            #     'social_bonus': social_bonus.get('fallback_used'),
            #     'meter_charge': meter_charge.get('fallback_used'),
            # }
            # traceability_payload = {
            #     'tariff_code': tariff_code,
            #     'powers': powers,
            #     'concept_sources': {
            #         'power_price': power_price.get('source'),
            #         'social_bonus': social_bonus.get('source'),
            #         'meter_charge': meter_charge.get('source'),
            #     },
            #     'annual_kwh': annual_kwh,
            #     'monthly_kwh': monthly_kwh,
            #     'period_kwh': period_kwh_map,
            #     'period_kwh_exact': period_kwh_exact_map,
            #     'coeff_ids': [row['id'] for row in coeff_rows],
            # }

            # result_id = result_obj.create(cr, uid, {
            #     'name': request.get('name'),
            #     'request_id': request['id'],
            #     'untaxed_total': untaxed_total,
            #     'selected_energy_price_id': selected_energy_price_id,
            #     # 'selected_coeff_set_id': coeff_rows and coeff_rows[0]['id'] or False,
            #     # 'fallback_flags': repr(fallback_flags),
            #     # 'traceability_payload': repr(traceability_payload),
            # }, context=context)

            # line_obj.create(cr, uid, {
            #     'result_id': result_id,
            #     'concept': 'power_price',
            #     'amount': power_price_total,
            #     'source_record': '%s:%s' % (
            #         power_price.get('source'), power_price.get('record_id')
            #     ),
            # }, context=context)
            # line_obj.create(cr, uid, {
            #     'result_id': result_id,
            #     'concept': 'social_bonus',
            #     'amount': social_bonus.get('value') or 0.0,
            #     'source_record': '%s:%s' % (
            #         social_bonus.get('source'), social_bonus.get('record_id')
            #     ),
            # }, context=context)
            # line_obj.create(cr, uid, {
            #     'result_id': result_id,
            #     'concept': 'meter_charge',
            #     'amount': meter_charge.get('value') or 0.0,
            #     'source_record': '%s:%s' % (
            #         meter_charge.get('source'), meter_charge.get('record_id')
            #     ),
            # }, context=context)

            # for coeff_row in coeff_rows:
            #     period = coeff_row['period']
            #     period_energy = self._round_2(period_kwh_exact_map[period] *
            #       prices_by_period[period])
            #     line_obj.create(cr, uid, {
            #         'result_id': result_id,
            #         'concept': 'energy',
            #         'period': period,
            #         'amount': period_energy,
            #         'source_record': 'monthly_price:%s' % period,
            #     }, context=context)

            # created_result_ids.append(result_id)

        return untaxed_total


SomSimulacioRequest()
