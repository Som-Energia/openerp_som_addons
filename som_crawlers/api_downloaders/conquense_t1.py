# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_T1(_config)


class Conquense_T1(Conquense):
    name = 'conquense_t1'
    process = 'T1'
