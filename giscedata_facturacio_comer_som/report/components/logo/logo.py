# -*- coding: utf-8 -*-
from .. import base_component_data

class ComponentLogoData(base_component_data.BaseComponentData):

    def get_data(self):
        """
        returns a dictionary with all required logo component data
        """
        global_data = self.container.global_data

        data = base_component_data.BaseComponentData.get_data(self)
        data['logo'] = 'logo_som.png'
        data['has_agreement_partner'] = global_data.has_agreement_partner
        if global_data.has_agreement_partner:
            data['logo_agreement_partner'] = u'logo_' + self.pol.soci.ref + u".png"

        return data