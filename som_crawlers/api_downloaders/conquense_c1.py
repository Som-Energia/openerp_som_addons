# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_C1(_config)


class Conquense_C1(Conquense):
    name = 'conquense_c1'
    process = 'C1'
