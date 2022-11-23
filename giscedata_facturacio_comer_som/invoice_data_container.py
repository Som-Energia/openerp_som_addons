# -*- coding: utf-8 -*-

class SmartInvoiceDataContainer():

    def __init__(self, cursor, uid, report, fact, pol, context):
        self.data = {}
        self.cursor = cursor
        self.uid = uid
        self.report = report
        self.factura = fact
        self.polissa = pol
        self.context = context

    def set_old_data(self, data):
        self.data = data
    
    def __getattr__(self, key):
        if key in self.data:
            return self.data[key]
        return {}
