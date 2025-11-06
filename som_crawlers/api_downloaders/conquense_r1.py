# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.conquense import Conquense


def instance(_config):
    return Conquense_R1(_config)


class Conquense_R1(Conquense):
    name = 'conquense_r1'
    process = 'R1'
