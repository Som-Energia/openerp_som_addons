# -*- coding: utf-8 -*-
from libfacturacioatr.pool.tarifes import *
from libfacturacioatr.tarifes import *


class TarifaPoolSOM(TarifaPool):

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

        A = (((prmncur - pc3_ree) * 0.001) + pc3_boe + (omie * 0.001))
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
            self.audit_data[key].extend(
                com.get_audit_data(start=start_date.day)
            )

        return component


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


TARIFFS_FACT = {
    '2.0A': Tarifa20APoolSOM,
    '2.0DHA': Tarifa20DHAPoolSOM,
    '2.1A': Tarifa21APoolSOM,
    '2.1DHA': Tarifa21DHAPoolSOM,
    '3.0A': Tarifa30APoolSOM,
    '3.1A': Tarifa31APoolSOM,
    '3.1A LB': Tarifa31ALBPoolSOM,
    '6.1A': Tarifa61APoolSOM,
    '6.1B': Tarifa61BPoolSOM,
}
