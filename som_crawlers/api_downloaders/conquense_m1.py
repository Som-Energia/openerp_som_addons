# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_M1(_config)


class Conquense_M1(Conquense):
    name = 'conquense_m1'
    process = 'M1'
