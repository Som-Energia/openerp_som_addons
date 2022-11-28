# -*- coding: utf-8 -*-

class BaseComponentData():
    def __init__(self):
        pass

    def te_autoconsum(self):
        ctxt = {'date': self.fact.data_final }
        return self.pol.te_autoconsum(amb_o_sense_excedents=2, context=ctxt)

    def set_data(self, cursor, uid, fact, pol, cont, report):
        self.cursor = cursor
        self.uid = uid
        self.fact = fact
        self.pol = pol
        self.container = cont
        self.report = report

    def is_visible(self):
        return True

    def get_data(self):
        return {
            'is_visible': self.is_visible()
        }
