# -*- coding: utf-8 -*-
from libfacturacioatr.pool.tarifes import *
from libfacturacioatr.tarifes import *

import osv.osv

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
            res['curve'] = 'curve_real'
            res['corba_real_qh'] = 'curve_real_qh'
            res['corba_fact'] = 'curve_fact'
            res['corba_qh'] = 'H'
            res['dsv'] = 'dsv'
            res['gdos'] = 'gdos'
            res['pmd'] = 'prmdiari'
            res['k'] = 'k'
            res['d'] = 'd'
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
            res['curve'] = 'curve_real'
            res['corba_real_qh'] = 'curve_real_qh'
            res['corba_fact'] = 'curve_fact'
            res['corba_qh'] = 'H'
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

        if self.phf_function == 'phf_calc_auvi':
            # only if 'phf_calc_auvi' formula is used
            res = {}
            res['curve_auvi'] = 'curve_autocons'
            res['ph_auvi'] = 'G'
            res['pauvi'] = 'pauvi'

        return res

    def get_alter_prmdiari(self):

        # Obtenir el fitxer
        file_path = self.conf['pdbc_path']
        file_name = 'marginalpdbc_%s.1' % date
        marginal_path = file_path + '/' + file_name
        try:
            fdata = open(marginal_path, 'r')
        except:
            raise osv.except_osv('Error', "No se ha encontrado MarginalPDBC para el período {}".format(date))
        csv_reader = csv.reader(fdata, delimiter=';')

        # Formatarlo obtenint dia-hora i preu
        year = int(date[:4])
        month = int(date[4:6])
        comp_start_date = TIMEZONE.normalize(
            TIMEZONE.localize(datetime(year, month, 1) + timedelta(hours=1)))

        # APliquem el preu pel dia
        if comp_start_date.year > 2025 or (comp_start_date.year == 2025 and comp_start_date.month >= 10):
            res = Component(comp_start_date)
        else:
            res = ComponentQH(comp_start_date)
        next(csv_reader)
        for row in csv_reader:
            if row[0] == '*':
                break
            else:
                day = int(row[2])
                hour = int(row[3])
                price = float(row[5].strip())
                res.set(day, hour - 1, price)  # El index que ens arriba com a hora comença a 1
        res.file_version = 'PDBC'
        if isinstance(res, ComponentQH):
            res = res.get_component_mean()
        return res

    def get_component_class(self, component):
        try:
            res = globals()[component]
        except KeyError:
            raise ValueError('Component %s not found' % component)
        return res

    def get_component_with_fallback(self, component, data_inici, data_final, day, fallback=False):

        try:
            component_class = self.get_component_class(component.title())
            start_date = datetime.strptime(data_inici, '%Y-%m-%d')
            postfix = ('%s_%s' % (data_inici, data_final))
            if component == 'prmdiari' and (start_date.year > 2025 or (start_date.year == 2025 and start_date.month >= 10)):
                component_inst = Pmdiario('C2_pmdiario_%(postfix)s' % locals(), self.conf['esios_token'])
            else:
                component_inst = component_class('C2_%(component)s_%(postfix)s' % locals(), self.conf['esios_token'])
            if component == 'prmdiari' and fallback and day:
                if sum(component_inst.matrix[int(datetime.strptime(day, '%Y-%m-%d').day) - 1]) == 0:
                    raise REECoeficientsNotFound('Prmdiari for day %(day)s not found' % locals())
        except REECoeficientsNotFound as e:
            if fallback:
                if component == 'prmdiari':
                    component_inst = self.get_alter_prmdiari()
                else:
                    component_inst = Component(datetime.strptime(data_inici, "%Y-%m-%d"))
            else:
                raise e

        return component_inst

    def get_available_audit_coefs_gen(self):
        """
        changes 'pvpc_gen' to 'prmdiari'
        :return: {
            'pvpc_gen': 'prmdiari',
            'curve_gen': 'B',
            'phf_gen': 'component',
        }
        """
        res = super(TarifaPoolSOM, self).get_available_audit_coefs_gen()
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
        if self.geom_zone == '1' or not self.geom_zone:
            # Precio medio diario
            # A partir de l'1 d'Octubre passa a ser QH
            if start_date.year > 2025 or (start_date.year == 2025 and start_date.month >= 10):
                pmd_qh = Pmdiario('C2_pmdiario_%(postfix)s' % locals(), esios_token)  # [€/MWh]
                prmdiari = pmd_qh.get_component_mean()
            else:
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
        day = False

        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")

        # Comprovem si estem calculant el preu de demà
        preu_dema = self.conf.get('preu_dema', False)
        day = False
        if preu_dema:
            day = self.conf['preu_dema']['day']

        esios_token = self.conf['esios_token']
        holidays = self.conf['holidays']

        # Curva de consumo real
        curve_real = self.get_curve_from_consum_magn(start_date, magn='activa_real')
        curve_real = curve_real * 0.001 # in kWh
        curve_real_qh = curve_real.get_component_qh_interpolated()

        # Curva cuarto-horaria
        curve_qh = curve.get_component_qh_interpolated()
        curve_fact = curve * 0.001 # in kWh

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
        postfix = ('%s_%s' % (start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")))
        prmdiari = self.get_component_with_fallback('prmdiari', start_date_str, end_date_str, day, fallback=preu_dema)  # [€/MWh]

        # Pérdidas
        if start_date.year < 2024 or (start_date.year == 2024 and start_date.month < 12):
            fname = self.perdclass.name
            perdues = self.perdclass('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]
        else:
            fname = self.perdclassqh.name
            perdues = self.perdclassqh('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]

        # Prdemcad
        prdemcad = self.get_component_with_fallback('prdemcad', start_date_str, end_date_str, day, fallback=preu_dema)  # [€/MWh]

        # Componentes Desvios
        if start_date.year < 2024 or (start_date.year == 2024 and start_date.month < 12):
            csdvbaj = self.get_component_with_fallback('csdvbaj', start_date_str, end_date_str, day, fallback=preu_dema)  # [€/MWh]
            csdvsub = self.get_component_with_fallback('csdvsub', start_date_str, end_date_str, day, fallback=preu_dema)  # [€/MWh]
        else:
            csdvbaj = self.get_component_with_fallback('codsvbaqh', start_date_str, end_date_str, day, fallback=preu_dema)  # [€/MWh]
            csdvsub = self.get_component_with_fallback('codsvsuqh', start_date_str, end_date_str, day, fallback=preu_dema)  # [€/MWh]

        # get first version date on version
        first_version = self.conf.get('versions', {}).keys()[0]

        # BS3 format QH from REGANECU
        all_bs3 = self.conf.get('versions', {})[first_version]['bs3qh']
        current_bs3 = [x for x in all_bs3 if x.start_date == start_date]
        bs3 = current_bs3[0]

        # RAD3 format QH from REGANECU
        all_rad3 = self.conf.get('versions', {})[first_version]['rad3qh']
        current_rad3 = [x for x in all_rad3 if x.start_date == start_date]
        rad3 = current_rad3[0]

        # Let's transform them in ComponentsQH
        # First, which components must be divided by 4
        # (the rest will set same value on each quarter)
        divided_var_names = []
        excluded_var_names = ['curve_real', 'curve_fact']

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

        # Curva de consumo real
        curve_real = self.get_curve_from_consum_magn(start_date, magn='activa_real')
        curve_real = curve_real * 0.001 # in kWh
        curve_real_qh = curve_real.get_component_qh_interpolated()

        # Curva cuarto-horaria
        curve_qh = curve.get_component_qh_interpolated()
        curve_fact = curve * 0.001 # in kWh

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
        if start_date.year < 2024 or (start_date.year == 2024 and start_date.month < 12):
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
        excluded_var_names = ['curve_real', 'curve_fact']

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

        # Curva de consumo real
        curve_real = self.get_curve_from_consum_magn(start_date, magn='activa_real')
        curve_real = curve_real * 0.001 # in kWh
        curve_real_qh = curve_real.get_component_qh_interpolated()

        # Curva cuarto-horaria
        curve_qh = curve.get_component_qh_interpolated()
        curve_fact = curve * 0.001 # in kWh

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
        if start_date.year < 2024 or (start_date.year == 2024 and start_date.month < 12):
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
        excluded_var_names = ['curve_real', 'curve_fact']

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

        # Curva de consumo real
        curve_real = self.get_curve_from_consum_magn(start_date, magn='activa_real')
        curve_real = curve_real * 0.001 # in kWh
        curve_real_qh = curve_real.get_component_qh_interpolated()

        # Curva cuarto-horaria
        curve_qh = curve.get_component_qh_interpolated()
        curve_fact = curve * 0.001 # in kWh

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
        postfix = ('%s_%s' % (start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")))

        # Precio medio diario
        # A partir de l'1 d'Octubre passa a ser QH
        if start_date.year > 2025 or (start_date.year == 2025 and start_date.month >= 10):
            prmdiari = Pmdiario('C2_pmdiario_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        else:
            prmdiari = Prmdiari('C2_prmdiari_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        si = SI('C2_si_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        # Pérdidas
        if start_date.year < 2024 or (start_date.year == 2024 and start_date.month < 12):
            fname = self.perdclass.name
            perdues = self.perdclass('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]
        else:
            fname = self.perdclassqh.name
            perdues = self.perdclassqh('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]

        # prdemcad file
        prdemcad = Prdemcad('C2_prdemcad_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        # preu del desvío
        dsv = MeasuredDeviationsFree('C2_mdsvfree_%(postfix)s' % locals(), esios_token) # [€/MWh]

        # MAJ RDL 10/2022
        # Use AJOM if invoice includes june'22 or later days and variable is activated
        maj_activated = self.conf.get('maj_activated', 0)
        if maj_activated and (
                (start_date.year == 2022 and start_date.month >= 6) or
                (start_date.year == 2023)
        ):
            ajom = self.get_coeficient_from_dict(start_date, 'ajom')  # [€/MWh]
        else:
            ajom = None

        # Let's transform them in ComponentsQH
        # First, which components must be divided by 4
        # (the rest will set same value on each quarter)
        divided_var_names = []
        excluded_var_names = ['curve_real', 'curve_fact']

        for key, var in locals().items():
            if (isinstance(var, Component)
                    and not isinstance(var, ComponentQH)
                    and key not in excluded_var_names
            ):
                new_var = self.transform_local_to_qh(var, key, divided_var_names)
                exec('{} = new_var'.format(key))

        A = (prmdiari + prdemcad + dsv + omie + si) * 0.001
        A += pc3_boe
        if ajom is not None:
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
    
    def phf_calc_auvi(self, curve, start_date):
        """
        Fòrmula pels kWh AUVI:
        PHAUVI = 1,015 * [PAUVI + PHM(Perd) + (Pc + Sc + Dsv + GdO + POsOm) (1 + Perd) + FE + F] + PTD + CA
        PHM(Perd) = prmdiari * % perdues.
        """
        num_days = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = datetime(
            start_date.year, start_date.month, num_days
        ).date()

        esios_token = self.conf['esios_token']
        holidays = self.conf['holidays']

        # Guardem la corba d'autoconsumida per l'adjunt
        curve_autocons = curve

        # Curva cuarto-horaria
        curve = self.get_coeficient_component(start_date, 1000)
        curve.get_sub_component(curve_autocons.start_date.day, curve_autocons.end_date.day)
        curve_qh = curve.get_component_qh_interpolated()

        # peajes
        pa = self.get_peaje_component(start_date, holidays)  # [€/kWh]
        # Payments by capacity (PC3) BOE
        pc3_boe = self.get_pricexperiod_component(start_date, 'pc', holidays)  # [€/kWh]

        # From pricelist
        factor_dsv = self.get_coeficient_component(start_date, 'factor_dsv')  # [%]
        gdos = self.get_coeficient_component(start_date, 'gdos')  # [€/MWh]
        pauvi = self.get_coeficient_component(start_date, 'pauvi')  # [€/MWh]
        f = self.get_coeficient_component(start_date, 'k')  # [€/MWh]

        # Coste remuneración OMIE REE
        omie = self.get_coeficient_component(start_date, 'omie')  # [€/MWh]
        # Fondo de Eficiencia
        fe = self.get_coeficient_component(start_date, 'fe')  # [€/MWh]
        # Municipal fee
        imu = self.get_coeficient_component(start_date, 'imu')  # [%]

        # REE
        postfix = ('%s_%s' % (start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")))

        # Precio medio diario
        # A partir de l'1 d'Octubre passa a ser QH
        if start_date.year > 2025 or (start_date.year == 2025 and start_date.month >= 10):
            prmdiari = Pmdiario('C2_pmdiario_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        else:
            prmdiari = Prmdiari('C2_prmdiari_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        # Prdemcad
        prdemcad = Prdemcad('C2_prdemcad_%(postfix)s' % locals(), esios_token)  # [€/MWh]

        # Pérdidas
        if start_date.year <= 2024 or (start_date.year == 2024 and start_date.month < 12):
            fname = self.perdclass.name
            perdues = self.perdclass('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]
        else:
            fname = self.perdclassqh.name
            perdues = self.perdclassqh('C2_%(fname)s_%(postfix)s' % locals(), esios_token)  # [%]

        # Componentes Desvios
        if start_date.year <= 2024 or (start_date.year == 2024 and start_date.month < 12):
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
        divided_var_names = ['curve_autocons']
        excluded_var_names = ['curve']

        for key, var in locals().items():
            if (isinstance(var, Component)
                    and not isinstance(var, ComponentQH)
                    and key not in excluded_var_names
            ):
                new_var = self.transform_local_to_qh(var, key, divided_var_names)
                exec('{} = new_var'.format(key))

        dsv = (0.5 * (csdvbaj + csdvsub) + rad3 + bs3) * (factor_dsv * 0.01)
        phm = prmdiari * (perdues * 0.01)

        A = ((pauvi + phm) * 0.001)
        B = (pc3_boe + (prdemcad + dsv + gdos + omie) * 0.001)
        C = A + B * (1 + perdues * 0.01)
        D = (fe * 0.001) + f
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
            u'Indexada AUVI': 'phf_calc_auvi',
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
