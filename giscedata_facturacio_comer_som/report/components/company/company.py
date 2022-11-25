# -*- coding: utf-8 -*-
from .. import base_component_data

class ComponentCompanyData(base_component_data.BaseComponentData):

    def get_data(self):
        data = base_component_data.BaseComponentData.get_data(self)
        """
        returns a dictionary with all required company address data
        """
        data['name'] = self.fact.company_id.partner_id.name
        data['cif'] = self.fact.company_id.partner_id.vat.replace('ES', '')
        data['street'] = self.fact.company_id.partner_id.address[0].street
        data['zip'] = self.fact.company_id.partner_id.address[0].zip
        data['city'] = self.fact.company_id.partner_id.address[0].city
        data['email'] = self.fact.company_id.partner_id.address[0].email
        return data