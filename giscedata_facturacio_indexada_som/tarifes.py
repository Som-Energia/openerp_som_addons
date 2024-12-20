# -*- coding: utf-8 -*-
from libfacturacioatr.pool.tarifes import *
from libfacturacioatr.tarifes import *

EXTRAPENINSULAR_FORMULAS = [
    'phf_calc_balears',
    'phf_calc_canaries',
    'phf_calc_balears_2024',
    'phf_calc_canaries_2024'
]


class TarifaPoolSOM(TarifaPool):

    def get_available_audit_coefs(self):
        """
        changes 'pmd' to 'prmdiari' if 'phf_calc_peninsula' formula is used
        :return: {
            'pmd': 'prmncur',
            'pc3_ree': 'pc3_ree',
            'perdues': 'perdues',
            'phf': 'component',
            'ph': 'G',
            'curve': 'H'
        }
        """
        res = super(TarifaPoolSOM, self).get_available_audit_coefs()
        if '2024' in self.phf_function:
            res['curve'] = 'curve'
            res['curve_qh'] = 'H'
            res['dsv'] = 'dsv'
            res['gdos'] = 'gdos'
            res['pmd'] = 'prmdiari'
            if 'ajom' in res:
                del res['ajom']
            if 'peninsula' in self.phf_function:
                res['prdemcad'] = 'prdemcad'
                res['csdvbaj'] = 'csdvbaj'
                res['csdvsub'] = 'csdvsub'
                res['pc3_boe'] = 'pc3_boe'
                res['peatges'] = 'pa'
                res['fe'] = 'fe'
                res['rad3'] = 'rad3'
                res['bs3'] = 'bs3'
                res['factor_dsv'] = 'factor_dsv'

        if self.phf_function == 'phf_calc_peninsula':
            # only if 'phf_calc_peninsula' formula is used
            res['pmd'] = 'prmdiari'
            del res['pc3_ree']
            res['pc3_boe'] = 'pc3_boe'
            res['pos'] = 'sobrecostes_ree'
            res['peatges'] = 'pa'
            res['omie_ree'] = 'omie'
            res['fe'] = 'fe'
            res['imu'] = 'imu'
            res['k'] = 'k'
            res['d'] = 'd'
            res['si'] = 'si'

        if self.phf_function in EXTRAPENINSULAR_FORMULAS:
            # only if 'phf_calc_peninsula' formula is used
            res['pmd'] = 'sphdem'
            res['pc3_ree'] = 'pc3_ree'
            if 'ajom' in res:
                del res['ajom']

        if self.phf_function == 'phf_calc_esmasa':
            # only if 'phf_calc_esmasa' formula is used
            res['curve'] = 'curve'
            res['curve_qh'] = 'curve_qh'
            res['pmd'] = 'prmdiari'
            del res['pc3_ree']
            res['peatges'] = 'pa'
            res['omie_ree'] = 'omie'
            res['imu'] = 'imu'
            res['k'] = 'k'
            res['d'] = 'd'
            if 'h' in res:
                del res['h']
            res['si'] = 'si'
            res['dsv'] = 'dsv'
            res['prdemcad'] = 'prdemcad'

        return res

    def get_available_audit_coefs_gen(self):
        """
        changes 'pvpc_gen' to 'prmdiari'
        :return: {
            'pvpc_gen': 'prmdiari',
            'curve_gen': 'B',
            'phf_gen': 'component',
        }
        """
        res = super(TarifaPoolSOM, self).get_available_audit_coefs()
        res['pvpc_gen'] = 'prmdiari'
        res['sphdem'] = 'sphdem'
        res['sphauto'] = 'sphauto'
        return res

    def phf_calc_generacio(self, curve, start_date):
        """
        Calcs component PHF as:
        PHF = [PMD]
        :param curve: Component curve
        :param start_date: component start date
        :return: returns a component
        """
        num_days = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = datetime(start_date.year, start_date.month, num_days).date()

        esios_token = self.conf['esios_token']
        holidays = self.conf['holidays']

        # REE
        postfix = ('%s_%s' % (start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")))
        if self.geom_zone == '1' or not self.geom_zone:  # Peninsula
            prmdiari = Prmdiari('C2_prmdiari_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        else:
            # Subsystems are the same for SPHDEM and SPHAUTO
            subsystem = SUBSYSTEMS_SPHDEM[self.geom_zone]

            filename_dem = 'SphdemDD_{}'.format(subsystem)
            classname_dem = globals()[filename_dem]
            sphdem = classname_dem('C2_%(filename_dem)s_%(postfix)s' % locals(), esios_token)  # [€/MWh]

            filename_auto = 'Sphauto_{}'.format(subsystem)
            classname_auto = globals()[filename_auto]
            sphauto = classname_auto('C2_%(filename_auto)s_%(postfix)s' % locals(), esios_token)  # [€/MWh]

            prmdiari = sphdem - sphauto

        A = (prmdiari * 0.001)
        B = curve * 0.001
        component = A * B

        audit_keys = self.get_available_audit_coefs_gen()
        for key in self.conf.get('audit_gen', []):
            if key not in self.audit_data.keys():
                self.audit_data[key] = []
            if key not in self.audit_components.keys():
                self.audit_components[key] = None
            var_name = audit_keys[key]
            com = locals()[var_name]
            self.audit_components[key] = com
            self.audit_data[key].extend(
                com.get_audit_data(start=start_date.day)
            )

        return component

    def phf_calc(self, curve, start_date):
        '''
        Calcs component PHF as:
        PHF = (1 + IMU) * [(PMD + POS + [PC3] + OMIE_REE ) * (1 + Perdidas) +
              K + D + FONDO_EFICIENCIA ] + PA
        :param curve: Component curve
        :param start_date: component start date
        :return: returns a component
        '''
        num_days = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = datetime(
            start_date.year, start_date.month, num_days
        ).date()

        esios_token = self.conf['esios_token']
        holidays = self.conf['holidays']

        # peajes
        pa = self.get_peaje_component(start_date, holidays)
        # Payments by capacity (PC3) BOE
        pc3_boe = self.get_pricexperiod_component(start_date, 'pc', holidays)
        # Contract specific coeficient €/kWh
        k = self.get_coeficient_component(start_date, 'k')
        # Fixed €/kWh
        desvios = self.get_coeficient_component(start_date, 'd')
        # Coste remuneración OMIE REE €/MWh
        omie = self.get_coeficient_component(start_date, 'omie')
        # Fondo de Eficiencia €/MWh
        fe = self.get_coeficient_component(start_date, 'fe')
        # Municipal fee in %
        imu = self.get_coeficient_component(start_date, 'imu')

        # REE
        postfix = ('%s_%s' % (start_date.strftime("%Y%m%d"),
                              end_date.strftime("%Y%m%d")))
        prmncur = Prmncur('C2_prmncur_%(postfix)s' % locals(), esios_token)
        pc3_ree = Prgpncur('C2_prgpncur_%(postfix)s' % locals(), esios_token)

        fname = self.perdclass.name
        perdues = self.perdclass(
            'C2_%(fname)s_%(postfix)s' % locals(), esios_token
        )

        # MAJ RDL 10/2022
        maj_activated = self.conf.get('maj_activated', 0)

        A = (((prmncur - pc3_ree) * 0.001) + pc3_boe + (omie * 0.001))

        # Use AJOM if invoice includes june'22 or later days and variable is activated
        if maj_activated and (
                (start_date.year == 2022 and start_date.month >= 6) or
                (start_date.year == 2023)
        ):
            ajom = self.get_coeficient_from_dict(start_date, 'ajom')
            A += ajom * 0.001
        else:
            ajom = None

        B = (1 + (perdues * 0.01))
        C = A * B
        D = (k + desvios) + (fe * 0.001)
        E = C + D
        F = E * (1 + (imu * 0.01))
        G = F + pa
        H = curve * 0.001
        component = H * G

        audit_keys = self.get_available_audit_coefs()
        for key in self.conf.get('audit', []):
            if key not in self.audit_data.keys():
                self.audit_data[key] = []
            var_name = audit_keys[key]
            com = locals()[var_name]
            if com is None:
                continue
            self.audit_data[key].extend(
                com.get_audit_data(start=start_date.day)
            )

        return component

    def phf_calc_peninsula(self, curve, start_date):
        """
        Calcs component PHF as:
        PHF = (1 + IMU) * [(PMD + PC + POS + OMIE_REE + H) * (1 + Perdidas) + FNEE + K + D] + PA
        :param curve: Component curve
        :param start_date: component start date
        :return: returns a component
        """
        num_days = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = datetime(
            start_date.year, start_date.month, num_days
        ).date()

        esios_token = self.conf['esios_token']
        holidays = self.conf['holidays']

        # peajes
        pa = self.get_peaje_component(start_date, holidays)    # [€/kWh]
        # Payments by capacity (PC3) BOE
        pc3_boe = self.get_pricexperiod_component(start_date, 'pc', holidays)    # [€/kWh]

        # Contract specific coeficients
        k = self.get_coeficient_component(start_date, 'k')  # [€/kWh]
        d = self.get_coeficient_component(start_date, 'd')  # [€/kWh]
        h = self.get_coeficient_component(start_date, 'h')  # [€/kWh]

        # Coste remuneración OMIE REE
        omie = self.get_coeficient_component(start_date, 'omie')  # [€/MWh]
        # Fondo de Eficiencia
        fe = self.get_coeficient_component(start_date, 'fe')  # [€/MWh]
        # Municipal fee
        imu = self.get_coeficient_component(start_date, 'imu')  # [%]

        # REE
        postfix = ('%s_%s' % (start_date.strftime("%Y%m%d"),
                              end_date.strftime("%Y%m%d")))
        prmdiari = Prmdiari('C2_prmdiari_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        si = SI('C2_si_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        fname = self.perdclass.name
        perdues = self.perdclass(
            'C2_%(fname)s_%(postfix)s' % locals(), esios_token
        )

        # Sobrecostes REE
        compodem = MonthlyCompodem('C2_monthlycompodem_%(postfix)s' % locals(), esios_token)
        sobrecostes_ree = (
                compodem.get_component("RT3") + compodem.get_component("RT6") + compodem.get_component("BS3") +
                compodem.get_component("EXD") + compodem.get_component("IN7") + compodem.get_component("CFP") +
                compodem.get_component("BALX") + compodem.get_component("DSV") + compodem.get_component("PS3") +
                compodem.get_component("IN3") + compodem.get_component("CT3")
        )

        if (start_date.year >= 2022 and start_date.month >= 11) or (start_date.year > 2022):
            try:
                srad = SRAD('C2_srad_%(postfix)s' % locals(), esios_token)
            except REECoeficientsNotFound as e:
                srad = 0
            sobrecostes_ree += srad

        # MAJ RDL 10/2022
        maj_activated = self.conf.get('maj_activated', 0)

        A = ((prmdiari + sobrecostes_ree + si) * 0.001) + pc3_boe + (omie * 0.001) + h

        # Use AJOM if invoice includes june'22 or later days and variable is activated
        if maj_activated and (
                (start_date.year == 2022 and start_date.month >= 6) or
                (start_date.year == 2023)
        ):
            ajom = self.get_coeficient_from_dict(start_date, 'ajom')
            A += ajom * 0.001
        else:
            ajom = None

        B = (1 + (perdues * 0.01))
        C = A * B
        D = (fe * 0.001) + k + d
        E = C + D
        F = E * (1 + (imu * 0.01))
        G = F + pa
        H = curve * 0.001
        component = H * G

        audit_keys = self.get_available_audit_coefs()
        for key in self.conf.get('audit', []):
            if key not in self.audit_data.keys():
                self.audit_data[key] = []
            var_name = audit_keys[key]
            com = locals()[var_name]
            if com is None:
                continue
            self.audit_data[key].extend(
                com.get_audit_data(start=start_date.day)
            )

        return component

    def phf_calc_peninsula_2024(self, curve, start_date):
        """
        Calcs component PHF as:
        PHF = (1 + IMU) * [(PMD + PC + SC + DSV + OMIE_REE + GDOs) * (1 + Perdidas) + FNEE + K + D] + PA
        :param curve: Component curve
        :param start_date: component start date
        :return: returns a component
        """
        num_days = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = datetime(
            start_date.year, start_date.month, num_days
        ).date()

        esios_token = self.conf['esios_token']
        holidays = self.conf['holidays']

        # Curva cuarto-horaria
        curve_qh = curve.get_component_qh_divided()
        curve = curve * 0.001

        # peajes
        pa = self.get_peaje_component(start_date, holidays)    # [€/kWh]
        # Payments by capacity (PC3) BOE
        pc3_boe = self.get_pricexperiod_component(start_date, 'pc', holidays)    # [€/kWh]

        # Contract specific coeficients
        k = self.get_coeficient_component(start_date, 'k')  # [€/kWh]
        d = self.get_coeficient_component(start_date, 'd')  # [€/kWh]

        # From pricelist
        factor_dsv = self.get_coeficient_component(start_date, 'factor_dsv')  # [%]
        gdos = self.get_coeficient_component(start_date, 'gdos')  # [€/MWh]

        d = self.get_coeficient_component(start_date, 'd')  # [€/kWh]

        # Coste remuneración OMIE REE
        omie = self.get_coeficient_component(start_date, 'omie')  # [€/MWh]
        # Fondo de Eficiencia
        fe = self.get_coeficient_component(start_date, 'fe')  # [€/MWh]
        # Municipal fee
        imu = self.get_coeficient_component(start_date, 'imu')  # [%]

        # REE
        postfix = ('%s_%s' % (start_date.strftime("%Y%m%d"),
                              end_date.strftime("%Y%m%d")))
        prmdiari = Prmdiari('C2_prmdiari_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        # Pérdidas
        if start_date.year <= 2024 and start_date.month < 12:
            fname = self.perdclass.name
            perdues = self.perdclass('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]
        else:
            fname = self.perdclassqh.name
            perdues = self.perdclassqh('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]

        # Prdemcad
        prdemcad = Prdemcad('C2_prdemcad_%(postfix)s' % locals(), esios_token)  # prdemcad [€/MWh]

        # Componentes Desvios
        if start_date.year <= 2024 and start_date.month < 12:
            csdvbaj = Codsvbaj('C2_codsvbaj_%(postfix)s' % locals(), esios_token)  # [€/MWh]
            csdvsub = Codsvsub('C2_codsvsub_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        else:
            csdvbaj = Codsvbaqh('C2_codsvbaqh_%(postfix)s' % locals(), esios_token)  # [€/MWh]
            csdvsub = Codsvsuqh('C2_codsvsuqh_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        compodem = MonthlyCompodem('C2_monthlycompodem_%(postfix)s' % locals(), esios_token)
        rad3 = compodem.get_component("RAD3")
        bs3 = compodem.get_component("BS3")

        # Let's transform them in ComponentsQH
        # First, which components must be divided by 4
        # (the rest will set same value on each quarter)
        divided_var_names = []
        excluded_var_names = ['curve']

        for key, var in locals().items():
            if (isinstance(var, Component)
                    and not isinstance(var, ComponentQH)
                    and key not in excluded_var_names
            ):
                new_var = self.transform_local_to_qh(var, key, divided_var_names)
                exec('{} = new_var'.format(key))

        # Cálculo Desvios
        dsv = (0.5 * (csdvbaj + csdvsub) + rad3 + bs3) * (factor_dsv * 0.01)

        A = ((prmdiari + prdemcad + dsv + gdos + omie) * 0.001) + pc3_boe
        B = (1 + (perdues * 0.01))
        C = A * B
        D = (fe * 0.001) + k + d
        E = C + D
        F = E * (1 + (imu * 0.01))
        G = F + pa
        H = curve_qh * 0.001
        component = H * G

        # Let's return component as an hourly Component
        component = component.get_component()

        audit_keys = self.get_available_audit_coefs()
        for key in self.conf.get('audit', []):
            if key not in self.audit_data.keys():
                self.audit_data[key] = []
            var_name = audit_keys[key]
            com = locals()[var_name]
            if com is None:
                continue
            self.audit_data[key].extend(
                com.get_audit_data(start=start_date.day)
            )

        return component

    def phf_calc_balears(self, curve, start_date):
        """
        Calcs component PHF as:
        PHF = (1 + IMU) * [(SPHDEM + PC_REE + SI + POS) * (1 + Perdidas) + FNEE + K] + PA + CA
        :param curve: Component curve
        :param start_date: component start date
        :return: returns a component
        """
        num_days = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = datetime(
            start_date.year, start_date.month, num_days
        ).date()

        esios_token = self.conf['esios_token']
        holidays = self.conf['holidays']

        # REE
        # Precio horario demanda aplicable sistema no peninsular
        postfix = ('%s_%s' % (start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")))
        if self.geom_zone is None or self.geom_zone != '2':
            raise ValueError('Geom Zone must be Balear subsystem')
        filename = 'SphdemDD_{}'.format(SUBSYSTEMS_SPHDEM[self.geom_zone])
        classname = globals()[filename]
        sphdem = classname('C2_%(filename)s_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        # Pagos por capacidad
        filename = 'Sprpcap{}_{}'.format(self.code.replace('.', ''), SUBSYSTEMS_SPHDEM[self.geom_zone])
        classname = globals()[filename]
        pc3_ree = classname('C2_%(filename)s_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        # Servicio de Interrumpibilidad
        si = SIFree('C2_sifree_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        # Coeficientes de pérdidas
        self.get_perdclass()
        fname = self.perdclass.name
        perdues = self.perdclass('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]

        # Pricelist and contract
        # Coste remuneración REE
        ree = self.get_coeficient_component(start_date, 'omie')  # [€/MWh]
        # Fondo de Eficiencia
        fe = self.get_coeficient_component(start_date, 'fe')  # [€/MWh]
        # Contract specific coeficients
        k = self.get_coeficient_component(start_date, 'k')  # [€/kWh]
        d = self.get_coeficient_component(start_date, 'd')  # [€/kWh]
        # Municipal fee
        imu = self.get_coeficient_component(start_date, 'imu')  # [%]

        # peajes y cargos
        pa = self.get_peaje_component(start_date, holidays)  # [€/kWh]

        A = ((sphdem + pc3_ree + si + ree) * 0.001)
        B = (1 + (perdues * 0.01))
        C = A * B
        D = (fe * 0.001) + k + d
        E = C + D
        F = E * (1 + (imu * 0.01))
        G = F + pa
        H = curve * 0.001
        component = H * G

        audit_keys = self.get_available_audit_coefs()
        for key in self.conf.get('audit', []):
            if key not in self.audit_data.keys():
                self.audit_data[key] = []
            var_name = audit_keys[key]
            com = locals()[var_name]
            self.audit_data[key].extend(
                com.get_audit_data(start=start_date.day)
            )

        return component

    def phf_calc_balears_2024(self, curve, start_date):
        """
        Calcs component PHF as:
        PHF = (1 + IMU) * [(SPHDEM + PC_REE + POS + DSV + GDOs) * (1 + Perdidas) + FNEE + K + D] + PA + CA
        :param curve: Component curve
        :param start_date: component start date
        :return: returns a component
        """
        num_days = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = datetime(
            start_date.year, start_date.month, num_days
        ).date()

        esios_token = self.conf['esios_token']
        holidays = self.conf['holidays']

        # Curva cuarto-horaria
        curve_qh = curve.get_component_qh_divided()
        curve = curve * 0.001

        # REE
        # Precio horario demanda aplicable sistema no peninsular
        postfix = ('%s_%s' % (start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")))
        if self.geom_zone is None or self.geom_zone != '2':
            raise ValueError('Geom Zone must be Balear subsystem')
        filename = 'SphdemDD_{}'.format(SUBSYSTEMS_SPHDEM[self.geom_zone])
        classname = globals()[filename]
        sphdem = classname('C2_%(filename)s_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        # Pagos por capacidad
        filename = 'Sprpcap{}_{}'.format(self.code.replace('.', ''), SUBSYSTEMS_SPHDEM[self.geom_zone])
        classname = globals()[filename]
        pc3_ree = classname('C2_%(filename)s_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        # Coeficientes de pérdidas
        self.get_perdclass()
        fname = self.perdclass.name

        # Pérdidas
        if start_date.year <= 2024 and start_date.month < 12:
            fname = self.perdclass.name
            perdues = self.perdclass('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]
        else:
            fname = self.perdclassqh.name
            perdues = self.perdclassqh('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]

        # Pricelist and contract

        # From pricelist
        factor_dsv = self.get_coeficient_component(start_date, 'factor_dsv')  # [%]
        gdos = self.get_coeficient_component(start_date, 'gdos')  # [€/MWh]

        # Desvios
        scdsvdem = Scdsvdem('C2_Scdsvdem_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        dsv = scdsvdem * (factor_dsv * 0.01)

        # Coste remuneración REE
        ree = self.get_coeficient_component(start_date, 'omie')  # [€/MWh]
        # Fondo de Eficiencia
        fe = self.get_coeficient_component(start_date, 'fe')  # [€/MWh]
        # Contract specific coeficients
        k = self.get_coeficient_component(start_date, 'k')  # [€/kWh]
        d = self.get_coeficient_component(start_date, 'd')  # [€/kWh]
        # Municipal fee
        imu = self.get_coeficient_component(start_date, 'imu')  # [%]

        # peajes y cargos
        pa = self.get_peaje_component(start_date, holidays)  # [€/kWh]

        # Let's transform them in ComponentsQH
        # First, which components must be divided by 4
        # (the rest will set same value on each quarter)
        divided_var_names = []
        excluded_var_names = ['curve']

        for key, var in locals().items():
            if (isinstance(var, Component)
                    and not isinstance(var, ComponentQH)
                    and key not in excluded_var_names
            ):
                new_var = self.transform_local_to_qh(var, key, divided_var_names)
                exec('{} = new_var'.format(key))

        A = ((sphdem + pc3_ree + dsv + ree + gdos) * 0.001)
        B = (1 + (perdues * 0.01))
        C = A * B
        D = (fe * 0.001) + k + d
        E = C + D
        F = E * (1 + (imu * 0.01))
        G = F + pa
        H = curve_qh * 0.001
        component = H * G

        # Let's return component as an hourly Component
        component = component.get_component()

        audit_keys = self.get_available_audit_coefs()
        for key in self.conf.get('audit', []):
            if key not in self.audit_data.keys():
                self.audit_data[key] = []
            var_name = audit_keys[key]
            com = locals()[var_name]
            self.audit_data[key].extend(
                com.get_audit_data(start=start_date.day)
            )

        return component

    def phf_calc_canaries(self, curve, start_date):
        """
        Calcs component PHF as:
        PHF = (1 + IMU) * [(SPHDEM + PC_REE + SI + POS) * (1 + Perdidas) + FNEE + K] + PA + CA
        :param curve: Component curve
        :param start_date: component start date
        :return: returns a component
        """
        num_days = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = datetime(
            start_date.year, start_date.month, num_days
        ).date()

        esios_token = self.conf['esios_token']
        holidays = self.conf['holidays']

        # REE
        # Precio horario demanda aplicable sistema no peninsular
        postfix = ('%s_%s' % (start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")))
        if self.geom_zone is None or self.geom_zone != '3':
            raise ValueError('Geom Zone must be Canarian subsystem')
        filename = 'SphdemDD_{}'.format(SUBSYSTEMS_SPHDEM[self.geom_zone])
        classname = globals()[filename]
        sphdem = classname('C2_%(filename)s_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        # Pagos por capacidad
        filename = 'Sprpcap{}_{}'.format(self.code.replace('.', ''), SUBSYSTEMS_SPHDEM[self.geom_zone])
        classname = globals()[filename]
        pc3_ree = classname('C2_%(filename)s_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        # Servicio de Interrumpibilidad
        si = SIFree('C2_sifree_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        # Coeficientes de pérdidas
        self.get_perdclass()
        fname = self.perdclass.name
        perdues = self.perdclass('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]

        # Pricelist and contract
        # Coste remuneración REE
        ree = self.get_coeficient_component(start_date, 'omie')  # [€/MWh]
        # Fondo de Eficiencia
        fe = self.get_coeficient_component(start_date, 'fe')  # [€/MWh]
        # Contract specific coeficients
        k = self.get_coeficient_component(start_date, 'k')  # [€/kWh]
        d = self.get_coeficient_component(start_date, 'd')  # [€/kWh]
        # Municipal fee
        imu = self.get_coeficient_component(start_date, 'imu')  # [%]

        # peajes y cargos
        pa = self.get_peaje_component(start_date, holidays)  # [€/kWh]

        A = ((sphdem + pc3_ree + si + ree) * 0.001)
        B = (1 + (perdues * 0.01))
        C = A * B
        D = (fe * 0.001) + k + d
        E = C + D
        F = E * (1 + (imu * 0.01))
        G = F + pa
        H = curve * 0.001
        component = H * G

        audit_keys = self.get_available_audit_coefs()
        for key in self.conf.get('audit', []):
            if key not in self.audit_data.keys():
                self.audit_data[key] = []
            var_name = audit_keys[key]
            com = locals()[var_name]
            self.audit_data[key].extend(
                com.get_audit_data(start=start_date.day)
            )

        return component

    def phf_calc_canaries_2024(self, curve, start_date):
        """
        Calcs component PHF as:
        PHF = (1 + IMU) * [(SPHDEM + PC_REE + POS + DSV + GDOs) * (1 + Perdidas) + FNEE + K + D] + PA + CA
        :param curve: Component curve
        :param start_date: component start date
        :return: returns a component
        """
        num_days = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = datetime(
            start_date.year, start_date.month, num_days
        ).date()

        esios_token = self.conf['esios_token']
        holidays = self.conf['holidays']

        # Curva cuarto-horaria
        curve_qh = curve.get_component_qh_divided()
        curve = curve * 0.001

        # REE
        # Precio horario demanda aplicable sistema no peninsular
        postfix = ('%s_%s' % (start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")))
        if self.geom_zone is None or self.geom_zone != '3':
            raise ValueError('Geom Zone must be Canarian subsystem')
        filename = 'SphdemDD_{}'.format(SUBSYSTEMS_SPHDEM[self.geom_zone])
        classname = globals()[filename]
        sphdem = classname('C2_%(filename)s_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        # Pagos por capacidad
        filename = 'Sprpcap{}_{}'.format(self.code.replace('.', ''), SUBSYSTEMS_SPHDEM[self.geom_zone])
        classname = globals()[filename]
        pc3_ree = classname('C2_%(filename)s_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        # Coeficientes de pérdidas
        self.get_perdclass()
        fname = self.perdclass.name

        # Pérdidas
        if start_date.year <= 2024 and start_date.month < 12:
            fname = self.perdclass.name
            perdues = self.perdclass('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]
        else:
            fname = self.perdclassqh.name
            perdues = self.perdclassqh('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]

        # Pricelist and contract

        # From pricelist
        factor_dsv = self.get_coeficient_component(start_date, 'factor_dsv')  # [%]
        gdos = self.get_coeficient_component(start_date, 'gdos')  # [€/MWh]

        # Desvios
        scdsvdem = Scdsvdem('C2_Scdsvdem_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        dsv = scdsvdem * (factor_dsv * 0.01)

        # Coste remuneración REE
        ree = self.get_coeficient_component(start_date, 'omie')  # [€/MWh]
        # Fondo de Eficiencia
        fe = self.get_coeficient_component(start_date, 'fe')  # [€/MWh]
        # Contract specific coeficients
        k = self.get_coeficient_component(start_date, 'k')  # [€/kWh]
        d = self.get_coeficient_component(start_date, 'd')  # [€/kWh]
        # Municipal fee
        imu = self.get_coeficient_component(start_date, 'imu')  # [%]

        # peajes y cargos
        pa = self.get_peaje_component(start_date, holidays)  # [€/kWh]

        # Let's transform them in ComponentsQH
        # First, which components must be divided by 4
        # (the rest will set same value on each quarter)
        divided_var_names = []
        excluded_var_names = ['curve']

        for key, var in locals().items():
            if (isinstance(var, Component)
                    and not isinstance(var, ComponentQH)
                    and key not in excluded_var_names
            ):
                new_var = self.transform_local_to_qh(var, key, divided_var_names)
                exec('{} = new_var'.format(key))

        A = ((sphdem + pc3_ree + ree + dsv + gdos) * 0.001)
        B = (1 + (perdues * 0.01))
        C = A * B
        D = (fe * 0.001) + k + d
        E = C + D
        F = E * (1 + (imu * 0.01))
        G = F + pa
        H = curve_qh * 0.001
        component = H * G

        # Let's return component as an hourly Component
        component = component.get_component()

        audit_keys = self.get_available_audit_coefs()
        for key in self.conf.get('audit', []):
            if key not in self.audit_data.keys():
                self.audit_data[key] = []
            var_name = audit_keys[key]
            com = locals()[var_name]
            self.audit_data[key].extend(
                com.get_audit_data(start=start_date.day)
            )

        return component

    def phf_calc_esmasa(self, curve, start_date):
        """
        Calcs component PHF as:

        PHF = (1 + IMU) * [(Prm + PMAJ + Pc + CAD + DSV + POsOm + I) * (1 + Perd)] + Ptd + Ca + F

        :param curve: Component curve
        :param start_date: component start date
        :return: returns a component
        """
        num_days = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = datetime(
            start_date.year, start_date.month, num_days
        ).date()

        esios_token = self.conf['esios_token']
        holidays = self.conf['holidays']

        # Curva cuarto-horaria
        curve_qh = curve.get_component_qh_divided()
        curve = curve * 0.001

        # peajes
        pa = self.get_peaje_component(start_date, holidays)    # [€/kWh]
        # Payments by capacity (PC3) BOE
        pc3_boe = self.get_pricexperiod_component(start_date, 'pc', holidays)    # [€/kWh]

        # Contract specific coeficients
        k = self.get_coeficient_component(start_date, 'k')  # [€/kWh]
        d = self.get_coeficient_component(start_date, 'd')  # [€/kWh]

        # Coste remuneración OMIE REE
        omie = self.get_coeficient_component(start_date, 'omie')  # [€/MWh]
        # Fondo de Eficiencia
        fe = self.get_coeficient_component(start_date, 'fe')  # [€/MWh]
        # Municipal fee
        imu = self.get_coeficient_component(start_date, 'imu')  # [%]

        # REE
        postfix = ('%s_%s' % (start_date.strftime("%Y%m%d"),
                              end_date.strftime("%Y%m%d")))
        prmdiari = Prmdiari('C2_prmdiari_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        si = SI('C2_si_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        # Pérdidas
        if start_date.year <= 2024 and start_date.month < 12:
            fname = self.perdclass.name
            perdues = self.perdclass('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]
        else:
            fname = self.perdclassqh.name
            perdues = self.perdclassqh('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]

        # prdemcad file
        prdemcad = Prdemcad('C2_prdemcad_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        # preu del desvío corresponent als NOCUR
        compodem = MonthlyCompodem('C2_monthlycompodem_%(postfix)s' % locals(), esios_token)
        dsv = compodem.get_component("DSV")  # [€/MWh]

        # MAJ RDL 10/2022
        # Use AJOM if invoice includes june'22 or later days and variable is activated
        maj_activated = self.conf.get('maj_activated', 0)
        if maj_activated and (
                (start_date.year == 2022 and start_date.month >= 6) or
                (start_date.year == 2023)
        ):
            ajom = self.get_coeficient_from_dict(start_date, 'ajom')  # [€/MWh]
        else:
            ajom = 0

        # Let's transform them in ComponentsQH
        # First, which components must be divided by 4
        # (the rest will set same value on each quarter)
        divided_var_names = []
        excluded_var_names = ['curve']

        for key, var in locals().items():
            if (isinstance(var, Component)
                    and not isinstance(var, ComponentQH)
                    and key not in excluded_var_names
            ):
                new_var = self.transform_local_to_qh(var, key, divided_var_names)
                exec('{} = new_var'.format(key))

        A = (prmdiari + prdemcad + dsv + omie + si) * 0.001
        A += pc3_boe
        A += ajom * 0.001
        B = A * (1 + (perdues * 0.01))
        C = B * (1 + (imu * 0.01))
        G = C + pa + k + d
        H = curve_qh * 0.001
        component = G * H

        # Let's return component as an hourly Component
        component = component.get_component()

        audit_keys = self.get_available_audit_coefs()
        for key in self.conf.get('audit', []):
            if key not in self.audit_data.keys():
                self.audit_data[key] = []
            var_name = audit_keys[key]
            com = locals()[var_name]
            if com is None:
                continue
            self.audit_data[key].extend(
                com.get_audit_data(start=start_date.day)
            )

        return component

    def get_available_indexed_formulas(self):
        """
        Gets available formulas for indexed invoicing
        :return: {'Indexada': 'phf_calc',
                  'Indexada Península': 'phf_calc_peninsula'}
        """
        return {
            u'Indexada': 'phf_calc',
            u'Indexada Península': 'phf_calc_peninsula',
            u'Indexada Balears': 'phf_calc_balears',
            u'Indexada Canàries': 'phf_calc_canaries',
            u'Indexada ESMASA': 'phf_calc_esmasa',
            u'Indexada Península 2024': 'phf_calc_peninsula_2024',
            u'Indexada Balears 2024': 'phf_calc_balears_2024',
            u'Indexada Canàries 2024': 'phf_calc_canaries_2024',
        }


class Tarifa20TDPoolSOM(TarifaPoolSOM, Tarifa20TDPool):
    pass


class Tarifa30TDPoolSOM(TarifaPoolSOM, Tarifa30TDPool):
    pass


class Tarifa30TDVEPoolSOM(TarifaPoolSOM, Tarifa30TDVEPool):
    pass


class Tarifa61TDPoolSOM(TarifaPoolSOM, Tarifa61TDPool):
    pass


class Tarifa61TDVEPoolSOM(TarifaPoolSOM, Tarifa61TDVEPool):
    pass


class Tarifa62TDPoolSOM(TarifaPoolSOM, Tarifa61TDPool):
    pass


class Tarifa63TDPoolSOM(TarifaPoolSOM, Tarifa63TDPool):
    pass


class Tarifa64TDPoolSOM(TarifaPoolSOM, Tarifa64TDPool):
    pass


class Tarifa20APoolSOM(TarifaPoolSOM, Tarifa20APool):
    pass


class Tarifa20DHAPoolSOM(TarifaPoolSOM, Tarifa20DHAPool):
    pass


class Tarifa21APoolSOM(TarifaPoolSOM, Tarifa21APool):
    pass


class Tarifa21DHAPoolSOM(TarifaPoolSOM, Tarifa21DHAPool):
    pass


class Tarifa30APoolSOM(TarifaPoolSOM, Tarifa30APool):
    pass


class Tarifa31APoolSOM(TarifaPoolSOM, Tarifa31APool):
    pass


class Tarifa31ALBPoolSOM(TarifaPoolSOM, Tarifa31ALBPool):
    pass


class Tarifa61APoolSOM(TarifaPoolSOM, Tarifa61APool):
    pass


class Tarifa61BPoolSOM(TarifaPoolSOM, Tarifa61BPool):
    pass


class Tarifa62PoolSOM(TarifaPoolSOM, Tarifa62Pool):
    pass


TARIFFS_FACT = {
    '2.0TD': Tarifa20TDPoolSOM,
    '3.0TD': Tarifa30TDPoolSOM,
    '3.0TDVE': Tarifa30TDVEPoolSOM,
    '6.1TD': Tarifa61TDPoolSOM,
    '6.1TDVE': Tarifa61TDVEPoolSOM,
    '6.2TD': Tarifa62TDPoolSOM,
    '6.3TD': Tarifa63TDPoolSOM,
    '6.4TD': Tarifa64TDPoolSOM,
    '2.0A': Tarifa20APoolSOM,
    '2.0DHA': Tarifa20DHAPoolSOM,
    '2.1A': Tarifa21APoolSOM,
    '2.1DHA': Tarifa21DHAPoolSOM,
    '3.0A': Tarifa30APoolSOM,
    '3.1A': Tarifa31APoolSOM,
    '3.1A LB': Tarifa31ALBPoolSOM,
    '6.1A': Tarifa61APoolSOM,
    '6.1B': Tarifa61BPoolSOM,
    '6.2': Tarifa62PoolSOM,
}
