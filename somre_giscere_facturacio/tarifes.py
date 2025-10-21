# -*- coding: utf-8 -*-
from __future__ import absolute_import
from libfacturacioatr.pool.generation import (Representa, pd, REEcurve, REEcurveQH,
                                              Codsvbaj, Codsvbaqh, Component, ComponentQH,
                                              Codsvsub, Codsvsuqh)
import numpy as np


class RepresentaSom(Representa):

    def get_available_audit_coefs_all(self):
        """
        Afegim dos adjunts nous: desviament de la comercialitzadora i desviament de representació
        :return: dict
        """
        res = super(RepresentaSom, self).get_available_audit_coefs_all()
        res.update({'desvio_com': 'desvio_com',
                    'desvio_rep': 'desvio_rep',
                    'desvio_bruto_subir': 'desvio_bruto_subir',
                    'desvio_bruto_bajar': 'desvio_bruto_bajar'})
        return res

    def get_available_audit_coefs_desvios(self):
        '''
        Afegim dos adjunts nous al càlcul de desviaments
        :return: dict
        '''
        desired_audit_components = ('desvios_bajar', 'desvios_subir',
                                    'desvio_bruto_subir', 'desvio_bruto_bajar',
                                    'desvio_com', 'desvio_rep')
        return dict([x for x in self.get_available_audit_coefs_all().items()
                     if x[0] in desired_audit_components])

    # Desviaments
    def factura_desviaments(self):
        is_isp15 = self.conf.get('ISP15', False)

        desv_instalacio = self.corbes.get('desviament_instalacio', [])
        desv_sistema_per_hora = self.corbes.get('desviaments_sistema_per_hora', [])  # UoF

        desviaments_df = pd.DataFrame(data=desv_instalacio)
        desviaments_df.rename(columns={'value': 'desviament_instalacio'}, inplace=True)  # KWh

        desv_instalacions = self.corbes.get('desviament_instalacions', [])
        desviaments_instalacions_df = pd.DataFrame(data=desv_instalacions)
        desviaments_instalacions_df.rename(columns={'value': 'desviament_instalacions',
                                                    'subir': 'desviament_subir_instalacions',
                                                    'bajar': 'desviament_bajar_instalacions'},
                                           inplace=True)  # KWh
        desviaments_instalacions_df = desviaments_instalacions_df.groupby([
            'local_timestamp',
            'timestamp'
        ]).agg({
            'desviament_instalacions': 'sum',
            'desviament_subir_instalacions': 'sum',
            'desviament_bajar_instalacions': 'sum',
        }).reset_index()

        desv_instalacions_actual = self.corbes.get('desviament_instalacions_actual', [])
        if len(desv_instalacions_actual):
            desviaments_instalacions_actual_df = pd.DataFrame(data=desv_instalacions_actual)
            desviaments_instalacions_actual_df.rename(
                columns={'value': 'desviament_instalacions_actual',
                         'subir': 'desviament_subir_instalacions_actual',
                         'bajar': 'desviament_bajar_instalacions_actual'},
                inplace=True)  # KWh
            desviaments_instalacions_actual_df = desviaments_instalacions_actual_df.groupby([
                'local_timestamp',
                'timestamp'
            ]).agg({
                'desviament_instalacions_actual': 'sum',
                'desviament_subir_instalacions_actual': 'sum',
                'desviament_bajar_instalacions_actual': 'sum',
            }).reset_index()

        desv_sistema_per_hora.rename(columns={'value': 'desviament_sistema',
                                              'subir': 'desviament_subir_sistema',
                                              'bajar': 'desviament_bajar_sistema'},
                                     inplace=True)  # KWh

        desviaments_representacio_net = self.corbes.get('desviament_representacio_net')
        desviaments_representacio_net_df = pd.DataFrame(data=desviaments_representacio_net)
        desviaments_representacio_net_df = desviaments_representacio_net_df.rename(
            columns={'value': 'value_rep_net',
                     'subir': 'subir_rep_net',
                     'bajar': 'bajar_rep_net'}
        )

        desviaments_comercialitzadora_net = self.corbes.get('desviament_comercialitzadora_net')
        desviaments_comercialitzadora_net_df = pd.DataFrame(data=desviaments_comercialitzadora_net)
        desviaments_comercialitzadora_net_df = desviaments_comercialitzadora_net_df.rename(
            columns={'value': 'value_com_net',
                     'subir': 'subir_com_net',
                     'bajar': 'bajar_com_net'}
        )

        esios_token = self.conf['esios_token']

        if is_isp15:
            desvio_bajar = REEcurveQH('Codsvbaqh', self.data_inici,
                                      self.data_final, esios_token)  # €/MWh
            desvio_subir = REEcurveQH('Codsvsuqh', self.data_inici,
                                      self.data_final, esios_token)  # €/MWh
            desvio_bajar_curve = desvio_bajar.get_curve()
            desvio_subir_curve = desvio_subir.get_curve()
        else:
            desvio_bajar = REEcurve('Codsvbaj', self.data_inici,
                                    self.data_final, esios_token)  # €/MWh
            desvio_subir = REEcurve('Codsvsub', self.data_inici,
                                    self.data_final, esios_token)  # €/MWh
            desvio_bajar_curve = desvio_bajar.get_curve()
            desvio_subir_curve = desvio_subir.get_curve()

        desvio_bajar_df = pd.DataFrame(data=desvio_bajar_curve)
        canvi_noms_columnes = {
            'value': 'preu_desvio_bajar',
            'timestamp': 'local_timestamp',
            'timestamp_utc': 'timestamp',
        }
        desvio_bajar_df.rename(columns=canvi_noms_columnes, inplace=True)

        desvio_subir_df = pd.DataFrame(data=desvio_subir_curve)
        canvi_noms_columnes = {
            'value': 'preu_desvio_subir',
            'timestamp': 'local_timestamp',
            'timestamp_utc': 'timestamp',
        }
        desvio_subir_df.rename(columns=canvi_noms_columnes, inplace=True)

        # passem de €/MWh a €/KWh
        desvio_bajar_df['preu_desvio_bajar'] = desvio_bajar_df['preu_desvio_bajar'] * 0.001
        desvio_subir_df['preu_desvio_subir'] = desvio_subir_df['preu_desvio_subir'] * 0.001

        desviaments_df = desviaments_df.merge(
            desvio_bajar_df, on=['timestamp'], how='left')
        desviaments_df = desviaments_df.merge(
            desvio_subir_df, on=['timestamp'], how='left')
        desviaments_df = desviaments_df.merge(
            desviaments_instalacions_df, on=['timestamp'], how='left')

        desviaments_df = desviaments_df.sort_values(by=['timestamp'])

        desviaments_df['preu_desv_instalacio'] = (
            (desviaments_df['subir'] * desviaments_df['preu_desvio_subir'])
            + (desviaments_df['bajar'] * desviaments_df['preu_desvio_bajar']))

        desviaments_df = desviaments_df.merge(desv_sistema_per_hora, on=['timestamp'], how='left')
        desviaments_df['preu_desv_sistema'] = ((desviaments_df['desviament_subir_sistema']
                                                * desviaments_df['preu_desvio_subir'])
                                               + (desviaments_df['desviament_bajar_sistema']
                                                  * desviaments_df['preu_desvio_bajar']))

        desviaments_df = desviaments_df.merge(
            desviaments_representacio_net_df, on=['timestamp'], how='left')
        desviaments_df = desviaments_df.merge(
            desviaments_comercialitzadora_net_df, on=['timestamp'], how='left')

        # Càlcul de percentatge a ponderar
        # Pesos
        """
        pct_rep_sub =
        (dsv_brp_sub/ (dsv_brp_sub + dsv_brp_baj))*
        (dsv_rep_net_sub/(dsv_rep_net_sub+dsv_rep_net_baj)*
        (dsv_rep_net_sub - dsv_com_net_baj)/(dsv_rep_brut_sub)
        """
        desviaments_df['pct_rep_sub_1'] = np.where(
            (desviaments_df['desviament_subir_sistema']
             + desviaments_df['desviament_bajar_sistema']) > 0,
            desviaments_df['desviament_subir_sistema'] / (
                desviaments_df['desviament_subir_sistema']
                + desviaments_df['desviament_bajar_sistema']),
            0)

        desviaments_df['pct_rep_sub_2'] = np.where(
            (desviaments_df['subir_rep_net']
             + desviaments_df['bajar_rep_net']) > 0,
            desviaments_df['subir_rep_net'] / (
                desviaments_df['subir_rep_net']
                + desviaments_df['bajar_rep_net']),
            0)

        desviaments_df['pct_rep_sub_3'] = np.where(
            desviaments_df['desviament_subir_instalacions'] > 0,
            (desviaments_df['subir_rep_net'] - desviaments_df['bajar_com_net'])
            / desviaments_df['desviament_subir_instalacions'],
            0)

        desviaments_df['pct_rep_sub'] = (desviaments_df['pct_rep_sub_1']
                                         * desviaments_df['pct_rep_sub_2']
                                         * desviaments_df['pct_rep_sub_3'])

        """
        pct_rep_baj = (dsv_brp_baj/ (dsv_brp_sub + dsv_brp_baj))*
        (dsv_rep_net_baj/(dsv_rep_net_sub+dsv_rep_net_baj)*
        (dsv_rep_net_baj - dsv_com_net_sub)/(dsv_rep_brut_baj)
        """
        desviaments_df['pct_rep_baj_1'] = np.where(
            (desviaments_df['desviament_subir_sistema']
             + desviaments_df['desviament_bajar_sistema']) > 0,
            desviaments_df['desviament_bajar_sistema']
            / (desviaments_df['desviament_subir_sistema']
               + desviaments_df['desviament_bajar_sistema']),
            0)
        desviaments_df['pct_rep_baj_2'] = np.where(
            (desviaments_df['subir_rep_net']
             + desviaments_df['bajar_rep_net']) > 0,
            desviaments_df['bajar_rep_net']
            / (desviaments_df['subir_rep_net']
               + desviaments_df['bajar_rep_net']),
            0)
        desviaments_df['pct_rep_baj_3'] = np.where(
            desviaments_df['desviament_bajar_instalacions'] > 0,
            (desviaments_df['bajar_rep_net']
             - desviaments_df['subir_com_net'])
            / desviaments_df['desviament_bajar_instalacions'],
            0)

        desviaments_df['pct_rep_baj'] = (desviaments_df['pct_rep_baj_1']
                                         * desviaments_df['pct_rep_baj_2']
                                         * desviaments_df['pct_rep_baj_3'])

        # Desviament ponderat segons pes
        desviaments_df['desviament_instalacio_apantallat_subir'] = (
            desviaments_df['pct_rep_sub'] * desviaments_df['subir']
        )
        desviaments_df['desviament_instalacio_apantallat_bajar'] = (
            desviaments_df['pct_rep_baj'] * desviaments_df['bajar']
        )

        # Preu de desviament
        desviaments_df['preu_desviament_apantallat'] = (
            (desviaments_df['desviament_instalacio_apantallat_subir']
             * desviaments_df['preu_desvio_subir'])
            + (desviaments_df['desviament_instalacio_apantallat_bajar']
               * desviaments_df['preu_desvio_bajar'])
        )

        # Preparem adjunts per a auditar
        # Preus DSV
        postfix = ('%s_%s' % (self.data_inici.strftime(
            "%Y%m%d"), self.data_final.strftime("%Y%m%d")))
        if is_isp15:
            csdvbaj = Codsvbaqh('C2_codsvbaqh_%(postfix)s' % locals(), esios_token)  # [€/MWh]
            csdvsub = Codsvsuqh('C2_codsvsuqh_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        else:
            csdvbaj = Codsvbaj('C2_codsvbaj_%(postfix)s' % locals(), esios_token)  # [€/MWh]
            csdvsub = Codsvsub('C2_codsvsub_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        # DSV REP (Brut)
        if len(desv_instalacions_actual):
            desvios_cils = desviaments_instalacions_actual_df.to_dict('records')
            desvios_cils = sorted(desvios_cils, key=lambda d: d['timestamp'])
            if is_isp15:
                desvio_bruto_subir = self.get_componentQH_from_dict_list(
                    desvios_cils, self.data_inici,
                    magn='desviament_subir_instalacions_actual'
                )
                desvio_bruto_bajar = self.get_componentQH_from_dict_list(
                    desvios_cils, self.data_inici, magn='desviament_bajar_instalacions_actual'
                )
            else:
                desvio_bruto_subir = self.get_component_from_dict_list(
                    desvios_cils, self.data_inici, magn='desviament_subir_instalacions_actual'
                )
                desvio_bruto_bajar = self.get_component_from_dict_list(
                    desvios_cils, self.data_inici, magn='desviament_bajar_instalacions_actual'
                )
        else:
            if is_isp15:
                desvio_bruto_subir = ComponentQH(self.data_inici)
                desvio_bruto_bajar = ComponentQH(self.data_inici)
            else:
                desvio_bruto_subir = Component(self.data_inici)
                desvio_bruto_bajar = Component(self.data_inici)

        # DSV REP (Net)
        desvio_rep_list = desviaments_representacio_net_df.to_dict('records')
        if is_isp15:
            desvio_rep = self.get_componentQH_from_dict_list(
                desvio_rep_list, self.data_inici, magn='value_rep_net')
        else:
            desvio_rep = self.get_component_from_dict_list(
                desvio_rep_list, self.data_inici, magn='value_rep_net')

        # DSV COM (Net)
        desvio_com_list = desviaments_comercialitzadora_net_df.to_dict('records')
        if is_isp15:
            desvio_com = self.get_componentQH_from_dict_list(
                desvio_com_list, self.data_inici, magn='value_com_net')
        else:
            desvio_com = self.get_component_from_dict_list(
                desvio_com_list, self.data_inici, magn='value_com_net')

        audit_keys = self.get_available_audit_coefs_desvios()
        for key in self.conf.get('audit', []):
            if key in audit_keys:
                if key not in self.audit_data.keys():
                    self.audit_data[key] = []
                var_name = audit_keys[key]
                com = locals()[var_name]
                if com is None:
                    continue
                self.audit_data[key].extend(
                    com.get_audit_data(start=self.data_inici.day)
                )

        return desviaments_df

    # Banda Secundària
    def factura_banda_secundaria(self):
        is_isp15 = self.conf.get('ISP15', False)

        desv_instalacio = self.corbes.get('desviament_instalacio', [])
        desv_sistema_per_hora = self.corbes.get('desviaments_sistema_per_hora', [])  # UoF
        bs3_curve = self.corbes.get('bs3', [])

        banda_secundaria_df = pd.DataFrame(data=desv_instalacio)
        banda_secundaria_df.rename(columns={'value': 'desviament_instalacio'}, inplace=True)  # KWh

        desv_instalacions = self.corbes.get('desviament_instalacions', [])
        desviaments_instalacions_df = pd.DataFrame(data=desv_instalacions)
        desviaments_instalacions_df.rename(columns={'value': 'desviament_instalacions',
                                                    'subir': 'desviament_subir_instalacions',
                                                    'bajar': 'desviament_bajar_instalacions'},
                                           inplace=True)  # KWh
        desviaments_instalacions_df = desviaments_instalacions_df.groupby([
            'local_timestamp',
            'timestamp'
        ]).agg({
            'desviament_instalacions': 'sum',
            'desviament_subir_instalacions': 'sum',
            'desviament_bajar_instalacions': 'sum',
        }).reset_index()

        banda_secundaria_df.rename(
            columns={'value': 'desviament_instalacio', }, inplace=True)  # KWh
        desv_sistema_per_hora.rename(columns={'value': 'desviament_sistema',
                                              'subir': 'desviament_subir_sistema',
                                              'bajar': 'desviament_bajar_sistema'},
                                     inplace=True)  # KWh
        bs3_curve_df = pd.DataFrame(data=bs3_curve)
        bs3_version = bs3_curve_df.maturity.max()

        desviaments_representacio_net = self.corbes.get('desviament_representacio_net')
        desviaments_representacio_net_df = pd.DataFrame(data=desviaments_representacio_net)
        desviaments_representacio_net_df = desviaments_representacio_net_df.rename(
            columns={'value': 'value_rep_net',
                     'subir': 'subir_rep_net',
                     'bajar': 'bajar_rep_net'}
        )

        desviaments_comercialitzadora_net = self.corbes.get('desviament_comercialitzadora_net')
        desviaments_comercialitzadora_net_df = pd.DataFrame(data=desviaments_comercialitzadora_net)
        desviaments_comercialitzadora_net_df = desviaments_comercialitzadora_net_df.rename(
            columns={'value': 'value_com_net',
                     'subir': 'subir_com_net',
                     'bajar': 'bajar_com_net'}
        )

        # passem de €/MWh a €/KWh
        bs3_curve_df['preu_bs3'] = bs3_curve_df['precio'] * 0.001

        banda_secundaria_df = banda_secundaria_df.merge(bs3_curve_df, on=['timestamp'], how='left')

        banda_secundaria_df = banda_secundaria_df.merge(desviaments_instalacions_df,
                                                        on=['timestamp'],
                                                        how='left')

        banda_secundaria_df = banda_secundaria_df.sort_values(by=['timestamp'])

        banda_secundaria_df['preu_bs3_instalacio'] = (
            (banda_secundaria_df['subir']
             + banda_secundaria_df['bajar'])
            * banda_secundaria_df['preu_bs3']
        )

        banda_secundaria_df = banda_secundaria_df.merge(
            desv_sistema_per_hora, on=['timestamp'], how='left')
        banda_secundaria_df['preu_bs3_sistema'] = (
            (banda_secundaria_df['desviament_subir_sistema']
             + banda_secundaria_df['desviament_subir_sistema'])
            * banda_secundaria_df['preu_bs3']
        )

        banda_secundaria_df = banda_secundaria_df.merge(
            desviaments_representacio_net_df, on=['timestamp'], how='left')
        banda_secundaria_df = banda_secundaria_df.merge(
            desviaments_comercialitzadora_net_df, on=['timestamp'], how='left')

        # Càlcul de percentatge a ponderar
        # Pesos
        """
        pct_rep_sub =
        (dsv_brp_sub/ (dsv_brp_sub + dsv_brp_baj))*
        (dsv_rep_net_sub/(dsv_rep_net_sub+dsv_rep_net_baj)*
        (dsv_rep_net_sub - dsv_com_net_baj)/(dsv_rep_brut_sub)
        """
        banda_secundaria_df['pct_rep_sub_1'] = np.where(
            (banda_secundaria_df['desviament_subir_sistema']
             + banda_secundaria_df['desviament_bajar_sistema']) > 0,
            banda_secundaria_df['desviament_subir_sistema']
            / (banda_secundaria_df['desviament_subir_sistema']
               + banda_secundaria_df['desviament_bajar_sistema']),
            0)

        banda_secundaria_df['pct_rep_sub_2'] = np.where(
            (banda_secundaria_df['subir_rep_net']
             + banda_secundaria_df['bajar_rep_net']) > 0,
            banda_secundaria_df['subir_rep_net']
            / (banda_secundaria_df['subir_rep_net']
               + banda_secundaria_df['bajar_rep_net']),
            0)

        banda_secundaria_df['pct_rep_sub_3'] = np.where(
            banda_secundaria_df['desviament_subir_instalacions'] > 0,
            (banda_secundaria_df['subir_rep_net']
             - banda_secundaria_df['bajar_com_net'])
            / banda_secundaria_df['desviament_subir_instalacions'],
            0)

        banda_secundaria_df['pct_rep_sub'] = (banda_secundaria_df['pct_rep_sub_1']
                                              * banda_secundaria_df['pct_rep_sub_2']
                                              * banda_secundaria_df['pct_rep_sub_3'])

        """
        pct_rep_baj = (dsv_brp_baj/ (dsv_brp_sub + dsv_brp_baj))*
        (dsv_rep_net_baj/(dsv_rep_net_sub+dsv_rep_net_baj)*
        (dsv_rep_net_baj - dsv_com_net_sub)/(dsv_rep_brut_baj)
        """
        banda_secundaria_df['pct_rep_baj_1'] = np.where(
            (banda_secundaria_df['desviament_subir_sistema']
             + banda_secundaria_df['desviament_bajar_sistema']) > 0,
            banda_secundaria_df['desviament_bajar_sistema']
            / (banda_secundaria_df['desviament_subir_sistema']
               + banda_secundaria_df['desviament_bajar_sistema']),
            0)

        banda_secundaria_df['pct_rep_baj_2'] = np.where(
            (banda_secundaria_df['subir_rep_net']
             + banda_secundaria_df['bajar_rep_net']) > 0,
            banda_secundaria_df['bajar_rep_net']
            / (banda_secundaria_df['subir_rep_net']
               + banda_secundaria_df['bajar_rep_net']),
            0)

        banda_secundaria_df['pct_rep_baj_3'] = np.where(
            banda_secundaria_df['desviament_bajar_instalacions'] > 0,
            (banda_secundaria_df['bajar_rep_net']
             - banda_secundaria_df['subir_com_net'])
            / banda_secundaria_df['desviament_bajar_instalacions'],
            0)

        banda_secundaria_df['pct_rep_baj'] = (banda_secundaria_df['pct_rep_baj_1']
                                              * banda_secundaria_df['pct_rep_baj_2']
                                              * banda_secundaria_df['pct_rep_baj_3'])

        # Desviament ponderat segons pes
        banda_secundaria_df['desviament_instalacio_apantallat_subir'] = (
            banda_secundaria_df['pct_rep_sub'] * banda_secundaria_df['subir'])

        banda_secundaria_df['desviament_instalacio_apantallat_bajar'] = (
            banda_secundaria_df['pct_rep_baj'] * banda_secundaria_df['bajar'])

        banda_secundaria_df['preu_bs3_apantallat'] = (
            (banda_secundaria_df['desviament_instalacio_apantallat_subir']
             + banda_secundaria_df['desviament_instalacio_apantallat_bajar'])
            * banda_secundaria_df['preu_bs3'])

        if is_isp15:
            bs3 = ComponentQH(self.data_inici)
            if len(bs3_curve):
                bs3_curve = sorted(bs3_curve, key=lambda d: d['timestamp'])
                bs3 = self.get_componentQH_from_dict_list(
                    bs3_curve, self.data_inici, version=bs3_version, magn='precio')
        else:
            bs3 = Component(self.data_inici)
            if len(bs3_curve):
                bs3_curve = sorted(bs3_curve, key=lambda d: d['timestamp'])
                bs3 = self.get_component_from_dict_list(
                    bs3_curve, self.data_inici, version=bs3_version, magn='precio')

        audit_keys = self.get_available_audit_coefs_banda_secundaria()
        for key in self.conf.get('audit', []):
            if key in audit_keys:
                if key not in self.audit_data.keys():
                    self.audit_data[key] = []
                var_name = audit_keys[key]
                com = locals()[var_name]
                if com is None:
                    continue
                self.audit_data[key].extend(
                    com.get_audit_data(start=self.data_inici.day)
                )

        return banda_secundaria_df

    # SRAD
    def factura_rad3(self):
        is_isp15 = self.conf.get('ISP15', False)

        desv_instalacio = self.corbes.get('desviament_instalacio', [])
        desv_sistema_per_hora = self.corbes.get('desviaments_sistema_per_hora', [])  # UoF
        rad3_curve = self.corbes.get('rad3', [])

        rad3_df = pd.DataFrame(data=desv_instalacio)
        rad3_df.rename(columns={'value': 'desviament_instalacio'}, inplace=True)  # KWh

        desv_instalacions = self.corbes.get('desviament_instalacions', [])
        desviaments_instalacions_df = pd.DataFrame(data=desv_instalacions)
        desviaments_instalacions_df.rename(columns={'value': 'desviament_instalacions',
                                                    'subir': 'desviament_subir_instalacions',
                                                    'bajar': 'desviament_bajar_instalacions'},
                                           inplace=True)  # KWh
        desviaments_instalacions_df = desviaments_instalacions_df.groupby([
            'local_timestamp',
            'timestamp'
        ]).agg({
            'desviament_instalacions': 'sum',
            'desviament_subir_instalacions': 'sum',
            'desviament_bajar_instalacions': 'sum',
        }).reset_index()

        rad3_df.rename(columns={'value': 'desviament_instalacio', }, inplace=True)  # KWh
        desv_sistema_per_hora.rename(columns={'value': 'desviament_sistema',
                                              'subir': 'desviament_subir_sistema',
                                              'bajar': 'desviament_bajar_sistema'},
                                     inplace=True)  # KWh

        desviaments_representacio_net = self.corbes.get('desviament_representacio_net')
        desviaments_representacio_net_df = pd.DataFrame(data=desviaments_representacio_net)
        desviaments_representacio_net_df = desviaments_representacio_net_df.rename(
            columns={'value': 'value_rep_net',
                     'subir': 'subir_rep_net',
                     'bajar': 'bajar_rep_net'}
        )

        desviaments_comercialitzadora_net = self.corbes.get('desviament_comercialitzadora_net')
        desviaments_comercialitzadora_net_df = pd.DataFrame(data=desviaments_comercialitzadora_net)
        desviaments_comercialitzadora_net_df = desviaments_comercialitzadora_net_df.rename(
            columns={'value': 'value_com_net',
                     'subir': 'subir_com_net',
                     'bajar': 'bajar_com_net'}
        )

        rad3_version = None
        if len(rad3_curve):
            rad3_curve_df = pd.DataFrame(data=rad3_curve)
            rad3_version = rad3_curve_df.maturity.max()
            # passem de €/MWh a €/KWh
            rad3_curve_df['preu_rad3'] = rad3_curve_df['precio'] * 0.001
            rad3_df = rad3_df.merge(rad3_curve_df, on=['timestamp'], how='left')
        else:  # Si no tenim rad3 posem el preu a 0 i aixi no es cobrara res
            rad3_df['preu_rad3'] = 0.0

        rad3_df = rad3_df.merge(desviaments_instalacions_df, on=['timestamp'], how='left')

        rad3_df = rad3_df.sort_values(by=['timestamp'])

        rad3_df['preu_rad3_instalacio'] = ((rad3_df['subir'] + rad3_df['bajar'])
                                           * rad3_df['preu_rad3'])

        rad3_df = rad3_df.merge(desv_sistema_per_hora, on=['timestamp'], how='left')
        rad3_df['preu_rad3_sistema'] = (
            (rad3_df['desviament_subir_sistema']
             + rad3_df['desviament_bajar_sistema'])
            * rad3_df['preu_rad3'])

        rad3_df = rad3_df.merge(desviaments_representacio_net_df, on=['timestamp'], how='left')
        rad3_df = rad3_df.merge(desviaments_comercialitzadora_net_df, on=['timestamp'], how='left')

        # Càlcul de percentatge a ponderar
        # Pesos
        """
        pct_rep_sub =
        (dsv_brp_sub/ (dsv_brp_sub + dsv_brp_baj))*
        (dsv_rep_net_sub/(dsv_rep_net_sub+dsv_rep_net_baj)*
        (dsv_rep_net_sub - dsv_com_net_baj)/(dsv_rep_brut_sub)
        """
        rad3_df['pct_rep_sub_1'] = np.where(
            (rad3_df['desviament_subir_sistema']
             + rad3_df['desviament_bajar_sistema']) > 0,
            rad3_df['desviament_subir_sistema']
            / (rad3_df['desviament_subir_sistema']
               + rad3_df['desviament_bajar_sistema']),
            0)

        rad3_df['pct_rep_sub_2'] = np.where(
            (rad3_df['subir_rep_net']
             + rad3_df['bajar_rep_net']) > 0,
            rad3_df['subir_rep_net']
            / (rad3_df['subir_rep_net']
               + rad3_df['bajar_rep_net']),
            0)

        rad3_df['pct_rep_sub_3'] = np.where(
            rad3_df['desviament_subir_instalacions'] > 0,
            (rad3_df['subir_rep_net']
             - rad3_df['bajar_com_net'])
            / rad3_df['desviament_subir_instalacions'],
            0)

        rad3_df['pct_rep_sub'] = (rad3_df['pct_rep_sub_1']
                                  * rad3_df['pct_rep_sub_2']
                                  * rad3_df['pct_rep_sub_3'])

        """
        pct_rep_baj = (dsv_brp_baj/ (dsv_brp_sub + dsv_brp_baj))*
        (dsv_rep_net_baj/(dsv_rep_net_sub+dsv_rep_net_baj)*
        (dsv_rep_net_baj - dsv_com_net_sub)/(dsv_rep_brut_baj)
        """
        rad3_df['pct_rep_baj_1'] = np.where(
            (rad3_df['desviament_subir_sistema']
             + rad3_df['desviament_bajar_sistema']) > 0,
            rad3_df['desviament_bajar_sistema']
            / (rad3_df['desviament_subir_sistema']
               + rad3_df['desviament_bajar_sistema']),
            0)

        rad3_df['pct_rep_baj_2'] = np.where(
            (rad3_df['subir_rep_net']
             + rad3_df['bajar_rep_net']) > 0,
            rad3_df['bajar_rep_net']
            / (rad3_df['subir_rep_net']
               + rad3_df['bajar_rep_net']),
            0)

        rad3_df['pct_rep_baj_3'] = np.where(
            rad3_df['desviament_bajar_instalacions'] > 0,
            (rad3_df['bajar_rep_net']
             - rad3_df['subir_com_net'])
            / rad3_df['desviament_bajar_instalacions'],
            0)

        rad3_df['pct_rep_baj'] = (rad3_df['pct_rep_baj_1']
                                  * rad3_df['pct_rep_baj_2']
                                  * rad3_df['pct_rep_baj_3'])

        # Desviament ponderat segons pes
        rad3_df['desviament_instalacio_apantallat_subir'] = (rad3_df['pct_rep_sub']
                                                             * rad3_df['subir'])

        rad3_df['desviament_instalacio_apantallat_bajar'] = (rad3_df['pct_rep_baj']
                                                             * rad3_df['bajar'])

        rad3_df['preu_rad3_apantallat'] = ((rad3_df['desviament_instalacio_apantallat_subir']
                                            + rad3_df['desviament_instalacio_apantallat_bajar'])
                                           * rad3_df['preu_rad3'])

        postfix = ('%s_%s' % (self.data_inici.strftime(
            "%Y%m%d"), self.data_final.strftime("%Y%m%d")))

        if is_isp15:
            rad3 = ComponentQH(self.data_inici)
            if len(rad3_curve):
                rad3_curve = sorted(rad3_curve, key=lambda d: d['timestamp'])
                rad3 = self.get_componentQH_from_dict_list(
                    rad3_curve, self.data_inici, version=rad3_version, magn='precio'
                )
        else:
            rad3 = Component(self.data_inici)
            if len(rad3_curve):
                rad3_curve = sorted(rad3_curve, key=lambda d: d['timestamp'])
                rad3 = self.get_component_from_dict_list(
                    rad3_curve, self.data_inici, version=rad3_version, magn='precio'
                )

        audit_keys = self.get_available_audit_coefs_srad3()
        for key in self.conf.get('audit', []):
            if key in audit_keys:
                if key not in self.audit_data.keys():
                    self.audit_data[key] = []
                var_name = audit_keys[key]
                com = locals()[var_name]
                if com is None:
                    continue
                self.audit_data[key].extend(
                    com.get_audit_data(start=self.data_inici.day)
                )

        return rad3_df


TARIFES = {
    'Representa': RepresentaSom,
}
