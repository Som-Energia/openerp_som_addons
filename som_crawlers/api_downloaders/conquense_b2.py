# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_B2(_config)


class Conquense_B2(Conquense):
    name = 'conquense_b2'
    process = 'B2'
