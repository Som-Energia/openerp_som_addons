# -*- coding: utf-8 -*-
from osv import osv
from tools.translate import _
from tools import config

from libfacturacioatr.pool.tarifes import *
from libfacturacioatr.pool import REECoeficientsNotFound
from enerdata.datetime.holidays import get_holidays
from datetime import datetime

import logging

logger = logging.getLogger('openerp.' + __name__)


class GiscedataNextDaysEnergyPrice(osv.osv):
    _inherit = 'giscedata.next.days.energy.price'

    def get_monthly_price_baleares(self, cursor, uid, tarifa, data_inici, day=None, context=None):
        """
                    Returns a list with the price for every month hour
                    and the maturity of de prmdiari according to baleares phf calc.
                    :param cursor: OpenERP DB Cursor
                    :param uid: OpenERP User ID
                    :param tarifa: Dict with tarif name and tarif id {'name': '2.0TD', 'id': 12}
                    :param data_inici: str first day of the month to calculate price ('2023-02-15')
                    :param day: str day of wich we want the price ('2023-02-15')
                    :param context: OpenERP Current Context
                    :return: list, str list with the prices for each day
                    and str with the maturity of the prmdiari
                """
        if context is None:
            context = {}

        required_components = ['fe', 'imu', 'atr', 'pc', 'k', 'd']

        # OBJ declaration
        tarifa_obj = self.pool.get('giscedata.polissa.tarifa')
        imd_obj = self.pool.get('ir.model.data')
        pricelist_obj = self.pool.get('product.pricelist')
        periode_obj = self.pool.get('giscedata.polissa.tarifa.periodes')
        facturador_obj = self.pool.get('giscedata.facturacio.facturador')
        config_obj = self.pool.get('res.config')
        esios_token = config.get('esios_token', '')

        # PRPARE DATES
        ctx = {'date': data_inici}
        data_inici_dt = datetime.strptime(data_inici, '%Y-%m-%d')
        num_days = calendar.monthrange(data_inici_dt.year, data_inici_dt.month)[1]  # noqa:F405
        data_final_dt = datetime(
            data_inici_dt.year, data_inici_dt.month, num_days
        ).date()
        data_final = datetime.strftime(data_final_dt, '%Y-%m-%d')
        ym = '%4d%02d' % (data_inici_dt.year, data_inici_dt.month)

        # VERSIONS DEFINITON
        te_pl = pricelist_obj.search(cursor, uid, [('name', '=', 'TARIFAS ELECTRICIDAD')])[0]
        te = tarifa_obj.get_periodes_preus(cursor, uid, tarifa['id'], 'te', te_pl, context=ctx)
        periode_ids = periode_obj.search(cursor, uid, [('tarifa', '=', tarifa['id']),
                                                       ('tipus', '=', 'te')], context=ctx)
        for periode in periode_obj.browse(cursor, uid, periode_ids, context=ctx):
            if periode.agrupat_amb:
                prod = periode.agrupat_amb.product_id.id
            else:
                prod = periode.product_id.id
        versions = {
            data_inici: {
                'atr': te,
            }
        }
        # CONFIGURATION
        config_data = eval(config_obj.get(cursor, uid, 'custom_component_pricelist_id', '{}'))
        imu_pl = config_data.get('imu', False)
        om_pl = config_data.get('om', False)
        fe_pl = config_data.get('fe', False)

        # MARGIN PRICELIST OBTENTION
        pl_config_data = eval(config_obj.get(cursor, uid, 'tarifa_acces_to_pl_mapeig_b', '{}'))
        # TODO: Veure com ho fem per balears i canaries
        margins_pl = pl_config_data.get(tarifa['name'])

        # NON-VARIABLE COMPONENTS PRODUCT OBTENTION
        if margins_pl:
            # K
            k_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_factor_k'
            )[1]
            k = pricelist_obj.price_get(
                cursor, uid, [margins_pl], k_item, 1, context=ctx)[margins_pl]
            versions[data_inici].update({'k': k})
            # D
            d_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_desvios'
            )[1]
            d = pricelist_obj.price_get(
                cursor, uid, [margins_pl], d_item, 1, context=ctx)[margins_pl]
            versions[data_inici].update({'d': d})
            # GDOS
            gdos_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada_som', 'product_gdos_som'
            )[1]
            gdos = pricelist_obj.price_get(
                cursor, uid, [margins_pl], gdos_item, 1, context=ctx)[margins_pl]
            versions[data_inici].update({'gdos': gdos})
            # Factor DSV
            dsv_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada_som', 'product_factor_dsv_som'
            )[1]
            factor_dsv = pricelist_obj.price_get(
                cursor, uid, [margins_pl], dsv_item, 1, context=ctx)[margins_pl]
            versions[data_inici].update({'factor_dsv': factor_dsv})
        if imu_pl:
            imu_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_imu'
            )[1]
            imu = pricelist_obj.price_get(cursor, uid, [imu_pl], imu_item, 1, context=ctx)[imu_pl]
            versions[data_inici].update({'imu': imu})
        if fe_pl:
            fe_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_fondo_eficiencia'
            )[1]
            fe = pricelist_obj.price_get(cursor, uid, [fe_pl], fe_item, 1, context=ctx)[fe_pl]
            versions[data_inici].update({'fe': fe})
        if om_pl:
            om_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_omie'
            )[1]
            om = pricelist_obj.price_get(cursor, uid, [om_pl], om_item, 1, context=ctx)[om_pl]
            versions[data_inici].update({'om': om})

        # DECLARATION OF THE CURRENT TARIF
        TariffClass = self.get_tarifa_class(cursor, uid, tarifa['name'])
        holidays = list(set(get_holidays(data_inici_dt.year)))
        Tarifa = TariffClass({}, {}, data_inici, data_final, versions=versions,
                             holidays=holidays, geom_zone='2')

        # COMPONENTS
        postfix = '%s_%s' % (data_inici.replace("-", ""), data_final.replace("-", ""))
        filename = 'SphdemDD_BALEARES'
        sphdem = SphdemDD_BALEARES('A1_%(filename)s_%(postfix)s' % locals(), esios_token)  # noqa: F405, E501 [€/MWh]

        filename = 'Sprpcap{}_{}'.format(Tarifa.code.replace('.', ''), 'BALEARES')
        classname = globals()[filename]
        pc3_ree = classname('A1_%(filename)s_%(postfix)s' % locals(), esios_token)  # noqa: F405, E501 [€/MWh]
        si = SIFree('A1_sifree_%(postfix)s' % locals(), esios_token)  # noqa: F405 [€/MWh]
        ree = Tarifa.get_coeficient_component(data_inici_dt, 'om')  # [€/MWh]
        perdfname = Tarifa.perdclass.name
        perdues = Tarifa.perdclass('A1_%(perdfname)s_%(postfix)s' % locals(), esios_token)  # [%]

        # Desvios
        scdsvdem = Scdsvdem('C2_Scdsvdem_%(postfix)s' % locals())  # noqa: F405 [€/MWh]
        factor_dsv = self.get_coeficient_component(data_inici_dt, 'factor_dsv')  # [%]
        dsv = scdsvdem * (factor_dsv * 0.01)

        # NON-VARIABLE COMPONENTS PRICE OBTENTION
        fe = Tarifa.get_coeficient_component(data_inici_dt, 'fe')  # [€/MWh]
        imu = Tarifa.get_coeficient_component(data_inici_dt, 'imu')  # [%]
        pa = Tarifa.get_peaje_component(data_inici_dt, holidays)  # [€/kWh]
        k = Tarifa.get_coeficient_component(data_inici_dt, 'k')  # [€/kWh]
        d = Tarifa.get_coeficient_component(data_inici_dt, 'd')  # [€/kWh]
        gdos = self.get_coeficient_component(data_inici_dt, 'gdos')  # [€/MWh]

        A = ((sphdem + pc3_ree + dsv + ree + gdos) * 0.001)
        B = (1 + (perdues * 0.01))
        C = A * B
        D = (fe * 0.001) + k + d
        E = C + D
        F = E * (1 + (imu * 0.01))
        G = F + pa

        # RESULT
        period_prices = G
        price_res = period_prices.matrix
        maturity_res = sphdem.file_version
        calculation_date = datetime.today().strftime("%Y-%m-%d")
        res = {
            'price': price_res,
            'maturity': maturity_res,
            'prmdiari': sphdem.matrix,
        }
        return res

    def get_monthly_price_canaries(self, cursor, uid, tarifa, data_inici, day=None, context=None):
        """
                    Returns a list with the price for every month hour
                    and the maturity of de prmdiari according to baleares phf calc.
                    :param cursor: OpenERP DB Cursor
                    :param uid: OpenERP User ID
                    :param tarifa: Dict with tarif name and tarif id {'name': '2.0TD', 'id': 12}
                    :param data_inici: str first day of the month to calculate price ('2023-02-15')
                    :param day: str day of wich we want the price ('2023-02-15')
                    :param context: OpenERP Current Context
                    :return: list, str list with the prices for each day
                    and str with the maturity of the prmdiari
                """
        if context is None:
            context = {}

        required_components = ['fe', 'imu', 'atr', 'pc', 'k', 'd']

        # OBJ declaration
        tarifa_obj = self.pool.get('giscedata.polissa.tarifa')
        imd_obj = self.pool.get('ir.model.data')
        pricelist_obj = self.pool.get('product.pricelist')
        periode_obj = self.pool.get('giscedata.polissa.tarifa.periodes')
        facturador_obj = self.pool.get('giscedata.facturacio.facturador')
        config_obj = self.pool.get('res.config')
        esios_token = config.get('esios_token', '')

        # PRPARE DATES
        ctx = {'date': data_inici}
        data_inici_dt = datetime.strptime(data_inici, '%Y-%m-%d')
        num_days = calendar.monthrange(data_inici_dt.year, data_inici_dt.month)[1]  # noqa: F405
        data_final_dt = datetime(
            data_inici_dt.year, data_inici_dt.month, num_days
        ).date()
        data_final = datetime.strftime(data_final_dt, '%Y-%m-%d')
        ym = '%4d%02d' % (data_inici_dt.year, data_inici_dt.month)

        # VERSIONS DEFINITON
        te_pl = pricelist_obj.search(cursor, uid, [('name', '=', 'TARIFAS ELECTRICIDAD')])[0]
        te = tarifa_obj.get_periodes_preus(cursor, uid, tarifa['id'], 'te', te_pl, context=ctx)
        periode_ids = periode_obj.search(cursor, uid, [('tarifa', '=', tarifa['id']),
                                                       ('tipus', '=', 'te')],
                                         context=ctx)
        for periode in periode_obj.browse(cursor, uid, periode_ids, context=ctx):
            if periode.agrupat_amb:
                prod = periode.agrupat_amb.product_id.id
            else:
                prod = periode.product_id.id
        versions = {
            data_inici: {
                'atr': te,
            }
        }
        # CONFIGURATION
        config_data = eval(config_obj.get(cursor, uid, 'custom_component_pricelist_id', '{}'))
        imu_pl = config_data.get('imu', False)
        om_pl = config_data.get('om', False)
        fe_pl = config_data.get('fe', False)

        # MARGIN PRICELIST OBTENTION
        pl_config_data = eval(config_obj.get(cursor, uid, 'tarifa_acces_to_pl_mapeig_c', '{}'))
        # TODO: Veure com ho fem per balears i canaries
        margins_pl = pl_config_data.get(tarifa['name'])

        # NON-VARIABLE COMPONENTS PRODUCT OBTENTION
        if margins_pl:
            # K
            k_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_factor_k'
            )[1]
            k = pricelist_obj.price_get(
                cursor, uid, [margins_pl], k_item, 1, context=ctx)[margins_pl]
            versions[data_inici].update({'k': k})
            # D
            d_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_desvios'
            )[1]
            d = pricelist_obj.price_get(
                cursor, uid, [margins_pl], d_item, 1, context=ctx)[margins_pl]
            versions[data_inici].update({'d': d})
            # GDOS
            gdos_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada_som', 'product_gdos_som'
            )[1]
            gdos = pricelist_obj.price_get(
                cursor, uid, [margins_pl], gdos_item, 1, context=ctx)[margins_pl]
            versions[data_inici].update({'gdos': gdos})
            # Factor DSV
            dsv_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada_som', 'product_factor_dsv_som'
            )[1]
            factor_dsv = pricelist_obj.price_get(
                cursor, uid, [margins_pl], dsv_item, 1, context=ctx)[margins_pl]
            versions[data_inici].update({'factor_dsv': factor_dsv})
        if imu_pl:
            imu_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_imu'
            )[1]
            imu = pricelist_obj.price_get(cursor, uid, [imu_pl], imu_item, 1, context=ctx)[imu_pl]
            versions[data_inici].update({'imu': imu})
        if fe_pl:
            fe_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_fondo_eficiencia'
            )[1]
            fe = pricelist_obj.price_get(cursor, uid, [fe_pl], fe_item, 1, context=ctx)[fe_pl]
            versions[data_inici].update({'fe': fe})
        if om_pl:
            om_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_omie'
            )[1]
            om = pricelist_obj.price_get(cursor, uid, [om_pl], om_item, 1, context=ctx)[om_pl]
            versions[data_inici].update({'om': om})

        # DECLARATION OF THE CURRENT TARIF
        TariffClass = self.get_tarifa_class(cursor, uid, tarifa['name'])
        holidays = list(set(get_holidays(data_inici_dt.year)))
        Tarifa = TariffClass({}, {}, data_inici, data_final, versions=versions,
                             holidays=holidays, geom_zone='3')

        # COMPONENTS
        postfix = '%s_%s' % (data_inici.replace("-", ""), data_final.replace("-", ""))
        filename = 'SphdemDD_CANARIAS'
        sphdem = SphdemDD_CANARIAS('A1_%(filename)s_%(postfix)s' % locals(), esios_token)  # noqa: F405, E501 [€/MWh]

        # Desvios
        scdsvdem = Scdsvdem('C2_Scdsvdem_%(postfix)s' % locals())  # noqa: F405 [€/MWh]
        factor_dsv = self.get_coeficient_component(data_inici_dt, 'factor_dsv')  # [%]
        dsv = scdsvdem * (factor_dsv * 0.01)

        filename = 'Sprpcap{}_{}'.format(Tarifa.code.replace('.', ''), 'CANARIAS')
        classname = globals()[filename]
        pc3_ree = classname('A1_%(filename)s_%(postfix)s' % locals(), esios_token)  # [€/MWh]
        si = SIFree('A1_sifree_%(postfix)s' % locals(), esios_token)  # noqa: F405 [€/MWh]
        ree = Tarifa.get_coeficient_component(data_inici_dt, 'om')  # [€/MWh]
        perdfname = Tarifa.perdclass.name
        perdues = Tarifa.perdclass('A1_%(perdfname)s_%(postfix)s' % locals(), esios_token)  # [%]

        # NON-VARIABLE COMPONENTS PRICE OBTENTION
        fe = Tarifa.get_coeficient_component(data_inici_dt, 'fe')  # [€/MWh]
        imu = Tarifa.get_coeficient_component(data_inici_dt, 'imu')  # [%]
        pa = Tarifa.get_peaje_component(data_inici_dt, holidays)  # [€/kWh]
        k = Tarifa.get_coeficient_component(data_inici_dt, 'k')  # [€/kWh]
        d = Tarifa.get_coeficient_component(data_inici_dt, 'd')  # [€/kWh]
        gdos = self.get_coeficient_component(data_inici_dt, 'gdos')  # [€/MWh]

        A = ((sphdem + pc3_ree + ree + gdos + dsv) * 0.001)
        B = (1 + (perdues * 0.01))
        C = A * B
        D = (fe * 0.001) + k + d
        E = C + D
        F = E * (1 + (imu * 0.01))
        G = F + pa

        # RESULT
        period_prices = G
        price_res = period_prices.matrix
        maturity_res = sphdem.file_version
        calculation_date = datetime.today().strftime("%Y-%m-%d")
        res = {
            'price': price_res,
            'maturity': maturity_res,
            'prmdiari': sphdem.matrix,
        }
        return res

    def get_monthly_price(self, cursor, uid, tarifa, data_inici, day=None, context=None):  # noqa: C901, E501
        """
                Returns a list with the price for every month hour and the maturity of de prmdiari.
                :param cursor: OpenERP DB Cursor
                :param uid: OpenERP User ID
                :param tarifa: Dict with tarif name and tarif id {'name': '2.0TD', 'id': 12}
                :param data_inici: str first day of the month to calculate price ('2023-02-15')
                :param day: str day of wich we want the price ('2023-02-15')
                :param context: OpenERP Current Context
                :return: list, str list with the prices for each day
                and str with the maturity of the prmdiari
            """

        if context is None:
            context = {}

        required_components = ['omie', 'fe', 'imu', 'atr', 'pc', 'ajom', 'k']

        # OBJ declaration
        tarifa_obj = self.pool.get('giscedata.polissa.tarifa')
        imd_obj = self.pool.get('ir.model.data')
        pricelist_obj = self.pool.get('product.pricelist')
        periode_obj = self.pool.get('giscedata.polissa.tarifa.periodes')
        facturador_obj = self.pool.get('giscedata.facturacio.facturador')
        config_obj = self.pool.get('res.config')
        esios_token = config.get('esios_token', '')

        # PRPARE DATES
        data_inici_dt = datetime.strptime(data_inici, '%Y-%m-%d')
        num_days = calendar.monthrange(data_inici_dt.year, data_inici_dt.month)[1]  # noqa: F405
        data_final_dt = datetime(
            data_inici_dt.year, data_inici_dt.month, num_days
        ).date()
        data_final = datetime.strftime(data_final_dt, '%Y-%m-%d')
        ym = '%4d%02d' % (data_inici_dt.year, data_inici_dt.month)

        # COMPONENTS
        postfix = '%s_%s' % (data_inici.replace("-", ""), data_final.replace("-", ""))
        maturity_res = False
        try:
            prmdiari = Prmdiari('A1_prmdiari_{}'.format(postfix), esios_token)  # noqa: F405
        except REECoeficientsNotFound as e:
            marginal_date = day.replace('-', '')
            marginalpdbc = self.get_marginalpbdc(cursor, uid, marginal_date, context=context)
            if sum(marginalpdbc.matrix[int(datetime.strptime(day, '%Y-%m-%d').day) - 1]) == 0:
                raise Exception(_('El precio para el día {} aún no está disponible.\n').format(day))
            else:
                prmdiari = marginalpdbc
                maturity_res = 'PDBC'
        # DESV
        try:
            csdvbaj = Codsvbaj('C2_codsvbaj_%(postfix)s' % locals(), esios_token)  # noqa: F405, E501 [€/MWh]
            csdvsub = Codsvsub('C2_codsvsub_%(postfix)s' % locals(), esios_token)  # noqa: F405, E501 [€/MWh]
        except REECoeficientsNotFound as e:
            csdvbaj = Component(datetime.strptime(data_inici, "%Y-%m-%d"))  # noqa: F405
            csdvsub = Component(datetime.strptime(data_inici, "%Y-%m-%d"))  # noqa: F405

        # IN CASE OF A SINGLE DAY CALCULATION WE CHECK FOR THE DAY'S PRICE
        if day is not None:
            if sum(prmdiari.matrix[int(datetime.strptime(day, '%Y-%m-%d').day) - 1]) == 0:
                marginal_date = day.replace('-', '')
                marginalpdbc = self.get_marginalpbdc(cursor, uid, marginal_date, context=context)
                if sum(marginalpdbc.matrix[int(datetime.strptime(day, '%Y-%m-%d').day) - 1]) == 0:
                    raise Exception(
                        _('El precio para el día {} aún no está disponible.\n').format(day))
                else:
                    prmdiari = marginalpdbc
                    maturity_res = 'PDBC'

        try:
            # COMPODEM
            compodem = MonthlyCompodem('A1_monthlycompodem_%(postfix)s' % locals(), esios_token)  # noqa: F405, E501
            rad3 = compodem.get_component("RAD3")
            bs3 = compodem.get_component("BS3")
        except REECoeficientsNotFound as e:
            rad3 = Component(datetime.strptime(data_inici, "%Y-%m-%d"))  # noqa: F405
            bs3 = Component(datetime.strptime(data_inici, "%Y-%m-%d"))  # noqa: F405

        try:
            # SOBRECOSTOS
            sobrecostos = Prdemcad('C2_prdemcad_%(postfix)s' % locals(), esios_token)  # noqa: F405
        except REECoeficientsNotFound as e:
            sobrecostos = Component(datetime.strptime(data_inici, "%Y-%m-%d"))  # noqa: F405

        # CONFIGURATION
        config_data = eval(config_obj.get(cursor, uid, 'custom_component_pricelist_id', '{}'))
        ctx = {'date': data_inici}
        imu_pl = config_data.get('imu', False)
        omie_pl = config_data.get('omie', False)
        fe_pl = config_data.get('fe', False)

        # AJOM APLICATION
        aplica_ajom = False
        if ((data_inici_dt.year >= 2022 and data_inici_dt.month >= 6)
                or (data_inici_dt.year == 2023 and data_inici_dt.month < 6)):
            aplica_ajom = True

        # VERSIONS DEFINITON
        pc_pl = pricelist_obj.search(cursor, uid, [('name', '=', 'PAGOS POR CAPACIDAD')])[0]
        te_pl = pricelist_obj.search(cursor, uid, [('name', '=', 'TARIFAS ELECTRICIDAD')])[0]
        te = tarifa_obj.get_periodes_preus(cursor, uid, tarifa['id'], 'te', te_pl, context=ctx)
        pc = {}
        periode_ids = periode_obj.search(cursor, uid, [('tarifa', '=', tarifa['id']),
                                                       ('tipus', '=', 'te')], context=context)
        for periode in periode_obj.browse(cursor, uid, periode_ids, context=context):
            if periode.agrupat_amb:
                prod = periode.agrupat_amb.product_id.id
            else:
                prod = periode.product_id.id
            pc[periode.name] = pricelist_obj.price_get(
                cursor, uid, [pc_pl], prod, 1, context=ctx)[pc_pl]
        versions = {
            data_inici: {
                'pc': pc,
                'atr': te,
            }
        }
        if aplica_ajom:
            if day is None:
                data_final_ajom = data_final
            else:
                data_final_ajom = day
            ajom = facturador_obj.get_ajom_prices_from_omie(
                cursor, uid, data_inici, data_final_ajom)
            versions[data_inici].update({'ajom': ajom})

        # MARGIN PRICELIST OBTENTION
        pl_config_data = eval(config_obj.get(cursor, uid, 'tarifa_acces_to_pl_mapeig', '{}'))
        margins_pl = pl_config_data.get(tarifa['name'])

        # NON-VARIABLE COMPONENTS PRODUCT OBTENTION
        if margins_pl:
            # K
            k_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_factor_k'
            )[1]
            k = pricelist_obj.price_get(
                cursor, uid, [margins_pl], k_item, 1, context=ctx)[margins_pl]
            versions[data_inici].update({'k': k})
            # D
            d_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_desvios'
            )[1]
            d = pricelist_obj.price_get(
                cursor, uid, [margins_pl], d_item, 1, context=ctx)[margins_pl]
            versions[data_inici].update({'d': d})
            # GDOS
            gdos_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada_som', 'product_gdos_som'
            )[1]
            gdos = pricelist_obj.price_get(
                cursor, uid, [margins_pl], gdos_item, 1, context=ctx)[margins_pl]
            versions[data_inici].update({'gdos': gdos})
            # Factor DSV
            dsv_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada_som', 'product_factor_dsv_som'
            )[1]
            factor_dsv = pricelist_obj.price_get(
                cursor, uid, [margins_pl], dsv_item, 1, context=ctx)[margins_pl]
            versions[data_inici].update({'factor_dsv': factor_dsv})
        if imu_pl:
            imu_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_imu'
            )[1]
            imu = pricelist_obj.price_get(cursor, uid, [imu_pl], imu_item, 1, context=ctx)[imu_pl]
            versions[data_inici].update({'imu': imu})

        if omie_pl:
            omie_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_omie'
            )[1]
            omie = pricelist_obj.price_get(
                cursor, uid, [omie_pl], omie_item, 1, context=ctx)[omie_pl]
            versions[data_inici].update({'omie': omie})
        if fe_pl:
            fe_item = imd_obj.get_object_reference(
                cursor, uid, 'giscedata_facturacio_indexada', 'product_fondo_eficiencia'
            )[1]
            fe = pricelist_obj.price_get(cursor, uid, [fe_pl], fe_item, 1, context=ctx)[fe_pl]
            versions[data_inici].update({'fe': fe})

        # DECLARATION OF THE CURRENT TARIF
        TariffClass = self.get_tarifa_class(cursor, uid, tarifa['name'])
        holidays = list(set(get_holidays(data_inici_dt.year)))
        Tarifa = TariffClass({}, {}, data_inici, data_final, versions=versions, holidays=holidays)

        # PERD BY TARIFF
        perdfname = Tarifa.perdclass.name
        perdues = perdues = Tarifa.perdclass(
            'A1_%(perdfname)s_%(ym)s01_%(ym)s%(num_days)s' % locals(), esios_token)

        # NON-VARIABLE COMPONENTS PRICE OBTENTION
        pc3_boe = Tarifa.get_pricexperiod_component(data_inici_dt, 'pc', holidays=holidays)
        imu = Tarifa.get_coeficient_component(data_inici_dt, 'imu')  # [%]
        omie = Tarifa.get_coeficient_component(data_inici_dt, 'omie')
        fe = Tarifa.get_coeficient_component(data_inici_dt, 'fe')
        k = Tarifa.get_coeficient_component(data_inici_dt, 'k')
        d = Tarifa.get_coeficient_component(data_inici_dt, 'd')
        factor_dsv = Tarifa.get_coeficient_component(data_inici_dt, 'factor_dsv')
        gdos = Tarifa.get_coeficient_component(data_inici_dt, 'gdos')
        pa = Tarifa.get_peaje_component(data_inici_dt, holidays)

        dsv = (0.5 * (csdvbaj + csdvsub) + rad3 + bs3) * (factor_dsv * 0.01)

        # PRICE CALCULATION
        A = ((prmdiari + sobrecostos + dsv + gdos + omie) * 0.001) + pc3_boe

        # AJOM APLICATION
        if aplica_ajom:
            ajom = Tarifa.get_coeficient_from_dict(data_inici_dt, 'ajom')
            A += (ajom * 0.001)

        B = (1 + (perdues * 0.01))
        C = A * B
        D = (fe * 0.001) + k + d
        E = C + D
        F = E * (1 + (imu * 0.01))
        G = F + pa

        # RESULT
        period_prices = G
        price_res = period_prices.matrix
        if not maturity_res:
            maturity_res = prmdiari.file_version
        calculation_date = datetime.today().strftime("%Y-%m-%d")
        res = {
            'price': price_res,
            'maturity': maturity_res,
            'prmdiari': prmdiari.matrix,
        }
        return res


GiscedataNextDaysEnergyPrice()
