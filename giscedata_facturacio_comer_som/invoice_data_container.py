# -*- coding: utf-8 -*-
from yamlns import namespace as ns

class SmartInvoiceDataContainer():

    def __init__(self, cursor, uid, report, fact, pol, context):
        self.data = ns({})
        self.cursor = cursor
        self.uid = uid
        self.report = report
        self.factura = fact
        self.polissa = pol
        self.context = context

    def set_old_data(self, data):
        self.data = data

    def factory_data_generator(self, component_name):
        exec("from report.components."+component_name+" import "+component_name+";generator = "+component_name+"."+component_name+"()")
        return generator

    def __getattr__(self, key):
        if key not in self.data:
            data_generator = self.factory_data_generator(key)
            data_generator.set_data(self.polissa)
            data = data_generator.get_data()
            self.data[key] = ns(data)

        return self.data[key]
