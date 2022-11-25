# -*- coding: utf-8 -*-
from .. import base_component_data

agreementPartners = {
        'S019753': {'logo': 'logo_S019753.png'},
        'S076331': {'logo': 'logo_S076331.png'},
        }

class ComponentLogoData(base_component_data.BaseComponentData):

    def get_data(self):
        """
        returns a dictionary with all required logo component data
        """
        data = base_component_data.BaseComponentData.get_data(self)
        data['logo'] = 'logo_som.png'
        if self.pol.soci.ref in agreementPartners.keys():
            data['has_agreement_partner'] = True
            data['logo_agreement_partner'] = agreementPartners[self.pol.soci.ref]['logo']
        else:
            data['has_agreement_partner'] = False
        return data