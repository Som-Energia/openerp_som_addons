# -*- coding: utf-8 -*-
from datetime import datetime
from .. import base_component_data

class ComponentReadingsTableData(base_component_data.BaseComponentData):

    def get_data(self):
        """
        return a dictionary with all readings table component needed data
        """
        readings = self.container.readings_data

        dies_factura = (datetime.strptime(self.fact.data_final, '%Y-%m-%d') - datetime.strptime(self.fact.data_inici, '%Y-%m-%d')).days + 1
        diari_factura_actual_eur = self.fact.total_energia / (dies_factura or 1.0)
        diari_factura_actual_kwh = (self.fact.energia_kwh * 1.0) / (dies_factura or 1.0)

        data = base_component_data.BaseComponentData.get_data(self)
        data['periodes_a'] = readings.periodes_a
        data['lectures_a'] = readings.lectures_a
        data['total_lectures_a'] = readings.total_lectures_a
        data['dies_factura'] = dies_factura
        data['diari_factura_actual_eur'] = diari_factura_actual_eur
        data['diari_factura_actual_kwh'] = diari_factura_actual_kwh
        data['has_autoconsum'] = self.te_autoconsum()

        return data