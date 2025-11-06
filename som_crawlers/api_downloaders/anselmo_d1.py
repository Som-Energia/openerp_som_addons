# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config):
    return Anselmo_D1(_config)


class Anselmo_D1(Anselmo):
    name = 'anselmo_d1'
    process = 'D1'
