# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_B1(_config)


class Conquense_B1(Conquense):
    name = 'conquense_b1'
    process = 'B1'
