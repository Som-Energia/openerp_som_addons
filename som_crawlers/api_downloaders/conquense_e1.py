# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_E1(_config)


class Conquense_E1(Conquense):
    name = 'conquense_e1'
    process = 'E1'
