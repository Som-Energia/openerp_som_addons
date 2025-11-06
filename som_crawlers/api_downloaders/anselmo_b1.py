# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config):
    return Anselmo_B1(_config)


class Anselmo_B1(Anselmo):
    name = 'anselmo_b1'
    process = 'B1'
