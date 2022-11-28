# -*- coding: utf-8 -*-
from .. import base_component_data

agreementPartners = ['S019753','S076331']

def is_6X(pol):
    return pol.tarifa.codi_ocsum in ('012', '013', '014', '015', '016', '017')

def is_TD(pol):
    return pol.tarifa.codi_ocsum in ('018', '019', '020', '021', '022', '023', '024', '025')

def is_6XTD(pol):
    return pol.tarifa.codi_ocsum in ('020', '021', '022', '023', '025')

def is_indexed(fact):
    return 'Indexada' in fact.llista_preu.name

def te_autoconsum(fact, pol):
    ctxt = {'date': fact.data_final }
    return pol.te_autoconsum(amb_o_sense_excedents=2, context=ctxt)

class ComponentGlobalDataData(base_component_data.BaseComponentData):

    def get_data(self):
        readings = self.container.readings_data

        data = base_component_data.BaseComponentData.get_data(self)
        data['num_periodes'] = len(readings.periodes_a)
        data['is_6x'] = is_6X(self.pol)
        data['is_TD'] = is_TD(self.pol)
        data['is_6xTD'] = is_6XTD(self.pol)
        data['is_indexed'] = is_indexed(self.fact)
        data['te_autoconsum'] = te_autoconsum(self.fact, self.pol)
        data['has_agreement_partner'] = self.pol.soci.ref in agreementPartners
        data['is_energetica'] = self.pol.soci.ref in agreementPartners and self.pol.soci.ref == "S019753"

        return data