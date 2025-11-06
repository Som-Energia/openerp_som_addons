# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config):
    return Anselmo_M1(_config)


class Anselmo_M1(Anselmo):
    name = 'anselmo_m1'
    process = 'M1'
