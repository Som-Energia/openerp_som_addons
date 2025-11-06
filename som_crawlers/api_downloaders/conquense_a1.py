# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_A1(_config)


class Conquense_A1(Conquense):
    name = 'conquense_a1'
    process = 'A1'
