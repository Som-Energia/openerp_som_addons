# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config):
    return Anselmo_C1(_config)


class Anselmo_C1(Anselmo):
    name = 'anselmo_c1'
    process = 'C1'
