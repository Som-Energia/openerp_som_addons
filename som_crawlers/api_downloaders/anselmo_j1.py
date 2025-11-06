# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config):
    return Anselmo_J1(_config)


class Anselmo_J1(Anselmo):
    name = 'anselmo_j1'
    process = 'J1'
