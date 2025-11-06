# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_R0(_config)


class Conquense_R0(Conquense):
    name = 'conquense_r0'
    process = 'R0'
