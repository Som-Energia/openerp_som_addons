# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_M2(_config)


class Conquense_M2(Conquense):
    name = 'conquense_m2'
    process = 'M2'
