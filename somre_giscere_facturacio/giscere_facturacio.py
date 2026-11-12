# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .tarifes import TARIFES
from datetime import datetime, timedelta
from giscere_facturacio.defs import ISP15_start_date
from osv import osv
from pytz import timezone, utc
import pandas as pd
import numpy as np

from tools.translate import _


TIMEZONE = timezone('Europe/Madrid')

REGANECU_LIQUIDACIO = {'H2': 'C2',
                       'H3': 'C3',
                       'HP': 'C4',
                       'HC': 'C5'}


class GiscereFacturacioFacturador(osv.osv):

    _name = 'giscere.facturacio.facturador'
    _inherit = 'giscere.facturacio.facturador'

    def get_tarifa_class(self, modcontractual):
        return TARIFES['Representa']

    # Sobreescribim la funció per a calcular els desviaments i l'apantallament de forma personalitzada  # noqa: E501
    def obtenir_desviaments(self, cursor, uid, cil_id, datetime_inici, datetime_fi, maduresa, context=None):  # noqa: E501
        """
        Overwrites function to use REGANECU instead of Market Offers to calculate System Bias
        :param cursor: OpenERP DB Cursor
        :param uid: OpenERP User ID
        :param cil_id: cil ID
        :param datetime_inici: str (e.g. '2024-01-01 01:00:00')
        :param datetime_fi: str (e.g. '2024-02-01 00:00:00')
        :param maduresa: str (e.g. 'C2')
        :param context: OpenERP Current Context
        :return: dict
        """
        if context is None:
            context = {}

        # Individual bias for single CIL  [kWh]
        desviaments_instalacio = self.obtenir_desviaments_instalacions(
            cursor, uid, datetime_inici, datetime_fi, maduresa, cil_id, context=context
        )

        # dsv_rep_brut
        # Individual bias for all CIL  [kWh]
        dsv_rep_brut = self.obtenir_desviaments_instalacions(
            cursor, uid, datetime_inici, datetime_fi, maduresa, cil_id=False, context=context
        )

        # dsv_rep_net
        # System bias between MHCIL and OFFERS  [kWh]
        # Context is None to allow CACHE in function
        previsio_sistema = self.obtenir_previsio_sistema(
            cursor, uid, datetime_inici, datetime_fi, context=None)  # [MWh]

        # Context is None to allow CACHE in function
        generacio = self.obtenir_generacio_sistema(
            cursor, uid, datetime_inici, datetime_fi, maduresa, context=None)  # [MWh]
        dsv_rep_net = self.obtenir_desviament_sistema(
            generacio, previsio_sistema, context=context)  # [kWh]

        # dsv_brp
        # Calc system bias from REGANECU  [kWh]
        dsv_brp = self.obtenir_desviament_sistema_reganecu(cursor, uid,
                                                           datetime_inici, datetime_fi, maduresa,
                                                           context=context)

        # dsv_com_net
        # dsv_com_net = dsv_brp - dsv_rep_net
        dsv_com_net = dsv_brp.copy()
        dsv_com_net = dsv_com_net.rename(columns={'value': 'value_dsv_brp'})
        dsv_com_net = dsv_com_net.merge(dsv_rep_net, on=['local_timestamp', 'timestamp'])
        dsv_com_net = dsv_com_net.rename(columns={'value': 'value_dsv_rep'})
        dsv_com_net['value'] = dsv_com_net['value_dsv_brp'] - dsv_com_net['value_dsv_rep']
        dsv_com_net['subir'] = np.where(dsv_com_net['value'] > 0,
                                        dsv_com_net['value'],
                                        0)
        dsv_com_net['bajar'] = np.where(dsv_com_net['value'] < 0,
                                        dsv_com_net['value'].abs(),
                                        0)
        fields_to_keep = ['local_timestamp', 'timestamp', 'value', 'subir', 'bajar']
        dsv_com_net = dsv_com_net[fields_to_keep]

        res = {
            'desviaments_sistema': dsv_brp,
            'desviaments_instalacio': desviaments_instalacio,
            'desviaments_instalacions': dsv_rep_brut,
            'previsio_sistema': previsio_sistema,
            'desviaments_representacio_net': dsv_rep_net,
            'desviaments_comercialitzadora_net': dsv_com_net,
            'generacio_sistema': generacio
        }

        return res

    def obtenir_desviament_sistema_reganecu(self, cursor, uid, datetime_inici, datetime_fi, maduresa, context=None):  # noqa: E501
        """
        Calculates and returns SYSTEM BIAS from REGANECU
        :param cursor: OpenERP DB Cursor
        :param uid: OpenERP User ID
        :@param datetime_inici: str (e.g. '2024-01-01 01:00:00')
        :@param datetime_fi: str (e.g. '2024-02-01 00:00:00')
        :param maduresa: str (e.g. 'H2')
        :param context: OpenERP Current Context
        :return: dataframe
        """
        if context is None:
            context = {}

        reganecu_o = self.pool.get('giscere.reganecu')

        use_newest_reganecu = context.get('use_newest_reganecu', False)

        type_integrity = 'p4' if datetime_inici[:10] >= ISP15_start_date else 'p'

        if type_integrity == 'p4':
            datetime_inici = '{} 00:15:00'.format(datetime_inici[:10])

        start_dt = TIMEZONE.localize(datetime.strptime(datetime_inici, '%Y-%m-%d %H:%M:%S'))
        end_dt = TIMEZONE.localize(datetime.strptime(datetime_fi, '%Y-%m-%d %H:%M:%S'))
        if type_integrity == 'p':
            num_hours = int((end_dt - start_dt).total_seconds() / 3600) + 1
            minutes_step = 60
        else:
            num_hours = int((end_dt - start_dt).total_seconds() / 3600 * 4) + 1
            minutes_step = 15

        # Get reganecu
        search_vals = [
            ("local_timestamp", ">=", datetime_inici),
            ("local_timestamp", "<=", datetime_fi),
            ("segmento", "=", "DSV"),
            ("type", "=", type_integrity)
        ]
        maturity = 'qualsevol'

        # Patch maturity according to liquidacio
        if not use_newest_reganecu:
            maturity = REGANECU_LIQUIDACIO[maduresa]
            search_vals += [("maturity", "=", maturity)]

        reganecu_ids = reganecu_o.search(cursor, uid, search_vals, context=context)

        if len(reganecu_ids) == 0:
            raise osv.except_osv(_('Error'),
                                 _("No s'han trobat registres de segment DSV entre {} i {} amb versió {} al REGANECU.").format(  # noqa: E501
                                     datetime_inici, datetime_fi, maturity)
                                 )

        if use_newest_reganecu:
            # use max maturity
            max_maturity = max([x['maturity']
                               for x in reganecu_o.read(cursor, uid, reganecu_ids, ['maturity'])])
            search_vals += [("maturity", "=", max_maturity)]
            reganecu_ids = reganecu_o.search(cursor, uid, search_vals, context=context)

        read_fields = ['timestamp', 'local_timestamp', 'energia', 'precio', 'importe',
                       'signo_importe', 'signo_magnitud', 'codigo_magnitud', 'maturity']
        reganecu = reganecu_o.read(cursor, uid, reganecu_ids, read_fields, context=context)

        df = pd.DataFrame(data=reganecu)
        df['energia_amb_signe'] = df['energia'].astype(float) * df['signo_magnitud'].astype(int)
        df['energia_amb_signe'] = df['energia_amb_signe'] * 1000.0  # from MWh to kWh

        df = df.groupby(
            ['timestamp', 'local_timestamp']
        ).aggregate(
            {'energia_amb_signe': 'sum'}
        ).reset_index()

        df = df.rename(columns={"energia_amb_signe": "value"})
        df['subir'] = np.where(df['value'] > 0,
                               df['value'],
                               0)
        df['bajar'] = np.where(df['value'] < 0,
                               df['value'].abs(),
                               0)

        reganecu_filtered = df.to_dict('records')

        # fill DSV gaps
        if len(reganecu_filtered) < num_hours:
            # fill gaps with 0
            expected_hours = []
            temp_dt = start_dt.astimezone(utc)
            while temp_dt <= end_dt.astimezone(utc):
                expected_hours.append(temp_dt.strftime('%Y-%m-%d %H:%M:%S'))
                temp_dt += timedelta(minutes=minutes_step)

            found_hours = list(set([x['timestamp'] for x in reganecu_filtered]))
            gap_hours = list(set(expected_hours) - set(found_hours))
            for gap in gap_hours:
                gap_filler = {
                    'value': 0,
                    'subir': 0,
                    'bajar': 0,
                    'timestamp': gap,
                    'codigo_magnitud': '-',
                    'maturity': '-',
                    'local_timestamp': TIMEZONE.normalize(
                        utc.localize(datetime.strptime(
                            gap, '%Y-%m-%d %H:%M:%S')).astimezone(TIMEZONE)
                    ).strftime('%Y-%m-%d %H:%M:%S')
                }
                reganecu_filtered.append(gap_filler)

        df = pd.DataFrame(data=reganecu_filtered)

        return df


GiscereFacturacioFacturador()
