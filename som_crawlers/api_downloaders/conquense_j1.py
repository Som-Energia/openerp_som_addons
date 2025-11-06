# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_J1(_config)


class Conquense_J1(Conquense):
    name = 'conquense_j1'
    process = 'J1'
