# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_C2(_config)


class Conquense_C2(Conquense):
    name = 'conquense_c2'
    process = 'C2'
