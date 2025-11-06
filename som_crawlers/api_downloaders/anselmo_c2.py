# -*- coding: utf-8 -*-
from som_crawlers.api_downloaders.anselmo import Anselmo


def instance(_config):
    return Anselmo_C2(_config)


class Anselmo_C2(Anselmo):
    name = 'anselmo_c2'
    process = 'C2'
