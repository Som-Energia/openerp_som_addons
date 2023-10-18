# -*- coding: utf-8 -*-
from tools.translate import _
from .. import base_component_data
from ..base_component_utils import getYMDdate

def adjust_readings_priority(adjust_readings_list):
    adjust_readings_list = [adjust for adjust in adjust_readings_list if adjust != False]
    if len(adjust_readings_list) == 0:
        return False

    adjust_auto = '98' in adjust_readings_list
    adjust_trTD = '97' in adjust_readings_list
    adjust_deci = '96' in adjust_readings_list
    adjust_remaining = [adjust for adjust in adjust_readings_list if adjust not in ('98', '97', '96')]
    if len(adjust_remaining) > 0:
        return '99'
    if adjust_auto:
        return '98'
    if adjust_trTD:
        return '97'
    return False

def visibility(subs):
    return any([sub['is_visible'] for sub in subs])

def adjust_reason(subs):
    return [sub['adjust_reason'] for sub in subs]

def add_last_visible(item, subs):
    item['last_visible'] = not visibility(subs)
    return item

class ComponentEnergyConsumptionDetailTdData(base_component_data.BaseComponentData):

    def get_data(self):
        global_data = self.container.global_data

        data = base_component_data.BaseComponentData.get_data(self)
        if not global_data.is_TD:
            return data

        adjust_reason = []
        meters = []
        for meter in self.pol.comptadors:
            data = self.get_meter_data(meter)
            if data['is_visible']:
                meters.append(data)

            adjust_reason.append(data['adjust_reason'])

        highest_adjust_reason = adjust_readings_priority(adjust_reason)

        data['meters'] = meters
        data['info'] =  self.get_info_data(highest_adjust_reason)
        return data

    def get_meter_data(self, meter):

        active = self.get_meter_active_data(meter)
        surplus = self.get_meter_surplus_data(meter)
        inductive = self.get_meter_inductive_data(meter)
        capacitive = self.get_meter_capacitive_data(meter)
        maximeter = self.get_meter_maximeter_data(meter)

        data = {
            'name': meter.name,
            'showing_periods': self.container.global_data.matrix_show_periods,
            'active': add_last_visible(active, [surplus, inductive, capacitive, maximeter]),
            'surplus': add_last_visible(surplus, [inductive, capacitive, maximeter]),
            'inductive': add_last_visible(inductive, [capacitive, maximeter]),
            'capacitive': add_last_visible(capacitive, [maximeter]),
            'maximeter': maximeter,
            'is_visible': visibility([active, surplus, inductive, capacitive]),
            'adjust_reason': adjust_readings_priority(adjust_reason([active, surplus, inductive, capacitive, maximeter])),
        }
        return data


    def get_meter_generic_data(self, meter, lectures, title, visible, active):
        data = {
            'showing_periods': self.container.global_data.matrix_show_periods,
            'is_visible': False,
            'title': title,
            'is_active': active,
        }

        adjust_reason = []
        if meter.name in lectures:
            data['is_visible'] = visible
            for reading in lectures[meter.name]:
                data[reading[0]] = {
                    'initial': reading[1],
                    'final': reading[2],
                    'total': reading[3],
                }
                data['initial_date'] = reading[4]
                if 'initial_type' not in data or reading[6] != u'real':
                    data['initial_type'] = reading[6]
                data['final_date'] = reading[5]
                if 'final_type' not in data or reading[7] != u'real':
                    data['final_type'] = reading[7]
                adjust_reason.append(reading[9])

        data['adjust_reason'] = adjust_readings_priority(adjust_reason)
        return data

    def get_meter_active_data(self, meter):
        return self.get_meter_generic_data(
            meter,
            self.container.readings_data.lectures_a,
            _(u"Energia Activa (kWh)"),
            len(self.container.readings_data.lectures_a[meter.name]) > 0 if meter.name in self.container.readings_data.lectures_a else False,
            True
        )

    def get_meter_surplus_data(self, meter):
        return self.get_meter_generic_data(
            meter,
            self.container.readings_data.lectures_g,
            _(u"Energia Excedentària (kWh)"),
            (len(self.container.readings_data.lectures_g[meter.name]) > 0 and self.container.global_data.te_autoconsum_amb_excedents) if meter.name in self.container.readings_data.lectures_g else False,
            False
        )

    def get_meter_generic_reactiva_data(self, meter, lectures, title):
        data = {
            'showing_periods': self.container.global_data.matrix_show_periods,
            'is_visible': False,
            'title': title,
            'adjust_reason': False,
            'is_active': False,
        }
        if meter.name in lectures:
            readings_list = lectures[meter.name]
            for reading in readings_list:
                data['is_visible'] = True,
                data[reading[0]] = {
                    'initial': reading[1],
                    'final': reading[2],
                    'total': reading[3],
                }
                data['initial_date'] = reading[4]
                if 'initial_type' not in data or reading[6] != u'real':
                    data['initial_type'] = reading[6]
                data['final_date'] = reading[5]
                if 'final_type' not in data or reading[7] != u'real':
                    data['final_type'] = reading[7]
                if len(reading) == 9 and reading[8] != 0.0:
                    data['has_adjust'] = True

        return data

    def get_meter_inductive_data(self, meter):
        return self.get_meter_generic_reactiva_data(
            meter,
            self.container.readings_data.lectures_r,
            _(u"Energia Reactiva Inductiva (kVArh)")
        )

    def get_meter_capacitive_data(self, meter):
        return self.get_meter_generic_reactiva_data(
            meter,
            self.container.readings_data.lectures_c,
            _(u"Energia Reactiva Capacitiva (kVArh)")
        )

    def get_meter_maximeter_data(self, meter):
        global_data = self.container.global_data

        excess_lines = [l for l in self.fact.linia_ids if l.tipus == 'exces_potencia']

        data = {
            'showing_periods': global_data.matrix_show_periods,
            'is_visible': self.pol.facturacio_potencia=='max',
            'title': _(u"Maxímetre (kW)"),
            'adjust_reason': False,
            'is_active': False,
            'is_visible_surplus': len(excess_lines) > 0 and global_data.te_quartihoraria,
        }

        periodes_m = sorted(list(set([lectura.name for lectura in self.fact.lectures_potencia_ids])))

        lectures_m = []
        for lectura in self.fact.lectures_potencia_ids:
            lectures_m.append((lectura.name, lectura.pot_contract, lectura.pot_maximetre ))

        fact_potencia = dict([(p,0) for p in periodes_m])
        for p in [(p.product_id.name, p.quantity) for p in excess_lines]:
            fact_potencia.update({p[0]: max(fact_potencia.get(p[0], 0), p[1])})

        for reading in lectures_m:
            data[reading[0]] = {
                'contracted': reading[1],
                'reading': reading[2],
                'surplus': fact_potencia[reading[0]],
            }
        return data

    def get_info_data(self, adjust_reason):
        dies_factura = (getYMDdate(self.fact.data_final) - getYMDdate(self.fact.data_inici)).days + 1
        diari_factura_actual_eur = self.fact.total_energia / (dies_factura or 1.0)
        diari_factura_actual_kwh = (self.fact.energia_kwh * 1.0) / (dies_factura or 1.0)

        data = {
            'diari_factura_actual_eur': diari_factura_actual_eur,
            'diari_factura_actual_kwh': diari_factura_actual_kwh,
            'dies_factura': dies_factura,
            'lang': self.container.global_data.lang,
            'adjust_reason': adjust_reason,
            'has_web': bool(self.pol.distribuidora.website),
            'web_distri': self.pol.distribuidora.website,
            'distri_name': self.pol.distribuidora.name,
        }
        return data