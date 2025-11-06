# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_D1(_config)


class Conquense_D1(Conquense):
    name = 'conquense_d1'
    process = 'D1'
