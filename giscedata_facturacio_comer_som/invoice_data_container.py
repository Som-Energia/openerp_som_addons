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

    @staticmethod
    def _component_class_name(component_name):
        parts = component_name.split('_')
        ComponentName = u''.join([part.title() for part in parts])
        return u"Component" + ComponentName + u"Data"

    @staticmethod
    def factory_data_generator(component_name):
        exec(u"from report.components."+component_name+u" import "+component_name+u";generator = "+component_name+u"."+SmartInvoiceDataContainer._component_class_name(component_name)+u"()")
        return generator

    def __getattr__(self, key):
        if key not in self.data:
            data_generator = SmartInvoiceDataContainer.factory_data_generator(key)
            data_generator.set_data(self.factura, self.polissa)
            data = data_generator.get_data()
            self.data[key] = ns(data)

        return self.data[key]
