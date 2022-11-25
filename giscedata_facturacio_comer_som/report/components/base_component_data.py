# -*- coding: utf-8 -*-

class BaseComponentData():
    def __init__(self):
        pass

    def set_data(self, pol):
        self.pol = pol

    def is_visible(self):
        return True

    def get_data(self):
        return {
            'is_visible': self.is_visible()
        }
