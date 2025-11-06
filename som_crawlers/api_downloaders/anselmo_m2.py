# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config):
    return Anselmo_M2(_config)


class Anselmo_M2(Anselmo):
    name = 'anselmo_m2'
    process = 'M2'
