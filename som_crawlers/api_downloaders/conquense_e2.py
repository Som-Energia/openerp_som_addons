# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_E2(_config)


class Conquense_E2(Conquense):
    name = 'conquense_e2'
    process = 'E2'
